"""Sauvegarde la base de données (SQLite en local, PostgreSQL en production
via Docker) vers un fichier horodaté dans BACKUP_DIR, puis purge les
sauvegardes plus vieilles que BACKUP_RETENTION_DAYS.

Usage : python scripts/backup.py
À planifier toutes les 4h (cf. DEPLOYMENT.md / scripts/register_backup_task.ps1).
"""
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.services.backup import backup_sqlite, copy_offsite, prune_old_backups

TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"


def backup_postgres(database_url: str, backup_dir: Path, now: datetime) -> Path:
    """Lance pg_dump à l'intérieur du conteneur 'db' via docker compose exec.
    Suppose que ce script est lancé depuis le PC hôte, dans le dossier du
    projet (là où se trouve docker-compose.yml)."""
    parsed = urlsplit(database_url.replace("postgresql+psycopg2", "postgresql"))
    user = parsed.username or "cave_du_coin"
    dbname = (parsed.path or "/cave_du_coin").lstrip("/")

    backup_dir.mkdir(parents=True, exist_ok=True)
    target = backup_dir / f"cave_du_coin_{now.strftime(TIMESTAMP_FORMAT)}.sql"

    with target.open("wb") as f:
        result = subprocess.run(
            ["docker", "compose", "exec", "-T", "db", "pg_dump", "-U", user, dbname],
            cwd=PROJECT_ROOT,
            stdout=f,
        )

    if result.returncode != 0:
        target.unlink(missing_ok=True)
        raise RuntimeError(f"pg_dump a échoué (code {result.returncode}). Docker Desktop est-il démarré ?")

    return target


def main():
    now = datetime.now(timezone.utc)
    backup_dir = PROJECT_ROOT / settings.BACKUP_DIR

    if settings.DATABASE_URL.startswith("sqlite"):
        db_path = PROJECT_ROOT / settings.DATABASE_URL.split("///")[-1]
        if not db_path.exists():
            print(f"Base introuvable: {db_path}")
            sys.exit(1)
        target = backup_sqlite(db_path, backup_dir, now)
    else:
        target = backup_postgres(settings.DATABASE_URL, backup_dir, now)

    print(f"Sauvegarde créée: {target}")

    if settings.OFFSITE_BACKUP_DIR:
        offsite_dir = Path(settings.OFFSITE_BACKUP_DIR)
        try:
            offsite_target = copy_offsite(target, offsite_dir)
            print(f"Copie hors-site: {offsite_target}")
        except OSError as exc:
            print(f"ATTENTION: copie hors-site échouée ({exc}). La sauvegarde locale reste disponible.")
        else:
            deleted_offsite = prune_old_backups(offsite_dir, settings.BACKUP_RETENTION_DAYS, now)
            for path in deleted_offsite:
                print(f"Ancienne sauvegarde hors-site supprimée: {path}")

    deleted = prune_old_backups(backup_dir, settings.BACKUP_RETENTION_DAYS, now)
    for path in deleted:
        print(f"Ancienne sauvegarde supprimée: {path}")


if __name__ == "__main__":
    main()
