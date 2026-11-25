from __future__ import annotations

import sqlite3


def synchronize_vehicle_status(
    connection: sqlite3.Connection,
    vehicle_id: int,
    *,
    recover_damaged: bool = False,
) -> str | None:
    vehicle = connection.execute(
        "SELECT status FROM vehicles WHERE id = ?",
        (vehicle_id,),
    ).fetchone()
    if vehicle is None:
        return None

    active_ride = connection.execute(
        "SELECT 1 FROM rides WHERE vehicle_id = ? AND status = 'ACTIVE' LIMIT 1",
        (vehicle_id,),
    ).fetchone()
    active_reservation = connection.execute(
        """
        SELECT 1 FROM reservations
        WHERE vehicle_id = ? AND status IN ('ACTIVE', 'STARTED')
        LIMIT 1
        """,
        (vehicle_id,),
    ).fetchone()
    unresolved_fault = connection.execute(
        """
        SELECT 1 FROM fault_reports
        WHERE vehicle_id = ? AND status != 'RESOLVED'
        LIMIT 1
        """,
        (vehicle_id,),
    ).fetchone()

    if unresolved_fault is not None:
        status = "DAMAGED"
    elif active_ride is not None:
        status = "IN_USE"
    elif active_reservation is not None:
        reservation_status = connection.execute(
            """
            SELECT status FROM reservations
            WHERE vehicle_id = ? AND status IN ('ACTIVE', 'STARTED')
            ORDER BY CASE status WHEN 'STARTED' THEN 0 ELSE 1 END
            LIMIT 1
            """,
            (vehicle_id,),
        ).fetchone()
        status = "IN_USE" if reservation_status["status"] == "STARTED" else "RESERVED"
    elif vehicle["status"] in ("RESERVED", "IN_USE") or (
        recover_damaged and vehicle["status"] == "DAMAGED"
    ):
        status = "AVAILABLE"
    else:
        status = vehicle["status"]

    if status != vehicle["status"]:
        connection.execute(
            "UPDATE vehicles SET status = ? WHERE id = ?",
            (status, vehicle_id),
        )
    return status
