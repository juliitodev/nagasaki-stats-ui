from __future__ import annotations

from src.models import DashboardNote, EntityBookmark, SavedView
from src.storage import Storage


def find_bookmark_for(
    store: Storage, owner: str, entity_id: str, attribute: str
) -> EntityBookmark | None:
    eid, attr = entity_id.strip(), attribute.strip()
    for bm in store.list_bookmarks(owner):
        if bm.entity_id == eid and bm.attribute == attr:
            return bm
    return None


def normalize_note(note: DashboardNote, store: Storage, owner: str) -> tuple[DashboardNote, str | None]:
    if note.bookmark_id:
        bm = store.get_bookmark(owner, note.bookmark_id)
        if not bm:
            return note, "El marcador indicado no existe"
        note.entity_id = note.entity_id or bm.entity_id
        note.attribute = note.attribute or bm.attribute
        note.metric = note.metric or bm.default_metric
    elif note.entity_id and note.attribute:
        bm = find_bookmark_for(store, owner, note.entity_id, note.attribute)
        if bm:
            note.bookmark_id = bm.id
            note.metric = note.metric or bm.default_metric
    else:
        return note, "La nota debe ir ligada a un marcador o indicar fuente y magnitud"

    if not note.entity_id or not note.attribute:
        return note, "No se pudo resolver el contexto de la nota"
    return note, None


def view_summary(view: SavedView) -> str:
    return f"{view.entity_id} · {view.attribute} · ranking por {view.metric}"


def bookmark_summary(bm: EntityBookmark) -> str:
    return f"{bm.entity_id} · {bm.attribute} (métrica habitual: {bm.default_metric})"
