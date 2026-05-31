from __future__ import annotations

import fakeredis
import redis


def _build_app(monkeypatch):
    fake_server = fakeredis.FakeServer()

    def _fake_from_url(_url: str, decode_responses: bool = True):
        return fakeredis.FakeRedis(server=fake_server, decode_responses=decode_responses)

    monkeypatch.setattr(redis.Redis, "from_url", staticmethod(_fake_from_url))

    from src.app import create_app

    app = create_app()
    app.config["TESTING"] = True
    return app


def _login(client):
    return client.post(
        "/login",
        data={"edUsername": "profesor", "edPassword": "profesor123"},
        follow_redirects=False,
    )


def test_login_and_dashboard(monkeypatch):
    app = _build_app(monkeypatch)
    client = app.test_client()

    resp = _login(client)
    assert resp.status_code == 302

    page = client.get("/dashboard")
    assert page.status_code == 200
    assert b"series-chart" in page.data
    assert b"sel-entity" in page.data
    assert b"Explorar" in page.data


def test_api_stats_without_external_api(monkeypatch):
    app = _build_app(monkeypatch)
    client = app.test_client()
    _login(client)

    resp = client.get(
        "/api/stats",
        query_string={
            "entityId": "urn:nagasaki:solar:plant-1",
            "attribute": "powerKw",
            "metric": "mean",
        },
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["stats"]["entityId"] == "urn:nagasaki:solar:plant-1"
    assert "labeledStats" in data["stats"]
    assert len(data["ranking"]["ranking"]) >= 10


def test_api_stats_both_fail_returns_400(monkeypatch):
    app = _build_app(monkeypatch)
    client = app.test_client()
    _login(client)

    resp = client.get(
        "/api/stats",
        query_string={
            "entityId": "urn:nagasaki:solar:plant-1",
            "attribute": "atributoInexistente",
            "metric": "mean",
        },
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["stats"].get("error")
    assert data["ranking"].get("error")


def test_api_series(monkeypatch):
    app = _build_app(monkeypatch)
    client = app.test_client()
    _login(client)

    resp = client.get(
        "/api/series",
        query_string={
            "entityId": "urn:nagasaki:solar:plant-1",
            "attribute": "powerKw",
        },
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["values"]) >= 30


def test_api_compare(monkeypatch):
    app = _build_app(monkeypatch)
    client = app.test_client()
    _login(client)

    resp = client.get(
        "/api/compare",
        query_string={
            "entityIds": "urn:nagasaki:solar:plant-1,urn:nagasaki:solar:plant-2",
            "attribute": "powerKw",
            "metric": "mean",
        },
    )
    assert resp.status_code == 200
    assert len(resp.get_json()["items"]) == 2


def test_api_stats_batch(monkeypatch):
    app = _build_app(monkeypatch)
    client = app.test_client()
    _login(client)

    resp = client.post(
        "/api/stats/batch",
        json={"requests": [{"entityId": "urn:nagasaki:solar:plant-1", "attribute": "powerKw"}]},
    )
    assert resp.status_code == 200
    assert len(resp.get_json()["results"]) == 1


def test_create_and_delete_view(monkeypatch):
    app = _build_app(monkeypatch)
    client = app.test_client()
    _login(client)

    create = client.post(
        "/api/views",
        json={"name": "demo", "entityId": "urn:x", "attribute": "powerKw", "metric": "mean"},
    )
    assert create.status_code == 200
    item_id = create.get_json()["item"]["id"]

    listed = client.get("/api/views").get_json()["items"]
    assert any(x["id"] == item_id for x in listed)

    deleted = client.delete(f"/api/views/{item_id}")
    assert deleted.status_code == 200


def test_bookmark_delete_unlinks_notes(monkeypatch):
    app = _build_app(monkeypatch)
    client = app.test_client()
    _login(client)

    bm = client.post(
        "/api/bookmarks",
        json={"label": "bm", "entityId": "urn:e", "attribute": "powerKw"},
    ).get_json()["item"]
    note = client.post(
        "/api/notes",
        json={"text": "nota", "bookmarkId": bm["id"]},
    ).get_json()["item"]
    assert note["bookmark_id"] == bm["id"]

    client.delete(f"/api/bookmarks/{bm['id']}")
    notes = client.get("/api/notes").get_json()["items"]
    restored = next(x for x in notes if x["id"] == note["id"])
    assert restored["bookmark_id"] is None


def test_note_invalid_bookmark(monkeypatch):
    app = _build_app(monkeypatch)
    client = app.test_client()
    _login(client)

    resp = client.post(
        "/api/notes",
        json={"text": "hola", "bookmarkId": "no-existe"},
    )
    assert resp.status_code == 400


def test_note_with_query_context(monkeypatch):
    app = _build_app(monkeypatch)
    client = app.test_client()
    _login(client)

    resp = client.post(
        "/api/notes",
        json={
            "text": "obs",
            "entityId": "urn:nagasaki:solar:plant-1",
            "attribute": "powerKw",
            "metric": "mean",
        },
    )
    assert resp.status_code == 200
    item = resp.get_json()["item"]
    assert item["entity_id"] == "urn:nagasaki:solar:plant-1"


def test_notes_form_post(monkeypatch):
    app = _build_app(monkeypatch)
    client = app.test_client()
    _login(client)

    resp = client.post(
        "/notes",
        data={
            "text": "desde formulario",
            "entityId": "urn:nagasaki:solar:plant-1",
            "attribute": "powerKw",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"desde formulario" in resp.data

    api = client.get("/api/notes").get_json()["items"]
    assert any(x["text"] == "desde formulario" for x in api)


def test_views_form_post(monkeypatch):
    app = _build_app(monkeypatch)
    client = app.test_client()
    _login(client)

    resp = client.post(
        "/views",
        data={
            "name": "mi vista",
            "entityId": "urn:nagasaki:solar:plant-1",
            "attribute": "powerKw",
            "metric": "mean",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    items = client.get("/api/views").get_json()["items"]
    assert any(x["name"] == "mi vista" for x in items)


def test_comparison_and_alert_crud(monkeypatch):
    app = _build_app(monkeypatch)
    client = app.test_client()
    _login(client)

    cmp_resp = client.post(
        "/api/comparisons",
        json={
            "name": "dos plantas",
            "entityIds": "urn:nagasaki:solar:plant-1,urn:nagasaki:solar:plant-2",
            "attribute": "powerKw",
            "metric": "mean",
        },
    )
    assert cmp_resp.status_code == 200
    cmp_id = cmp_resp.get_json()["item"]["id"]

    alert_resp = client.post(
        "/api/alerts",
        json={
            "name": "techo",
            "entityId": "urn:nagasaki:solar:plant-1",
            "attribute": "powerKw",
            "maxValue": 999999,
        },
    )
    assert alert_resp.status_code == 200

    check = client.get(
        "/api/alerts/check",
        query_string={
            "entityId": "urn:nagasaki:solar:plant-1",
            "attribute": "powerKw",
        },
    )
    assert check.status_code == 200
    assert check.get_json()["messages"] == []

    client.delete(f"/api/comparisons/{cmp_id}")
    assert client.get("/api/comparisons").get_json()["items"] == []


def test_html_404(monkeypatch):
    app = _build_app(monkeypatch)
    client = app.test_client()
    _login(client)

    resp = client.get("/ruta-inexistente", headers={"Accept": "text/html"})
    assert resp.status_code == 404
    assert b"No encontrada" in resp.data or b"encontrada" in resp.data
