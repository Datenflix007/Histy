from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Generator

from .migrations import apply_migrations, seed_db

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = os.getenv("HISTY_DB_PATH", str(BASE_DIR / "histy.db"))


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    path = db_path or DEFAULT_DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: str | None = None) -> None:
    path = db_path or DEFAULT_DB_PATH
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection(path)
    try:
        migrations_path = BASE_DIR / "migrations"
        seed_path = BASE_DIR / "seed"
        apply_migrations(conn, migrations_path)
        seed_db(conn, seed_path)
    finally:
        conn.close()


def db_dependency() -> Generator[sqlite3.Connection, None, None]:
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
