from __future__ import annotations

import math
from datetime import datetime
from typing import Any

from flask import current_app, flash, redirect, render_template, session, url_for

from database.db import query_one
from models.rides import cancel_active_ride, completed_for_user, finish, start


def start_ride(reservation_id: int) -> Any:
    reservation = query_one(
        "SELECT vehicle_id FROM reservations WHERE id = ? AND user_id = ?",
        (reservation_id, session["user_id"]),
    )
    ride_id = start(
        session["user_id"], reservation_id, datetime.now().isoformat(timespec="seconds")
    )
    if ride_id is None or reservation is None:
        flash("Nie znaleziono aktywnej rezerwacji.", "error")
        return redirect(url_for("vehicles"))
    flash("Przejazd rozpoczęty.", "success")
    return redirect(url_for("activity"))


def end_ride(ride_id: int) -> Any:
    now = datetime.now()
    # The model supplies the persisted start time; this lookup is kept in the
    # controller only for calculating the tariff from the request context.
    ride = query_one(
        "SELECT started_at, vehicle_id FROM rides WHERE id = ? AND user_id = ? AND status = 'ACTIVE'",
        (ride_id, session["user_id"]),
    )
    if ride is None:
        flash("Nie znaleziono aktywnego przejazdu.", "error")
        return redirect(url_for("vehicles"))
    duration = max(1, math.ceil((now - datetime.fromisoformat(ride["started_at"])).total_seconds() / 60))
    cost = current_app.config["START_FEE"] + duration * current_app.config["RATE_PER_MINUTE"]
    distance_km = round(max(0.5, duration * 0.18 + (ride["vehicle_id"] % 5) * 0.2), 2)
    if not finish(
        session["user_id"],
        ride_id,
        now.isoformat(timespec="seconds"),
        duration,
        cost,
        distance_km,
    ):
        flash("Nie znaleziono aktywnego przejazdu.", "error")
        return redirect(url_for("vehicles"))
    flash(f"Przejazd zakończony. Opłata: {cost:.2f} zł.", "success")
    return redirect(url_for("history"))


def history() -> Any:
    rides = completed_for_user(session["user_id"])
    return render_template(
        "history.html",
        rides=rides,
        total=sum((ride["cost"] or 0) for ride in rides),
    )


def cancel_ride(ride_id: int) -> Any:
    if not cancel_active_ride(session["user_id"], ride_id):
        flash("Nie znaleziono aktywnego przejazdu.", "error")
        return redirect(url_for("vehicles"))
    flash("Przejazd został anulowany. Pojazd ponownie jest dostępny.", "success")
    return redirect(url_for("vehicles"))
