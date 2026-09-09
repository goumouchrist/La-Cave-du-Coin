async function init() {
  requireAuth(["admin", "manager", "caissier"]);
  renderNavbar("/cash");
  await refreshStatus();

  document.getElementById("open-session").addEventListener("click", openSession);
  document.getElementById("close-session").addEventListener("click", closeSession);
}

async function refreshStatus() {
  const session = await apiFetch("/api/cash-sessions/current");
  const box = document.getElementById("session-status");
  if (!session) {
    box.innerHTML = `<span style="color:var(--text-dim)">Aucune session ouverte.</span>`;
  } else {
    box.innerHTML = `Session #${session.id} ouverte — fond de caisse initial: ${formatGNF(session.opening_amount)}`;
  }
}

async function openSession() {
  const errorBox = document.getElementById("open-error");
  errorBox.style.display = "none";
  const opening_amount = parseInt(document.getElementById("opening-amount").value || "0", 10);
  try {
    await apiFetch("/api/cash-sessions/open", { method: "POST", body: JSON.stringify({ opening_amount }) });
    await refreshStatus();
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.style.display = "block";
  }
}

async function closeSession() {
  const errorBox = document.getElementById("close-error");
  const resultBox = document.getElementById("close-result");
  errorBox.style.display = "none";
  resultBox.innerHTML = "";

  const session = await apiFetch("/api/cash-sessions/current");
  if (!session) {
    errorBox.textContent = "Aucune session ouverte à fermer.";
    errorBox.style.display = "block";
    return;
  }

  const closing_physical = parseInt(document.getElementById("closing-physical").value || "0", 10);
  try {
    const closed = await apiFetch(`/api/cash-sessions/${session.id}/close`, {
      method: "POST",
      body: JSON.stringify({ closing_physical }),
    });
    const alertClass = closed.status === "blocked" ? "alert-error" : "alert-success";
    resultBox.innerHTML = `
      <div class="alert ${alertClass}">
        Théorique: ${formatGNF(closed.closing_theoretical)} — Physique: ${formatGNF(closed.closing_physical)} —
        Écart: ${formatGNF(closed.gap_amount)} — Statut: ${closed.status}
        ${closed.status === "blocked" ? "<br/>Écart supérieur au seuil autorisé : validation Manager requise." : ""}
      </div>`;
    await refreshStatus();
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.style.display = "block";
  }
}

init();
