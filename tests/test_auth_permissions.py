from app.models import Role


def test_login_success_and_failure(client, make_user):
    make_user("alice", Role.ADMIN, "Secret123!")

    ok = client.post("/api/auth/login", json={"username": "alice", "password": "Secret123!"})
    assert ok.status_code == 200
    assert ok.json()["role"] == "admin"

    bad = client.post("/api/auth/login", json={"username": "alice", "password": "wrong"})
    assert bad.status_code == 401


def test_unauthenticated_request_is_rejected(client):
    res = client.get("/api/products")
    assert res.status_code == 401


def test_caissier_cannot_create_product(client, auth_headers):
    headers = auth_headers("cashier1", Role.CAISSIER)
    res = client.post(
        "/api/products",
        json={"name": "Soda", "category": "Sodas", "prix_achat": 1000, "prix_vente": 1500},
        headers=headers,
    )
    assert res.status_code == 403


def test_admin_can_create_product(client, auth_headers):
    headers = auth_headers("admin1", Role.ADMIN)
    res = client.post(
        "/api/products",
        json={"name": "Soda", "category": "Sodas", "prix_achat": 1000, "prix_vente": 1500},
        headers=headers,
    )
    assert res.status_code == 201


def test_caissier_cannot_update_price(client, auth_headers, make_user):
    admin_headers = auth_headers("admin2", Role.ADMIN)
    create = client.post(
        "/api/products",
        json={"name": "Bière", "category": "Bières", "prix_achat": 4000, "prix_vente": 6000},
        headers=admin_headers,
    )
    product_id = create.json()["id"]

    cashier_headers = auth_headers("cashier2", Role.CAISSIER)
    res = client.patch(f"/api/products/{product_id}/price", json={"prix_vente": 7000}, headers=cashier_headers)
    assert res.status_code == 403


def test_admin_can_set_tva_rate_on_a_product(client, auth_headers):
    admin_headers = auth_headers("admin3", Role.ADMIN)
    create = client.post(
        "/api/products",
        json={"name": "Jus local", "category": "Jus", "prix_achat": 2000, "prix_vente": 3500},
        headers=admin_headers,
    )
    product_id = create.json()["id"]
    assert create.json()["tva_rate"] == 0.0

    res = client.patch(f"/api/products/{product_id}/price", json={"tva_rate": 0.18}, headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["tva_rate"] == 0.18


def test_only_admin_can_create_user(client, auth_headers):
    manager_headers = auth_headers("manager1", Role.MANAGER)
    res = client.post(
        "/api/users",
        json={"username": "newuser", "password": "Password123!", "role": "caissier"},
        headers=manager_headers,
    )
    assert res.status_code == 403
