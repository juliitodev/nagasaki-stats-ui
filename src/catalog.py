from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.labels import attribute_label, friendly_entity_name, type_label
from src.stats import (
    RANKING_METRICS,
    compare_entities,
    compute_stats,
    insight_from_stats,
    metric_label,
    round_metric_value,
    round_stats_dict,
    series_to_chart,
    stats_to_labeled_rows,
)

_seed_cache: dict[str, Any] | None = None
_seed_path: Path | None = None


def configure(seed_path: str | Path) -> None:
    global _seed_cache, _seed_path
    _seed_cache = None
    _seed_path = Path(seed_path)


def _default_seed_path() -> Path:
    return Path(__file__).resolve().parent / "data" / "demo_seed.json"


def _load_seed() -> dict[str, Any]:
    global _seed_cache
    if _seed_cache is not None:
        return _seed_cache

    p = _seed_path or _default_seed_path()
    if not p.is_absolute():
        p = Path.cwd() / p
    if not p.exists():
        _seed_cache = {"entities": {}, "entitySchemas": {}}
        return _seed_cache

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    entities = data.get("entities") if isinstance(data, dict) else None
    schemas = data.get("entitySchemas") if isinstance(data, dict) else None
    _seed_cache = {
        "entities": entities if isinstance(entities, dict) else {},
        "entitySchemas": schemas if isinstance(schemas, dict) else {},
        "source": str(p),
    }
    return _seed_cache


def _parse_iso(ts: str) -> datetime:
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def get_health() -> dict[str, Any]:
    seed = _load_seed()
    entities = seed.get("entities", {})
    return {
        "status": "ok",
        "mode": "standalone",
        "entityCount": len(entities) if isinstance(entities, dict) else 0,
        "catalogSource": seed.get("source", str(_seed_path or _default_seed_path())),
    }


def list_entities() -> list[dict[str, Any]]:
    seed = _load_seed()
    entities: dict[str, Any] = seed.get("entities", {})
    out: list[dict[str, Any]] = []
    for eid, ent in sorted(entities.items()):
        if not isinstance(ent, dict):
            continue
        attrs = _attributes_for_entity(ent)
        latest = ent.get("latestAttrs") if isinstance(ent.get("latestAttrs"), dict) else {}
        out.append(
            {
                "entityId": eid,
                "displayName": friendly_entity_name(eid),
                "type": ent.get("type"),
                "typeLabel": type_label(ent.get("type")),
                "attributes": attrs,
                "attributeLabels": {a: attribute_label(a) for a in attrs},
                "latestAttrs": latest,
                "points": _history_point_count(ent),
            }
        )
    return out


def _history_point_count(ent: dict[str, Any]) -> int:
    hist = ent.get("history")
    return len(hist) if isinstance(hist, list) else 0


def _attributes_for_entity(ent: dict[str, Any]) -> list[str]:
    attrs: set[str] = set()
    hist = ent.get("history")
    if isinstance(hist, list):
        for point in hist:
            if not isinstance(point, dict):
                continue
            row = point.get("attrs")
            if not isinstance(row, dict):
                continue
            for k, v in row.items():
                if isinstance(v, (int, float)):
                    attrs.add(str(k))
    latest = ent.get("latestAttrs")
    if isinstance(latest, dict):
        for k, v in latest.items():
            if isinstance(v, (int, float)):
                attrs.add(str(k))
    return sorted(attrs)


def list_entities_with_attribute(attribute: str) -> list[str]:
    attr = attribute.strip()
    seed = _load_seed()
    entities: dict[str, Any] = seed.get("entities", {})
    out: list[str] = []
    for eid, ent in entities.items():
        if attr in _attributes_for_entity(ent if isinstance(ent, dict) else {}):
            out.append(str(eid))
    return sorted(set(out))


