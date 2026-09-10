let products = [];
let suppliers = [];

async function init() {
  requireAuth(["admin", "manager"]);
  renderNavbar("/stock");

  document.getElementById("create-product").addEventListener("click", createProduct);
  document.getElementById("create-movement").addEventListener("click", createMovement);
  document.getElementById("import-submit").addEventListener("click", importCsv);
  document.getElementById("import-movement-submit").addEventListener("click", importMovementsCsv);
  document.getElementById("create-supplier").addEventListener("click", createSupplier);

  await loadSuppliers();
  await loadProducts();
  await loadPendingMovements();
}

async function loadSuppliers() {
  suppliers = await apiFetch("/api/suppliers");
  const body = document.getElementById("suppliers-body");
  body.innerHTML = suppliers
    .map(
      (s) => `
      <tr>
        <td>${s.name}</td>
        <td>${s.phone || "-"}</td>
        <td>${s.address || "-"}</td>
        <td>
          <button class="secondary" onclick="showSupplierHistory(${s.id})">Voir</button>
          <button class="danger" onclick="deleteSupplier(${s.id})">Supprimer</button>
        </td>
      </tr>`
    )
    .join("");

  const optionsHtml = suppliers.map((s) => `<option value="${s.id}">${s.name}</option>`).join("");
  document.getElementById("p-supplier").innerHTML = `<option value="">Fournisseur habituel (optionnel)</option>${optionsHtml}`;
  document.getElementById("m-supplier").innerHTML = `<option value="">Fournisseur (si entrée)</option>${optionsHtml}`;
}

async function createSupplier() {
  const errorBox = document.getElementById("supplier-error");
  errorBox.style.display = "none";
  const payload = {
    name: document.getElementById("s-name").value,
    phone: document.getElementById("s-phone").value || null,
    address: document.getElementById("s-address").value || null,
  };
  if (!payload.name) {
    errorBox.textContent = "Le nom du fournisseur est requis.";
    errorBox.style.display = "block";
    return;
  }
  try {
    await apiFetch("/api/suppliers", { method: "POST", body: JSON.stringify(payload) });
    document.getElementById("s-name").value = "";
    document.getElementById("s-phone").value = "";
    document.getElementById("s-address").value = "";
    await loadSuppliers();
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.style.display = "block";
  }
}

async function deleteSupplier(supplierId) {
  if (!confirm("Supprimer ce fournisseur ? L'historique des livraisons déjà enregistrées sera conservé.")) {
    return;
  }
  try {
    await apiFetch(`/api/suppliers/${supplierId}`, { method: "DELETE" });
    await loadSuppliers();
  } catch (err) {
    alert(err.message);
  }
}

async function showSupplierHistory(supplierId) {
  const box = document.getElementById("supplier-history");
  try {
    const movements = await apiFetch(`/api/suppliers/${supplierId}/movements`);
    const supplier = suppliers.find((s) => s.id === supplierId);
    if (movements.length === 0) {
      box.innerHTML = `<p>Aucune livraison enregistrée pour ${supplier.name}.</p>`;
      return;
    }
    box.innerHTML = `
      <h3>Historique des livraisons — ${supplier.name}</h3>
      <table>
        <thead><tr><th>Date</th><th>Produit</th><th>Qté (unités)</th><th>N° facture</th></tr></thead>
        <tbody>
          ${movements
            .map((m) => {
              const product = products.find((p) => p.id === m.product_id);
              return `<tr>
                <td>${new Date(m.created_at).toLocaleDateString("fr-FR")}</td>
                <td>${product ? product.name : m.product_id}</td>
                <td>${m.qty_units}</td>
                <td>${m.invoice_number || "-"}</td>
              </tr>`;
            })
            .join("")}
        </tbody>
      </table>
    `;
  } catch (err) {
    box.innerHTML = `<div class="alert alert-error">${err.message}</div>`;
  }
}

