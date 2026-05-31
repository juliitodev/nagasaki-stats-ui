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
    client.post("/login", data={"edUsername": "profesor", "edPassword": "profesor123"})


def test_compare_page_renders(monkeypatch):
    app = _build_app(monkeypatch)
    client = app.test_client()
    _login(client)

    resp = client.get(
        "/compare",
        query_string={
            "attribute": "powerKw",
            "metric": "mean",
            "entityIds": [
                "urn:nagasaki:solar:plant-1",
                "urn:nagasaki:solar:plant-2",
            ],
        },
    )
    assert resp.status_code == 200
    assert b"compare-chart" in resp.data
