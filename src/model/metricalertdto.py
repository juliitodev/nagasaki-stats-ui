from __future__ import annotations

import uuid


class MetricAlertDto:
    def __init__(
        self,
        owner: str = "",
        name: str = "",
        entity_id: str = "",
        attribute: str = "",
        min_value: float | None = None,
        max_value: float | None = None,
        id: str = "",
    ):
        self.id = id or str(uuid.uuid4())
        self.owner = owner
        self.name = name
        self.entity_id = entity_id
        self.attribute = attribute
        self.min_value = min_value
        self.max_value = max_value

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "owner": self.owner,
            "name": self.name,
            "entity_id": self.entity_id,
            "attribute": self.attribute,
            "min_value": self.min_value,
            "max_value": self.max_value,
        }

    def __str__(self) -> str:
        return f"MetricAlertDto({self.name!r}, {self.entity_id}, {self.attribute})"
