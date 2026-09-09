import pytest

from app.models import Role
from app.services import users as users_service


def test_change_own_password_success(db_session):
    user = users_service.create_user(db_session, "caissier1", "OldPass123!", Role.CAISSIER)

    users_service.change_own_password(db_session, user, "OldPass123!", "NewPass456!")

    assert users_service.authenticate(db_session, "caissier1", "OldPass123!") is None
    assert users_service.authenticate(db_session, "caissier1", "NewPass456!") is not None


def test_change_own_password_rejects_wrong_current_password(db_session):
    user = users_service.create_user(db_session, "caissier1", "OldPass123!", Role.CAISSIER)

    with pytest.raises(users_service.WrongCurrentPasswordError):
        users_service.change_own_password(db_session, user, "WrongPassword", "NewPass456!")

    assert users_service.authenticate(db_session, "caissier1", "OldPass123!") is not None


def test_admin_reset_password_does_not_require_current_password(db_session):
    user = users_service.create_user(db_session, "caissier1", "OldPass123!", Role.CAISSIER)

    users_service.reset_password(db_session, user, "ResetByAdmin789!")

    assert users_service.authenticate(db_session, "caissier1", "OldPass123!") is None
    assert users_service.authenticate(db_session, "caissier1", "ResetByAdmin789!") is not None


def test_manager_cannot_reset_another_users_password(client, auth_headers, make_user):
    make_user("caissier1", Role.CAISSIER, "Caissier123!")
    manager_headers = auth_headers("manager1", Role.MANAGER)

    res = client.get("/api/users", headers=manager_headers)
    caissier_id = next(u["id"] for u in res.json() if u["username"] == "caissier1")

    res = client.patch(f"/api/users/{caissier_id}/password", json={"new_password": "Hacked123!"}, headers=manager_headers)
    assert res.status_code == 403


def test_admin_can_reset_another_users_password_via_api(client, auth_headers, make_user):
    make_user("caissier1", Role.CAISSIER, "Caissier123!")
    admin_headers = auth_headers("admin1", Role.ADMIN)

    res = client.get("/api/users", headers=admin_headers)
    caissier_id = next(u["id"] for u in res.json() if u["username"] == "caissier1")

    res = client.patch(f"/api/users/{caissier_id}/password", json={"new_password": "NewSecure123!"}, headers=admin_headers)
    assert res.status_code == 200

    login = client.post("/api/auth/login", json={"username": "caissier1", "password": "NewSecure123!"})
    assert login.status_code == 200


def test_deactivating_user_blocks_login(db_session):
    admin = users_service.create_user(db_session, "admin1", "AdminPass123!", Role.ADMIN)
    caissier = users_service.create_user(db_session, "caissier1", "Caissier123!", Role.CAISSIER)

    users_service.set_active(db_session, caissier, admin, is_active=False)

    assert users_service.authenticate(db_session, "caissier1", "Caissier123!") is None
    assert caissier.is_active is False


def test_reactivating_user_restores_login(db_session):
    admin = users_service.create_user(db_session, "admin1", "AdminPass123!", Role.ADMIN)
    caissier = users_service.create_user(db_session, "caissier1", "Caissier123!", Role.CAISSIER)
    users_service.set_active(db_session, caissier, admin, is_active=False)

    users_service.set_active(db_session, caissier, admin, is_active=True)

    assert users_service.authenticate(db_session, "caissier1", "Caissier123!") is not None


def test_admin_cannot_deactivate_own_account(db_session):
    admin = users_service.create_user(db_session, "admin1", "AdminPass123!", Role.ADMIN)

    with pytest.raises(users_service.CannotDeactivateSelfError):
        users_service.set_active(db_session, admin, admin, is_active=False)


def test_deactivate_user_via_api(client, auth_headers, make_user):
    make_user("caissier1", Role.CAISSIER, "Caissier123!")
    admin_headers = auth_headers("admin1", Role.ADMIN)

    res = client.get("/api/users", headers=admin_headers)
    caissier_id = next(u["id"] for u in res.json() if u["username"] == "caissier1")

    res = client.patch(f"/api/users/{caissier_id}/status", json={"is_active": False}, headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["is_active"] is False

    login = client.post("/api/auth/login", json={"username": "caissier1", "password": "Caissier123!"})
    assert login.status_code == 401


def test_user_can_change_own_password_via_api(client, auth_headers):
    headers = auth_headers("caissier1", Role.CAISSIER, "OldPass123!")

    res = client.patch(
        "/api/users/me/password",
        json={"current_password": "OldPass123!", "new_password": "NewPass456!"},
        headers=headers,
    )
    assert res.status_code == 200

    login = client.post("/api/auth/login", json={"username": "caissier1", "password": "NewPass456!"})
    assert login.status_code == 200
