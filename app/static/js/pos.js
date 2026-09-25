const IDENTICAL_ITEMS_CONFIRM_THRESHOLD = 5;

let cart = []; // { product_id, name, prix_vente, qty, quantity_confirmed }
let currentSession = null;
let avoirCustomer = null;
let creditCustomer = null;
let returnSale = null;
let allProducts = [];
let activeQuote = null;

async function init() {
  requireAuth(["admin", "manager", "caissier"]);
  renderNavbar("/pos");

  try {
    currentSession = await apiFetch("/api/cash-sessions/current");
  } catch (e) {
    currentSession = null;
  }
  document.getElementById("no-session").style.display = currentSession ? "none" : "block";

  document.getElementById("barcode-input").addEventListener("keydown", async (e) => {
    if (e.key !== "Enter") return;
    const barcode = e.target.value.trim();
    e.target.value = "";
    if (!barcode) return;
    await scanBarcode(barcode);
  });

  document.getElementById("amount-given").addEventListener("input", updateChange);
  document.getElementById("validate-sale").addEventListener("click", validateSale);
  document.getElementById("create-quote").addEventListener("click", createQuote);
  document.getElementById("load-quote").addEventListener("click", loadQuoteForConversion);
  document.getElementById("quote-number-input").addEventListener("keydown", async (e) => {
    if (e.key !== "Enter") return;
    e.preventDefault();
    await loadQuoteForConversion();
  });
  document.getElementById("convert-quote").addEventListener("click", convertQuote);
  document.getElementById("search-quote").addEventListener("click", searchQuoteByCustomer);
  document.getElementById("quote-search-input").addEventListener("keydown", async (e) => {
    if (e.key !== "Enter") return;
    e.preventDefault();
    await searchQuoteByCustomer();
  });
  document.getElementById("quote-payment-mode").addEventListener("change", () => {
    const mode = document.getElementById("quote-payment-mode").value;
    document.getElementById("quote-credit-fields").style.display = mode === "credit" ? "block" : "none";
  });
  document.getElementById("payment-mode").addEventListener("change", onPaymentModeChange);
  document.getElementById("avoir-lookup").addEventListener("click", lookupAvoirCustomer);
  document.getElementById("credit-lookup").addEventListener("click", lookupCreditCustomer);
  document.getElementById("return-search").addEventListener("click", searchReturnSale);
  document.getElementById("return-transaction").addEventListener("keydown", async (e) => {
    if (e.key !== "Enter") return;
    e.preventDefault();
    await searchReturnSale();
  });
  document.getElementById("return-submit").addEventListener("click", submitReturn);

  renderCart();
  loadQuickProducts();
}

function onPaymentModeChange() {
  const mode = document.getElementById("payment-mode").value;
  document.getElementById("avoir-fields").style.display = mode === "avoir" ? "block" : "none";
  document.getElementById("credit-fields").style.display = mode === "credit" ? "block" : "none";
  if (mode !== "avoir") {
    avoirCustomer = null;
    document.getElementById("avoir-balance").textContent = "";
  }
  if (mode !== "credit") {
    creditCustomer = null;
    document.getElementById("credit-found").textContent = "";
  }
}

async function lookupCreditCustomer() {
  const phone = document.getElementById("credit-phone").value.trim();
  const foundBox = document.getElementById("credit-found");
  creditCustomer = null;
  if (!phone) {
    foundBox.textContent = "Saisissez un numéro de téléphone.";
    return;
  }
  try {
    const results = await apiFetch(`/api/customers/search?phone=${encodeURIComponent(phone)}`);
    if (results.length === 0) {
      foundBox.textContent = "Aucun client existant avec ce numéro : renseignez son nom et son adresse ci-dessous.";
      return;
    }
    creditCustomer = results[0];
    document.getElementById("credit-name").value = creditCustomer.name;
    document.getElementById("credit-address").value = creditCustomer.address || "";
    const owed = creditCustomer.credit_balance_gnf < 0 ? -creditCustomer.credit_balance_gnf : 0;
    foundBox.textContent = `${creditCustomer.name} — dette actuelle : ${formatGNF(owed)}`;
  } catch (err) {
    foundBox.textContent = err.message;
  }
}

