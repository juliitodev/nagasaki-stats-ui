from __future__ import annotations

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from src import catalog
from src.labels import attribute_label
from src.alert_checks import messages_for_alerts
from src.user_workspace import normalize_note
from src.persist_forms import (
    parse_alert,
    parse_bookmark,
    parse_comparison,
    parse_note,
    parse_view,
    read_body,
)
from src.stats import RANKING_METRICS, metric_label


bp = Blueprint("stats", __name__)


def _catalog_entities():
    return catalog.list_entities()


def _bookmark_labels(owner: str) -> dict[str, str]:
    store = current_app.config["STORE"]
    return {b.id: b.label for b in store.list_bookmarks(owner)}


def _notes_for_display(owner: str) -> list[dict]:
    store = current_app.config["STORE"]
    labels = _bookmark_labels(owner)
    items = []
    for n in store.list_notes(owner):
        row = n.to_dict()
        if n.bookmark_id and labels.get(n.bookmark_id):
            row["anchor_type"] = "Marcador"
            row["anchor_label"] = labels[n.bookmark_id]
        elif n.entity_id and n.attribute:
            row["anchor_type"] = "Consulta"
            row["anchor_label"] = f"{n.entity_id} · {n.attribute}"
        else:
            row["anchor_type"] = "Sin contexto"
            row["anchor_label"] = "—"
        items.append(row)
    return items


def _note_count_by_bookmark(owner: str) -> dict[str, int]:
    store = current_app.config["STORE"]
    counts: dict[str, int] = {}
    for n in store.list_notes(owner):
        if n.bookmark_id:
            counts[n.bookmark_id] = counts.get(n.bookmark_id, 0) + 1
    return counts


def _catalog():
    return catalog


def _ui_context(**extra):
    return {
        "health": _catalog().get_health(),
        "catalog_entities": _catalog().list_entities(),
        "ranking_metrics": sorted(RANKING_METRICS),
        "metric_labels": {m: metric_label(m) for m in RANKING_METRICS},
        "attribute_labels": {
            a: attribute_label(a)
            for e in _catalog().list_entities()
            for a in e.get("attributes", [])
        },
        **extra,
    }


@bp.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    entity_id = request.args.get("entityId", "urn:nagasaki:solar:plant-1")
    attribute = request.args.get("attribute", "powerKw")
    metric = request.args.get("metric", "mean")

    stats_data = _safe_stats(entity_id, attribute)
    ranking_data = _safe_ranking(attribute, metric)
    return render_template(
        "dashboard.html",
        title="Explorar datos",
        active_nav="explore",
        stats_data=stats_data,
        ranking_data=ranking_data,
        entity_id=entity_id,
        attribute=attribute,
        metric=metric,
        **_ui_context(),
    )


@bp.get("/compare")
@login_required
def compare_page():
    attribute = request.args.get("attribute", "powerKw")
    metric = request.args.get("metric", "mean")
    selected = [x.strip() for x in request.args.getlist("entityIds") if x.strip()]
    if not selected:
        selected = [x.strip() for x in request.args.get("entityIds", "").split(",") if x.strip()]
    compare_data = None
    if len(selected) >= 2:
        compare_data = _catalog().entity_compare(selected, attribute, metric)
    return render_template(
        "compare.html",
        title="Comparar",
        active_nav="compare",
        attribute=attribute,
        metric=metric,
        selected_ids=selected,
        compare_data=compare_data,
        **_ui_context(),
    )


def _safe_stats(entity_id: str, attribute: str) -> dict:
    try:
        return _catalog().entity_stats(entity_id, attribute)
    except ValueError as exc:
        return {"error": str(exc)}
    except Exception as exc:
        return {"error": f"Error al calcular estadísticas: {exc!s}"}


def _safe_ranking(attribute: str, metric: str) -> dict:
    try:
        data = _catalog().entity_ranking(attribute, metric)
        if data.get("error"):
            return data
        return data
    except Exception as exc:
        return {"error": f"Error al calcular ranking: {exc!s}"}


@bp.get("/catalog")
@login_required
def catalog_page():
    entities = _catalog().list_entities()
    health = _catalog().get_health()
    return render_template(
        "catalog.html",
        title="Fuentes de datos",
        active_nav="catalog",
        entities=entities,
        health=health,
    )


