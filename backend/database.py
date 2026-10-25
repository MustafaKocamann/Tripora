import json
import os
import sqlite3
from collections.abc import Callable
from contextlib import closing
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

JsonObject = dict[str, object]


def database_path() -> Path:
    """Return the configured SQLite database path."""
    configured = os.getenv("UNDERCOVER_DB_PATH")
    return Path(configured) if configured else ROOT / "backend" / "undercover.db"


def connect(path: Path | None = None) -> sqlite3.Connection:
    """Open a SQLite connection with named columns."""
    connection = sqlite3.connect(path or database_path())
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            data TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS plans (
            plan_id TEXT PRIMARY KEY,
            data TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            data TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS policies (
            policy_id TEXT PRIMARY KEY,
            data TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS handlers (
            handler_id TEXT PRIMARY KEY,
            data TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS claims (
            claim_id TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            status TEXT NOT NULL CHECK (
                status IN ('waiting', 'in_progress', 'waiting_for_sign_off', 'decided')
            )
        );
        CREATE TABLE IF NOT EXISTS decisions (
            claim_id TEXT PRIMARY KEY REFERENCES claims(claim_id),
            decision TEXT NOT NULL CHECK (decision IN ('approve', 'decline', 'refer')),
            payout REAL NOT NULL,
            rationale TEXT NOT NULL,
            policy_section TEXT NOT NULL,
            thread_id TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS activities (
            activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
            claim_id TEXT NOT NULL REFERENCES claims(claim_id),
            step TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS sign_offs (
            claim_id TEXT PRIMARY KEY REFERENCES claims(claim_id),
            handler_id TEXT NOT NULL REFERENCES handlers(handler_id),
            signed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS payments (
            claim_id TEXT PRIMARY KEY REFERENCES claims(claim_id),
            amount REAL NOT NULL,
            recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )


def _as_objects(value: object) -> list[JsonObject]:
    return cast(list[JsonObject], value)


def _insert_json_rows(
    connection: sqlite3.Connection,
    table: str,
    id_column: str,
    rows: list[JsonObject],
) -> None:
    for row in rows:
        identifier = str(row[id_column])
        connection.execute(
            f"INSERT OR IGNORE INTO {table} ({id_column}, data) VALUES (?, ?)",
            (identifier, json.dumps(row)),
        )


def initialize_database(
    path: Path | None = None,
    data_dir: Path = DATA_DIR,
    read_json: Callable[[Path], object] = _read_json,
    read_text: Callable[[Path], str] = _read_text,
) -> Path:
    """Create and seed the operational database."""
    target = path or database_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    company = cast(JsonObject, read_json(data_dir / "company.json"))
    plan_file = cast(JsonObject, read_json(data_dir / "plans.json"))
    customers = _as_objects(read_json(data_dir / "customers.json"))
    policies = _as_objects(read_json(data_dir / "policies.json"))
    handlers = _as_objects(read_json(data_dir / "handlers.json"))
    claims = _as_objects(read_json(data_dir / "claims.json"))
    policy_wording = read_text(data_dir / "policy_wording.md")

    with closing(connect(target)) as connection:
        _create_schema(connection)
        connection.execute(
            "INSERT OR IGNORE INTO settings (key, data) VALUES (?, ?)",
            ("company", json.dumps(company)),
        )
        connection.execute(
            "INSERT OR IGNORE INTO settings (key, data) VALUES (?, ?)",
            ("policy_wording", policy_wording),
        )
        _insert_json_rows(
            connection,
            "plans",
            "plan_id",
            [
                {**plan, "plan_id": plan["plan"]}
                for plan in _as_objects(plan_file["plans"])
            ],
        )
        _insert_json_rows(connection, "customers", "customer_id", customers)
        _insert_json_rows(connection, "policies", "policy_id", policies)
        _insert_json_rows(connection, "handlers", "handler_id", handlers)
        for claim in claims:
            connection.execute(
                "INSERT OR IGNORE INTO claims (claim_id, data, status) VALUES (?, ?, ?)",
                (str(claim["claim_id"]), json.dumps(claim), "waiting"),
            )
        connection.commit()
    return target
