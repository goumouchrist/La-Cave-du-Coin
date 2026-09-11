#!/usr/bin/env bash
# Détecte automatiquement le fichier de sauvegarde le plus récent produit
# par reset_prod_database.sh (backup_before_reset_*.dump) et le restaure dans
# l'environnement staging, sans avoir à taper son nom (évite tout risque de
# faute de frappe sur les underscores à la console Hetzner). Voir
# DEPLOYMENT.md.
#
# Usage : ./scripts/restore_latest_reset_backup_into_staging.sh
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

DUMP_FILE="$(ls -1t backup_before_reset_*.dump 2>/dev/null | head -n 1 || true)"

if [ -z "$DUMP_FILE" ]; then
  echo "ERREUR : aucun fichier backup_before_reset_*.dump trouve dans $PROJECT_DIR"
  exit 1
fi

echo "Fichier detecte automatiquement : $DUMP_FILE"
./scripts/restore_dump_into_staging.sh "$DUMP_FILE"
