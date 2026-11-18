from __future__ import annotations

import sqlite3
from functools import wraps
from pathlib import Path
from typing import Any, Callable

from flask import Flask, flash, redirect, render_template, request, send_from_directory, session, url_for
from database.db import get_connection, query_all, query_one
from database.init_db import initialize_database
from controllers.auth import login as auth_login
from controllers.auth import logout as auth_logout
from controllers.auth import register as auth_register
from controllers.vehicles import (
    activity as vehicle_activity,
    cancel_reservation as vehicle_cancel_reservation,
    details as vehicle_details_view,
    list_vehicles as vehicle_list,
    report_vehicle_fault as vehicle_report_fault,
    reserve_vehicle as vehicle_reserve,
)
from controllers.vehicles import reserve_vehicle as mvc_reserve_vehicle
from controllers.rides import (
    cancel_ride as ride_cancel,
    end_ride as ride_end,
    history as ride_history,
    start_ride as ride_start,
)
from models.vehicles import expire_reservations as expire_vehicle_reservations


app = Flask(__name__)
app.config["SECRET_KEY"] = "turborower-local-development-key"
app.config["RATE_PER_MINUTE"] = 0.50
app.config["START_FEE"] = 3.00

initialize_database()
ROOT_DIR = Path(__file__).resolve().parent


@app.get("/assets/logo/<path:filename>")
def project_asset(filename: str) -> Any:
    return send_from_directory(ROOT_DIR, f"assets/logo/{filename}")


