async function init() {
  requireAuth(["admin"]);
  renderNavbar("/users");

  document.getElementById("create-user").addEventListener("click", createUser);
  await loadUsers();
}

async function loadUsers() {
  const users = await apiFetch("/api/users");
  document.getElementById("users-body").innerHTML = users
    .map(
      (u) => `<tr><td>${u.username}</td><td>${u.full_name || "-"}</td><td>${u.role}</td><td>${u.is_active ? "Oui" : "Non"}</td></tr>`
    )
    .join("");
}

async function createUser() {
  const errorBox = document.getElementById("user-error");
  errorBox.style.display = "none";
  const payload = {
    username: document.getElementById("u-username").value,
    full_name: document.getElementById("u-fullname").value,
    password: document.getElementById("u-password").value,
    role: document.getElementById("u-role").value,
  };
  try {
    await apiFetch("/api/users", { method: "POST", body: JSON.stringify(payload) });
    document.getElementById("u-username").value = "";
    document.getElementById("u-fullname").value = "";
    document.getElementById("u-password").value = "";
    await loadUsers();
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.style.display = "block";
  }
}

init();
