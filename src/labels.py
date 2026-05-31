from __future__ import annotations

import re

ATTRIBUTE_LABELS: dict[str, str] = {
    "powerKw": "Potencia (kW)",
    "temperatureC": "Temperatura (°C)",
    "irradianceWm2": "Irradiancia (W/m²)",
    "flowVehH": "Caudal vehicular (veh/h)",
    "avgSpeedKmh": "Velocidad media (km/h)",
}

TYPE_LABELS: dict[str, str] = {
    "SolarPlant": "Planta solar",
    "TrafficSensor": "Sensor de tráfico",
}


def attribute_label(key: str) -> str:
    return ATTRIBUTE_LABELS.get(key, key)


def type_label(key: str | None) -> str:
    if not key:
        return "Entidad"
    return TYPE_LABELS.get(key, key)


def friendly_entity_name(entity_id: str) -> str:
    m = re.search(r":(solar|traffic):([^:]+)$", entity_id)
    if not m:
        return entity_id
    kind, slug = m.group(1), m.group(2)
    if kind == "solar":
        num = slug.replace("plant-", "")
        return f"Planta solar {num}"
    if kind == "traffic":
        num = slug.replace("sensor-", "")
        return f"Sensor tráfico {num}"
    return slug.replace("-", " ").title()
