#!/usr/bin/env bash
# Vérifie rapidement le nombre de lignes dans les tables métier principales.
# Usage : ./scripts/check_prod_data.sh
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

docker compose exec -T db psql -U cave_du_coin -d cave_du_coin \
  -c "SELECT count(id) AS produits FROM products;" \
  -c "SELECT count(id) AS ventes FROM sales;" \
  -c "SELECT count(id) AS mouvements_stock FROM stock_movements;" \
  -c "SELECT count(id) AS clients FROM customers;" \
  -c "SELECT username, role FROM users ORDER BY id;"
