const GOLD_PALETTE = ["#c9a24b", "#8a6f3a", "#5a9a6f", "#c65a4a", "#5a7a9a", "#9a5a8f"];
let todayProductsChart = null;

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

function pulse(el) {
  el.classList.remove("pulse");
  void el.offsetWidth; // force le reflow pour pouvoir redéclencher l'animation CSS
  el.classList.add("pulse");
}

function animateTileNumber(el, newValue, formatFn = (v) => String(v)) {
  const oldValue = parseInt(el.dataset.rawValue || "0", 10);
  el.dataset.rawValue = newValue;
  if (oldValue === newValue) return;

  const duration = 500;
  const start = performance.now();
  function step(now) {
    const progress = Math.min((now - start) / duration, 1);
    const current = Math.round(oldValue + (newValue - oldValue) * progress);
    el.textContent = formatFn(current);
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
  pulse(el);
}

async function loadToday() {
  try {
    const summary = await apiFetch("/api/stats/today-summary");
    animateTileNumber(document.getElementById("today-revenue"), summary.revenue_gnf, formatGNF);
    animateTileNumber(document.getElementById("today-sales-count"), summary.sales_count);
    animateTileNumber(document.getElementById("today-stock-count"), summary.stock_movements_count);

    const quotesEl = document.getElementById("today-quotes-count");
    const quotesText = `${summary.quotes_created_count} / ${summary.quotes_converted_count}`;
    if (quotesEl.textContent !== quotesText) {
      quotesEl.textContent = quotesText;
      pulse(quotesEl);
    }

    const gapTile = document.getElementById("today-cash-gap-tile");
    gapTile.dataset.accent = summary.cash_gap_alerts_count > 0 ? "danger" : "success";
    animateTileNumber(document.getElementById("today-cash-gap-count"), summary.cash_gap_alerts_count);

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

    await loadTodayProducts();
  } catch (e) {
    // silencieux : un échec de rafraîchissement ne doit pas casser le reste du tableau de bord
  }
}

async function loadTodayProducts() {
  const data = await apiFetch("/api/stats/today-products");
  const canvas = document.getElementById("today-products-chart");
  const emptyMsg = document.getElementById("today-products-empty");

  if (data.length === 0) {
    canvas.style.display = "none";
    emptyMsg.style.display = "block";
    return;
  }
  canvas.style.display = "block";
  emptyMsg.style.display = "none";

  if (todayProductsChart) {
    todayProductsChart.data.labels = data.map((d) => d.name);
    todayProductsChart.data.datasets[0].data = data.map((d) => d.qty_sold);
    todayProductsChart.update();
  } else {
    todayProductsChart = new Chart(canvas, {
      type: "pie",
      data: {
        labels: data.map((d) => d.name),
        datasets: [{ data: data.map((d) => d.qty_sold), backgroundColor: GOLD_PALETTE }],
      },
      options: { animation: { duration: 700, easing: "easeOutQuart" } },
    });
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

  const expiring = await apiFetch("/api/stats/expiry-alerts");
  const expiryBody = document.getElementById("expiry-body");
  expiryBody.innerHTML = expiring
    .sort((a, b) => a.days_left - b.days_left)
    .map(
      (e) => `
      <tr style="${e.days_left <= 3 ? "color:#ff9a8a" : ""}">
        <td>${e.name}</td>
        <td>${e.remaining_units}</td>
        <td>${e.expiry_date}</td>
        <td>${e.days_left} ${e.days_left <= 3 ? "⚠️ Péremption proche" : ""}</td>
      </tr>`
    )
    .join("");
}

init();
