from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from flask import flash, redirect, render_template, request, session, url_for

from models.rides import get_active_ride
from models.vehicles import (
    available_vehicles,
    all_vehicles,
    active_reservations_for_user,
    cancel_reservation as cancel_model,
    create_fault_report,
    get_user_reservation,
    get_vehicle,
    reserve,
)


def list_vehicles() -> Any:
    return render_template(
        "vehicles.html",
        vehicles=available_vehicles(),
        all_vehicles=all_vehicles(),
    )


def details(vehicle_id: int) -> Any:
    vehicle = get_vehicle(vehicle_id)
    if vehicle is None:
        flash("Nie znaleziono pojazdu.", "error")
        return redirect(url_for("vehicles"))
    user_id = session["user_id"]
    return render_template(
        "vehicle.html",
        vehicle=vehicle,
        reservation=get_user_reservation(user_id, vehicle_id),
        ride=get_active_ride(user_id, vehicle_id),
    )


def reserve_vehicle(vehicle_id: int) -> Any:
    now = datetime.now()
    if not reserve(
        session["user_id"],
        vehicle_id,
        now.isoformat(timespec="seconds"),
        (now + timedelta(minutes=15)).isoformat(timespec="seconds"),
    ):
        flash("Ten pojazd nie jest już dostępny.", "error")
        return redirect(url_for("vehicle_details", vehicle_id=vehicle_id))
    flash("Pojazd został zarezerwowany na 15 minut.", "success")
    return redirect(url_for("activity"))


def cancel_reservation(reservation_id: int) -> Any:
    vehicle_id = cancel_model(session["user_id"], reservation_id)
    if vehicle_id is None:
        flash("Nie znaleziono aktywnej rezerwacji.", "error")
        return redirect(url_for("vehicles"))
    flash("Rezerwacja została anulowana.", "success")
    return redirect(url_for("activity"))


def report_vehicle_fault(vehicle_id: int) -> Any:
    vehicle = get_vehicle(vehicle_id)
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
        if not create_fault_report(
            session["user_id"],
            vehicle_id,
            category,
            description,
        ):
            flash("Nie znaleziono pojazdu.", "error")
            return redirect(url_for("vehicles"))
        flash("Zgłoszenie usterki zostało przesłane.", "success")
        return redirect(url_for("vehicle_details", vehicle_id=vehicle_id))
    return render_template("fault_report.html", vehicle=vehicle)


def activity() -> Any:
    reservations = active_reservations_for_user(session["user_id"])
    from models.rides import active_rides_for_user
    rides = active_rides_for_user(session["user_id"])
    return render_template(
        "activity.html",
        reservations=reservations,
        rides=rides,
    )
