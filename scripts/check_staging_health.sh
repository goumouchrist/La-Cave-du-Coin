#!/usr/bin/env bash
# Verifie l'etat de cash_sessions/returns dans staging apres un refresh, pour
# detecter une incoherence causee par un pg_restore --clean partiel.
# Usage : bash scripts/check_staging_health.sh
set -euo pipefail

docker exec staging-db-1 psql -U cave_du_coin -d cave_du_coin -c \
  "SELECT count(*) AS cash_sessions FROM cash_sessions;"
docker exec staging-db-1 psql -U cave_du_coin -d cave_du_coin -c \
  "SELECT count(*) AS returns, count(*) FILTER (WHERE refund_mode = 'ESPECES') AS especes FROM returns;"
docker exec staging-db-1 psql -U cave_du_coin -d cave_du_coin -c \
  "SELECT conname FROM pg_constraint WHERE conname = 'fk_returns_cash_session_id';"
