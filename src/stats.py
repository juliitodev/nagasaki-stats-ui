from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from statistics import mean, median


@dataclass
class StatsResult:
    count: int
    mean: float
    median: float
    min: float
    max: float
    std: float
    p95: float
    trend_slope: float
    trend_direction: str
    coverage_ratio: float
    gaps: int
    outliers: int


METRIC_LABELS: dict[str, str] = {
    "mean": "Media",
    "median": "Mediana",
    "min": "Mínimo",
    "max": "Máximo",
    "std": "Desviación típica",
    "p95": "Percentil 95",
    "trend_slope": "Pendiente de tendencia",
    "trend_direction": "Dirección de tendencia",
    "coverage_ratio": "Cobertura de la serie",
    "gaps": "Huecos estimados",
    "outliers": "Valores atípicos",
    "count": "Número de puntos",
}


TREND_LABELS: dict[str, str] = {
    "up": "Ascendente",
    "down": "Descendente",
    "flat": "Estable",
}

INTEGER_METRICS = frozenset({"count", "gaps", "outliers"})


def round_metric_value(key: str, value: float | int | str) -> float | int:
    if key in INTEGER_METRICS:
        return int(round(float(value)))
    if key == "trend_slope":
        return round(float(value), 3)
    if key == "coverage_ratio":
        return round(float(value), 4)
    v = float(value)
    if abs(v) >= 100:
        return round(v, 0)
    if abs(v) >= 10:
        return round(v, 1)
    return round(v, 2)


def format_metric_display(key: str, value: float | int | str) -> str | int | float:
    if key == "trend_direction":
        return TREND_LABELS.get(str(value), str(value))
    if key == "coverage_ratio" and isinstance(value, (int, float)):
        return f"{round(float(value) * 100, 1)}%"
    if key in INTEGER_METRICS:
        return int(round(float(value)))
    if isinstance(value, (int, float)):
        rounded = round_metric_value(key, value)
        if isinstance(rounded, float) and rounded == int(rounded):
            return int(rounded)
        return rounded
    return value


def metric_label(key: str) -> str:
    return METRIC_LABELS.get(key, key)


