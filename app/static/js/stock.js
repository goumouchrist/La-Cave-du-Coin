let products = [];

async function init() {
  requireAuth(["admin", "manager"]);
  renderNavbar("/stock");

  document.getElementById("create-product").addEventListener("click", createProduct);
  document.getElementById("create-movement").addEventListener("click", createMovement);
  document.getElementById("import-submit").addEventListener("click", importCsv);

  await loadProducts();
  await loadPendingMovements();
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
      </tr>`
    )
    .join("");

  const select = document.getElementById("m-product");
  select.innerHTML = products.map((p) => `<option value="${p.id}">${p.name}</option>`).join("");
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

init();
