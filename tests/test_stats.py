from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.stats import (
    compute_stats,
    insight_from_stats,
    rolling_mean,
    series_to_chart,
)


def _series(vals: list[float]) -> list[tuple[datetime, float]]:
    start = datetime(2026, 4, 20, 6, 0, tzinfo=timezone.utc)
    return [(start + timedelta(hours=2 * i), v) for i, v in enumerate(vals)]


def test_compute_stats_ascending_trend():
    stats = compute_stats(_series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]))
    assert stats.trend_direction == "up"
    assert stats.mean == 4.5
    assert stats.count == 8


def test_compute_stats_empty_raises():
    try:
        compute_stats([])
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "vacía" in str(exc).lower() or "empty" in str(exc).lower()


def test_rolling_mean_window():
    series = _series([10.0, 20.0, 30.0, 40.0])
    rolled = rolling_mean(series, window=3)
    assert rolled[0][1] is None
    assert rolled[2][1] == 20.0


def test_series_to_chart_payload():
    series = _series([1.0, 2.0, 3.0])
    chart = series_to_chart("urn:test", "powerKw", series, rolling_window=2)
    assert chart["entityId"] == "urn:test"
    assert len(chart["timestamps"]) == 3
    assert len(chart["values"]) == 3


def test_insight_from_stats_spanish():
    text = insight_from_stats(
        {"mean": 42.5, "trend_direction": "up", "coverage_ratio": 0.95, "outliers": 2}
    )
    assert "42.50" in text or "42.5" in text
    assert "atípico" in text.lower() or "atipico" in text.lower()