async function lookupAvoirCustomer() {
  const phone = document.getElementById("avoir-phone").value.trim();
  const balanceBox = document.getElementById("avoir-balance");
  if (!phone) {
    balanceBox.textContent = "Saisissez un numéro de téléphone.";
    return;
  }
  try {
    const results = await apiFetch(`/api/customers/search?phone=${encodeURIComponent(phone)}`);
    if (results.length === 0) {
      avoirCustomer = null;
      balanceBox.textContent = "Aucun client trouvé avec ce numéro (pas d'avoir disponible).";
      return;
    }
    avoirCustomer = results[0];
    balanceBox.textContent = `${avoirCustomer.name} — solde avoir : ${formatGNF(avoirCustomer.credit_balance_gnf)}`;
  } catch (err) {
    balanceBox.textContent = err.message;
  }
}

async function loadQuickProducts() {
  try {
    const products = await apiFetch("/api/products");
    allProducts = products;
    const box = document.getElementById("quick-products");
    box.innerHTML = products
      .map(
        (p) =>
          `<button onclick='addToCart(${JSON.stringify({ product_id: p.id, name: p.name, prix_vente: p.prix_vente })})'>${p.name} — ${formatGNF(p.prix_vente)}</button>`
      )
      .join("");
  } catch (e) {
    // silencieux : la recherche rapide est un plus, pas bloquant pour la vente au scan
  }
}

async function scanBarcode(barcode) {
  const errorBox = document.getElementById("scan-error");
  errorBox.style.display = "none";
  try {
    const product = await apiFetch("/api/sales/scan", {
      method: "POST",
      body: JSON.stringify({ barcode, action_type: "vente" }),
    });
    if (product.double_scan_alert) {
      if (!confirm(`Double scan détecté pour "${product.name}" en moins de 2s. Confirmer l'ajout ?`)) {
        return;
      }
    }
    addToCart(product);
  } catch (err) {
    errorBox.textContent = err.message === "Not Found" ? "Produit inconnu" : err.message;
    errorBox.style.display = "block";
  }
}

function addToCart(product) {
  let line = cart.find((l) => l.product_id === product.product_id);
  if (!line) {
    line = { product_id: product.product_id, name: product.name, prix_vente: product.prix_vente, qty: 0, quantity_confirmed: false };
    cart.push(line);
  }
  line.qty += 1;
  if (line.qty > IDENTICAL_ITEMS_CONFIRM_THRESHOLD) {
    line.quantity_confirmed = false;
  }
  renderCart();
}