@bp.route("/views", methods=["GET", "POST"])
@login_required
def views_page():
    store = current_app.config["STORE"]
    owner = current_user.id
    if request.method == "POST":
        view, err = parse_view(read_body(request), owner)
        if err:
            flash(err, "error")
        else:
            try:
                store.save_view(view)
                flash("Vista guardada.", "ok")
                return redirect(url_for("stats.views_page"))
            except Exception:
                flash("No se pudo guardar. Comprueba que Redis esté en marcha.", "error")
    return render_template(
        "views.html",
        title="Vistas guardadas",
        active_nav="views",
        views=store.list_views(owner),
        catalog_entities=_catalog_entities(),
        ranking_metrics=sorted(RANKING_METRICS),
        metric_labels={m: metric_label(m) for m in RANKING_METRICS},
    )


@bp.route("/bookmarks", methods=["GET", "POST"])
@login_required
def bookmarks_page():
    store = current_app.config["STORE"]
    owner = current_user.id
    if request.method == "POST":
        bm, err = parse_bookmark(read_body(request), owner)
        if err:
            flash(err, "error")
        else:
            try:
                store.save_bookmark(bm)
                flash("Marcador guardado.", "ok")
                return redirect(url_for("stats.bookmarks_page"))
            except Exception:
                flash("No se pudo guardar. Comprueba que Redis esté en marcha.", "error")
    return render_template(
        "bookmarks.html",
        title="Marcadores",
        active_nav="bookmarks",
        bookmarks=store.list_bookmarks(owner),
        catalog_entities=_catalog_entities(),
        note_counts=_note_count_by_bookmark(owner),
    )


@bp.route("/notes", methods=["GET", "POST"])
@login_required
def notes_page():
    store = current_app.config["STORE"]
    owner = current_user.id
    if request.method == "POST":
        note, err = parse_note(read_body(request), owner)
        if err:
            flash(err, "error")
        else:
            note, err = normalize_note(note, store, owner)
        if err:
            flash(err, "error")
        else:
            try:
                store.save_note(note)
                flash("Nota guardada.", "ok")
                return redirect(url_for("stats.notes_page"))
            except Exception:
                flash("No se pudo guardar. Comprueba que Redis esté en marcha.", "error")
    return render_template(
        "notes.html",
        title="Notas",
        active_nav="notes",
        notes=_notes_for_display(owner),
        bookmarks=store.list_bookmarks(owner),
        bookmark_labels=_bookmark_labels(owner),
        catalog_entities=_catalog_entities(),
        metric_labels={m: metric_label(m) for m in RANKING_METRICS},
    )


@bp.route("/comparisons", methods=["GET", "POST"])
@login_required
def comparisons_page():
    store = current_app.config["STORE"]
    owner = current_user.id
    if request.method == "POST":
        comp, err = parse_comparison(read_body(request), owner)
        if err:
            flash(err, "error")
        else:
            try:
                store.save_comparison(comp)
                flash("Comparativa guardada.", "ok")
                return redirect(url_for("stats.comparisons_page"))
            except Exception:
                flash("No se pudo guardar. Comprueba que Redis esté en marcha.", "error")
    catalog = _catalog_entities()
    return render_template(
        "comparisons.html",
        title="Comparativas guardadas",
        active_nav="comparisons",
        comparisons=store.list_comparisons(owner),
        catalog_entities=catalog,
        ranking_metrics=sorted(RANKING_METRICS),
        metric_labels={m: metric_label(m) for m in RANKING_METRICS},
        attribute_labels={
            a: attribute_label(a) for e in catalog for a in e.get("attributes", [])
        },
    )


