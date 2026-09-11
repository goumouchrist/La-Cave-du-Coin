const AUTH_KEY = "cave_du_coin_auth";

// Déconnexion automatique après ce délai d'inactivité (aucun clic/frappe/scroll).
// N'affecte jamais la session de caisse ni les ventes déjà enregistrées : tout
// est stocké côté serveur, une reconnexion avec le même compte reprend là où
// on en était (la caisse reste ouverte).
//
// L'horodatage de la dernière activité est persisté dans localStorage (et pas
// seulement gardé en mémoire via un unique setTimeout) car un onglet inactif
// en arrière-plan peut être déchargé par le navigateur pour économiser la
// mémoire : le minuteur en mémoire disparaît alors silencieusement et la
// déconnexion ne se produit jamais. En vérifiant périodiquement l'horodatage
// persistant (et dès le chargement de la page), la déconnexion s'applique
// même dans ce cas.
const LAST_ACTIVITY_KEY = "cave_du_coin_last_activity";
const INACTIVITY_TIMEOUT_MINUTES = 15;
const INACTIVITY_CHECK_INTERVAL_MS = 15000;

function getAuth() {
  const raw = localStorage.getItem(AUTH_KEY);
  return raw ? JSON.parse(raw) : null;
}

function setAuth(auth) {
  localStorage.setItem(AUTH_KEY, JSON.stringify(auth));
  localStorage.setItem(LAST_ACTIVITY_KEY, Date.now().toString());
}

function logout(reason) {
  localStorage.removeItem(AUTH_KEY);
  localStorage.removeItem(LAST_ACTIVITY_KEY);
  window.location.href = reason ? `/?reason=${reason}` : "/";
}

function isInactiveTooLong() {
  const last = parseInt(localStorage.getItem(LAST_ACTIVITY_KEY) || "0", 10);
  return Date.now() - last > INACTIVITY_TIMEOUT_MINUTES * 60 * 1000;
}

function checkInactivity() {
  if (isInactiveTooLong()) {
    logout("inactivity");
  }
}

let lastActivityPersistAt = 0;

function markActivity() {
  const now = Date.now();
  if (now - lastActivityPersistAt > 5000) {
    localStorage.setItem(LAST_ACTIVITY_KEY, now.toString());
    lastActivityPersistAt = now;
  }
}

function setupInactivityLogout() {
  // Vérifie d'abord l'horodatage laissé par une éventuelle session précédente
  // (ex: onglet déchargé puis rechargé après le délai) avant de le rafraîchir.
  if (isInactiveTooLong() && localStorage.getItem(LAST_ACTIVITY_KEY)) {
    logout("inactivity");
    return;
  }
  localStorage.setItem(LAST_ACTIVITY_KEY, Date.now().toString());

  ["mousemove", "mousedown", "keydown", "scroll", "touchstart", "click"].forEach((evt) =>
    document.addEventListener(evt, markActivity, { passive: true })
  );
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) checkInactivity();
  });

  setInterval(checkInactivity, INACTIVITY_CHECK_INTERVAL_MS);
}

function requireAuth(allowedRoles) {
  const auth = getAuth();
  if (!auth) {
    window.location.href = "/";
    return null;
  }
  // Le Super Admin a accès à tout, comme côté serveur (require_role).
  if (auth.role !== "super_admin" && allowedRoles && !allowedRoles.includes(auth.role)) {
    alert("Accès refusé pour votre rôle: " + auth.role);
    window.location.href = "/pos";
    return null;
  }
  setupInactivityLogout();
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

async function openAuthenticatedPdf(url) {
  const auth = getAuth();
  const res = await fetch(url, { headers: { Authorization: "Bearer " + auth.access_token } });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    alert(body.detail || "Erreur lors de la génération du PDF");
    return;
  }
  const blob = await res.blob();
  const blobUrl = URL.createObjectURL(blob);
  window.open(blobUrl, "_blank");
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
    { href: "/debts", label: "Créances clients", roles: ["admin", "manager", "caissier"] },
    { href: "/users", label: "Utilisateurs", roles: ["admin"] },
    { href: "/account", label: "Mon compte", roles: ["admin", "manager", "caissier"] },
  ];

  const linksHtml = links
    .filter((l) => !auth || auth.role === "super_admin" || l.roles.includes(auth.role))
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
