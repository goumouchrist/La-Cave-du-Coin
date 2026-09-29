#!/usr/bin/env bash
# Verification en LECTURE UNIQUEMENT (schema seulement, aucune donnee) que la
# prod a bien la derniere migration appliquee.
# Usage : bash scripts/check_prod_schema.sh
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "=== Version de migration Alembic appliquee en prod ==="
docker compose exec -T db psql -U cave_du_coin -d cave_du_coin -c \
  "SELECT version_num FROM alembic_version;"

echo
echo "=== Colonnes de la table returns en prod ==="
docker compose exec -T db psql -U cave_du_coin -d cave_du_coin -c \
  "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'returns' ORDER BY ordinal_position;"

echo
echo "=== Contrainte fk_returns_cash_session_id presente ? ==="
docker compose exec -T db psql -U cave_du_coin -d cave_du_coin -c \
  "SELECT conname FROM pg_constraint WHERE conname = 'fk_returns_cash_session_id';"
