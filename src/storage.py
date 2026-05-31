from __future__ import annotations

import uuid

import redis
from sirope import Sirope

from src.model.dashboardnotedto import DashboardNoteDto
from src.model.entitybookmarkdto import EntityBookmarkDto
from src.model.metricalertdto import MetricAlertDto
from src.model.savedcomparisondto import SavedComparisonDto
from src.model.savedviewdto import SavedViewDto
from src.model.userdto import UserDto, _looks_hashed
from src.models import DashboardNote, EntityBookmark, MetricAlert, SavedComparison, SavedView


class Storage:
    def __init__(self, redis_url: str):
        self._redis = redis.Redis.from_url(redis_url, decode_responses=True)
        self._sirope = Sirope(self._redis)

    def ensure_user(self, username: str, password: str, role: str = "professor") -> None:
        existing = self._sirope.find_first(
            UserDto,
            lambda u: getattr(u, "username", None) == username,
        )
        if existing:
            was_plain = not _looks_hashed(getattr(existing, "password", ""))
            if not existing.check_password(password):
                existing.set_password(password)
                self._sirope.save(existing)
            elif was_plain:
                # contraseña antigua en claro: ya quedó hasheada en check_password
                self._sirope.save(existing)
            return
        user = UserDto(username=username, password=password, role=role)
        self._sirope.save(user)

    def get_user_role(self, username: str) -> str | None:
        user = self._sirope.find_first(
            UserDto,
            lambda u: getattr(u, "username", None) == username,
        )
        if not user:
            return None
        return getattr(user, "role", None) or "user"

    def check_password(self, username: str, password: str) -> bool:
        user = self._sirope.find_first(
            UserDto,
            lambda u: getattr(u, "username", None) == username,
        )
        if not user:
            return False
        was_plain = not _looks_hashed(getattr(user, "password", ""))
        if user.check_password(password):
            if was_plain:
                self._sirope.save(user)
            return True
        return False

    def _find_view(self, owner: str, view_id: str) -> SavedViewDto | None:
        return self._sirope.find_first(
            SavedViewDto,
            lambda v: getattr(v, "owner", None) == owner and getattr(v, "id", None) == view_id,
        )

    def save_view(self, view: SavedView) -> str:
        entity = SavedViewDto(
            id=view.id or str(uuid.uuid4()),
            owner=view.owner,
            name=view.name,
            entity_id=view.entity_id,
            attribute=view.attribute,
            metric=view.metric,
        )
        existing = self._find_view(view.owner, entity.id)
        if existing:
            entity.__dict__[Sirope.OID_ID] = existing.__dict__.get(Sirope.OID_ID)
        self._sirope.save(entity)
        return entity.id

    def list_views(self, owner: str) -> list[SavedView]:
        return [
            SavedView(**e.to_dict())
            for e in self._sirope.filter(SavedViewDto, lambda v: getattr(v, "owner", None) == owner)
        ]

    def delete_view(self, owner: str, view_id: str) -> None:
        entity = self._find_view(owner, view_id)
        if entity and Sirope.OID_ID in entity.__dict__:
            self._sirope.delete(entity.__dict__[Sirope.OID_ID])

    def _find_bookmark(self, owner: str, bookmark_id: str) -> EntityBookmarkDto | None:
        return self._sirope.find_first(
            EntityBookmarkDto,
            lambda b: getattr(b, "owner", None) == owner and getattr(b, "id", None) == bookmark_id,
        )

    def save_bookmark(self, bookmark: EntityBookmark) -> str:
        entity = EntityBookmarkDto(
            id=bookmark.id or str(uuid.uuid4()),
            owner=bookmark.owner,
            label=bookmark.label,
            entity_id=bookmark.entity_id,
            attribute=bookmark.attribute,
            default_metric=bookmark.default_metric,
        )
        existing = self._find_bookmark(bookmark.owner, entity.id)
        if existing:
            entity.__dict__[Sirope.OID_ID] = existing.__dict__.get(Sirope.OID_ID)
        self._sirope.save(entity)
        return entity.id

    def list_bookmarks(self, owner: str) -> list[EntityBookmark]:
        return [
            EntityBookmark(**e.to_dict())
            for e in self._sirope.filter(
                EntityBookmarkDto, lambda b: getattr(b, "owner", None) == owner
            )
        ]

    def delete_bookmark(self, owner: str, bookmark_id: str) -> None:
        entity = self._find_bookmark(owner, bookmark_id)
        if entity and Sirope.OID_ID in entity.__dict__:
            self._sirope.delete(entity.__dict__[Sirope.OID_ID])
        for note in self.list_notes(owner):
            if note.bookmark_id == bookmark_id:
                note.bookmark_id = None
                self.save_note(note)

    def bookmark_exists(self, owner: str, bookmark_id: str) -> bool:
        return self._find_bookmark(owner, bookmark_id) is not None

    def get_bookmark(self, owner: str, bookmark_id: str) -> EntityBookmark | None:
        entity = self._find_bookmark(owner, bookmark_id)
        return EntityBookmark(**entity.to_dict()) if entity else None

    def _find_note(self, owner: str, note_id: str) -> DashboardNoteDto | None:
        return self._sirope.find_first(
            DashboardNoteDto,
            lambda n: getattr(n, "owner", None) == owner and getattr(n, "id", None) == note_id,
        )

    def save_note(self, note: DashboardNote) -> str:
        entity = DashboardNoteDto(
            id=note.id or str(uuid.uuid4()),
            owner=note.owner,
            text=note.text,
            bookmark_id=note.bookmark_id,
            entity_id=note.entity_id,
            attribute=note.attribute,
            metric=note.metric,
        )
        existing = self._find_note(note.owner, entity.id)
        if existing:
            entity.__dict__[Sirope.OID_ID] = existing.__dict__.get(Sirope.OID_ID)
        self._sirope.save(entity)
        return entity.id

    def list_notes(self, owner: str) -> list[DashboardNote]:
        return [
            DashboardNote(**e.to_dict())
            for e in self._sirope.filter(
                DashboardNoteDto, lambda n: getattr(n, "owner", None) == owner
            )
        ]

    def delete_note(self, owner: str, note_id: str) -> None:
        entity = self._find_note(owner, note_id)
        if entity and Sirope.OID_ID in entity.__dict__:
            self._sirope.delete(entity.__dict__[Sirope.OID_ID])

    def _find_comparison(self, owner: str, comp_id: str) -> SavedComparisonDto | None:
        return self._sirope.find_first(
            SavedComparisonDto,
            lambda c: getattr(c, "owner", None) == owner and getattr(c, "id", None) == comp_id,
        )

    def save_comparison(self, comp: SavedComparison) -> str:
        entity = SavedComparisonDto(
            id=comp.id or str(uuid.uuid4()),
            owner=comp.owner,
            name=comp.name,
            entity_ids=comp.entity_ids,
            attribute=comp.attribute,
            metric=comp.metric,
        )
        existing = self._find_comparison(comp.owner, entity.id)
        if existing:
            entity.__dict__[Sirope.OID_ID] = existing.__dict__.get(Sirope.OID_ID)
        self._sirope.save(entity)
        return entity.id

    def list_comparisons(self, owner: str) -> list[SavedComparison]:
        return [
            SavedComparison(**e.to_dict())
            for e in self._sirope.filter(
                SavedComparisonDto, lambda c: getattr(c, "owner", None) == owner
            )
        ]

    def delete_comparison(self, owner: str, comp_id: str) -> None:
        entity = self._find_comparison(owner, comp_id)
        if entity and Sirope.OID_ID in entity.__dict__:
            self._sirope.delete(entity.__dict__[Sirope.OID_ID])

    def _find_alert(self, owner: str, alert_id: str) -> MetricAlertDto | None:
        return self._sirope.find_first(
            MetricAlertDto,
            lambda a: getattr(a, "owner", None) == owner and getattr(a, "id", None) == alert_id,
        )

    def save_alert(self, alert: MetricAlert) -> str:
        entity = MetricAlertDto(
            id=alert.id or str(uuid.uuid4()),
            owner=alert.owner,
            name=alert.name,
            entity_id=alert.entity_id,
            attribute=alert.attribute,
            min_value=alert.min_value,
            max_value=alert.max_value,
        )
        existing = self._find_alert(alert.owner, entity.id)
        if existing:
            entity.__dict__[Sirope.OID_ID] = existing.__dict__.get(Sirope.OID_ID)
        self._sirope.save(entity)
        return entity.id

    def list_alerts(self, owner: str) -> list[MetricAlert]:
        return [
            MetricAlert(**e.to_dict())
            for e in self._sirope.filter(
                MetricAlertDto, lambda a: getattr(a, "owner", None) == owner
            )
        ]

    def list_alerts_for(self, owner: str, entity_id: str, attribute: str) -> list[MetricAlert]:
        eid, attr = entity_id.strip(), attribute.strip()
        return [
            a
            for a in self.list_alerts(owner)
            if a.entity_id == eid and a.attribute == attr
        ]

    def delete_alert(self, owner: str, alert_id: str) -> None:
        entity = self._find_alert(owner, alert_id)
        if entity and Sirope.OID_ID in entity.__dict__:
            self._sirope.delete(entity.__dict__[Sirope.OID_ID])
