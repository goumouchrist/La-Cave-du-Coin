"""Crée les utilisateurs par défaut et un catalogue de démonstration.

Prérequis : le schéma de base doit déjà exister (lancer `alembic upgrade head`
avant ce script — voir README.md).

Usage: python scripts/seed_data.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models import Product, Role, User
from app.services.users import create_user, DuplicateUsernameError

DEMO_PRODUCTS = [
    dict(name="Coca-Cola 33cl", category="Sodas", barcode="6001234500017", unit_carton_qty=24, unit_pack_qty=6, prix_achat=3000, prix_vente=5000, stock_min_cartons=5),
    dict(name="Fanta Orange 33cl", category="Sodas", barcode="6001234500024", unit_carton_qty=24, unit_pack_qty=6, prix_achat=3000, prix_vente=5000, stock_min_cartons=5),
    dict(name="Eau minérale 1.5L", category="Eaux", barcode="6001234500031", unit_carton_qty=12, unit_pack_qty=6, prix_achat=2000, prix_vente=3500, stock_min_cartons=8),
    dict(name="Jus d'ananas 1L", category="Jus", barcode="6001234500048", unit_carton_qty=12, unit_pack_qty=4, prix_achat=4000, prix_vente=6500, stock_min_cartons=5),
    dict(name="Guinness 33cl", category="Bières", barcode="6001234500055", unit_carton_qty=24, unit_pack_qty=6, prix_achat=4500, prix_vente=7000, stock_min_cartons=5),
    dict(name="Heineken 33cl", category="Bières", barcode="6001234500062", unit_carton_qty=24, unit_pack_qty=6, prix_achat=4500, prix_vente=7500, stock_min_cartons=5),
    dict(name="Red Bull 25cl", category="Boissons énergisantes", barcode="6001234500079", unit_carton_qty=24, unit_pack_qty=4, prix_achat=6000, prix_vente=10000, stock_min_cartons=3),
    dict(name="Whisky Label 5 70cl", category="Spiritueux", barcode="6001234500086", unit_carton_qty=6, unit_pack_qty=1, prix_achat=45000, prix_vente=70000, stock_min_cartons=2),
]


def seed(users_only: bool = False):
    db = SessionLocal()
    try:
        default_users = [
            ("superadmin", "SuperAdmin123!", Role.SUPER_ADMIN, "Super Administrateur"),
            ("admin", "Admin123!", Role.ADMIN, "Administrateur"),
            ("manager", "Manager123!", Role.MANAGER, "Manager Boutique"),
            ("caissier", "Caissier123!", Role.CAISSIER, "Caissier Principal"),
        ]
        for username, password, role, full_name in default_users:
            try:
                create_user(db, username, password, role, full_name)
                print(f"Utilisateur créé: {username} / {password} ({role.value})")
            except DuplicateUsernameError:
                print(f"Utilisateur déjà existant: {username}")

        if users_only:
            db.commit()
            return

        for data in DEMO_PRODUCTS:
            existing = db.query(Product).filter(Product.barcode == data["barcode"]).first()
            if existing:
                print(f"Produit déjà existant: {data['name']}")
                continue
            db.add(Product(**data))
            print(f"Produit créé: {data['name']}")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed(users_only="--users-only" in sys.argv)
