const PAYMENT_MODE_LABELS = {
  especes: "Espèces",
  mobile_money: "Mobile Money",
  soutra_money: "Soutra Money",
  credit_money: "Crédit Money",
  paycard: "Paycard",
  credit: "Crédit (client fidèle)",
  avoir: "Avoir",
};

async function init() {
  requireAuth(["admin", "manager", "caissier"]);
  renderNavbar("/cash");
  await refreshStatus();
  await loadHistory();

  document.getElementById("open-session").addEventListener("click", openSession);
  document.getElementById("close-session").addEventListener("click", closeSession);
}

async function refreshStatus() {
  const session = await apiFetch("/api/cash-sessions/current");
  const box = document.getElementById("session-status");
  const summaryBox = document.getElementById("summary-box");
  if (!session) {
    box.innerHTML = `<span style="color:var(--text-dim)">Aucune session ouverte.</span>`;
    summaryBox.style.display = "none";
    return;
  }

  box.innerHTML = `Session #${session.id} ouverte — fond de caisse initial: ${formatGNF(session.opening_amount)}`;

  const summary = await apiFetch(`/api/cash-sessions/${session.id}/summary`);
  const modes = Object.keys(summary.by_payment_mode);
  document.getElementById("summary-body").innerHTML = modes.length
    ? modes
        .map(
          (mode) =>
            `<tr><td>${PAYMENT_MODE_LABELS[mode] || mode}</td><td>${formatGNF(summary.by_payment_mode[mode])}</td></tr>`
        )
        .join("")
    : `<tr><td colspan="2">Aucune vente enregistrée sur cette session pour l'instant.</td></tr>`;
  summaryBox.style.display = "block";
}

async function loadHistory() {
  const sessions = await apiFetch("/api/cash-sessions");
  document.getElementById("history-body").innerHTML = sessions
    .map(
      (s) => `
      <tr>
        <td>${new Date(s.opened_at).toLocaleString("fr-FR")}</td>
        <td>${formatGNF(s.opening_amount)}</td>
        <td>${s.closing_theoretical !== null ? formatGNF(s.closing_theoretical) : "-"}</td>
        <td>${s.closing_physical !== null ? formatGNF(s.closing_physical) : "-"}</td>
        <td>${s.gap_amount !== null ? formatGNF(s.gap_amount) : "-"}</td>
        <td>${s.status}</td>
        <td>${s.closed_at ? new Date(s.closed_at).toLocaleString("fr-FR") : "-"}</td>
      </tr>`
    )
    .join("");
}

async function openSession() {
  const errorBox = document.getElementById("open-error");
  errorBox.style.display = "none";
  const opening_amount = parseInt(document.getElementById("opening-amount").value || "0", 10);
  try {
    await apiFetch("/api/cash-sessions/open", { method: "POST", body: JSON.stringify({ opening_amount }) });
    await refreshStatus();
    await loadHistory();
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
    await loadHistory();
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.style.display = "block";
  }
}

init();
