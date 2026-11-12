from __future__ import annotations

import math
import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import get_connection, query_all, query_one
from database.init_db import initialize_database


app = Flask(__name__)
app.config["SECRET_KEY"] = "turborower-local-development-key"
app.config["RATE_PER_MINUTE"] = 0.50
app.config["START_FEE"] = 3.00

initialize_database()


def login_required(view: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(view)
    def wrapped_view(*args: Any, **kwargs: Any) -> Any:
        if "user_id" not in session:
            flash("Zaloguj się, aby kontynuować.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


def current_user() -> sqlite3.Row | None:
    user_id = session.get("user_id")
    if user_id is None:
        return None
    return query_one("SELECT * FROM users WHERE id = ?", (user_id,))


@app.context_processor
def inject_current_user() -> dict[str, sqlite3.Row | None]:
    return {"current_user": current_user()}


@app.get("/")
def index() -> Any:
    if "user_id" in session:
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
    rows = query_all(
        """
        SELECT * FROM vehicles
        WHERE status = 'AVAILABLE'
        ORDER BY type, code
        """
    )
    return render_template("vehicles.html", vehicles=rows)


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
    return redirect(url_for("vehicle_details", vehicle_id=vehicle_id))


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
    return redirect(url_for("vehicle_details", vehicle_id=reservation["vehicle_id"]))


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
    return redirect(url_for("vehicle_details", vehicle_id=reservation["vehicle_id"]))


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
        connection.execute(
            """
            UPDATE rides
            SET ended_at = ?, duration_minutes = ?, cost = ?, status = 'COMPLETED'
            WHERE id = ?
            """,
            (now.isoformat(timespec="seconds"), duration_minutes, cost, ride_id),
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


@app.get("/history")
@login_required
def history() -> Any:
    rides = query_all(
        """
        SELECT r.*, v.code, v.type
        FROM rides r
        JOIN vehicles v ON v.id = r.vehicle_id
        WHERE r.user_id = ? AND r.status = 'COMPLETED'
        ORDER BY r.ended_at DESC
        """,
        (session["user_id"],),
    )
    total = sum((ride["cost"] or 0) for ride in rides)
    return render_template("history.html", rides=rides, total=total)


if __name__ == "__main__":
    app.run(debug=True)

