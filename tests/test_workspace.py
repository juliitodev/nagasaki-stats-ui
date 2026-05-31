from __future__ import annotations

from tests.test_ui import _build_app, _login


def test_note_links_to_existing_bookmark(monkeypatch):
    app = _build_app(monkeypatch)
    client = app.test_client()
    _login(client)

    bm = client.post(
        "/api/bookmarks",
        json={
            "label": "planta",
            "entityId": "urn:nagasaki:solar:plant-1",
            "attribute": "powerKw",
            "defaultMetric": "mean",
        },
    ).get_json()["item"]

    note = client.post(
        "/api/notes",
        json={"text": "observación", "entityId": bm["entity_id"], "attribute": bm["attribute"]},
    ).get_json()["item"]
    assert note["bookmark_id"] == bm["id"]
    assert note["entity_id"] == bm["entity_id"]


def test_note_requires_anchor(monkeypatch):
    app = _build_app(monkeypatch)
    client = app.test_client()
    _login(client)

    resp = client.post("/api/notes", json={"text": "solo texto suelto"})
    assert resp.status_code == 400
    assert "marcador" in resp.get_json()["error"].lower() or "fuente" in resp.get_json()["error"].lower()


def test_bookmark_stores_default_metric(monkeypatch):
    app = _build_app(monkeypatch)
    client = app.test_client()
    _login(client)

    item = client.post(
        "/api/bookmarks",
        json={
            "label": "t",
            "entityId": "urn:nagasaki:solar:plant-2",
            "attribute": "powerKw",
            "defaultMetric": "median",
        },
    ).get_json()["item"]
    assert item["default_metric"] == "median"
