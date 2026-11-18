from __future__ import annotations

import math
import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Callable

from flask import Flask, flash, redirect, render_template, request, send_from_directory, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import get_connection, query_all, query_one
from database.init_db import initialize_database


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


def expire_reservations() -> int:
    now = datetime.now()
    expired_count = 0
    with get_connection() as connection:
        expired = connection.execute(
            """
            SELECT id, vehicle_id
            FROM reservations
            WHERE status = 'ACTIVE' AND expires_at <= ?
            """,
            (now.isoformat(timespec="seconds"),),
        ).fetchall()
        for reservation in expired:
            active_ride = connection.execute(
                """
                SELECT id FROM rides
                WHERE user_id = (
                    SELECT user_id FROM reservations WHERE id = ?
                ) AND vehicle_id = ? AND status = 'ACTIVE'
                """,
                (reservation["id"], reservation["vehicle_id"]),
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


@app.before_request
def cleanup_expired_reservations() -> None:
    expire_reservations()


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
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = query_one("SELECT * FROM users WHERE email = ?", (email,))
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Nieprawidłowy e-mail lub hasło.", "error")
            return render_template("login.html", mode="login", email=email)
        session.clear()
        session["user_id"] = user["id"]
        session["role"] = user["role"]
        flash("Zalogowano pomyślnie.", "success")
        return redirect(url_for("vehicles"))
    return render_template("login.html", mode="login", email="")


@app.route("/register", methods=("GET", "POST"))
def register() -> Any:
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 8:
            flash("Podaj nazwę, poprawny e-mail i hasło mające co najmniej 8 znaków.", "error")
            return render_template("login.html", mode="register", name=name, email=email)
        try:
            with get_connection() as connection:
                cursor = connection.execute(
                    """
                    INSERT INTO users (name, email, password_hash)
                    VALUES (?, ?, ?)
                    """,
                    (name, email, generate_password_hash(password)),
                )
                session.clear()
                session["user_id"] = cursor.lastrowid
                session["role"] = "USER"
        except sqlite3.IntegrityError:
            flash("Konto z podanym adresem e-mail już istnieje.", "error")
            return render_template("login.html", mode="register", name=name, email=email)
        flash("Konto zostało utworzone.", "success")
        return redirect(url_for("vehicles"))
    return render_template("login.html", mode="register", name="", email="")


@app.post("/logout")
def logout() -> Any:
    session.clear()
    flash("Wylogowano.", "success")
    return redirect(url_for("login"))


@app.get("/vehicles")
@login_required
def vehicles() -> Any:
    available_rows = query_all(
        """
        SELECT * FROM vehicles
        WHERE status = 'AVAILABLE'
        ORDER BY type, code
        """
    )
    all_rows = query_all("SELECT * FROM vehicles ORDER BY type, code")
    return render_template("vehicles.html", vehicles=available_rows, all_vehicles=all_rows)


@app.get("/vehicles/<int:vehicle_id>")
@login_required
def vehicle_details(vehicle_id: int) -> Any:
    vehicle = query_one("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,))
    if vehicle is None:
        flash("Nie znaleziono pojazdu.", "error")
        return redirect(url_for("vehicles"))
    reservation = query_one(
        """
        SELECT r.*, v.code, v.type
        FROM reservations r
        JOIN vehicles v ON v.id = r.vehicle_id
        WHERE r.user_id = ? AND r.vehicle_id = ? AND r.status IN ('ACTIVE', 'STARTED')
        ORDER BY r.id DESC
        LIMIT 1
        """,
        (session["user_id"], vehicle_id),
    )
    ride = query_one(
        """
        SELECT * FROM rides
        WHERE user_id = ? AND vehicle_id = ? AND status = 'ACTIVE'
        ORDER BY id DESC LIMIT 1
        """,
        (session["user_id"], vehicle_id),
    )
    return render_template("vehicle.html", vehicle=vehicle, reservation=reservation, ride=ride)


@app.post("/vehicles/<int:vehicle_id>/reserve")
@login_required
def reserve_vehicle(vehicle_id: int) -> Any:
    now = datetime.now()
    expires_at = now + timedelta(minutes=15)
    with get_connection() as connection:
        vehicle = connection.execute(
            "SELECT status FROM vehicles WHERE id = ?", (vehicle_id,)
        ).fetchone()
        if vehicle is None:
            flash("Nie znaleziono pojazdu.", "error")
            return redirect(url_for("vehicles"))
        if vehicle["status"] != "AVAILABLE":
            flash("Ten pojazd nie jest już dostępny.", "error")
            return redirect(url_for("vehicle_details", vehicle_id=vehicle_id))
        connection.execute(
            """
            INSERT INTO reservations
                (user_id, vehicle_id, reserved_at, expires_at, status)
            VALUES (?, ?, ?, ?, 'ACTIVE')
            """,
            (session["user_id"], vehicle_id, now.isoformat(timespec="seconds"), expires_at.isoformat(timespec="seconds")),
        )
        connection.execute(
            "UPDATE vehicles SET status = 'RESERVED' WHERE id = ? AND status = 'AVAILABLE'",
            (vehicle_id,),
        )
    flash("Pojazd został zarezerwowany na 15 minut.", "success")
    return redirect(url_for("activity"))


@app.post("/reservations/<int:reservation_id>/cancel")
@login_required
def cancel_reservation(reservation_id: int) -> Any:
    with get_connection() as connection:
        reservation = connection.execute(
            """
            SELECT * FROM reservations
            WHERE id = ? AND user_id = ? AND status = 'ACTIVE'
            """,
            (reservation_id, session["user_id"]),
        ).fetchone()
        if reservation is None:
            flash("Nie znaleziono aktywnej rezerwacji.", "error")
            return redirect(url_for("vehicles"))
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
    flash("Rezerwacja została anulowana.", "success")
    return redirect(url_for("activity"))


@app.post("/reservations/<int:reservation_id>/start")
@login_required
def start_ride(reservation_id: int) -> Any:
    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as connection:
        reservation = connection.execute(
            """
            SELECT * FROM reservations
            WHERE id = ? AND user_id = ? AND status = 'ACTIVE'
            """,
            (reservation_id, session["user_id"]),
        ).fetchone()
        if reservation is None:
            flash("Nie znaleziono aktywnej rezerwacji.", "error")
            return redirect(url_for("vehicles"))
        connection.execute(
            """
            INSERT INTO rides (user_id, vehicle_id, started_at, status)
            VALUES (?, ?, ?, 'ACTIVE')
            """,
            (session["user_id"], reservation["vehicle_id"], now),
        )
        connection.execute(
            "UPDATE reservations SET status = 'STARTED' WHERE id = ?",
            (reservation_id,),
        )
        connection.execute(
            "UPDATE vehicles SET status = 'IN_USE' WHERE id = ?",
            (reservation["vehicle_id"],),
        )
    flash("Przejazd rozpoczęty.", "success")
    return redirect(url_for("activity"))


@app.post("/rides/<int:ride_id>/end")
@login_required
def end_ride(ride_id: int) -> Any:
    now = datetime.now()
    with get_connection() as connection:
        ride = connection.execute(
            """
            SELECT * FROM rides
            WHERE id = ? AND user_id = ? AND status = 'ACTIVE'
            """,
            (ride_id, session["user_id"]),
        ).fetchone()
        if ride is None:
            flash("Nie znaleziono aktywnego przejazdu.", "error")
            return redirect(url_for("vehicles"))
        started_at = datetime.fromisoformat(ride["started_at"])
        duration_minutes = max(1, math.ceil((now - started_at).total_seconds() / 60))
        cost = app.config["START_FEE"] + duration_minutes * app.config["RATE_PER_MINUTE"]
        distance_km = round(max(0.5, duration_minutes * 0.18 + (ride["vehicle_id"] % 5) * 0.2), 2)
        connection.execute(
            """
            UPDATE rides
            SET ended_at = ?, duration_minutes = ?, cost = ?, distance_km = ?, status = 'COMPLETED'
            WHERE id = ?
            """,
            (now.isoformat(timespec="seconds"), duration_minutes, cost, distance_km, ride_id),
        )
        connection.execute(
            "UPDATE reservations SET status = 'CANCELLED' WHERE user_id = ? AND vehicle_id = ? AND status = 'STARTED'",
            (session["user_id"], ride["vehicle_id"]),
        )
        connection.execute(
            "UPDATE vehicles SET status = 'AVAILABLE' WHERE id = ?",
            (ride["vehicle_id"],),
        )
    flash(f"Przejazd zakończony. Opłata: {cost:.2f} zł.", "success")
    return redirect(url_for("history"))


@app.post("/rides/<int:ride_id>/cancel")
@login_required
def cancel_ride(ride_id: int) -> Any:
    with get_connection() as connection:
        ride = connection.execute(
            """
            SELECT * FROM rides
            WHERE id = ? AND user_id = ? AND status = 'ACTIVE'
            """,
            (ride_id, session["user_id"]),
        ).fetchone()
        if ride is None:
            flash("Nie znaleziono aktywnego przejazdu.", "error")
            return redirect(url_for("vehicles"))
        connection.execute(
            "UPDATE rides SET status = 'CANCELLED', ended_at = NULL, duration_minutes = NULL, cost = NULL WHERE id = ?",
            (ride_id,),
        )
        connection.execute(
            """
            UPDATE reservations
            SET status = 'CANCELLED'
            WHERE user_id = ? AND vehicle_id = ? AND status = 'STARTED'
            """,
            (session["user_id"], ride["vehicle_id"]),
        )
        connection.execute(
            "UPDATE vehicles SET status = 'AVAILABLE' WHERE id = ?",
            (ride["vehicle_id"],),
        )
    flash("Przejazd został anulowany. Pojazd ponownie jest dostępny.", "success")
    return redirect(url_for("vehicles"))


@app.route("/vehicles/<int:vehicle_id>/fault", methods=("GET", "POST"))
@login_required
def report_vehicle_fault(vehicle_id: int) -> Any:
    vehicle = query_one("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,))
    if vehicle is None:
        flash("Nie znaleziono pojazdu.", "error")
        return redirect(url_for("vehicles"))
    if request.method == "POST":
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        allowed_categories = ("HAMULCE", "KOLO_OPONA", "NAPED", "AKUMULATOR", "INNE")
        if category not in allowed_categories:
            flash("Wybierz kategorię usterki.", "error")
            return render_template("fault_report.html", vehicle=vehicle)
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO fault_reports
                    (user_id, vehicle_id, category, description, status)
                VALUES (?, ?, ?, ?, 'OPEN')
                """,
                (session["user_id"], vehicle_id, category, description),
            )
            connection.execute(
                "UPDATE vehicles SET status = 'DAMAGED' WHERE id = ?",
                (vehicle_id,),
            )
        flash("Zgłoszenie usterki zostało przesłane.", "success")
        return redirect(url_for("vehicle_details", vehicle_id=vehicle_id))
    return render_template("fault_report.html", vehicle=vehicle)


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
    rides = query_all(
        """
        SELECT r.*, v.code, v.type, v.latitude, v.longitude
        FROM rides r
        JOIN vehicles v ON v.id = r.vehicle_id
        WHERE r.user_id = ? AND r.status = 'COMPLETED'
        ORDER BY r.ended_at DESC
        """,
        (session["user_id"],),
    )
    total = sum((ride["cost"] or 0) for ride in rides)
    return render_template("history.html", rides=rides, total=total)


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
    expire_reservations()
    reservations = query_all(
        """
        SELECT r.*, v.code, v.type, v.latitude, v.longitude, v.status AS vehicle_status
        FROM reservations r
        JOIN vehicles v ON v.id = r.vehicle_id
        WHERE r.user_id = ? AND r.status = 'ACTIVE'
        ORDER BY r.reserved_at DESC
        """,
        (session["user_id"],),
    )
    ride_rows = query_all(
        """
        SELECT r.*, v.code, v.type, v.latitude, v.longitude
        FROM rides r
        JOIN vehicles v ON v.id = r.vehicle_id
        WHERE r.user_id = ? AND r.status = 'ACTIVE'
        ORDER BY r.started_at DESC
        """,
        (session["user_id"],),
    )

    rides = []
    for ride_row in ride_rows:
        started_at = datetime.fromisoformat(ride_row["started_at"])
        elapsed_minutes = max(0, math.floor((datetime.now() - started_at).total_seconds() / 60))
        elapsed_seconds = max(0, int((datetime.now() - started_at).total_seconds()))
        estimated_cost = app.config["START_FEE"] + elapsed_minutes * app.config["RATE_PER_MINUTE"]
        distance_km = round(max(0.5, elapsed_minutes * 0.18 + (ride_row["vehicle_id"] % 5) * 0.2), 2)
        ride = dict(ride_row)
        ride.update({
            "elapsed_minutes": elapsed_minutes,
            "elapsed_seconds": elapsed_seconds,
            "estimated_cost": estimated_cost,
            "distance_km": distance_km,
        })
        rides.append(ride)

    return render_template("activity.html", reservations=reservations, rides=rides)


if __name__ == "__main__":
    app.run(debug=True)

