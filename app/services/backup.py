import shutil
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"


def backup_sqlite(db_path: Path, backup_dir: Path, now: datetime | None = None) -> Path:
    """Copie une base SQLite vivante vers un fichier horodaté, sans verrouiller
    ni corrompre la base source (utilise l'API de sauvegarde native de SQLite,
    cohérente même si l'application écrit en même temps)."""
    now = now or datetime.now(timezone.utc)
    backup_dir.mkdir(parents=True, exist_ok=True)

    stem = db_path.stem
    target = backup_dir / f"{stem}_{now.strftime(TIMESTAMP_FORMAT)}.db"

    source_conn = sqlite3.connect(str(db_path))
    dest_conn = sqlite3.connect(str(target))
    try:
        source_conn.backup(dest_conn)
    finally:
        dest_conn.close()
        source_conn.close()

    return target


def copy_offsite(backup_file: Path, offsite_dir: Path) -> Path:
    """Copie une sauvegarde déjà créée vers un second dossier (ex: un dossier
    synchronisé OneDrive/Google Drive), pour survivre à une panne ou un vol du
    PC qui héberge la base."""
    offsite_dir.mkdir(parents=True, exist_ok=True)
    target = offsite_dir / backup_file.name
    shutil.copy2(backup_file, target)
    return target


def prune_old_backups(backup_dir: Path, retention_days: int, now: datetime | None = None) -> list[Path]:
    """Supprime les fichiers de sauvegarde plus vieux que retention_days. Renvoie
    la liste des fichiers supprimés."""
    if not backup_dir.exists():
        return []

    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=retention_days)
    deleted = []

    for path in backup_dir.iterdir():
        if not path.is_file():
            continue
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        if mtime < cutoff:
            path.unlink()
            deleted.append(path)

    return deleted
