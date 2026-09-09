const AUTH_KEY = "cave_du_coin_auth";

function getAuth() {
  const raw = localStorage.getItem(AUTH_KEY);
  return raw ? JSON.parse(raw) : null;
}

function setAuth(auth) {
  localStorage.setItem(AUTH_KEY, JSON.stringify(auth));
}

function logout() {
  localStorage.removeItem(AUTH_KEY);
  window.location.href = "/";
}

function requireAuth(allowedRoles) {
  const auth = getAuth();
  if (!auth) {
    window.location.href = "/";
    return null;
  }
  if (allowedRoles && !allowedRoles.includes(auth.role)) {
    alert("Accès refusé pour votre rôle: " + auth.role);
    window.location.href = "/pos";
    return null;
  }
  return auth;
}

async function apiFetch(path, options = {}) {
  const auth = getAuth();
  const headers = Object.assign({}, options.headers, {
    "Content-Type": "application/json",
  });
  if (auth) {
    headers["Authorization"] = "Bearer " + auth.access_token;
  }
  const res = await fetch(path, Object.assign({}, options, { headers }));
  if (res.status === 401) {
    logout();
    throw new Error("Non authentifié");
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || "Erreur");
  }
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return res.json();
  }
  return res;
}

function formatGNF(amount) {
  return new Intl.NumberFormat("fr-FR").format(amount) + " GNF";
}

function renderNavbar(activePage) {
  const auth = getAuth();
  const nav = document.getElementById("navbar");
  if (!nav) return;

  const links = [
    { href: "/pos", label: "Caisse", roles: ["admin", "manager", "caissier"] },
    { href: "/stock", label: "Stock", roles: ["admin", "manager"] },
    { href: "/cash", label: "Sessions caisse", roles: ["admin", "manager", "caissier"] },
    { href: "/dashboard", label: "Statistiques", roles: ["admin", "manager"] },
    { href: "/users", label: "Utilisateurs", roles: ["admin"] },
    { href: "/account", label: "Mon compte", roles: ["admin", "manager", "caissier"] },
  ];

  const linksHtml = links
    .filter((l) => !auth || l.roles.includes(auth.role))
    .map(
      (l) =>
        `<a href="${l.href}" class="nav-link ${l.href === activePage ? "active" : ""}">${l.label}</a>`
    )
    .join("");

  nav.innerHTML = `
    <div class="nav-brand">
      <img src="/static/img/logo.png" alt="La Cave du Coin" class="nav-logo" />
      <span>La Cave du Coin</span>
    </div>
    <div class="nav-links">${linksHtml}</div>
    <div class="nav-user">
      ${auth ? `<span>${auth.username} (${auth.role})</span><button onclick="logout()">Déconnexion</button>` : ""}
    </div>
  `;
}
