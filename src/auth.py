from __future__ import annotations

from dataclasses import dataclass

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import UserMixin, login_required, login_user, logout_user
from redis.exceptions import ConnectionError as RedisConnectionError


@dataclass
class DemoUser(UserMixin):
    id: str
    role: str


bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    store = current_app.config["STORE"]

    if request.method == "POST":
        username = request.form.get("edUsername", "").strip()
        password = request.form.get("edPassword", "").strip()
        try:
            if store.check_password(username, password):
                role = store.get_user_role(username) or "user"
                login_user(DemoUser(id=username, role=role))
                return redirect(url_for("stats.dashboard"))
            flash("Credenciales inválidas", "error")
        except RedisConnectionError:
            flash(
                "Redis no está disponible. Ejecuta: docker compose down && docker compose up --build",
                "error",
            )
    return render_template("login.html", title="Iniciar sesión")


@bp.get("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