@bp.route("/alerts", methods=["GET", "POST"])
@login_required
def alerts_page():
    store = current_app.config["STORE"]
    owner = current_user.id
    if request.method == "POST":
        alert, err = parse_alert(read_body(request), owner)
        if err:
            flash(err, "error")
        else:
            try:
                store.save_alert(alert)
                flash("Alerta guardada.", "ok")
                return redirect(url_for("stats.alerts_page"))
            except Exception:
                flash("No se pudo guardar. Comprueba que Redis esté en marcha.", "error")
    catalog = _catalog_entities()
    names = {e["entityId"]: e["displayName"] for e in catalog}
    return render_template(
        "alerts.html",
        title="Alertas de umbral",
        active_nav="alerts",
        alerts=store.list_alerts(owner),
        catalog_entities=catalog,
        entity_names=names,
        attribute_labels={
            a: attribute_label(a) for e in catalog for a in e.get("attributes", [])
        },
    )


@bp.get("/api/alerts/check")
@login_required
def api_alerts_check():
    entity_id = request.args.get("entityId", "").strip()
    attribute = request.args.get("attribute", "").strip()
    if not entity_id or not attribute:
        return jsonify({"error": "entityId y attribute son obligatorios"}), 400
    store = current_app.config["STORE"]
    alerts = store.list_alerts_for(current_user.id, entity_id, attribute)
    if not alerts:
        return jsonify({"messages": []})
    try:
        stats = _catalog().entity_stats(entity_id, attribute)
    except (ValueError, Exception) as exc:
        return jsonify({"error": str(exc)}), 400
    if stats.get("error"):
        return jsonify({"error": stats["error"]}), 400
    mean = stats.get("stats", {}).get("mean")
    if mean is None:
        return jsonify({"messages": []})
    return jsonify({"messages": messages_for_alerts(alerts, float(mean))})


@bp.get("/api/health")
@login_required
def api_health():
    return jsonify(_catalog().get_health())


@bp.get("/api/catalog")
@login_required
def api_catalog():
    return jsonify({"items": _catalog().list_entities()})


@bp.get("/api/stats")
@login_required
def api_stats():
    entity_id = request.args.get("entityId", "").strip()
    attribute = request.args.get("attribute", "").strip()
    metric = request.args.get("metric", "mean").strip()
    if not entity_id or not attribute:
        return jsonify({"error": "entityId y attribute son obligatorios"}), 400

    stats_data = _safe_stats(entity_id, attribute)
    ranking_data = _safe_ranking(attribute, metric)
    stats_ok = not stats_data.get("error")
    ranking_ok = not ranking_data.get("error")

    if not stats_ok and not ranking_ok:
        return jsonify({"stats": stats_data, "ranking": ranking_data}), 400
    return jsonify({"stats": stats_data, "ranking": ranking_data})


@bp.get("/api/series")
@login_required
def api_series():
    entity_id = request.args.get("entityId", "").strip()
    attribute = request.args.get("attribute", "").strip()
    window = request.args.get("rollingWindow", "3")
    if not entity_id or not attribute:
        return jsonify({"error": "entityId y attribute son obligatorios"}), 400
    try:
        w = max(1, min(int(window), 24))
    except ValueError:
        w = 3
    try:
        return jsonify(_catalog().entity_series(entity_id, attribute, rolling_window=w))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": f"Error al cargar la serie: {exc!s}"}), 500


@bp.get("/api/compare")
@login_required
def api_compare():
    raw_ids = request.args.get("entityIds", "").strip()
    attribute = request.args.get("attribute", "").strip()
    metric = request.args.get("metric", "mean").strip()
    if not raw_ids or not attribute:
        return jsonify({"error": "entityIds y attribute son obligatorios"}), 400
    entity_ids = [x.strip() for x in raw_ids.split(",") if x.strip()]
    if len(entity_ids) < 2:
        return jsonify({"error": "Indica al menos dos entidades separadas por comas"}), 400
    if len(entity_ids) > 5:
        return jsonify({"error": "Máximo 5 entidades en una comparativa"}), 400
    data = _catalog().entity_compare(entity_ids, attribute, metric)
    if data.get("error"):
        return jsonify(data), 400
    return jsonify(data)


@bp.post("/api/stats/batch")
@login_required
def api_stats_batch():
    body = request.get_json(silent=True) or {}
    requests_list = body.get("requests")
    if not isinstance(requests_list, list):
        return jsonify({"error": "Se espera un objeto con lista 'requests'"}), 400
    data = _catalog().entity_stats_batch(requests_list)
    if data.get("error"):
        return jsonify(data), 400
    return jsonify(data)
