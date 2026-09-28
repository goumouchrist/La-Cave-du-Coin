#!/usr/bin/env bash
# Verifie a quelle IP le conteneur caddy resout le nom "app", et compare
# avec les IP reelles des conteneurs app de prod et de staging sur chaque
# reseau. Objectif : detecter une collision d'alias Docker sur caddy-net.
# Usage : bash scripts/check_dns_collision.sh
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "=== Resolution DNS de 'app' depuis le conteneur caddy ==="
docker compose exec -T caddy nslookup app || true

echo
echo "=== IP du conteneur app de PROD sur chaque reseau ==="
docker inspect la_cave_du_coin-app-1 --format '{{range $net,$conf := .NetworkSettings.Networks}}{{$net}} -> {{$conf.IPAddress}}{{println}}{{end}}'

echo
echo "=== IP du conteneur app de STAGING sur chaque reseau ==="
docker inspect staging-app-1 --format '{{range $net,$conf := .NetworkSettings.Networks}}{{$net}} -> {{$conf.IPAddress}}{{println}}{{end}}'

echo
echo "=== Alias reseau declares pour chaque conteneur sur caddy-net ==="
docker inspect la_cave_du_coin-app-1 --format '{{json .NetworkSettings.Networks}}'
echo
docker inspect staging-app-1 --format '{{json .NetworkSettings.Networks}}'