function renderCart() {
  const body = document.getElementById("cart-body");
  body.innerHTML = "";
  let total = 0;

  cart.forEach((line, idx) => {
    const lineTotal = line.qty * line.prix_vente;
    total += lineTotal;
    const needsConfirm = line.qty > IDENTICAL_ITEMS_CONFIRM_THRESHOLD && !line.quantity_confirmed;

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${line.name}${needsConfirm ? ' <span style="color:#c65a4a">(confirmation requise)</span>' : ""}</td>
      <td>
        <button class="secondary" onclick="changeQty(${idx}, -1)">-</button>
        ${line.qty}
        <button class="secondary" onclick="changeQty(${idx}, 1)">+</button>
      </td>
      <td>${formatGNF(line.prix_vente)}</td>
      <td>${formatGNF(lineTotal)}</td>
      <td>
        ${needsConfirm ? `<button onclick="confirmQty(${idx})">Confirmer</button>` : ""}
        <button class="danger" onclick="removeLine(${idx})">X</button>
      </td>
    `;
    body.appendChild(tr);
  });

  document.getElementById("cart-total").textContent = formatGNF(total);
  updateChange();
}

function changeQty(idx, delta) {
  cart[idx].qty = Math.max(0, cart[idx].qty + delta);
  if (cart[idx].qty === 0) {
    cart.splice(idx, 1);
  } else if (cart[idx].qty <= IDENTICAL_ITEMS_CONFIRM_THRESHOLD) {
    cart[idx].quantity_confirmed = false;
  }
  renderCart();
}

function confirmQty(idx) {
  cart[idx].quantity_confirmed = true;
  renderCart();
}

function removeLine(idx) {
  cart.splice(idx, 1);
  renderCart();
}

function cartTotal() {
  return cart.reduce((sum, l) => sum + l.qty * l.prix_vente, 0);
}

function updateChange() {
  const given = parseInt(document.getElementById("amount-given").value || "0", 10);
  const change = Math.max(given - cartTotal(), 0);
  document.getElementById("change-amount").textContent = formatGNF(change);
}

async function validateSale() {
  const resultBox = document.getElementById("sale-result");
  resultBox.innerHTML = "";

  if (!currentSession) {
    resultBox.innerHTML = `<div class="alert alert-error">Aucune session de caisse ouverte.</div>`;
    return;
  }
  if (cart.length === 0) {
    resultBox.innerHTML = `<div class="alert alert-error">Le panier est vide.</div>`;
    return;
  }

  const paymentMode = document.getElementById("payment-mode").value;
  if (paymentMode === "avoir" && !avoirCustomer) {
    resultBox.innerHTML = `<div class="alert alert-error">Recherchez d'abord le client par téléphone pour payer par avoir.</div>`;
    return;
  }

  const amountGiven = parseInt(document.getElementById("amount-given").value || "0", 10);
  const creditName = document.getElementById("credit-name").value.trim();
  if (paymentMode === "credit" && amountGiven < cartTotal() && !creditCustomer && !creditName) {
    resultBox.innerHTML = `<div class="alert alert-error">Montant remis insuffisant : renseignez le client (nom, téléphone, adresse) pour enregistrer le reste dû.</div>`;
    return;
  }

  const payload = {
    cash_session_id: currentSession.id,
    payment_mode: paymentMode,
    amount_given: amountGiven,
    items: cart.map((l) => ({ product_id: l.product_id, qty: l.qty, quantity_confirmed: l.quantity_confirmed })),
    customer_id: paymentMode === "avoir" ? avoirCustomer.id : paymentMode === "credit" && creditCustomer ? creditCustomer.id : null,
    customer_name: paymentMode === "credit" && !creditCustomer ? creditName || null : null,
    customer_phone: paymentMode === "credit" && !creditCustomer ? document.getElementById("credit-phone").value.trim() || null : null,
    customer_address: paymentMode === "credit" && !creditCustomer ? document.getElementById("credit-address").value.trim() || null : null,
    customer_email: document.getElementById("customer-email").value.trim() || null,
    due_date: paymentMode === "credit" ? document.getElementById("credit-due-date").value || null : null,
  };

  try {
    const sale = await apiFetch("/api/sales", { method: "POST", body: JSON.stringify(payload) });
    const dueNotice = sale.remaining_due_gnf > 0
      ? ` Reste dû par le client : ${formatGNF(sale.remaining_due_gnf)}${sale.due_date ? ` (échéance : ${sale.due_date})` : ""}. Voir "Créances clients" pour la relance.`
      : "";
    const emailButton = sale.customer_email
      ? `<button class="secondary" onclick="emailReceipt(${sale.id}, 'email-status-${sale.id}')">Envoyer le reçu par email</button> <span id="email-status-${sale.id}"></span>`
      : "";
    resultBox.innerHTML = `
      <div class="alert alert-success">
        Vente #${sale.transaction_number} enregistrée. Monnaie à rendre : ${formatGNF(sale.change_amount)}.${dueNotice}
        <br /><br />
        <button class="secondary" onclick="openAuthenticatedPdf('/api/sales/${sale.id}/receipt.pdf')">Imprimer le reçu</button>
        ${emailButton}
      </div>
    `;
    cart = [];
    document.getElementById("amount-given").value = 0;
    document.getElementById("customer-email").value = "";
    document.getElementById("credit-name").value = "";
    document.getElementById("credit-phone").value = "";
    document.getElementById("credit-address").value = "";
    document.getElementById("credit-due-date").value = "";
    document.getElementById("credit-found").textContent = "";
    creditCustomer = null;
    renderCart();
  } catch (err) {
    resultBox.innerHTML = `<div class="alert alert-error">${err.message}</div>`;
  }
}

async function createQuote() {
  const resultBox = document.getElementById("quote-result");
  resultBox.innerHTML = "";

  if (cart.length === 0) {
    resultBox.innerHTML = `<div class="alert alert-error">Le panier est vide.</div>`;
    return;
  }

  const customerName = document.getElementById("quote-customer-name").value.trim();
  const customerPhone = document.getElementById("quote-customer-phone").value.trim();
  if (!customerName || !customerPhone) {
    resultBox.innerHTML = `<div class="alert alert-error">Le nom et le téléphone du client sont obligatoires (pour pouvoir retrouver le devis plus tard).</div>`;
    return;
  }

  const payload = {
    items: cart.map((l) => ({ product_id: l.product_id, qty: l.qty, quantity_confirmed: l.quantity_confirmed })),
    customer_name: customerName,
    customer_phone: customerPhone,
  };

  try {
    const quote = await apiFetch("/api/quotes", { method: "POST", body: JSON.stringify(payload) });
    resultBox.innerHTML = `
      <div class="alert alert-success">
        Devis #${quote.quote_number} créé${quote.expires_at ? ` (valable jusqu'au ${quote.expires_at})` : ""}.
        <br /><br />
        <button class="secondary" onclick="openAuthenticatedPdf('/api/quotes/${quote.id}/pdf')">Imprimer le devis</button>
      </div>
    `;
    cart = [];
    document.getElementById("quote-customer-name").value = "";
    document.getElementById("quote-customer-phone").value = "";
    renderCart();
  } catch (err) {
    resultBox.innerHTML = `<div class="alert alert-error">${err.message}</div>`;
  }
}

async function searchQuoteByCustomer() {
  const resultsBox = document.getElementById("quote-search-results");
  resultsBox.innerHTML = "";

  const term = document.getElementById("quote-search-input").value.trim().toLowerCase();
  if (!term) return;

  let quotes;
  try {
    quotes = await apiFetch("/api/quotes");
  } catch (err) {
    resultsBox.innerHTML = `<div class="alert alert-error">${err.message}</div>`;
    return;
  }

  const matches = quotes.filter(
    (q) =>
      q.status === "en_cours" &&
      ((q.customer_name && q.customer_name.toLowerCase().includes(term)) ||
        (q.customer_phone && q.customer_phone.toLowerCase().includes(term)))
  );

  if (matches.length === 0) {
    resultsBox.innerHTML = `<p>Aucun devis en cours trouvé pour "${term}".</p>`;
    return;
  }

  resultsBox.innerHTML = `
    <table>
      <thead><tr><th>Numéro</th><th>Client</th><th>Total</th><th>Créé le</th><th></th></tr></thead>
      <tbody>
        ${matches
          .map(
            (q) => `
          <tr>
            <td>${q.quote_number}</td>
            <td>${q.customer_name || "—"}${q.customer_phone ? ` (${q.customer_phone})` : ""}</td>
            <td>${formatGNF(q.total_amount)}</td>
            <td>${new Date(q.created_at).toLocaleDateString("fr-FR")}</td>
            <td><button class="secondary" onclick="loadQuoteByNumber('${q.quote_number}')">Charger</button></td>
          </tr>`
          )
          .join("")}
      </tbody>
    </table>
  `;
}

async function loadQuoteByNumber(number) {
  document.getElementById("quote-number-input").value = number;
  await loadQuoteForConversion();
}

async function loadQuoteForConversion() {
  const errorBox = document.getElementById("quote-load-error");
  const detailsBox = document.getElementById("quote-details");
  const resultBox = document.getElementById("quote-convert-result");
  errorBox.style.display = "none";
  detailsBox.style.display = "none";
  resultBox.innerHTML = "";
  activeQuote = null;

  const number = document.getElementById("quote-number-input").value.trim();
  if (!number) return;

  try {
    activeQuote = await apiFetch(`/api/quotes/by-number/${encodeURIComponent(number)}`);
  } catch (err) {
    errorBox.textContent = err.message === "Not Found" ? "Aucun devis avec ce numéro" : err.message;
    errorBox.style.display = "block";
    return;
  }

  const productName = (productId) => {
    const p = allProducts.find((x) => x.id === productId);
    return p ? p.name : `Produit #${productId}`;
  };

  const body = document.getElementById("quote-items-body");
  body.innerHTML = activeQuote.items
    .map((item) => {
      const lineTotal = item.qty_units * item.unit_price;
      return `<tr><td>${productName(item.product_id)}</td><td>${item.qty_units}</td><td>${formatGNF(item.unit_price)}</td><td>${formatGNF(lineTotal)}</td></tr>`;
    })
    .join("");
  document.getElementById("quote-total").textContent = formatGNF(activeQuote.total_amount);

  const clientLine = activeQuote.customer_name ? ` — Client : ${activeQuote.customer_name}${activeQuote.customer_phone ? " (" + activeQuote.customer_phone + ")" : ""}` : "";
  const expiryLine = activeQuote.expires_at ? ` — Valable jusqu'au ${activeQuote.expires_at}` : "";
  document.getElementById("quote-info").textContent = `Statut : ${activeQuote.status}${clientLine}${expiryLine}`;

  const convertForm = document.getElementById("quote-convert-form");
  if (activeQuote.status !== "en_cours") {
    convertForm.style.display = "none";
    errorBox.textContent = `Ce devis n'est plus convertible (statut : ${activeQuote.status}).`;
    errorBox.style.display = "block";
  } else {
    convertForm.style.display = "block";
  }

  detailsBox.style.display = "block";
}

async function convertQuote() {
  const resultBox = document.getElementById("quote-convert-result");
  resultBox.innerHTML = "";

  if (!activeQuote) return;

  if (!currentSession) {
    resultBox.innerHTML = `<div class="alert alert-error">Aucune session de caisse ouverte : impossible de convertir un devis en vente.</div>`;
    return;
  }

  const payload = {
    cash_session_id: currentSession.id,
    payment_mode: document.getElementById("quote-payment-mode").value,
    amount_given: parseInt(document.getElementById("quote-amount-given").value || "0", 10),
    customer_email: document.getElementById("quote-customer-email").value.trim() || null,
    due_date: document.getElementById("quote-payment-mode").value === "credit" ? document.getElementById("quote-credit-due-date").value || null : null,
  };

  try {
    const sale = await apiFetch(`/api/quotes/${activeQuote.id}/convert`, { method: "POST", body: JSON.stringify(payload) });
    resultBox.innerHTML = `
      <div class="alert alert-success">
        Devis converti en vente #${sale.transaction_number}. Monnaie à rendre : ${formatGNF(sale.change_amount)}.
        <br /><br />
        <button class="secondary" onclick="openAuthenticatedPdf('/api/sales/${sale.id}/receipt.pdf')">Imprimer le reçu</button>
      </div>
    `;
    document.getElementById("quote-details").style.display = "none";
    document.getElementById("quote-number-input").value = "";
    activeQuote = null;
  } catch (err) {
    resultBox.innerHTML = `<div class="alert alert-error">${err.message}</div>`;
  }
}

async function emailReceipt(saleId, statusElId) {
  const statusEl = document.getElementById(statusElId);
  statusEl.textContent = "Envoi en cours...";
  try {
    await apiFetch(`/api/sales/${saleId}/receipt/email`, { method: "POST", body: JSON.stringify({}) });
    statusEl.textContent = "Reçu envoyé par email ✓";
  } catch (err) {
    statusEl.textContent = "Erreur : " + err.message;
  }
}

async function searchReturnSale() {
  const errorBox = document.getElementById("return-error");
  const detailsBox = document.getElementById("return-details");
  errorBox.style.display = "none";
  detailsBox.style.display = "none";
  returnSale = null;

  const transactionNumber = document.getElementById("return-transaction").value.trim();
  if (!transactionNumber) return;

  try {
    returnSale = await apiFetch(`/api/sales/by-transaction/${encodeURIComponent(transactionNumber)}`);
    if (returnSale.status === "annulee") {
      errorBox.textContent = "Ce ticket est annulé, aucun retour possible.";
      errorBox.style.display = "block";
      returnSale = null;
      return;
    }

    const body = document.getElementById("return-items-body");
    body.innerHTML = returnSale.items
      .map(
        (item) => `
        <tr>
          <td>Produit #${item.product_id}</td>
          <td>${item.qty_units}</td>
          <td><input type="number" min="0" max="${item.qty_units}" value="0" data-sale-item-id="${item.id}" class="return-qty-input" /></td>
        </tr>`
      )
      .join("");
    detailsBox.style.display = "block";
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.style.display = "block";
  }
}

async function submitReturn() {
  const errorBox = document.getElementById("return-error");
  const resultBox = document.getElementById("return-result");
  errorBox.style.display = "none";
  resultBox.innerHTML = "";

  if (!returnSale) return;

  const items = [];
  document.querySelectorAll(".return-qty-input").forEach((input) => {
    const qty = parseInt(input.value || "0", 10);
    if (qty > 0) {
      items.push({ sale_item_id: parseInt(input.dataset.saleItemId, 10), qty });
    }
  });

  if (items.length === 0) {
    errorBox.textContent = "Indiquez une quantité à retourner sur au moins une ligne.";
    errorBox.style.display = "block";
    return;
  }

  const payload = {
    customer_name: document.getElementById("return-customer-name").value.trim(),
    customer_phone: document.getElementById("return-customer-phone").value.trim() || null,
    reason: document.getElementById("return-reason").value.trim() || null,
    items,
  };

  if (!payload.customer_name) {
    errorBox.textContent = "Le nom du client est requis pour créditer son avoir.";
    errorBox.style.display = "block";
    return;
  }

  try {
    const result = await apiFetch(`/api/sales/${returnSale.id}/return`, { method: "POST", body: JSON.stringify(payload) });
    resultBox.innerHTML = `<div class="alert alert-success">Retour enregistré : ${formatGNF(result.total_refund_gnf)} crédités sur l'avoir du client.</div>`;
    document.getElementById("return-details").style.display = "none";
    document.getElementById("return-transaction").value = "";
    returnSale = null;
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.style.display = "block";
  }
}

init();