async function loadProducts() {
  products = await apiFetch("/api/products");
  const body = document.getElementById("products-body");
  body.innerHTML = products
    .map(
      (p) => `
      <tr>
        <td>${p.name}</td>
        <td>${p.category}</td>
        <td>${p.barcode || "-"}</td>
        <td>${p.current_stock_units}</td>
        <td>${p.stock_min_cartons} carton(s)</td>
        <td>${formatGNF(p.prix_vente)}</td>
        <td>
          ${(p.tva_rate * 100).toFixed(2)}%
          <button class="secondary" onclick="editTvaRate(${p.id}, ${p.tva_rate})">Modifier</button>
        </td>
        <td>
          ${
            p.barcode
              ? `<button class="secondary" onclick="openAuthenticatedPdf('/api/products/${p.id}/label.pdf')">Imprimer étiquette</button>`
              : `<button class="secondary" onclick="generateBarcode(${p.id})">Générer code interne</button>`
          }
          <button class="danger" onclick="deleteProduct(${p.id})">Supprimer</button>
        </td>
      </tr>`
    )
    .join("");

  const select = document.getElementById("m-product");
  select.innerHTML = products.map((p) => `<option value="${p.id}">${p.name}</option>`).join("");
}

async function editTvaRate(productId, currentRate) {
  const input = prompt("Taux de TVA en % (ex: 18 pour 18%) :", (currentRate * 100).toFixed(2));
  if (input === null) return;
  const percent = parseFloat(input.replace(",", "."));
  if (isNaN(percent) || percent < 0 || percent > 100) {
    alert("Veuillez entrer un pourcentage valide entre 0 et 100.");
    return;
  }
  try {
    await apiFetch(`/api/products/${productId}/price`, { method: "PATCH", body: JSON.stringify({ tva_rate: percent / 100 }) });
    await loadProducts();
  } catch (err) {
    alert(err.message);
  }
}

async function deleteProduct(productId) {
  if (!confirm("Supprimer ce produit ? L'historique des ventes déjà enregistrées sera conservé.")) return;
  try {
    await apiFetch(`/api/products/${productId}`, { method: "DELETE" });
    await loadProducts();
  } catch (err) {
    alert(err.message);
  }
}

async function generateBarcode(productId) {
  try {
    await apiFetch(`/api/products/${productId}/generate-barcode`, { method: "POST" });
    await loadProducts();
  } catch (err) {
    alert(err.message);
  }
}

async function createProduct() {
  const errorBox = document.getElementById("product-error");
  errorBox.style.display = "none";
  const payload = {
    name: document.getElementById("p-name").value,
    category: document.getElementById("p-category").value,
    barcode: document.getElementById("p-barcode").value || null,
    unit_carton_qty: parseInt(document.getElementById("p-carton").value || "24", 10),
    unit_pack_qty: parseInt(document.getElementById("p-pack").value || "6", 10),
    prix_achat: parseInt(document.getElementById("p-achat").value || "0", 10),
    prix_vente: parseInt(document.getElementById("p-vente").value || "0", 10),
    stock_min_cartons: parseInt(document.getElementById("p-min").value || "5", 10),
    tva_rate: parseFloat(document.getElementById("p-tva").value || "0") / 100,
    supplier_id: document.getElementById("p-supplier").value ? parseInt(document.getElementById("p-supplier").value, 10) : null,
  };
  try {
    await apiFetch("/api/products", { method: "POST", body: JSON.stringify(payload) });
    await loadProducts();
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.style.display = "block";
  }
}

async function createMovement() {
  const errorBox = document.getElementById("movement-error");
  errorBox.style.display = "none";
  const payload = {
    product_id: parseInt(document.getElementById("m-product").value, 10),
    type: document.getElementById("m-type").value,
    qty: parseInt(document.getElementById("m-qty").value || "0", 10),
    unit: document.getElementById("m-unit").value,
    invoice_number: document.getElementById("m-invoice").value || null,
    reason: document.getElementById("m-reason").value || null,
    supplier_id: document.getElementById("m-supplier").value ? parseInt(document.getElementById("m-supplier").value, 10) : null,
  };
  try {
    await apiFetch("/api/stock/movements", { method: "POST", body: JSON.stringify(payload) });
    await loadPendingMovements();
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.style.display = "block";
  }
}

