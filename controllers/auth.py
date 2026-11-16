from __future__ import annotations

import sqlite3
from typing import Any

from flask import flash, redirect, render_template, request, session, url_for

from models.auth import create_user, find_user_by_email, password_matches


def login() -> Any:
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = find_user_by_email(email)
        if user is None or not password_matches(user["password_hash"], password):
            flash("Nieprawidłowy e-mail lub hasło.", "error")
            return render_template("login.html", mode="login", email=email)
        session.clear()
        session["user_id"] = user["id"]
        flash("Zalogowano pomyślnie.", "success")
        return redirect(url_for("vehicles"))
    return render_template("login.html", mode="login", email="")


def register() -> Any:
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    if not name or not email or len(password) < 8:
        flash("Podaj nazwę, poprawny e-mail i hasło mające co najmniej 8 znaków.", "error")
        return render_template("login.html", mode="register", name=name, email=email)
    try:
        user_id = create_user(name, email, password)
    except sqlite3.IntegrityError:
        flash("Konto z podanym adresem e-mail już istnieje.", "error")
        return render_template("login.html", mode="register", name=name, email=email)
    session.clear()
    session["user_id"] = user_id
    flash("Konto zostało utworzone.", "success")
    return redirect(url_for("vehicles"))


def logout() -> Any:
    session.clear()
    flash("Wylogowano.", "success")
    return redirect(url_for("login"))
