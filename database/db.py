from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = ROOT_DIR / "instance"
DATABASE_PATH = INSTANCE_DIR / "turborower.db"


def get_connection() -> sqlite3.Connection:
    INSTANCE_DIR.mkdir(exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def query_all(
    sql: str, parameters: tuple[Any, ...] = ()
) -> list[sqlite3.Row]:
    with get_connection() as connection:
        return connection.execute(sql, parameters).fetchall()


def query_one(
    sql: str, parameters: tuple[Any, ...] = ()
) -> sqlite3.Row | None:
    with get_connection() as connection:
        return connection.execute(sql, parameters).fetchone()

