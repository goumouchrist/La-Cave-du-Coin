#!/usr/bin/env bash
# Petite vérification que l'environnement staging contient bien des données
# (à lancer après scripts/refresh_staging_from_prod.sh). Voir DEPLOYMENT.md.
set -euo pipefail

echo "Utilisateurs dans staging :"
docker exec staging-db-1 psql -U cave_du_coin -c "select username, role from users;"

echo "Produits dans staging :"
docker exec staging-db-1 psql -U cave_du_coin -c "select name, prix_vente from products;"
