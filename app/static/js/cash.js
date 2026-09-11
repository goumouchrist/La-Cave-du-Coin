const PAYMENT_MODE_LABELS = {
  especes: "Espèces",
  mobile_money: "Mobile Money",
  soutra_money: "Soutra Money",
  credit_money: "Crédit Money",
  paycard: "Paycard",
  credit: "Crédit (client fidèle)",
  avoir: "Avoir",
};

const AUTO_REFRESH_INTERVAL_MS = 15000;

async function init() {
  requireAuth(["admin", "manager", "caissier"]);
  renderNavbar("/cash");
  await refreshStatus();
  await loadHistory();

  document.getElementById("open-session").addEventListener("click", openSession);
  document.getElementById("close-session").addEventListener("click", closeSession);

  // La session peut évoluer depuis la page Caisse (autre onglet/collègue) :
  // on rafraîchit périodiquement pour que le suivi reste à jour en temps réel.
  setInterval(refreshStatus, AUTO_REFRESH_INTERVAL_MS);
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

  const movements = await apiFetch(`/api/cash-sessions/${session.id}/cash-movements`);
  document.getElementById("cash-movements-body").innerHTML = movements.length
    ? movements
        .map(
          (m) => `
          <tr>
            <td>${new Date(m.created_at).toLocaleTimeString("fr-FR")}</td>
            <td>${m.transaction_number}</td>
            <td>${formatGNF(m.amount)}</td>
            <td><b>${formatGNF(m.running_total)}</b></td>
          </tr>`
        )
        .join("")
    : `<tr><td colspan="4">Aucune vente en espèces enregistrée sur cette session pour l'instant (fond de caisse initial : ${formatGNF(session.opening_amount)}).</td></tr>`;
}

const CAN_RESOLVE_ROLES = ["manager", "admin", "super_admin"];

async function loadHistory() {
  const auth = getAuth();
  const canResolve = auth && CAN_RESOLVE_ROLES.includes(auth.role);
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
        <td>${resolutionCell(s, canResolve)}</td>
      </tr>`
    )
    .join("");
}

function resolutionCell(session, canResolve) {
  if (session.status === "blocked") {
    return canResolve
      ? `<button class="secondary" onclick="resolveSession(${session.id})">Résoudre</button>`
      : "En attente de validation Manager";
  }
  if (session.resolution_comment) {
    return `Résolu le ${new Date(session.resolved_at).toLocaleString("fr-FR")} : "${session.resolution_comment}"`;
  }
  return "-";
}

async function resolveSession(sessionId) {
  const comment = prompt(
    "Expliquez l'écart constaté (motif obligatoire, 3 caractères minimum) avant de clôturer cette session :"
  );
  if (!comment) return;
  try {
    await apiFetch(`/api/cash-sessions/${sessionId}/resolve`, {
      method: "POST",
      body: JSON.stringify({ comment }),
    });
    await loadHistory();
  } catch (err) {
    alert(err.message);
  }
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