def load_series(entity_id: str, attribute: str) -> list[tuple[datetime, float]]:
    eid = entity_id.strip()
    attr = attribute.strip()
    seed = _load_seed()
    entities: dict[str, Any] = seed.get("entities", {})
    entity = entities.get(eid)
    if not isinstance(entity, dict):
        raise ValueError(f"Entidad desconocida: {eid}")

    history = entity.get("history")
    if not isinstance(history, list):
        raise ValueError(f"Sin histórico para {eid}")

    out: list[tuple[datetime, float]] = []
    for point in history:
        if not isinstance(point, dict):
            continue
        t = point.get("t")
        attrs = point.get("attrs")
        if not isinstance(t, str) or not isinstance(attrs, dict):
            continue
        v = attrs.get(attr)
        if not isinstance(v, (int, float)):
            continue
        out.append((_parse_iso(t), float(v)))

    if not out:
        raise ValueError(f"Atributo '{attr}' no disponible para {eid}")
    out.sort(key=lambda p: p[0].timestamp())
    return out


def entity_stats(entity_id: str, attribute: str) -> dict[str, Any]:
    eid = entity_id.strip()
    attr = attribute.strip()
    series = load_series(eid, attr)
    stats = compute_stats(series)
    stats_dict = round_stats_dict(stats.__dict__)
    return {
        "entityId": eid,
        "attribute": attr,
        "pointsUsed": len(series),
        "stats": stats_dict,
        "insight": insight_from_stats(stats_dict),
        "labeledStats": stats_to_labeled_rows(stats_dict),
    }


def entity_series(entity_id: str, attribute: str, *, rolling_window: int = 3) -> dict[str, Any]:
    eid = entity_id.strip()
    attr = attribute.strip()
    series = load_series(eid, attr)
    return series_to_chart(eid, attr, series, rolling_window=rolling_window)


def entity_compare(
    entity_ids: list[str],
    attribute: str,
    metric: str = "mean",
) -> dict[str, Any]:
    return compare_entities(entity_ids, attribute, metric, load_series_fn=load_series)


def entity_stats_batch(requests: list[dict[str, Any]]) -> dict[str, Any]:
    if not requests:
        return {"error": "La lista de consultas está vacía"}
    if len(requests) > 200:
        return {"error": "Máximo 200 consultas por lote"}

    results: list[dict[str, Any]] = []
    for req in requests:
        eid = str(req.get("entityId") or req.get("entity_id") or "").strip()
        attr = str(req.get("attribute") or "").strip()
        if not eid or not attr:
            results.append({"entityId": eid, "attribute": attr, "error": "entityId y attribute son obligatorios"})
            continue
        try:
            results.append(entity_stats(eid, attr))
        except ValueError as exc:
            results.append({"entityId": eid, "attribute": attr, "error": str(exc)})
        except Exception as exc:
            results.append({"entityId": eid, "attribute": attr, "error": f"Error: {exc!s}"})
    return {"results": results}


def entity_ranking(attribute: str, metric: str = "mean", limit: int = 10) -> dict[str, Any]:
    attr = attribute.strip()
    metric_name = metric.strip()
    if metric_name not in RANKING_METRICS:
        return {"error": f"Métrica no soportada: {metric_name}"}

    ids = list_entities_with_attribute(attr)
    if not ids:
        return {"error": "No hay entidades con ese atributo en el catálogo."}

    ranking: list[dict[str, Any]] = []
    for eid in ids:
        try:
            series = load_series(eid, attr)
            stats = round_stats_dict(compute_stats(series).__dict__)
            mval = stats.get(metric_name)
            if isinstance(mval, (int, float)):
                ranking.append(
                    {
                        "entityId": eid,
                        "metric": round_metric_value(metric_name, mval),
                        "stats": stats,
                    }
                )
        except Exception:
            continue

    ranking.sort(key=lambda x: x["metric"], reverse=True)
    lim = max(1, min(int(limit), 200))
    return {
        "attribute": attr,
        "metric": metric_name,
        "metricLabel": metric_label(metric_name),
        "ranking": ranking[:lim],
    }
