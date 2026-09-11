#!/usr/bin/env bash
# Met à jour l'environnement de test "staging" pour qu'il redevienne ISO prod :
# code à jour (git pull) + copie complète des données de production.
# À exécuter sur le VPS, depuis le dossier du projet. Voir DEPLOYMENT.md.
#
# Usage : ./scripts/refresh_staging_from_prod.sh
# (appelé automatiquement chaque mois par cron, cf. deploy/staging-refresh.cron)
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

log() { echo "[staging-refresh] $(date -Iseconds) - $1"; }

log "mise a jour du code (git pull)"
git pull

log "reconstruction du stack staging"
docker compose -p staging --env-file .env.staging -f docker-compose.yml -f docker-compose.staging.yml up -d --build

log "attente de la disponibilite de la base staging"
sleep 10

PROD_DB="$(docker compose ps -q db)"
STAGING_DB="$(docker compose -p staging --env-file .env.staging -f docker-compose.yml -f docker-compose.staging.yml ps -q db)"

if [ -z "$PROD_DB" ] || [ -z "$STAGING_DB" ]; then
  log "ERREUR : conteneur prod ou staging introuvable, abandon."
  exit 1
fi

log "copie des donnees prod -> staging (pg_dump | pg_restore)"
docker exec "$PROD_DB" pg_dump -U cave_du_coin -Fc cave_du_coin \
  | docker exec -i "$STAGING_DB" pg_restore -U cave_du_coin -d cave_du_coin --clean --if-exists

log "termine avec succes"
