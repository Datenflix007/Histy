from __future__ import annotations

from pathlib import Path
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.db.migrations import apply_migrations, seed_db
from app.db.connection import db_dependency
from app.main import app


@pytest.fixture
def db_conn(tmp_path: Path) -> sqlite3.Connection:
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    base_dir = Path(__file__).resolve().parents[1]
    apply_migrations(conn, base_dir / "migrations")
    seed_db(conn, base_dir / "seed")
    yield conn
    conn.close()


@pytest.fixture
def client(db_conn: sqlite3.Connection) -> TestClient:
    def override_db():
        yield db_conn

    app.dependency_overrides[db_dependency] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
