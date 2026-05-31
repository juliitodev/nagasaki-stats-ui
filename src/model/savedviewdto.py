from __future__ import annotations

import uuid


class SavedViewDto:
    def __init__(
        self,
        owner: str = "",
        name: str = "",
        entity_id: str = "",
        attribute: str = "",
        metric: str = "mean",
        id: str = "",
    ):
        self.id = id or str(uuid.uuid4())
        self.owner = owner
        self.name = name
        self.entity_id = entity_id
        self.attribute = attribute
        self.metric = metric

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "owner": self.owner,
            "name": self.name,
            "entity_id": self.entity_id,
            "attribute": self.attribute,
            "metric": self.metric,
        }

    def __str__(self) -> str:
        return f"SavedViewDto({self.name!r}, {self.entity_id}, {self.attribute})"
