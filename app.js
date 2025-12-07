async function loadQueue() {
  const res = await fetch('/api/tickets');
  const rows = await res.json();

  const tbody = document.querySelector('#queueTable tbody');
  if (tbody) {
    tbody.innerHTML = rows.map(r => `
      <tr>
        <td>${r.token || ""}</td>
        <td>${r.name}</td>
        <td>${r.service_type}</td>
        <td>${r.status}</td>
        <td>${r.teller_name || ""}</td>
      </tr>
    `).join("");
  }

  const abody = document.querySelector('#adminQueue tbody');
  if (abody) {
    abody.innerHTML = rows.map(r => `
      <tr>
        <td>${r.token}</td>
        <td>${r.name}</td>
        <td>${r.service_type}</td>
        <td>${r.est_duration_min}</td>
        <td>${r.status}</td>
        <td>${r.teller_name || ""}</td>
      </tr>
    `).join("");
  }
}

async function loadTellers() {
  const res = await fetch('/api/tellers');
  const rows = await res.json();

  const list = document.getElementById('tellersList');
  if (list) {
    list.innerHTML = rows.map(t => `
      <div class="card small">
        <b>${t.name}</b> (ID: ${t.id})<br>
        Skills: ${t.skill}<br>
        Status: <b>${t.status}</b>
      </div>
    `).join("");
  }
}
