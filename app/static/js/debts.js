async function init() {
  requireAuth(["admin", "manager", "caissier"]);
  renderNavbar("/debts");
  await loadDebts();
}

async function loadDebts() {
  const errorBox = document.getElementById("debts-error");
  errorBox.style.display = "none";
  try {
    const debts = await apiFetch("/api/customers/debts");
    renderDebts(debts);
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.style.display = "block";
  }
}

function renderDebts(debts) {
  const body = document.getElementById("debts-body");
  if (debts.length === 0) {
    body.innerHTML = `<tr><td colspan="7">Aucune créance en cours.</td></tr>`;
    return;
  }
  body.innerHTML = debts
    .map(
      (d) => `
      <tr>
        <td>${d.customer.name}</td>
        <td>${d.customer.phone || ""}</td>
        <td>${d.customer.address || ""}</td>
        <td>${formatGNF(d.amount_owed_gnf)}</td>
        <td>${d.oldest_due_date || ""}</td>
        <td>${d.most_recent_sale_at ? new Date(d.most_recent_sale_at).toLocaleDateString("fr-FR") : ""}</td>
        <td>
          <input type="number" min="1" max="${d.amount_owed_gnf}" placeholder="Montant réglé" class="repay-input" data-customer-id="${d.customer.id}" />
          <button class="secondary" onclick="repayDebt(${d.customer.id})">Enregistrer</button>
        </td>
      </tr>`
    )
    .join("");
}

async function repayDebt(customerId) {
  const input = document.querySelector(`.repay-input[data-customer-id="${customerId}"]`);
  const amount = parseInt(input.value || "0", 10);
  if (amount <= 0) return;
  const errorBox = document.getElementById("debts-error");
  errorBox.style.display = "none";
  try {
    await apiFetch(`/api/customers/${customerId}/repay-debt`, {
      method: "POST",
      body: JSON.stringify({ amount }),
    });
    await loadDebts();
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.style.display = "block";
  }
}

init();