async function loadPendingMovements() {
  const pending = await apiFetch("/api/stock/movements/pending");
  const body = document.getElementById("pending-body");
  body.innerHTML = pending
    .map((m) => {
      const product = products.find((p) => p.id === m.product_id);
      return `
      <tr>
        <td>${product ? product.name : m.product_id}</td>
        <td>${m.type}</td>
        <td>${m.qty_units}</td>
        <td>#${m.created_by}</td>
        <td>
          <button onclick="validateMovement(${m.id}, true)">Valider</button>
          <button class="danger" onclick="validateMovement(${m.id}, false)">Rejeter</button>
        </td>
      </tr>`;
    })
    .join("");
}

async function validateMovement(id, approve) {
  try {
    await apiFetch(`/api/stock/movements/${id}/validate`, {
      method: "POST",
      body: JSON.stringify({ approve }),
    });
    await loadProducts();
    await loadPendingMovements();
  } catch (err) {
    alert(err.message);
  }
}

async function importCsv() {
  const resultBox = document.getElementById("import-result");
  resultBox.innerHTML = "";

  const fileInput = document.getElementById("import-file");
  const file = fileInput.files[0];
  if (!file) {
    resultBox.innerHTML = `<div class="alert alert-error">Choisissez un fichier CSV.</div>`;
    return;
  }

  const auth = getAuth();
  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch("/api/products/import", {
      method: "POST",
      headers: { Authorization: "Bearer " + auth.access_token },
      body: formData,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(body.detail || "Erreur d'import");
    }
    const result = await res.json();

    const errorsHtml = result.errors.length
      ? `<ul>${result.errors.map((e) => `<li>Ligne ${e.line}: ${e.error}</li>`).join("")}</ul>`
      : "";
    resultBox.innerHTML = `
      <div class="alert ${result.errors.length ? "alert-error" : "alert-success"}">
        ${result.created.length} produit(s) importé(s) : ${result.created.join(", ") || "aucun"}.
        ${result.errors.length ? `${result.errors.length} ligne(s) en erreur :${errorsHtml}` : ""}
      </div>
    `;
    fileInput.value = "";
    await loadProducts();
  } catch (err) {
    resultBox.innerHTML = `<div class="alert alert-error">${err.message}</div>`;
  }
}

async function importMovementsCsv() {
  const resultBox = document.getElementById("import-movement-result");
  resultBox.innerHTML = "";

  const fileInput = document.getElementById("import-movement-file");
  const file = fileInput.files[0];
  if (!file) {
    resultBox.innerHTML = `<div class="alert alert-error">Choisissez un fichier CSV.</div>`;
    return;
  }

  const auth = getAuth();
  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch("/api/stock/movements/import", {
      method: "POST",
      headers: { Authorization: "Bearer " + auth.access_token },
      body: formData,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(body.detail || "Erreur d'import");
    }
    const result = await res.json();

    const errorsHtml = result.errors.length
      ? `<ul>${result.errors.map((e) => `<li>Ligne ${e.line}: ${e.error}</li>`).join("")}</ul>`
      : "";
    resultBox.innerHTML = `
      <div class="alert ${result.errors.length ? "alert-error" : "alert-success"}">
        ${result.created.length} mouvement(s) créé(s), en attente de validation : ${result.created.join(", ") || "aucun"}.
        ${result.errors.length ? `${result.errors.length} ligne(s) en erreur :${errorsHtml}` : ""}
      </div>
    `;
    fileInput.value = "";
    await loadPendingMovements();
  } catch (err) {
    resultBox.innerHTML = `<div class="alert alert-error">${err.message}</div>`;
  }
}

init();
