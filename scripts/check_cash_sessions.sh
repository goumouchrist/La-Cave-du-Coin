#!/usr/bin/env bash
# Verifie precisement le contenu de la table cash_sessions, cote base ET
# cote app (ORM), pour comparer avec ce que montre le navigateur.
# Usage : bash scripts/check_cash_sessions.sh
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "=== Comptage direct via psql sur le conteneur db ==="
docker compose exec -T db psql -U cave_du_coin -d cave_du_coin -c "SELECT count(id) AS total, max(id) AS dernier_id FROM cash_sessions;"

echo
echo "=== Comptage via l'app (ORM SQLAlchemy) ==="
docker compose exec -T app python -c "
from app.database import SessionLocal
from app.models import CashSession
db = SessionLocal()
print('total:', db.query(CashSession).count())
rows = db.query(CashSession).order_by(CashSession.id.desc()).limit(5).all()
for r in rows:
    print(r.id, r.opened_at, r.status)
"

echo
echo "=== Appel HTTP interne direct au conteneur app (contournant Caddy) ==="
docker compose exec -T app python -c "
import urllib.request
req = urllib.request.Request('http://localhost:8000/openapi.json')
print(urllib.request.urlopen(req).status)
"

echo
echo "=== Qui ecoute reellement sur le port 443 au niveau du systeme ==="
ss -tlnp | grep 443
