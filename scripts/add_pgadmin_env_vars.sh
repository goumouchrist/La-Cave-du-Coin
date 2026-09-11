#!/usr/bin/env bash
# Ajoute les identifiants pgAdmin par défaut à .env.staging s'ils n'y sont
# pas déjà (évite de taper "@" / ">>" dans une console qui déforme les
# caractères Shift). Voir DEPLOYMENT.md. Idempotent : sans effet si déjà fait.
set -euo pipefail

ENV_FILE=".env.staging"

if [ ! -f "$ENV_FILE" ]; then
  echo "ERREUR : $ENV_FILE introuvable. Lancez ce script depuis /opt/La_Cave_du_Coin."
  exit 1
fi

if grep -q PGADMIN_DEFAULT_EMAIL "$ENV_FILE"; then
  echo "$ENV_FILE contient déjà PGADMIN_DEFAULT_EMAIL, rien à faire."
else
  {
    echo ""
    echo "PGADMIN_DEFAULT_EMAIL=admin@lacaveducoin.com"
    echo "PGADMIN_DEFAULT_PASSWORD=ChangeMePgAdmin123"
  } >> "$ENV_FILE"
  echo "Ajouté à $ENV_FILE : PGADMIN_DEFAULT_EMAIL / PGADMIN_DEFAULT_PASSWORD (valeurs par défaut)."
  echo "Changez PGADMIN_DEFAULT_PASSWORD si vous voulez une autre valeur (via nano, alphanumérique uniquement)."
fi
