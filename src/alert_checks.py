from __future__ import annotations

from src.models import MetricAlert


def messages_for_alerts(alerts: list[MetricAlert], mean: float) -> list[str]:
    out: list[str] = []
    for a in alerts:
        if a.max_value is not None and mean > a.max_value:
            out.append(
                f"«{a.name}»: la media ({mean:.2f}) supera el máximo ({a.max_value:g})"
            )
        if a.min_value is not None and mean < a.min_value:
            out.append(
                f"«{a.name}»: la media ({mean:.2f}) está por debajo del mínimo ({a.min_value:g})"
            )
    return out
