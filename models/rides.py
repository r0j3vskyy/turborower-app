from __future__ import annotations

import sqlite3
import math
from datetime import datetime

from database.db import get_connection, query_all, query_one


def get_active_ride(user_id: int, vehicle_id: int) -> sqlite3.Row | None:
    return query_one(
        """
        SELECT * FROM rides
        WHERE user_id = ? AND vehicle_id = ? AND status = 'ACTIVE'
        ORDER BY id DESC LIMIT 1
        """,
        (user_id, vehicle_id),
    )


def active_rides_for_user(user_id: int) -> list[dict[str, object]]:
    rows = query_all(
        """
        SELECT r.*, v.code, v.type, v.latitude, v.longitude
        FROM rides r
        JOIN vehicles v ON v.id = r.vehicle_id
        WHERE r.user_id = ? AND r.status = 'ACTIVE'
        ORDER BY r.started_at DESC
        """,
        (user_id,),
    )
    now = datetime.now()
    rides: list[dict[str, object]] = []
    for row in rows:
        started_at = datetime.fromisoformat(row["started_at"])
        elapsed_minutes = max(0, math.floor((now - started_at).total_seconds() / 60))
        elapsed_seconds = max(0, int((now - started_at).total_seconds()))
        estimated_cost = 3.00 + elapsed_minutes * 0.50
        distance_km = round(
            max(0.5, elapsed_minutes * 0.18 + (row["vehicle_id"] % 5) * 0.2),
            2,
        )
        ride = dict(row)
        ride.update(
            {
                "elapsed_minutes": elapsed_minutes,
                "elapsed_seconds": elapsed_seconds,
                "estimated_cost": estimated_cost,
                "distance_km": distance_km,
            }
        )
        rides.append(ride)
    return rides


def cancel_active_ride(user_id: int, ride_id: int) -> bool:
    with get_connection() as connection:
        ride = connection.execute(
            """
            SELECT vehicle_id FROM rides
            WHERE id = ? AND user_id = ? AND status = 'ACTIVE'
            """,
            (ride_id, user_id),
        ).fetchone()
        if ride is None:
            return False
        connection.execute(
            """
            UPDATE rides
            SET status = 'CANCELLED', ended_at = NULL,
                duration_minutes = NULL, cost = NULL, distance_km = NULL
            WHERE id = ?
            """,
            (ride_id,),
        )
        connection.execute(
            """
            UPDATE reservations SET status = 'CANCELLED'
            WHERE user_id = ? AND vehicle_id = ? AND status = 'STARTED'
            """,
            (user_id, ride["vehicle_id"]),
        )
        connection.execute(
            "UPDATE vehicles SET status = 'AVAILABLE' WHERE id = ?",
            (ride["vehicle_id"],),
        )
        return True


def start(user_id: int, reservation_id: int, started_at: str) -> int | None:
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
        cursor = connection.execute(
            """
            INSERT INTO rides (user_id, vehicle_id, started_at, status)
            VALUES (?, ?, ?, 'ACTIVE')
            """,
            (user_id, reservation["vehicle_id"], started_at),
        )
        connection.execute(
            "UPDATE reservations SET status = 'STARTED' WHERE id = ?",
            (reservation_id,),
        )
        connection.execute(
            "UPDATE vehicles SET status = 'IN_USE' WHERE id = ?",
            (reservation["vehicle_id"],),
        )
        return int(cursor.lastrowid)


def finish(
    user_id: int,
    ride_id: int,
    ended_at: str,
    duration_minutes: int,
    cost: float,
    distance_km: float,
) -> bool:
    with get_connection() as connection:
        ride = connection.execute(
            """
            SELECT vehicle_id FROM rides
            WHERE id = ? AND user_id = ? AND status = 'ACTIVE'
            """,
            (ride_id, user_id),
        ).fetchone()
        if ride is None:
            return False
        connection.execute(
            """
            UPDATE rides
            SET ended_at = ?, duration_minutes = ?, cost = ?, distance_km = ?, status = 'COMPLETED'
            WHERE id = ?
            """,
            (ended_at, duration_minutes, cost, distance_km, ride_id),
        )
        connection.execute(
            """
            UPDATE reservations SET status = 'CANCELLED'
            WHERE user_id = ? AND vehicle_id = ? AND status = 'STARTED'
            """,
            (user_id, ride["vehicle_id"]),
        )
        connection.execute(
            "UPDATE vehicles SET status = 'AVAILABLE' WHERE id = ?",
            (ride["vehicle_id"],),
        )
        return True


def completed_for_user(user_id: int) -> list[sqlite3.Row]:
    return query_all(
        """
        SELECT r.*, v.code, v.type, v.latitude, v.longitude
        FROM rides r
        JOIN vehicles v ON v.id = r.vehicle_id
        WHERE r.user_id = ? AND r.status = 'COMPLETED'
        ORDER BY r.ended_at DESC
        """,
        (user_id,),
    )
