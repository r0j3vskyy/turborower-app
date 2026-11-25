from __future__ import annotations

import sqlite3
from datetime import datetime

from database.db import get_connection, query_all, query_one


def available_vehicles() -> list[sqlite3.Row]:
    return query_all(
        """
        SELECT * FROM vehicles
        WHERE status = 'AVAILABLE'
        ORDER BY type, code
        """
    )


def all_vehicles() -> list[sqlite3.Row]:
    return query_all("SELECT * FROM vehicles ORDER BY type, code")


def get_vehicle(vehicle_id: int) -> sqlite3.Row | None:
    return query_one("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,))


def get_user_reservation(user_id: int, vehicle_id: int) -> sqlite3.Row | None:
    return query_one(
        """
        SELECT r.*, v.code, v.type
        FROM reservations r
        JOIN vehicles v ON v.id = r.vehicle_id
        WHERE r.user_id = ? AND r.vehicle_id = ?
          AND r.status IN ('ACTIVE', 'STARTED')
        ORDER BY r.id DESC
        LIMIT 1
        """,
        (user_id, vehicle_id),
    )


def reserve(user_id: int, vehicle_id: int, reserved_at: str, expires_at: str) -> bool:
    with get_connection() as connection:
        vehicle = connection.execute(
            "SELECT status FROM vehicles WHERE id = ?", (vehicle_id,)
        ).fetchone()
        if vehicle is None or vehicle["status"] != "AVAILABLE":
            return False
        updated = connection.execute(
            """
                UPDATE vehicles SET status = 'RESERVED'
                WHERE id = ? AND status = 'AVAILABLE'
                """,
                (vehicle_id,),
        )
        if updated.rowcount != 1:
                return False
        connection.execute(
                """
                INSERT INTO reservations
                (user_id, vehicle_id, reserved_at, expires_at, status)
                VALUES (?, ?, ?, ?, 'ACTIVE')
                """,
                (user_id, vehicle_id, reserved_at, expires_at),
        )
        return True


def cancel_reservation(user_id: int, reservation_id: int) -> int | None:
    with get_connection() as connection:
        reservation = connection.execute(
            """
            SELECT vehicle_id FROM reservations
            WHERE id = ? AND user_id = ? AND status = 'ACTIVE'
            """,
            (reservation_id, user_id),
        ).fetchone()
        if reservation is None:
            return None
        connection.execute(
            "UPDATE reservations SET status = 'CANCELLED' WHERE id = ?",
            (reservation_id,),
        )
        connection.execute(
            """
            UPDATE vehicles SET status = 'AVAILABLE'
            WHERE id = ? AND status = 'RESERVED'
            """,
            (reservation["vehicle_id"],),
        )
        return int(reservation["vehicle_id"])


def expire_reservations(now: str) -> int:
    with get_connection() as connection:
        expired = connection.execute(
            """
            SELECT r.id, r.user_id, r.vehicle_id
            FROM reservations r
            WHERE r.status = 'ACTIVE' AND r.expires_at <= ?
            """,
            (now,),
        ).fetchall()
        expired_count = 0
        for reservation in expired:
            active_ride = connection.execute(
                """
                SELECT id FROM rides
                WHERE user_id = ? AND vehicle_id = ? AND status = 'ACTIVE'
                """,
                (reservation["user_id"], reservation["vehicle_id"]),
            ).fetchone()
            if active_ride is not None:
                continue
            connection.execute(
                "UPDATE reservations SET status = 'CANCELLED' WHERE id = ?",
                (reservation["id"],),
            )
            connection.execute(
                """
                UPDATE vehicles SET status = 'AVAILABLE'
                WHERE id = ? AND status = 'RESERVED'
                """,
                (reservation["vehicle_id"],),
            )
            expired_count += 1
        return expired_count


def active_reservations_for_user(user_id: int) -> list[sqlite3.Row]:
    expire_reservations(datetime.now().isoformat(timespec="seconds"))
    return query_all(
        """
        SELECT r.*, v.code, v.type, v.latitude, v.longitude,
               v.status AS vehicle_status
        FROM reservations r
        JOIN vehicles v ON v.id = r.vehicle_id
        WHERE r.user_id = ? AND r.status = 'ACTIVE'
        ORDER BY r.reserved_at DESC
        """,
        (user_id,),
    )


def create_fault_report(
    user_id: int,
    vehicle_id: int,
    category: str,
    description: str,
) -> bool:
    with get_connection() as connection:
        vehicle = connection.execute(
            "SELECT id FROM vehicles WHERE id = ?",
            (vehicle_id,),
        ).fetchone()
        if vehicle is None:
            return False
        connection.execute(
            """
            INSERT INTO fault_reports
                (user_id, vehicle_id, category, description, status)
            VALUES (?, ?, ?, ?, 'OPEN')
            """,
            (user_id, vehicle_id, category, description),
        )
        connection.execute(
            "UPDATE vehicles SET status = 'DAMAGED' WHERE id = ?",
            (vehicle_id,),
        )
        return True
