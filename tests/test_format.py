from __future__ import annotations

from src.stats import format_metric_display, round_metric_value, stats_to_labeled_rows


def test_round_metrics():
    assert round_metric_value("mean", 84.567) == 84.6
    assert round_metric_value("count", 36) == 36
    assert format_metric_display("coverage_ratio", 0.956) == "95.6%"
