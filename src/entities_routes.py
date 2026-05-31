from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required

from src.persist_forms import (
    parse_alert,
    parse_bookmark,
    parse_comparison,
    parse_note,
    parse_view,
    read_body,
)
from src.user_workspace import normalize_note


bp = Blueprint("entities", __name__)


def _storage_error(exc: Exception):
    return jsonify({"error": f"Error de almacenamiento: {exc!s}"}), 500


@bp.get("/api/views")
@login_required
def list_views():
    try:
        store = current_app.config["STORE"]
        return jsonify({"items": [v.to_dict() for v in store.list_views(current_user.id)]})
    except Exception as exc:
        return _storage_error(exc)


@bp.post("/api/views")
@login_required
def save_view():
    store = current_app.config["STORE"]
    view, err = parse_view(read_body(request), current_user.id)
    if err:
        return jsonify({"error": err}), 400
    try:
        store.save_view(view)
        return jsonify({"ok": True, "item": view.to_dict()})
    except Exception as exc:
        return _storage_error(exc)


@bp.delete("/api/views/<view_id>")
@login_required
def delete_view(view_id: str):
    try:
        store = current_app.config["STORE"]
        store.delete_view(current_user.id, view_id)
        return jsonify({"ok": True})
    except Exception as exc:
        return _storage_error(exc)


@bp.get("/api/bookmarks")
@login_required
def list_bookmarks():
    try:
        store = current_app.config["STORE"]
        return jsonify({"items": [b.to_dict() for b in store.list_bookmarks(current_user.id)]})
    except Exception as exc:
        return _storage_error(exc)


@bp.post("/api/bookmarks")
@login_required
def save_bookmark():
    store = current_app.config["STORE"]
    bm, err = parse_bookmark(read_body(request), current_user.id)
    if err:
        return jsonify({"error": err}), 400
    try:
        store.save_bookmark(bm)
        return jsonify({"ok": True, "item": bm.to_dict()})
    except Exception as exc:
        return _storage_error(exc)


@bp.delete("/api/bookmarks/<bookmark_id>")
@login_required
def delete_bookmark(bookmark_id: str):
    try:
        store = current_app.config["STORE"]
        store.delete_bookmark(current_user.id, bookmark_id)
        return jsonify({"ok": True})
    except Exception as exc:
        return _storage_error(exc)


@bp.get("/api/notes")
@login_required
def list_notes():
    try:
        store = current_app.config["STORE"]
        return jsonify({"items": [n.to_dict() for n in store.list_notes(current_user.id)]})
    except Exception as exc:
        return _storage_error(exc)


@bp.post("/api/notes")
@login_required
def save_note():
    store = current_app.config["STORE"]
    body = read_body(request)
    note, err = parse_note(body, current_user.id)
    if err:
        return jsonify({"error": err}), 400
    note, err = normalize_note(note, store, current_user.id)
    if err:
        return jsonify({"error": err}), 400
    try:
        store.save_note(note)
        return jsonify({"ok": True, "item": note.to_dict()})
    except Exception as exc:
        return _storage_error(exc)


@bp.delete("/api/notes/<note_id>")
@login_required
def delete_note(note_id: str):
    try:
        store = current_app.config["STORE"]
        store.delete_note(current_user.id, note_id)
        return jsonify({"ok": True})
    except Exception as exc:
        return _storage_error(exc)


@bp.get("/api/comparisons")
@login_required
def list_comparisons():
    try:
        store = current_app.config["STORE"]
        return jsonify({"items": [c.to_dict() for c in store.list_comparisons(current_user.id)]})
    except Exception as exc:
        return _storage_error(exc)


@bp.post("/api/comparisons")
@login_required
def save_comparison():
    store = current_app.config["STORE"]
    comp, err = parse_comparison(read_body(request), current_user.id)
    if err:
        return jsonify({"error": err}), 400
    try:
        store.save_comparison(comp)
        return jsonify({"ok": True, "item": comp.to_dict()})
    except Exception as exc:
        return _storage_error(exc)


@bp.delete("/api/comparisons/<comp_id>")
@login_required
def delete_comparison(comp_id: str):
    try:
        store = current_app.config["STORE"]
        store.delete_comparison(current_user.id, comp_id)
        return jsonify({"ok": True})
    except Exception as exc:
        return _storage_error(exc)


@bp.get("/api/alerts")
@login_required
def list_alerts():
    try:
        store = current_app.config["STORE"]
        return jsonify({"items": [a.to_dict() for a in store.list_alerts(current_user.id)]})
    except Exception as exc:
        return _storage_error(exc)


@bp.post("/api/alerts")
@login_required
def save_alert():
    store = current_app.config["STORE"]
    alert, err = parse_alert(read_body(request), current_user.id)
    if err:
        return jsonify({"error": err}), 400
    try:
        store.save_alert(alert)
        return jsonify({"ok": True, "item": alert.to_dict()})
    except Exception as exc:
        return _storage_error(exc)


@bp.delete("/api/alerts/<alert_id>")
@login_required
def delete_alert(alert_id: str):
    try:
        store = current_app.config["STORE"]
        store.delete_alert(current_user.id, alert_id)
        return jsonify({"ok": True})
    except Exception as exc:
        return _storage_error(exc)