def _percentile(sorted_vals: list[float], q: float) -> float:
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    pos = max(0.0, min(1.0, q)) * (len(sorted_vals) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = pos - lo
    return sorted_vals[lo] * (1.0 - frac) + sorted_vals[hi] * frac


def _std(vals: list[float], mu: float) -> float:
    if len(vals) <= 1:
        return 0.0
    return (sum((x - mu) ** 2 for x in vals) / len(vals)) ** 0.5


def _trend_slope_per_step(vals: list[float]) -> float:
    n = len(vals)
    if n <= 1:
        return 0.0
    xs = list(range(n))
    mx = (n - 1) / 2.0
    my = mean(vals)
    den = sum((x - mx) ** 2 for x in xs)
    if den <= 1e-12:
        return 0.0
    num = sum((x - mx) * (y - my) for x, y in zip(xs, vals))
    return num / den


def _trend_label(slope: float) -> str:
    eps = 1e-9
    if slope > eps:
        return "up"
    if slope < -eps:
        return "down"
    return "flat"


def _infer_expected_step_seconds(series: list[tuple[datetime, float]]) -> float | None:
    if len(series) < 2:
        return None
    deltas = sorted(
        (
            (series[i][0] - series[i - 1][0]).total_seconds()
            for i in range(1, len(series))
            if (series[i][0] - series[i - 1][0]).total_seconds() > 0
        )
    )
    if not deltas:
        return None
    return median(deltas)


def compute_stats(series: list[tuple[datetime, float]]) -> StatsResult:
    ordered = sorted(series, key=lambda p: p[0].timestamp())
    vals = [float(v) for _, v in ordered]
    if not vals:
        raise ValueError("Serie vacía")

    mu = float(mean(vals))
    mn = float(min(vals))
    mx = float(max(vals))
    med = float(median(vals))
    svals = sorted(vals)
    p95 = float(_percentile(svals, 0.95))
    sigma = float(_std(vals, mu))
    slope = float(_trend_slope_per_step(vals))

    q1 = _percentile(svals, 0.25)
    q3 = _percentile(svals, 0.75)
    iqr = max(0.0, q3 - q1)
    low = q1 - 1.5 * iqr
    high = q3 + 1.5 * iqr
    outliers = sum(1 for v in vals if v < low or v > high)

    expected_step = _infer_expected_step_seconds(ordered)
    gaps = 0
    coverage_ratio = 1.0
    if expected_step and expected_step > 0 and len(ordered) >= 2:
        start_ts = ordered[0][0].timestamp()
        end_ts = ordered[-1][0].timestamp()
        expected_points = int(round((end_ts - start_ts) / expected_step)) + 1
        expected_points = max(expected_points, len(ordered))
        gaps = max(0, expected_points - len(ordered))
        coverage_ratio = len(ordered) / expected_points if expected_points > 0 else 1.0

    return StatsResult(
        count=len(vals),
        mean=mu,
        median=med,
        min=mn,
        max=mx,
        std=sigma,
        p95=p95,
        trend_slope=slope,
        trend_direction=_trend_label(slope),
        coverage_ratio=coverage_ratio,
        gaps=gaps,
        outliers=outliers,
    )


def rolling_mean(series: list[tuple[datetime, float]], window: int = 3) -> list[tuple[datetime, float | None]]:
    ordered = sorted(series, key=lambda p: p[0].timestamp())
    w = max(1, int(window))
    out: list[tuple[datetime, float | None]] = []
    vals = [v for _, v in ordered]
    for i, (ts, _) in enumerate(ordered):
        if i < w - 1:
            out.append((ts, None))
            continue
        chunk = vals[i - w + 1 : i + 1]
        out.append((ts, float(mean(chunk))))
    return out


def series_to_chart(
    entity_id: str,
    attribute: str,
    series: list[tuple[datetime, float]],
    *,
    rolling_window: int = 3,
) -> dict:
    ordered = sorted(series, key=lambda p: p[0].timestamp())
    rolling = rolling_mean(ordered, rolling_window)
    vals = [p[1] for p in ordered]
    n = len(vals)
    stats = compute_stats(ordered)
    mu = round_metric_value("mean", stats.mean)
    med = round_metric_value("median", stats.median)
    mn = round_metric_value("min", stats.min)
    mx = round_metric_value("max", stats.max)

    def _round_series(v: float | None) -> float | None:
        if v is None:
            return None
        return round_metric_value("mean", v)

    return {
        "entityId": entity_id,
        "attribute": attribute,
        "timestamps": [p[0].isoformat() for p in ordered],
        "values": [_round_series(v) for v in vals],
        "rollingMean": [_round_series(v) for _, v in rolling],
        "meanLine": [mu] * n,
        "medianLine": [med] * n,
        "minLine": [mn] * n,
        "maxLine": [mx] * n,
        "rollingWindow": rolling_window,
        "pointsUsed": n,
        "summary": {
            "mean": mu,
            "median": med,
            "min": mn,
            "max": mx,
            "count": stats.count,
        },
    }


def compare_entities(
    entity_ids: list[str],
    attribute: str,
    metric: str,
    *,
    load_series_fn,
) -> dict:
    metric_name = metric.strip()
    if metric_name not in RANKING_METRICS:
        return {"error": f"Métrica no soportada: {metric_name}"}

    items: list[dict] = []
    for eid in entity_ids:
        eid = eid.strip()
        if not eid:
            continue
        try:
            series = load_series_fn(eid, attribute)
            stats = compute_stats(series).__dict__
            mval = stats.get(metric_name)
            if isinstance(mval, (int, float)):
                items.append(
                    {
                        "entityId": eid,
                        "metric": round_metric_value(metric_name, mval),
                        "stats": stats,
                    }
                )
        except ValueError:
            continue

    if not items:
        return {"error": "No se pudo comparar ninguna entidad con ese atributo."}

    items.sort(key=lambda x: x["metric"], reverse=True)
    return {
        "attribute": attribute.strip(),
        "metric": metric_name,
        "metricLabel": metric_label(metric_name),
        "items": items,
    }


def insight_from_stats(stats: dict) -> str:
    direction = TREND_LABELS.get(str(stats.get("trend_direction", "")), "sin tendencia clara")
    outliers = int(stats.get("outliers", 0))
    coverage = float(stats.get("coverage_ratio", 1.0))
    mean_v = stats.get("mean")
    parts = []
    if isinstance(mean_v, (int, float)):
        parts.append(f"La media de la serie es {format_metric_display('mean', mean_v)}.")
    parts.append(f"Tendencia {direction.lower()}.")
    parts.append(f"Cobertura del histórico: {coverage * 100:.0f}%.")
    if outliers > 0:
        parts.append(f"Se detectaron {outliers} valor(es) atípico(s).")
    else:
        parts.append("No hay valores atípicos según el criterio IQR.")
    return " ".join(parts)


def stats_to_labeled_rows(stats: dict) -> list[dict]:
    rows: list[dict] = []
    for key, value in stats.items():
        if isinstance(value, (int, float)) and key != "trend_direction":
            value = round_metric_value(key, value)
        rows.append(
            {
                "key": key,
                "label": metric_label(key),
                "value": format_metric_display(key, value),
            }
        )
    return rows


def round_stats_dict(stats: dict) -> dict:
    out = dict(stats)
    for key, value in list(out.items()):
        if key == "trend_direction":
            continue
        if isinstance(value, (int, float)):
            out[key] = round_metric_value(key, value)
    return out


RANKING_METRICS = frozenset(
    {
        "mean",
        "median",
        "min",
        "max",
        "std",
        "p95",
        "trend_slope",
        "coverage_ratio",
        "gaps",
        "outliers",
        "count",
    }
)
