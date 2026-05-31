from __future__ import annotations

import uuid

from flask import Request

from src.models import DashboardNote, EntityBookmark, MetricAlert, SavedComparison, SavedView


def read_body(request: Request) -> dict:
    data = request.get_json(silent=True)
    if data is not None:
        return data if isinstance(data, dict) else {}
    body = request.form.to_dict()
    if request.form.getlist("entityIds"):
        body["entityIds"] = ",".join(request.form.getlist("entityIds"))
    return body


def _pick(body: dict, *keys: str) -> str:
    for key in keys:
        val = body.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return ""


def parse_view(body: dict, owner: str) -> tuple[SavedView | None, str | None]:
    view = SavedView(
        id=str(uuid.uuid4()),
        owner=owner,
        name=_pick(body, "name") or "sin nombre",
        entity_id=_pick(body, "entityId", "entity_id"),
        attribute=_pick(body, "attribute"),
        metric=_pick(body, "metric") or "mean",
    )
    if not view.entity_id or not view.attribute:
        return None, "Indica la fuente y la magnitud."
    return view, None


def parse_bookmark(body: dict, owner: str) -> tuple[EntityBookmark | None, str | None]:
    bm = EntityBookmark(
        id=str(uuid.uuid4()),
        owner=owner,
        label=_pick(body, "label") or "marcador",
        entity_id=_pick(body, "entityId", "entity_id"),
        attribute=_pick(body, "attribute"),
        default_metric=_pick(body, "defaultMetric", "default_metric", "metric") or "mean",
    )
    if not bm.entity_id or not bm.attribute:
        return None, "Indica la fuente y la magnitud."
    return bm, None


def parse_note(body: dict, owner: str) -> tuple[DashboardNote | None, str | None]:
    raw_bm = body.get("bookmarkId") or body.get("bookmark_id")
    bookmark_id = str(raw_bm).strip() if raw_bm else None
    note = DashboardNote(
        id=str(uuid.uuid4()),
        owner=owner,
        bookmark_id=bookmark_id,
        text=_pick(body, "text"),
        entity_id=_pick(body, "entityId", "entity_id") or None,
        attribute=_pick(body, "attribute") or None,
        metric=_pick(body, "metric") or None,
    )
    if not note.text:
        return None, "Escribe el texto de la nota."
    return note, None


def parse_comparison(body: dict, owner: str) -> tuple[SavedComparison | None, str | None]:
    raw_ids = body.get("entityIds") or body.get("entity_ids") or ""
    if isinstance(raw_ids, list):
        joined = ",".join(str(x).strip() for x in raw_ids if str(x).strip())
    else:
        joined = str(raw_ids).strip()
    comp = SavedComparison(
        id=str(uuid.uuid4()),
        owner=owner,
        name=_pick(body, "name") or "comparativa",
        entity_ids=joined,
        attribute=_pick(body, "attribute"),
        metric=_pick(body, "metric") or "mean",
    )
    if len(comp.id_list()) < 2:
        return None, "Indica al menos dos fuentes."
    if not comp.attribute:
        return None, "Indica la magnitud."
    return comp, None


def _optional_float(value) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_alert(body: dict, owner: str) -> tuple[MetricAlert | None, str | None]:
    alert = MetricAlert(
        id=str(uuid.uuid4()),
        owner=owner,
        name=_pick(body, "name") or "alerta",
        entity_id=_pick(body, "entityId", "entity_id"),
        attribute=_pick(body, "attribute"),
        min_value=_optional_float(body.get("minValue") or body.get("min_value")),
        max_value=_optional_float(body.get("maxValue") or body.get("max_value")),
    )
    if not alert.entity_id or not alert.attribute:
        return None, "Indica la fuente y la magnitud."
    if alert.min_value is None and alert.max_value is None:
        return None, "Indica un mínimo o un máximo."
    if (
        alert.min_value is not None
        and alert.max_value is not None
        and alert.min_value > alert.max_value
    ):
        return None, "El mínimo no puede ser mayor que el máximo."
    return alert, None
