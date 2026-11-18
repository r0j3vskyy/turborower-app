from __future__ import annotations

import sqlite3

from database.db import get_connection, query_all


def dashboard_data() -> dict[str, object]:
    vehicles = query_all("SELECT * FROM vehicles ORDER BY code")
    users = query_all(
        "SELECT id, name, email, role, created_at FROM users ORDER BY id"
    )
    active_reservations = query_all(
        """
        SELECT r.id, r.reserved_at, r.expires_at, r.status,
               u.name AS user_name, v.code AS vehicle_code
        FROM reservations r
        JOIN users u ON u.id = r.user_id
        JOIN vehicles v ON v.id = r.vehicle_id
        WHERE r.status IN ('ACTIVE', 'STARTED')
        ORDER BY r.reserved_at DESC
        """
    )
    active_rides = query_all(
        """
        SELECT r.id, r.started_at, u.name AS user_name, v.code AS vehicle_code
        FROM rides r
        JOIN users u ON u.id = r.user_id
        JOIN vehicles v ON v.id = r.vehicle_id
        WHERE r.status = 'ACTIVE'
        ORDER BY r.started_at DESC
        """
    )
    fault_reports = query_all(
        """
        SELECT f.id, f.category, f.description, f.status, f.created_at,
               u.name AS user_name, v.code AS vehicle_code
        FROM fault_reports f
        JOIN users u ON u.id = f.user_id
        JOIN vehicles v ON v.id = f.vehicle_id
        WHERE f.status != 'RESOLVED'
        ORDER BY f.created_at DESC
        """
    )
    return {
        "vehicles": vehicles,
        "users": users,
        "active_reservations": active_reservations,
        "active_rides": active_rides,
        "fault_reports": fault_reports,
        "stats": {
            "vehicles": len(vehicles),
            "users": len(users),
            "reservations": len(active_reservations),
            "rides": len(active_rides),
        },
    }


def update_vehicle_status(vehicle_id: int, status: str) -> bool:
    allowed_statuses = (
        "AVAILABLE",
        "RESERVED",
        "IN_USE",
        "CHARGING",
        "DAMAGED",
        "UNAVAILABLE",
    )
    if status not in allowed_statuses:
        return False
    with get_connection() as connection:
        cursor = connection.execute(
            "UPDATE vehicles SET status = ? WHERE id = ?",
            (status, vehicle_id),
        )
        return cursor.rowcount == 1


def cancel_ride(ride_id: int) -> bool:
    with get_connection() as connection:
        ride = connection.execute(
            "SELECT * FROM rides WHERE id = ? AND status = 'ACTIVE'",
            (ride_id,),
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
            (ride["user_id"], ride["vehicle_id"]),
        )
        connection.execute(
            "UPDATE vehicles SET status = 'AVAILABLE' WHERE id = ?",
            (ride["vehicle_id"],),
        )
        return True


def cancel_reservation(reservation_id: int) -> bool:
    with get_connection() as connection:
        reservation = connection.execute(
            """
            SELECT id, vehicle_id
            FROM reservations
            WHERE id = ? AND status IN ('ACTIVE', 'STARTED')
            """,
            (reservation_id,),
        ).fetchone()
        if reservation is None:
            return False
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
        return True


def resolve_fault(report_id: int) -> bool:
    with get_connection() as connection:
        report = connection.execute(
            "SELECT vehicle_id FROM fault_reports WHERE id = ?",
            (report_id,),
        ).fetchone()
        if report is None:
            return False
        connection.execute(
            "UPDATE fault_reports SET status = 'RESOLVED' WHERE id = ?",
            (report_id,),
        )
        connection.execute(
            "UPDATE vehicles SET status = 'AVAILABLE' WHERE id = ?",
            (report["vehicle_id"],),
        )
        return True
