import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.services.backup import backup_sqlite, copy_offsite, prune_old_backups


def make_sqlite_db(path: Path):
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute("INSERT INTO t (name) VALUES ('hello')")
    conn.commit()
    conn.close()


def test_backup_sqlite_creates_timestamped_copy(tmp_path):
    db_path = tmp_path / "cave_du_coin.db"
    make_sqlite_db(db_path)
    backup_dir = tmp_path / "backups"
    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    target = backup_sqlite(db_path, backup_dir, now)

    assert target.exists()
    assert target.name == "cave_du_coin_20260101_120000.db"

    conn = sqlite3.connect(str(target))
    rows = conn.execute("SELECT name FROM t").fetchall()
    assert rows == [("hello",)]


def test_backup_sqlite_is_independent_copy(tmp_path):
    db_path = tmp_path / "cave_du_coin.db"
    make_sqlite_db(db_path)
    backup_dir = tmp_path / "backups"

    target = backup_sqlite(db_path, backup_dir)

    conn = sqlite3.connect(str(db_path))
    conn.execute("INSERT INTO t (name) VALUES ('added after backup')")
    conn.commit()
    conn.close()

    backup_conn = sqlite3.connect(str(target))
    rows = backup_conn.execute("SELECT COUNT(*) FROM t").fetchone()
    assert rows[0] == 1, "la sauvegarde ne doit pas voir les écritures faites après coup"


def test_prune_old_backups_deletes_only_expired_files(tmp_path):
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()

    old_file = backup_dir / "old.db"
    recent_file = backup_dir / "recent.db"
    old_file.write_text("old")
    recent_file.write_text("recent")

    now = datetime.now(timezone.utc)
    old_time = (now - timedelta(days=30)).timestamp()
    recent_time = (now - timedelta(hours=1)).timestamp()
    import os

    os.utime(old_file, (old_time, old_time))
    os.utime(recent_file, (recent_time, recent_time))

    deleted = prune_old_backups(backup_dir, retention_days=14, now=now)

    assert deleted == [old_file]
    assert not old_file.exists()
    assert recent_file.exists()


def test_prune_old_backups_on_missing_directory_returns_empty(tmp_path):
    deleted = prune_old_backups(tmp_path / "does-not-exist", retention_days=14)
    assert deleted == []


def test_copy_offsite_creates_identical_file_in_target_dir(tmp_path):
    db_path = tmp_path / "cave_du_coin.db"
    make_sqlite_db(db_path)
    backup_dir = tmp_path / "backups"
    offsite_dir = tmp_path / "onedrive" / "SauvegardesCaisse"

    target = backup_sqlite(db_path, backup_dir)
    offsite_target = copy_offsite(target, offsite_dir)

    assert offsite_target.exists()
    assert offsite_target.read_bytes() == target.read_bytes()


def test_copy_offsite_creates_missing_directories(tmp_path):
    db_path = tmp_path / "cave_du_coin.db"
    make_sqlite_db(db_path)
    target = backup_sqlite(db_path, tmp_path / "backups")

    offsite_dir = tmp_path / "does" / "not" / "exist" / "yet"
    assert not offsite_dir.exists()

    copy_offsite(target, offsite_dir)
    assert offsite_dir.exists()
