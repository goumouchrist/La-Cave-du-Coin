import pytest

from app.models import Role
from app.services import users as users_service


def test_super_admin_can_reset_an_admin_password(db_session):
    super_admin = users_service.create_user(db_session, "super1", "pw", Role.SUPER_ADMIN)
    admin = users_service.create_user(db_session, "admin1", "OldPass123!", Role.ADMIN)

    users_service.reset_password(db_session, admin, "NewPass456!", super_admin)

    assert users_service.authenticate(db_session, "admin1", "NewPass456!") is not None


def test_regular_admin_cannot_reset_another_admins_password(db_session):
    admin_a = users_service.create_user(db_session, "admin_a", "pw", Role.ADMIN)
    admin_b = users_service.create_user(db_session, "admin_b", "OldPass123!", Role.ADMIN)

    with pytest.raises(users_service.InsufficientPrivilegeError):
        users_service.reset_password(db_session, admin_b, "Hacked123!", admin_a)

    assert users_service.authenticate(db_session, "admin_b", "OldPass123!") is not None


def test_regular_admin_cannot_reset_a_super_admins_password(db_session):
    admin = users_service.create_user(db_session, "admin_a", "pw", Role.ADMIN)
    super_admin = users_service.create_user(db_session, "super1", "OldPass123!", Role.SUPER_ADMIN)

    with pytest.raises(users_service.InsufficientPrivilegeError):
        users_service.reset_password(db_session, super_admin, "Hacked123!", admin)


def test_regular_admin_cannot_deactivate_another_admin(db_session):
    admin_a = users_service.create_user(db_session, "admin_a", "pw", Role.ADMIN)
    admin_b = users_service.create_user(db_session, "admin_b", "pw", Role.ADMIN)

    with pytest.raises(users_service.InsufficientPrivilegeError):
        users_service.set_active(db_session, admin_b, admin_a, is_active=False)

    assert admin_b.is_active is True


def test_super_admin_can_deactivate_an_admin(db_session):
    super_admin = users_service.create_user(db_session, "super1", "pw", Role.SUPER_ADMIN)
    admin = users_service.create_user(db_session, "admin1", "pw", Role.ADMIN)

    users_service.set_active(db_session, admin, super_admin, is_active=False)

    assert admin.is_active is False


def test_admin_can_still_manage_manager_and_caissier_accounts(db_session):
    admin = users_service.create_user(db_session, "admin1", "pw", Role.ADMIN)
    caissier = users_service.create_user(db_session, "caissier1", "OldPass123!", Role.CAISSIER)

    users_service.reset_password(db_session, caissier, "NewPass456!", admin)
    users_service.set_active(db_session, caissier, admin, is_active=False)

    assert users_service.authenticate(db_session, "caissier1", "NewPass456!") is None  # désactivé
    assert caissier.is_active is False


def test_regular_admin_cannot_create_an_admin_account_via_api(db_session):
    admin = users_service.create_user(db_session, "admin1", "pw", Role.ADMIN)

    with pytest.raises(users_service.InsufficientPrivilegeError):
        users_service.create_user(db_session, "newadmin", "pw", Role.ADMIN, acting_user=admin)

    with pytest.raises(users_service.InsufficientPrivilegeError):
        users_service.create_user(db_session, "newsuper", "pw", Role.SUPER_ADMIN, acting_user=admin)


def test_super_admin_can_create_an_admin_account(db_session):
    super_admin = users_service.create_user(db_session, "super1", "pw", Role.SUPER_ADMIN)

    new_admin = users_service.create_user(db_session, "admin1", "pw", Role.ADMIN, acting_user=super_admin)

    assert new_admin.role == Role.ADMIN


def test_super_admin_role_bypasses_role_check_endpoints(client, auth_headers, make_user):
    make_user("caissier1", Role.CAISSIER, "Caissier123!")
    super_headers = auth_headers("super1", Role.SUPER_ADMIN)

    res = client.post(
        "/api/products",
        json={"name": "Soda", "category": "Sodas", "prix_achat": 1000, "prix_vente": 1500},
        headers=super_headers,
    )
    assert res.status_code == 201
