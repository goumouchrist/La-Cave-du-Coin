#!/usr/bin/env bash
# Restaure un fichier de sauvegarde PostgreSQL (format pg_dump -Fc, ex: celui
# produit par reset_prod_database.sh) dans la base de l'environnement
# staging. Utile pour réinjecter une ancienne sauvegarde (ex: les données de
# démo sauvegardées avant un nettoyage de prod) plutôt que les données
# actuelles de prod. Voir DEPLOYMENT.md.
#
# Usage : ./scripts/restore_dump_into_staging.sh chemin/vers/fichier.dump
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 chemin/vers/fichier.dump"
  exit 1
fi

DUMP_FILE="$1"

if [ ! -f "$DUMP_FILE" ]; then
  echo "ERREUR : fichier introuvable : $DUMP_FILE"
  exit 1
fi

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

STAGING_DB="$(docker compose -p staging --env-file .env.staging -f docker-compose.yml -f docker-compose.staging.yml ps -q db)"

if [ -z "$STAGING_DB" ]; then
  echo "ERREUR : conteneur staging introuvable. Le stack staging est-il démarré ?"
  exit 1
fi

echo "Restauration de $DUMP_FILE dans la base staging (écrase son contenu actuel)..."
docker exec -i "$STAGING_DB" pg_restore -U cave_du_coin -d cave_du_coin --clean --if-exists < "$DUMP_FILE"
echo "Terminé."
