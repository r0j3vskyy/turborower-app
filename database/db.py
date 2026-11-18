from __future__ import annotations

import sqlite3
import os
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = ROOT_DIR / "instance"
_database_setting = os.getenv("TURBOROWER_DATABASE")
if _database_setting:
    _database_path = Path(_database_setting)
    DATABASE_PATH = _database_path if _database_path.is_absolute() else ROOT_DIR / _database_path
else:
    DATABASE_PATH = INSTANCE_DIR / "turborower.db"


class ClosingConnection(sqlite3.Connection):
    def __enter__(self) -> "ClosingConnection":
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self.close()


def get_connection() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH, factory=ClosingConnection)
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

