#!/usr/bin/env bash
# Sauvegarde puis vide entièrement les données de la base de PRODUCTION
# (conserve le schéma des tables) et recrée uniquement les comptes
# utilisateurs par défaut (pas les produits de démo). À utiliser une seule
# fois pour repartir d'une base propre après la phase de démo/tests. Voir
# DEPLOYMENT.md.
#
# Usage : ./scripts/reset_prod_database.sh
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

log() { echo "[reset] $(date -Iseconds) - $1"; }

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="backup_before_reset_${TIMESTAMP}.dump"

log "sauvegarde de securite avant nettoyage : $BACKUP_FILE"
docker compose exec -T db pg_dump -U cave_du_coin -Fc cave_du_coin > "$BACKUP_FILE"
log "sauvegarde ecrite : $PROJECT_DIR/$BACKUP_FILE"

log "vidage des tables (schema conserve, comptes/produits/ventes/stock/clients effaces)"
docker compose exec -T db psql -U cave_du_coin -d cave_du_coin -c \
  "TRUNCATE TABLE users, suppliers, products, stock_movements, cash_sessions, sales, sale_items, logs, scan_logs, customers, customer_repayments, returns, return_items RESTART IDENTITY CASCADE;"

log "recreation des comptes par defaut (mots de passe a changer immediatement)"
docker compose exec -T app python scripts/seed_data.py --users-only

log "termine. Sauvegarde disponible : $PROJECT_DIR/$BACKUP_FILE"
