from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable


def _ensure_migration_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL
        );
        """
    )
    conn.commit()


def _existing_versions(conn: sqlite3.Connection) -> set[int]:
    cur = conn.execute("SELECT version FROM schema_migrations;")
    return {row[0] for row in cur.fetchall()}


def apply_migrations(conn: sqlite3.Connection, migrations_path: Path) -> None:
    _ensure_migration_table(conn)
    existing = _existing_versions(conn)
    for path in sorted(migrations_path.glob("*.sql")):
        version = int(path.name.split("_")[0])
        if version in existing:
            continue
        sql = path.read_text(encoding="ascii")
        conn.executescript(sql)
        conn.execute(
            "INSERT INTO schema_migrations (version, applied_at) VALUES (?, datetime('now'));",
            (version,),
        )
        conn.commit()


def seed_db(conn: sqlite3.Connection, seed_path: Path) -> None:
    cur = conn.execute("SELECT COUNT(1) FROM style_packages;")
    count = cur.fetchone()[0]
    if count:
        return
    sql = (seed_path / "seed.sql").read_text(encoding="ascii")
    conn.executescript(sql)
    conn.commit()
