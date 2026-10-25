import json
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.database import DATA_DIR, initialize_database
from backend.main import app


def table_count(path: Path, table: str) -> int:
    with closing(sqlite3.connect(path)) as connection:
        row = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    assert row is not None
    return int(row[0])


def test_seed_is_idempotent_and_operational_only(tmp_path: Path) -> None:
    opened: list[Path] = []

    def read_json(path: Path) -> object:
        opened.append(path)
        return json.loads(path.read_text(encoding="utf-8"))

    def read_text(path: Path) -> str:
        opened.append(path)
        return path.read_text(encoding="utf-8")

    database = tmp_path / "undercover.db"
    initialize_database(database, DATA_DIR, read_json, read_text)
    initialize_database(database, DATA_DIR, read_json, read_text)

    assert table_count(database, "claims") == 25
    assert table_count(database, "customers") == 49
    assert table_count(database, "policies") == 50
    assert table_count(database, "plans") == 3
    assert table_count(database, "handlers") == 3
    assert all("evals" not in path.parts for path in opened)
    assert all("security" not in path.parts for path in opened)
    assert all(path.name != "claims_manual.md" for path in opened)


def test_health_is_exact(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("UNDERCOVER_DB_PATH", str(tmp_path / "health.db"))
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
