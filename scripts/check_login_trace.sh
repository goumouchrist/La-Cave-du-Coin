#!/usr/bin/env bash
# Verifie si les tentatives de connexion recentes laissent une trace dans
# cette base precise, et si is_active est bien a True pour les comptes.
# Usage : bash scripts/check_login_trace.sh
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

docker compose exec -T app python -c "
from app.database import SessionLocal
from app.models import User, Log

db = SessionLocal()

print('=== is_active par compte ===')
for u in db.query(User).order_by(User.id).all():
    print(u.id, u.username, 'is_active=', u.is_active)

print()
print('=== 10 dernieres lignes de logs (toutes actions) ===')
for l in db.query(Log).order_by(Log.id.desc()).limit(10).all():
    print(l.id, l.created_at, l.action, l.details)
"
