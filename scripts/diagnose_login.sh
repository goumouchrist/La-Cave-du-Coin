#!/usr/bin/env bash
# Diagnostic en lecture seule : liste les comptes et verifie si le mot de
# passe par defaut de superadmin correspond bien au hash stocke.
# Ne modifie rien. Usage : bash scripts/diagnose_login.sh
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

docker compose exec -T app python -c "
from app.database import SessionLocal
from app.models import User
from app.security import verify_password

db = SessionLocal()

print('=== Comptes existants ===')
for u in db.query(User).order_by(User.id).all():
    print(u.id, u.username, u.role, u.password_hash[:15] + '...')

user = db.query(User).filter(User.username == 'superadmin').first()
if user is None:
    print()
    print('AUCUN compte superadmin trouve.')
else:
    ok = verify_password('SuperAdmin123!', user.password_hash)
    print()
    print('Verification du mot de passe SuperAdmin123! sur le hash actuel :', ok)
"
