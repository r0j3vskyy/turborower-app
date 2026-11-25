from __future__ import annotations

from typing import Any

from flask import flash, redirect, render_template, request, url_for

from models.admin import (
    cancel_reservation,
    cancel_ride,
    dashboard_data,
    resolve_fault,
    update_vehicle_status,
)


def dashboard() -> Any:
    data = dashboard_data()
    return render_template("admin.html", **data)


def change_vehicle_status(vehicle_id: int) -> Any:
    status = request.form.get("status", "")
    if not update_vehicle_status(vehicle_id, status):
        flash("Nieprawidłowy status lub pojazd nie istnieje.", "error")
    else:
        flash("Status pojazdu został zaktualizowany.", "success")
    return redirect(url_for("admin_dashboard"))


def cancel_admin_ride(ride_id: int) -> Any:
    if not cancel_ride(ride_id):
        flash("Nie znaleziono aktywnego przejazdu.", "error")
    else:
        flash("Przejazd został anulowany przez administratora.", "success")
    return redirect(url_for("admin_dashboard"))


def cancel_admin_reservation(reservation_id: int) -> Any:
    if not cancel_reservation(reservation_id):
        flash("Nie znaleziono aktywnej rezerwacji.", "error")
    else:
        flash("Rezerwacja została anulowana przez administratora.", "success")
    return redirect(url_for("admin_dashboard"))


def resolve_admin_fault(report_id: int) -> Any:
    if not resolve_fault(report_id):
        flash("Nie znaleziono zgłoszenia usterki.", "error")
    else:
        flash("Zgłoszenie usterki zostało rozwiązane.", "success")
    return redirect(url_for("admin_dashboard"))
