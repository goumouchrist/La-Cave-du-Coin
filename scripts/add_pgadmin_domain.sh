#!/usr/bin/env bash
# Ajoute PGADMIN_DOMAIN au .env de production s'il n'y est pas déjà (évite de
# taper "_" dans une console qui déforme les caractères Shift). Voir
# DEPLOYMENT.md. Idempotent : sans effet si déjà fait.
set -euo pipefail

ENV_FILE=".env"

if [ ! -f "$ENV_FILE" ]; then
  echo "ERREUR : $ENV_FILE introuvable. Lancez ce script depuis /opt/La_Cave_du_Coin."
  exit 1
fi

if grep -q PGADMIN_DOMAIN "$ENV_FILE"; then
  echo "$ENV_FILE contient déjà PGADMIN_DOMAIN, rien à faire."
else
  {
    echo ""
    echo "PGADMIN_DOMAIN=pgadmin.lacaveducoin.com"
  } >> "$ENV_FILE"
  echo "Ajouté à $ENV_FILE : PGADMIN_DOMAIN=pgadmin.lacaveducoin.com"
fi