def login_required(view: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(view)
    def wrapped_view(*args: Any, **kwargs: Any) -> Any:
        if "user_id" not in session:
            flash("Zaloguj się, aby kontynuować.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


def admin_required(view: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(view)
    def wrapped_view(*args: Any, **kwargs: Any) -> Any:
        user = current_user()
        if user is None:
            flash("Zaloguj się, aby kontynuować.", "error")
            return redirect(url_for("login"))
        if user["role"] != "ADMIN":
            flash("Brak uprawnień administratora.", "error")
            return redirect(url_for("vehicles"))
        return view(*args, **kwargs)

    return wrapped_view


def current_user() -> sqlite3.Row | None:
    user_id = session.get("user_id")
    if user_id is None:
        return None
    return query_one("SELECT * FROM users WHERE id = ?", (user_id,))


@app.before_request
def cleanup_expired_reservations() -> None:
    from datetime import datetime
    expire_vehicle_reservations(datetime.now().isoformat(timespec="seconds"))


@app.context_processor
def inject_current_user() -> dict[str, sqlite3.Row | None]:
    return {"current_user": current_user()}


@app.get("/")
def index() -> Any:
    if "user_id" in session:
        user = current_user()
        if user and user["role"] == "ADMIN":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("vehicles"))
    return redirect(url_for("login"))


@app.route("/login", methods=("GET", "POST"))
def login() -> Any:
    return auth_login()


@app.route("/register", methods=("GET", "POST"))
def register() -> Any:
    return auth_register()


@app.post("/logout")
def logout() -> Any:
    return auth_logout()


@app.get("/vehicles")
@login_required
def vehicles() -> Any:
    return vehicle_list()


@app.get("/vehicles/<int:vehicle_id>")
@login_required
def vehicle_details(vehicle_id: int) -> Any:
    return vehicle_details_view(vehicle_id)


@app.post("/vehicles/<int:vehicle_id>/reserve")
@login_required
def reserve_vehicle(vehicle_id: int) -> Any:
    return mvc_reserve_vehicle(vehicle_id)


@app.post("/reservations/<int:reservation_id>/cancel")
@login_required
def cancel_reservation(reservation_id: int) -> Any:
    return vehicle_cancel_reservation(reservation_id)


@app.post("/reservations/<int:reservation_id>/start")
@login_required
def start_ride(reservation_id: int) -> Any:
    return ride_start(reservation_id)


@app.post("/rides/<int:ride_id>/end")
@login_required
def end_ride(ride_id: int) -> Any:
    return ride_end(ride_id)


@app.post("/rides/<int:ride_id>/cancel")
@login_required
def cancel_ride(ride_id: int) -> Any:
    return ride_cancel(ride_id)


@app.route("/vehicles/<int:vehicle_id>/fault", methods=("GET", "POST"))
@login_required
def report_vehicle_fault(vehicle_id: int) -> Any:
    return vehicle_report_fault(vehicle_id)


@app.get("/admin")
@admin_required
def admin_dashboard() -> Any:
    vehicles = query_all("SELECT * FROM vehicles ORDER BY code")
    users = query_all("SELECT id, name, email, role, created_at FROM users ORDER BY id")
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
    stats = {
        "vehicles": len(vehicles),
        "users": len(users),
        "reservations": len(active_reservations),
        "rides": len(active_rides),
    }
    return render_template(
        "admin.html",
        vehicles=vehicles,
        users=users,
        active_reservations=active_reservations,
        active_rides=active_rides,
        fault_reports=fault_reports,
        stats=stats,
    )


@app.post("/admin/vehicles/<int:vehicle_id>/status")
@admin_required
def admin_update_vehicle_status(vehicle_id: int) -> Any:
    status = request.form.get("status", "")
    allowed_statuses = ("AVAILABLE", "RESERVED", "IN_USE", "CHARGING", "DAMAGED", "UNAVAILABLE")
    if status not in allowed_statuses:
        flash("Nieprawidłowy status pojazdu.", "error")
        return redirect(url_for("admin_dashboard"))
    with get_connection() as connection:
        cursor = connection.execute(
            "UPDATE vehicles SET status = ? WHERE id = ?",
            (status, vehicle_id),
        )
    if cursor.rowcount == 0:
        flash("Nie znaleziono pojazdu.", "error")
    else:
        flash("Status pojazdu został zaktualizowany.", "success")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/rides/<int:ride_id>/cancel")
@admin_required
def admin_cancel_ride(ride_id: int) -> Any:
    with get_connection() as connection:
        ride = connection.execute(
            "SELECT * FROM rides WHERE id = ? AND status = 'ACTIVE'",
            (ride_id,),
        ).fetchone()
        if ride is None:
            flash("Nie znaleziono aktywnego przejazdu.", "error")
            return redirect(url_for("admin_dashboard"))
        connection.execute(
            "UPDATE rides SET status = 'CANCELLED', ended_at = NULL, duration_minutes = NULL, cost = NULL WHERE id = ?",
            (ride_id,),
        )
        connection.execute(
            "UPDATE reservations SET status = 'CANCELLED' WHERE user_id = ? AND vehicle_id = ? AND status = 'STARTED'",
            (ride["user_id"], ride["vehicle_id"]),
        )
        connection.execute(
            "UPDATE vehicles SET status = 'AVAILABLE' WHERE id = ?",
            (ride["vehicle_id"],),
        )
    flash("Przejazd został anulowany przez administratora.", "success")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/reservations/<int:reservation_id>/cancel")
@admin_required
def admin_cancel_reservation(reservation_id: int) -> Any:
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
            flash("Nie znaleziono aktywnej rezerwacji.", "error")
            return redirect(url_for("admin_dashboard"))
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
    flash("Rezerwacja została anulowana przez administratora.", "success")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/faults/<int:report_id>/resolve")
@admin_required
def admin_resolve_fault(report_id: int) -> Any:
    with get_connection() as connection:
        report = connection.execute(
            "SELECT vehicle_id FROM fault_reports WHERE id = ?",
            (report_id,),
        ).fetchone()
        if report is None:
            flash("Nie znaleziono zgłoszenia usterki.", "error")
            return redirect(url_for("admin_dashboard"))
        connection.execute(
            "UPDATE fault_reports SET status = 'RESOLVED' WHERE id = ?",
            (report_id,),
        )
        connection.execute(
            "UPDATE vehicles SET status = 'AVAILABLE' WHERE id = ?",
            (report["vehicle_id"],),
        )
    flash("Zgłoszenie usterki zostało rozwiązane.", "success")
    return redirect(url_for("admin_dashboard"))


@app.get("/history")
@login_required
def history() -> Any:
    return ride_history()


@app.get("/pricing")
@login_required
def pricing() -> Any:
    return render_template(
        "pricing.html",
        start_fee=app.config["START_FEE"],
        rate_per_minute=app.config["RATE_PER_MINUTE"],
    )


@app.get("/activity")
@login_required
def activity() -> Any:
    return vehicle_activity()


if __name__ == "__main__":
    app.run(debug=True)

