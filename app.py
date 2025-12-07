from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os
import random
import string

DB = "sqms.db"
app = Flask(__name__, static_folder='static', static_url_path='/static')

# ---------------- UTIL ----------------
def get_conn():
    conn = sqlite3.connect(DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def generate_token():
    return "TKN-" + ''.join(random.choices(string.digits, k=4))

DEFAULT_DURATIONS = {
    "deposit": 23,
    "withdraw": 12,
    "account": 25,
    "loan": 40,
    "inquiry": 8
}

# ---------------- ASSIGN TELLER ----------------
def assign_teller(ticket_id):
    conn = get_conn()
    c = conn.cursor()

    c.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,))
    ticket = c.fetchone()
    if not ticket:
        conn.close()
        return None

    service = ticket["service_type"]

    c.execute("SELECT * FROM tellers")
    tellers = c.fetchall()

    loads = []
    for t in tellers:
        c.execute("""
            SELECT SUM(est_duration_min) AS load
            FROM tickets
            WHERE assigned_teller_id = ? AND status IN ('waiting', 'in_service')
        """, (t["id"],))
        load = c.fetchone()["load"] or 0
        loads.append((t, load))

    # Prefer skilled teller
    skilled = [(t, L) for t, L in loads if service in (t["skill"] or "").split(",")]
    candidates = skilled if skilled else loads

    best, _ = min(candidates, key=lambda x: x[1])

    c.execute("UPDATE tickets SET assigned_teller_id=?, status='waiting' WHERE id=?",
              (best["id"], ticket_id))
    conn.commit()
    conn.close()
    return best["id"]

# ---------------- ROUTES ----------------

@app.route("/")
def home():
    return send_from_directory("static", "customer.html")

@app.route("/teller")
def teller_page():
    return send_from_directory("static", "teller.html")

@app.route("/admin")
def admin_page():
    return send_from_directory("static", "admin.html")

# -------- CREATE TICKET -----------
@app.route("/api/tickets", methods=["POST"])
def create_ticket():
    data = request.json
    name = data.get("name", "Anonymous")
    service = data.get("service_type")

    if not service:
        return jsonify({"error": "service_type required"}), 400

    est = DEFAULT_DURATIONS.get(service, 10)
    token = generate_token()

    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        INSERT INTO tickets (name, service_type, est_duration_min, token)
        VALUES (?, ?, ?, ?)
    """, (name, service, est, token))

    ticket_id = c.lastrowid
    conn.commit()
    conn.close()

    assigned = assign_teller(ticket_id)

    return jsonify({
        "ticket_id": ticket_id,
        "token": token,
        "assigned_teller": assigned
    }), 201

# -------- LIST TICKETS ----------
@app.route("/api/tickets", methods=["GET"])
def list_tickets():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT t.*, tel.name AS teller_name
        FROM tickets t
        LEFT JOIN tellers tel ON tel.id = t.assigned_teller_id
        ORDER BY t.created_at
    """)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(rows)

# -------- TELLER GET NEXT ----------
@app.route("/api/teller/<int:teller_id>/next", methods=["GET"])
def teller_next(teller_id):
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        SELECT * FROM tickets
        WHERE assigned_teller_id=? AND status='waiting'
        ORDER BY created_at LIMIT 1
    """, (teller_id,))
    ticket = c.fetchone()

    if ticket:
        c.execute("UPDATE tickets SET status='in_service' WHERE id=?", (ticket["id"],))
        c.execute("UPDATE tellers SET status='busy' WHERE id=?", (teller_id,))
        conn.commit()
        conn.close()
        return jsonify(dict(ticket))

    conn.close()
    return jsonify({})

# -------- COMPLETE TICKET ----------
@app.route("/api/teller/<int:teller_id>/complete", methods=["POST"])
def teller_complete(teller_id):
    ticket_id = request.json.get("ticket_id")

    conn = get_conn()
    c = conn.cursor()

    c.execute("UPDATE tickets SET status='completed' WHERE id=?", (ticket_id,))
    c.execute("UPDATE tellers SET status='idle' WHERE id=?", (teller_id,))
    conn.commit()

    # Assign next unassigned ticket
    c.execute("""
        SELECT id FROM tickets
        WHERE assigned_teller_id IS NULL AND status='waiting'
    """)
    for r in c.fetchall():
        assign_teller(r["id"])

    conn.close()
    return jsonify({"ok": True})

# -------- LIST TELLERS ----------
@app.route("/api/tellers", methods=["GET"])
def list_tellers():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM tellers")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(rows)

# -------- CREATE TELLER ----------
@app.route("/api/tellers", methods=["POST"])
def create_teller():
    data = request.json
    name = data.get("name")
    skill = data.get("skill", "")
    if not name:
        return jsonify({"error": "name required"}), 400

    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO tellers (name, skill) VALUES (?, ?)", (name, skill))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

# ---------------- RUN ----------------
if __name__ == "__main__":
    if not os.path.exists(DB):
        print("Run db_init.py first!")
    app.run(host="0.0.0.0", port=5000, debug=True)
