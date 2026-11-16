from __future__ import annotations

import sqlite3
from functools import wraps
from typing import Any, Callable

from flask import Flask, redirect, session, url_for

from controllers.auth import login, logout, register
from controllers.rides import end_ride, history, start_ride
from controllers.vehicles import (
    cancel_reservation,
    details,
    list_vehicles,
    reserve_vehicle,
)
from database.init_db import initialize_database
from models.auth import find_user


app = Flask(__name__)
app.config["SECRET_KEY"] = "turborower-local-development-key"
app.config["RATE_PER_MINUTE"] = 0.50
app.config["START_FEE"] = 3.00

initialize_database()


def login_required(view: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(view)
    def wrapped_view(*args: Any, **kwargs: Any) -> Any:
        if "user_id" not in session:
            from flask import flash

            flash("Zaloguj się, aby kontynuować.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


def current_user() -> sqlite3.Row | None:
    user_id = session.get("user_id")
    return find_user(user_id) if user_id is not None else None


@app.context_processor
def inject_current_user() -> dict[str, sqlite3.Row | None]:
    return {"current_user": current_user()}


@app.get("/")
def index() -> Any:
    return redirect(url_for("vehicles" if "user_id" in session else "login"))


app.add_url_rule("/login", endpoint="login", view_func=login, methods=("GET", "POST"))
app.add_url_rule(
    "/register", endpoint="register", view_func=register, methods=("GET", "POST")
)
app.add_url_rule("/logout", endpoint="logout", view_func=logout, methods=("POST",))
app.add_url_rule(
    "/vehicles", endpoint="vehicles", view_func=login_required(list_vehicles)
)
app.add_url_rule(
    "/vehicles/<int:vehicle_id>",
    endpoint="vehicle_details",
    view_func=login_required(details),
)
app.add_url_rule(
    "/vehicles/<int:vehicle_id>/reserve",
    endpoint="reserve_vehicle",
    view_func=login_required(reserve_vehicle),
    methods=("POST",),
)
app.add_url_rule(
    "/reservations/<int:reservation_id>/cancel",
    endpoint="cancel_reservation",
    view_func=login_required(cancel_reservation),
    methods=("POST",),
)
app.add_url_rule(
    "/reservations/<int:reservation_id>/start",
    endpoint="start_ride",
    view_func=login_required(start_ride),
    methods=("POST",),
)
app.add_url_rule(
    "/rides/<int:ride_id>/end",
    endpoint="end_ride",
    view_func=login_required(end_ride),
    methods=("POST",),
)
app.add_url_rule(
    "/history", endpoint="history", view_func=login_required(history)
)


if __name__ == "__main__":
    app.run(debug=True)
