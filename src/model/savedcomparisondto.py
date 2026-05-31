from __future__ import annotations

import uuid


class SavedComparisonDto:
    def __init__(
        self,
        owner: str = "",
        name: str = "",
        entity_ids: str = "",
        attribute: str = "",
        metric: str = "mean",
        id: str = "",
    ):
        self.id = id or str(uuid.uuid4())
        self.owner = owner
        self.name = name
        self.entity_ids = entity_ids
        self.attribute = attribute
        self.metric = metric

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "owner": self.owner,
            "name": self.name,
            "entity_ids": self.entity_ids,
            "attribute": self.attribute,
            "metric": self.metric,
        }

    def entity_id_list(self) -> list[str]:
        return [x.strip() for x in self.entity_ids.split(",") if x.strip()]

    def __str__(self) -> str:
        return f"SavedComparisonDto({self.name!r}, {len(self.entity_id_list())} fuentes)"
