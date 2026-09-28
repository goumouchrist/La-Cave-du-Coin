#!/usr/bin/env bash
# Diagnostic : verifie ce que le conteneur app voit reellement comme base,
# via sa propre connexion (pas psql directement sur db), et liste tous les
# conteneurs actifs pour detecter un doublon eventuel.
# Usage : bash scripts/check_app_target.sh
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "=== docker compose ps (ce projet) ==="
docker compose ps

echo
echo "=== docker ps -a (tous conteneurs, tous projets) ==="
docker ps -a

echo
echo "=== DATABASE_URL vu par le conteneur app ==="
docker compose exec -T app env | grep DATABASE_URL

echo
echo "=== Comptage vu par l'app via sa propre connexion SQLAlchemy ==="
docker compose exec -T app python -c "
from app.database import SessionLocal
from app.models import Product, Sale, StockMovement
db = SessionLocal()
print('produits:', db.query(Product).count())
print('ventes:', db.query(Sale).count())
print('mouvements_stock:', db.query(StockMovement).count())
"
