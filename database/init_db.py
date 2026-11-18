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
    role TEXT NOT NULL DEFAULT 'USER' CHECK (role IN ('USER', 'ADMIN')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    battery_level INTEGER NOT NULL CHECK (battery_level BETWEEN 0 AND 100),
    status TEXT NOT NULL CHECK (
        status IN ('AVAILABLE', 'RESERVED', 'IN_USE', 'CHARGING', 'DAMAGED', 'UNAVAILABLE')
    )
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
    distance_km REAL,
    status TEXT NOT NULL CHECK (
        status IN ('ACTIVE', 'COMPLETED', 'CANCELLED')
    ),
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
);

CREATE TABLE IF NOT EXISTS fault_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    vehicle_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'OPEN' CHECK (
        status IN ('OPEN', 'IN_PROGRESS', 'RESOLVED')
    ),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
);
"""

DEMO_VEHICLES = (
    ("R-001", "Rower", 53.7784, 20.4801, 82, "AVAILABLE"),
    ("R-002", "Rower", 53.7768, 20.4825, 58, "AVAILABLE"),
    ("R-003", "Rower", 53.7812, 20.4738, 91, "AVAILABLE"),
    ("R-004", "Rower", 53.7836, 20.4872, 47, "CHARGING"),
    ("R-005", "Rower", 53.7719, 20.4951, 73, "AVAILABLE"),
    ("R-006", "Rower", 53.7685, 20.4724, 29, "DAMAGED"),
    ("H-004", "Hulajnoga", 53.7791, 20.4776, 64, "AVAILABLE"),
    ("H-005", "Hulajnoga", 53.7828, 20.4831, 88, "AVAILABLE"),
    ("H-006", "Hulajnoga", 53.7742, 20.4668, 54, "CHARGING"),
    ("H-007", "Hulajnoga", 53.7755, 20.4841, 35, "UNAVAILABLE"),
    ("H-008", "Hulajnoga", 53.7871, 20.4789, 76, "AVAILABLE"),
    ("H-009", "Hulajnoga", 53.7697, 20.4884, 22, "DAMAGED"),
)


def _columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()}


def initialize_database() -> None:
    INSTANCE_DIR.mkdir(exist_ok=True)
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA)

        if "role" not in _columns(connection, "users"):
            connection.execute(
                "ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'USER'"
            )
        if "distance_km" not in _columns(connection, "rides"):
            connection.execute("ALTER TABLE rides ADD COLUMN distance_km REAL")

        connection.execute(
            """
            INSERT OR IGNORE INTO users (name, email, password_hash, role)
            VALUES (?, ?, ?, 'USER')
            """,
            (
                "Użytkownik demonstracyjny",
                "demo@turborower.local",
                generate_password_hash("demo1234"),
            ),
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO users (name, email, password_hash, role)
            VALUES (?, ?, ?, 'ADMIN')
            """,
            (
                "Administrator demonstracyjny",
                "admin@turborower.local",
                generate_password_hash("admin1234"),
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
    print(f"Baza danych zostala zainicjalizowana: {Path(DATABASE_PATH)}")
