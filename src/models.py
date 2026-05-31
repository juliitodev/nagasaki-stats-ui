from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class SavedView:
    id: str
    owner: str
    name: str
    entity_id: str
    attribute: str
    metric: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class EntityBookmark:
    id: str
    owner: str
    label: str
    entity_id: str
    attribute: str
    default_metric: str = "mean"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DashboardNote:
    id: str
    owner: str
    bookmark_id: str | None
    text: str
    entity_id: str | None = None
    attribute: str | None = None
    metric: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SavedComparison:
    id: str
    owner: str
    name: str
    entity_ids: str
    attribute: str
    metric: str

    def to_dict(self) -> dict:
        return asdict(self)

    def id_list(self) -> list[str]:
        return [x.strip() for x in self.entity_ids.split(",") if x.strip()]


@dataclass
class MetricAlert:
    id: str
    owner: str
    name: str
    entity_id: str
    attribute: str
    min_value: float | None = None
    max_value: float | None = None

    def to_dict(self) -> dict:
        return asdict(self)
