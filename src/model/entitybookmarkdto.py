from __future__ import annotations

import uuid


class EntityBookmarkDto:
    def __init__(
        self,
        owner: str = "",
        label: str = "",
        entity_id: str = "",
        attribute: str = "",
        default_metric: str = "mean",
        id: str = "",
    ):
        self.id = id or str(uuid.uuid4())
        self.owner = owner
        self.label = label
        self.entity_id = entity_id
        self.attribute = attribute
        self.default_metric = default_metric or "mean"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "owner": self.owner,
            "label": self.label,
            "entity_id": self.entity_id,
            "attribute": self.attribute,
            "default_metric": getattr(self, "default_metric", None) or "mean",
        }

    def __str__(self) -> str:
        return f"EntityBookmarkDto({self.label!r}, {self.entity_id})"
