import sqlite3
import os

DB = "sqms.db"

if os.path.exists(DB):
    print("Removing existing", DB)
    os.remove(DB)

conn = sqlite3.connect(DB)
c = conn.cursor()

# ---------------- TABLES ----------------

c.execute("""
CREATE TABLE tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    service_type TEXT,
    est_duration_min INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'waiting',
    assigned_teller_id INTEGER,
    token TEXT
)
""")

c.execute("""
CREATE TABLE tellers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    skill TEXT,
    status TEXT DEFAULT 'idle',
    last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

# ---------------- SEED TELLERS ----------------

tellers = [
    ("Teller A", "deposit,withdraw"),
    ("Teller B", "account,loan"),
    ("Teller C", "deposit,account,withdraw"),
]

c.executemany("INSERT INTO tellers (name, skill) VALUES (?, ?)", tellers)
conn.commit()

print("Seeded tellers.")

# ---------------- SEED SAMPLE TICKETS ----------------

sample_tickets = [
    ("Ali", "deposit", 23, "TKN-001"),
    ("Sara", "account", 25, "TKN-002"),
]

c.executemany(
    "INSERT INTO tickets (name, service_type, est_duration_min, token) VALUES (?, ?, ?, ?)",
    sample_tickets
)
conn.commit()

print("Seeded sample tickets.")
conn.close()
print("DB initialized:", DB)
