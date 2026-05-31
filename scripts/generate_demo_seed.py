from __future__ import annotations

import json
import math
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def build_seed() -> dict:
    rng = random.Random(42)
    start = datetime(2026, 4, 20, 6, 0, tzinfo=timezone.utc)
    points = [start + timedelta(hours=2 * i) for i in range(36)]
    entities: dict[str, dict] = {}

    for i in range(1, 26):
        eid = f"urn:nagasaki:solar:plant-{i}"
        # Cada planta: fase distinta, eficiencia, ruido y eventos propios
        phase = (i * 0.47) % (2 * math.pi)
        efficiency = 0.72 + (i % 9) * 0.035 + rng.uniform(-0.05, 0.05)
        capacity = 28 + i * 2.8 + rng.uniform(-4, 4)
        cloud_day = (i * 3) % 11
        noise_scale = 2.5 + (i % 5) * 0.8

        hist = []
        for idx, ts in enumerate(points):
            t = idx / max(1, len(points) - 1)
            daylight = max(0.0, math.sin(t * math.pi + phase))
            # Pico desplazado y amplitud distinta por planta
            power = capacity + 95 * efficiency * daylight
            power += math.sin(idx * 0.9 + phase * 2) * (6 + i * 0.25)
            power += rng.uniform(-noise_scale, noise_scale)
            if idx == cloud_day:
                power *= 0.55 + rng.uniform(0, 0.15)
            if idx == (cloud_day + 5) % 36:
                power *= 1.12

            temp = 13 + 11 * daylight * efficiency + (i % 4) * 0.9
            temp += rng.uniform(-0.8, 0.8)

            irr = 180 + 680 * daylight * efficiency + (idx % 4) * 12
            irr += rng.uniform(-25, 25)

            hist.append(
                {
                    "t": _iso(ts),
                    "attrs": {
                        "powerKw": round(max(0, power), 1),
                        "temperatureC": round(temp, 1),
                        "irradianceWm2": round(max(0, irr), 0),
                    },
                }
            )
        entities[eid] = {
            "type": "SolarPlant",
            "latestAttrs": hist[-1]["attrs"],
            "history": hist,
        }

    for i in range(1, 11):
        eid = f"urn:nagasaki:traffic:sensor-{i}"
        lane_bias = 0.8 + i * 0.04
        hist = []
        for idx, ts in enumerate(points):
            rush = 1.0 if (idx % 12 in (1, 2, 7, 8)) else 0.35
            flow = 360 + 520 * rush * lane_bias + i * 11 + (idx % 7) * 7
            flow += rng.uniform(-18, 18)
            speed = 64 - 18 * rush - i * 0.45 + rng.uniform(-2, 2)
            hist.append(
                {
                    "t": _iso(ts),
                    "attrs": {
                        "flowVehH": round(max(0, flow), 0),
                        "avgSpeedKmh": round(max(5, speed), 1),
                    },
                }
            )
        entities[eid] = {
            "type": "TrafficSensor",
            "latestAttrs": hist[-1]["attrs"],
            "history": hist,
        }

    return {
        "entitySchemas": {
            "SolarPlant": {
                "ia": {
                    "enabled": True,
                    "predictAttributes": ["powerKw", "temperatureC", "irradianceWm2"],
                    "clipForecastMin": 0,
                }
            },
            "TrafficSensor": {
                "ia": {
                    "enabled": True,
                    "predictAttributes": ["flowVehH", "avgSpeedKmh"],
                    "clipForecastMin": 0,
                }
            },
        },
        "entities": entities,
    }


if __name__ == "__main__":
    payload = build_seed()
    out = Path(__file__).resolve().parents[1] / "src" / "data" / "demo_seed.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    print(f"Demo seed generated at {out} ({len(payload['entities'])} entities)")
