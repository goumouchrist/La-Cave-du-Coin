#!/usr/bin/env bash
# Restaure une sauvegarde pg_dump au format SQL brut (celle produite toutes
# les 4h par scripts/backup.py, dans le dossier backups/) dans la base de
# PRODUCTION, en écrasant son contenu actuel. Une sauvegarde de sécurité de
# l'état actuel est prise automatiquement avant toute modification.
# À n'utiliser qu'en cas de réel besoin de rollback. Voir DEPLOYMENT.md.
#
# Usage : ./scripts/restore_prod_from_backup.sh backups/cave_du_coin_20260901_120000.sql
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 chemin/vers/sauvegarde.sql"
  exit 1
fi

DUMP_FILE="$1"

if [ ! -f "$DUMP_FILE" ]; then
  echo "ERREUR : fichier introuvable : $DUMP_FILE"
  exit 1
fi

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

log() { echo "[restore-prod] $(date -Iseconds) - $1"; }

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
SAFETY_FILE="backups/avant_rollback_${TIMESTAMP}.sql"

log "sauvegarde de securite de l'etat actuel avant restauration : $SAFETY_FILE"
mkdir -p backups
docker compose exec -T db pg_dump -U cave_du_coin cave_du_coin > "$SAFETY_FILE"
log "sauvegarde de securite ecrite : $PROJECT_DIR/$SAFETY_FILE"

log "arret de l'application (evite les ecritures pendant la restauration)"
docker compose stop app

log "suppression et recreation de la base vide (le dump SQL contient deja les CREATE TABLE)"
docker compose exec -T db psql -U cave_du_coin -d postgres -c "DROP DATABASE IF EXISTS cave_du_coin;"
docker compose exec -T db psql -U cave_du_coin -d postgres -c "CREATE DATABASE cave_du_coin OWNER cave_du_coin;"

log "chargement de la sauvegarde : $DUMP_FILE"
docker compose exec -T db psql -U cave_du_coin -d cave_du_coin < "$DUMP_FILE"

log "redemarrage de l'application"
docker compose up -d app

log "termine. Si besoin de revenir en arriere : $SAFETY_FILE contient l'etat d'avant ce rollback."
