async function init() {
  requireAuth(["admin", "manager", "caissier"]);
  renderNavbar("/account");

  document.getElementById("change-password").addEventListener("click", changePassword);
}

async function changePassword() {
  const errorBox = document.getElementById("account-error");
  const successBox = document.getElementById("account-success");
  errorBox.style.display = "none";
  successBox.style.display = "none";

  const currentPassword = document.getElementById("current-password").value;
  const newPassword = document.getElementById("new-password").value;

  try {
    await apiFetch("/api/users/me/password", {
      method: "PATCH",
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    });
    successBox.textContent = "Mot de passe changé avec succès.";
    successBox.style.display = "block";
    document.getElementById("current-password").value = "";
    document.getElementById("new-password").value = "";
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.style.display = "block";
  }
}

init();
