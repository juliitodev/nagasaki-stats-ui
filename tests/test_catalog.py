from __future__ import annotations

from pathlib import Path

from src import catalog


def _configure_seed():
    seed = Path(__file__).resolve().parents[1] / "src" / "data" / "demo_seed.json"
    catalog.configure(seed)
    return seed


def test_seed_scale_and_ranking():
    _configure_seed()
    health = catalog.get_health()
    assert health["entityCount"] >= 30

    ranking = catalog.entity_ranking("powerKw", "mean", limit=10)
    assert ranking["metric"] == "mean"
    assert len(ranking["ranking"]) == 10
    metrics = [r["metric"] for r in ranking["ranking"]]
    assert metrics == sorted(metrics, reverse=True)


def test_entity_stats_and_series():
    _configure_seed()
    stats = catalog.entity_stats("urn:nagasaki:solar:plant-1", "powerKw")
    assert stats["entityId"] == "urn:nagasaki:solar:plant-1"
    assert stats["pointsUsed"] >= 30
    assert "labeledStats" in stats
    assert "insight" in stats

    series = catalog.entity_series("urn:nagasaki:solar:plant-1", "powerKw")
    assert len(series["values"]) >= 30


def test_compare_entities():
    _configure_seed()
    data = catalog.entity_compare(
        ["urn:nagasaki:solar:plant-1", "urn:nagasaki:solar:plant-2"],
        "powerKw",
        "mean",
    )
    assert len(data["items"]) == 2


def test_stats_batch():
    _configure_seed()
    batch = catalog.entity_stats_batch(
        [
            {"entityId": "urn:nagasaki:solar:plant-1", "attribute": "powerKw"},
            {"entityId": "urn:missing", "attribute": "powerKw"},
        ]
    )
    assert len(batch["results"]) == 2
    assert "stats" in batch["results"][0]
    assert "error" in batch["results"][1]


def test_solar_plants_have_distinct_power_curves():
    _configure_seed()
    s1 = catalog.entity_stats("urn:nagasaki:solar:plant-1", "powerKw")["stats"]["mean"]
    s5 = catalog.entity_stats("urn:nagasaki:solar:plant-5", "powerKw")["stats"]["mean"]
    s20 = catalog.entity_stats("urn:nagasaki:solar:plant-20", "powerKw")["stats"]["mean"]
    assert s1 != s5 != s20


def test_series_includes_chart_bands():
    _configure_seed()
    series = catalog.entity_series("urn:nagasaki:solar:plant-1", "powerKw")
    assert "meanLine" in series and "minLine" in series and "maxLine" in series
    assert len(series["meanLine"]) == len(series["values"])
    assert series["summary"]["mean"] == series["meanLine"][0]


def test_unknown_entity():
    _configure_seed()
    try:
        catalog.entity_stats("urn:missing", "powerKw")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "desconocida" in str(exc).lower() or "unknown" in str(exc).lower()
