from __future__ import annotations

import json
import os
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import current_user

from src import catalog
from src.auth import DemoUser, bp as auth_bp
from src.entities_routes import bp as entities_bp
from src.extensions import login_manager
from src.stats_routes import bp as stats_bp
from src.storage import Storage


def _load_config(app: Flask) -> None:
    config_path = Path(__file__).resolve().parent.parent / "config.json"
    if config_path.is_file():
        app.config.from_file(str(config_path), load=json.load)
    for key in ("SECRET_KEY", "DEMO_USER", "DEMO_PASSWORD", "REDIS_URL", "CATALOG_SEED_PATH"):
        env_val = os.getenv(key)
        if env_val:
            app.config[key] = env_val
    app.config.setdefault("SECRET_KEY", "change-me-demo")
    if not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-me-demo")
    app.secret_key = app.config["SECRET_KEY"]


def _bootstrap_demo_user(store: Storage, username: str, password: str) -> None:
    try:
        store.ensure_user(username, password)
    except Exception:
        pass


def create_app() -> Flask:
    app = Flask(__name__)
    _load_config(app)

    redis_url = app.config.get("REDIS_URL", os.getenv("REDIS_URL", "redis://redis:6379/0"))
    seed_path = app.config.get(
        "CATALOG_SEED_PATH",
        os.getenv(
            "CATALOG_SEED_PATH",
            str(Path(__file__).resolve().parent / "data" / "demo_seed.json"),
        ),
    )
    catalog.configure(seed_path)

    app.config.setdefault("DEMO_USER", os.getenv("DEMO_USER", "profesor"))
    app.config.setdefault("DEMO_PASSWORD", os.getenv("DEMO_PASSWORD", "profesor123"))
    app.config["CATALOG_SEED_PATH"] = seed_path
    store = Storage(redis_url)
    app.config["STORE"] = store
    _bootstrap_demo_user(store, app.config["DEMO_USER"], app.config["DEMO_PASSWORD"])

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id: str) -> DemoUser | None:
        role = app.config["STORE"].get_user_role(user_id)
        if not role:
            return None
        return DemoUser(id=user_id, role=role)

    @login_manager.unauthorized_handler
    def unauthorized():
        flash("Debes iniciar sesión para acceder.", "error")
        return redirect(url_for("auth.login", next=request.url))

    app.register_blueprint(auth_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(entities_bp)

    @app.context_processor
    def inject_globals():
        from flask_login import current_user as cu

        if cu.is_authenticated:
            return {"health": catalog.get_health()}
        return {}

    def _wants_html() -> bool:
        best = request.accept_mimetypes.best_match(["text/html", "application/json"])
        return best == "text/html" and request.accept_mimetypes[best] >= request.accept_mimetypes["application/json"]

    @app.errorhandler(404)
    def not_found(_):
        if _wants_html():
            return render_template("errors/404.html", title="No encontrado"), 404
        return {"error": "Ruta no encontrada"}, 404

    @app.errorhandler(500)
    def internal_error(_):
        if _wants_html():
            return (
                render_template(
                    "errors/500.html",
                    title="Error interno",
                ),
                500,
            )
        return {"error": "Error interno. Puedes continuar navegando o reintentar."}, 500

    @app.get("/")
    def home():
        if current_user.is_authenticated:
            return redirect(url_for("stats.dashboard"))
        return redirect(url_for("auth.login"))

    return app


app = create_app()
