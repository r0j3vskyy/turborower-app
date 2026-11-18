from __future__ import annotations

import sqlite3
from typing import Any

from werkzeug.security import check_password_hash, generate_password_hash

from database.db import get_connection, query_one


def find_user_by_email(email: str) -> sqlite3.Row | None:
    return query_one("SELECT * FROM users WHERE email = ?", (email,))


def find_user(user_id: int) -> sqlite3.Row | None:
    return query_one("SELECT * FROM users WHERE id = ?", (user_id,))


def create_user(name: str, email: str, password: str) -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO users (name, email, password_hash)
            VALUES (?, ?, ?)
            """,
            (name, email, generate_password_hash(password)),
        )
        return int(cursor.lastrowid)


def password_matches(password_hash: str, password: str) -> bool:
    return check_password_hash(password_hash, password)
