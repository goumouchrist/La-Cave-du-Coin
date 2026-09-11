#!/usr/bin/env bash
# Met à jour l'environnement de test "staging" pour qu'il redevienne ISO prod :
# code à jour (git pull) + copie des données. Si la prod ne contient encore
# aucun produit ni vente réelle (juste après un reset_prod_database.sh), copie
# la dernière sauvegarde de démo disponible plutôt qu'une prod vide ; bascule
# automatiquement sur la vraie prod dès qu'elle contient de vraies données.
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

log "verification de l'activite reelle en prod (produits + ventes)"
REAL_ACTIVITY_COUNT="$(docker exec "$PROD_DB" psql -U cave_du_coin -d cave_du_coin -tAc \
  "SELECT (SELECT COUNT(*) FROM products) + (SELECT COUNT(*) FROM sales);" | tr -d '[:space:]')"

DEMO_BACKUP="$(ls -1t backup_before_reset_*.dump 2>/dev/null | head -n 1 || true)"

if [ "$REAL_ACTIVITY_COUNT" -gt 0 ]; then
  log "prod contient de vraies donnees (produits+ventes=$REAL_ACTIVITY_COUNT) : copie normale prod -> staging"
  docker exec "$PROD_DB" pg_dump -U cave_du_coin -Fc cave_du_coin \
    | docker exec -i "$STAGING_DB" pg_restore -U cave_du_coin -d cave_du_coin --clean --if-exists
elif [ -n "$DEMO_BACKUP" ]; then
  log "prod ne contient encore aucun produit/vente reel : restauration des donnees de demo ($DEMO_BACKUP)"
  docker exec -i "$STAGING_DB" pg_restore -U cave_du_coin -d cave_du_coin --clean --if-exists < "$DEMO_BACKUP"
else
  log "prod vide et aucune sauvegarde de demo disponible : copie normale prod -> staging (base vide)"
  docker exec "$PROD_DB" pg_dump -U cave_du_coin -Fc cave_du_coin \
    | docker exec -i "$STAGING_DB" pg_restore -U cave_du_coin -d cave_du_coin --clean --if-exists
fi

log "termine avec succes"
