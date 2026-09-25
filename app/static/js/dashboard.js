const GOLD_PALETTE = ["#c9a24b", "#8a6f3a", "#5a9a6f", "#c65a4a", "#5a7a9a", "#9a5a8f"];

async function init() {
  requireAuth(["admin", "manager"]);
  renderNavbar("/dashboard");

  await loadTopProducts();
  await loadCategorySales();
  await loadCashierSales();
  await loadForecasts();

  await loadToday();
  setInterval(loadToday, 15000);
}

async function loadToday() {
  try {
    const summary = await apiFetch("/api/stats/today-summary");
    document.getElementById("today-revenue").textContent = formatGNF(summary.revenue_gnf);
    document.getElementById("today-sales-count").textContent = summary.sales_count;
    document.getElementById("today-quotes-count").textContent = `${summary.quotes_created_count} / ${summary.quotes_converted_count}`;
    document.getElementById("today-stock-count").textContent = summary.stock_movements_count;
    const gapEl = document.getElementById("today-cash-gap-count");
    gapEl.textContent = summary.cash_gap_alerts_count;
    gapEl.style.color = summary.cash_gap_alerts_count > 0 ? "#c65a4a" : "";

    const activity = await apiFetch("/api/stats/today-activity");
    const body = document.getElementById("today-activity-body");
    body.innerHTML = activity.length
      ? activity
          .map((item) => {
            const time = new Date(item.created_at).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
            return `<tr><td>${time}</td><td>${item.actor}</td><td>${item.label}</td></tr>`;
          })
          .join("")
      : `<tr><td colspan="3">Aucune activité aujourd'hui pour le moment.</td></tr>`;
  } catch (e) {
    // silencieux : un échec de rafraîchissement ne doit pas casser le reste du tableau de bord
  }
}

async function loadTopProducts() {
  const data = await apiFetch("/api/stats/top-products?days=7");
  new Chart(document.getElementById("top-products-chart"), {
    type: "bar",
    data: {
      labels: data.map((d) => d.name),
      datasets: [{ label: "Quantité vendue", data: data.map((d) => d.qty_sold), backgroundColor: GOLD_PALETTE[0] }],
    },
    options: { plugins: { legend: { display: false } } },
  });
}

async function loadCategorySales() {
  const data = await apiFetch("/api/stats/sales-by-category");
  new Chart(document.getElementById("category-chart"), {
    type: "pie",
    data: {
      labels: data.map((d) => d.category),
      datasets: [{ data: data.map((d) => d.total_gnf), backgroundColor: GOLD_PALETTE }],
    },
  });
}

async function loadCashierSales() {
  const data = await apiFetch("/api/stats/sales-by-cashier");
  new Chart(document.getElementById("cashier-chart"), {
    type: "bar",
    data: {
      labels: data.map((d) => d.cashier),
      datasets: [{ label: "CA (GNF)", data: data.map((d) => d.total_gnf), backgroundColor: GOLD_PALETTE[2] }],
    },
    options: { plugins: { legend: { display: false } } },
  });
}

async function loadForecasts() {
  const revenue = await apiFetch("/api/stats/revenue-forecast");
  document.getElementById("revenue-forecast").textContent =
    revenue.based_on_days > 0
      ? `CA prévu demain : ${formatGNF(revenue.predicted_revenue_gnf)} (basé sur ${revenue.based_on_days} jours d'historique)`
      : "Pas assez d'historique pour une prévision.";

  const stockout = await apiFetch("/api/stats/stockout-forecast");
  const body = document.getElementById("stockout-body");
  body.innerHTML = stockout
    .filter((s) => s.days_remaining !== null)
    .sort((a, b) => a.days_remaining - b.days_remaining)
    .map(
      (s) => `
      <tr style="${s.alert ? "color:#ff9a8a" : ""}">
        <td>${s.name}</td>
        <td>${s.avg_daily_consumption}</td>
        <td>${s.days_remaining} ${s.alert ? "⚠️ Risque de rupture" : ""}</td>
      </tr>`
    )
    .join("");
}

init();
