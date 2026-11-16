from __future__ import annotations

import sqlite3
from pathlib import Path

from werkzeug.security import generate_password_hash

from database.db import DATABASE_PATH, INSTANCE_DIR


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    battery_level INTEGER NOT NULL CHECK (battery_level BETWEEN 0 AND 100),
    status TEXT NOT NULL CHECK (status IN ('AVAILABLE', 'RESERVED', 'IN_USE', 'UNAVAILABLE'))
);

CREATE TABLE IF NOT EXISTS reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    vehicle_id INTEGER NOT NULL,
    reserved_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('ACTIVE', 'CANCELLED', 'STARTED')),
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
);

CREATE TABLE IF NOT EXISTS rides (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    vehicle_id INTEGER NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    duration_minutes INTEGER,
    cost REAL,
    status TEXT NOT NULL CHECK (status IN ('ACTIVE', 'COMPLETED')),
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
);
"""

DEMO_VEHICLES = (
    ("R-001", "Rower", 53.7784, 20.4801, 82, "AVAILABLE"),
    ("R-002", "Rower", 53.7768, 20.4825, 58, "AVAILABLE"),
    ("H-004", "Hulajnoga", 53.7791, 20.4776, 64, "AVAILABLE"),
    ("H-007", "Hulajnoga", 53.7755, 20.4841, 35, "UNAVAILABLE"),
)


def initialize_database() -> None:
    INSTANCE_DIR.mkdir(exist_ok=True)
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA)
        connection.execute(
            """
            INSERT OR IGNORE INTO users (id, name, email, password_hash)
            VALUES (1, ?, ?, ?)
            """,
            (
                "Użytkownik demonstracyjny",
                "demo@turborower.local",
                generate_password_hash("demo1234"),
            ),
        )
        connection.executemany(
            """
            INSERT OR IGNORE INTO vehicles
                (code, type, latitude, longitude, battery_level, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            DEMO_VEHICLES,
        )


if __name__ == "__main__":
    initialize_database()
    print(f"Baza danych została zainicjalizowana: {Path(DATABASE_PATH)}")

