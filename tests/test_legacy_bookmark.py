from __future__ import annotations

import fakeredis
import redis

from src.model.entitybookmarkdto import EntityBookmarkDto
from tests.test_ui import _build_app, _login


def test_notes_page_with_legacy_bookmark(monkeypatch):
    fake_server = fakeredis.FakeServer()

    def _fake_from_url(_url: str, decode_responses: bool = True):
        return fakeredis.FakeRedis(server=fake_server, decode_responses=decode_responses)

    monkeypatch.setattr(redis.Redis, "from_url", staticmethod(_fake_from_url))

    app = _build_app(monkeypatch)
    client = app.test_client()
    _login(client)

    store = app.config["STORE"]
    legacy = EntityBookmarkDto(
        owner="profesor",
        label="legacy",
        entity_id="urn:nagasaki:solar:plant-1",
        attribute="powerKw",
        id="legacy-bm",
    )
    if hasattr(legacy, "default_metric"):
        delattr(legacy, "default_metric")
    store._sirope.save(legacy)

    resp = client.get("/notes")
    assert resp.status_code == 200
    assert b"Nota" in resp.data
