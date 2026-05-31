from __future__ import annotations

import uuid


class DashboardNoteDto:
    def __init__(
        self,
        owner: str = "",
        text: str = "",
        bookmark_id: str | None = None,
        entity_id: str | None = None,
        attribute: str | None = None,
        metric: str | None = None,
        id: str = "",
    ):
        self.id = id or str(uuid.uuid4())
        self.owner = owner
        self.text = text
        self.bookmark_id = bookmark_id
        self.entity_id = entity_id
        self.attribute = attribute
        self.metric = metric

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "owner": self.owner,
            "text": self.text,
            "bookmark_id": self.bookmark_id,
            "entity_id": self.entity_id,
            "attribute": self.attribute,
            "metric": self.metric,
        }

    def __str__(self) -> str:
        preview = (self.text or "")[:40]
        return f"DashboardNoteDto({preview!r}…)" if len(self.text or "") > 40 else f"DashboardNoteDto({preview!r})"
