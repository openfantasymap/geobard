"""HTTP smoke tests with a stubbed OpenAI client."""
import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("GEOBARD_OPENAI_API_KEY", "test")
os.environ.setdefault("GEOBARD_OPENAI_MODEL", "fake-model")


def _stub_client(text: str = "a narrated scene"):
    c = MagicMock()
    choice = MagicMock()
    choice.message.content = text
    resp = MagicMock()
    resp.choices = [choice]
    c.chat.completions.create.return_value = resp
    return c


@pytest.fixture
def client():
    # Build the app *after* env is set so settings() doesn't raise.
    from geobard.app import create_app, _client, _settings
    _client.cache_clear()
    _settings.cache_clear()
    app = create_app()
    return TestClient(app)


def test_root_endpoint_lists_routes(client):
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["service"] == "geobard"
    assert "POST /narrate/window" in body["endpoints"]


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_narrate_window(client):
    fake = _stub_client("a quiet morning street")
    with patch("geobard.app._client", return_value=fake):
        r = client.post("/narrate/window", json={
            "geojson": {"type": "FeatureCollection", "features": []},
            "detail_level": "medium",
        })
    assert r.status_code == 200
    assert r.json() == {"text": "a quiet morning street", "model": "fake-model"}


def test_narrate_prompt(client):
    fake = _stub_client("south, along the river")
    with patch("geobard.app._client", return_value=fake):
        r = client.post("/narrate/prompt", json={
            "geojson": {},
            "prompt": "which way is the river?",
        })
    assert r.status_code == 200
    assert r.json()["text"] == "south, along the river"


def test_image_prompt(client):
    fake = _stub_client("a cobbled square at dawn")
    with patch("geobard.app._client", return_value=fake):
        r = client.post("/image/prompt", json={
            "geojson": {"pov": {"lat": 1, "lng": 2}},
            "image_system": ["photoreal"],
        })
    assert r.status_code == 200
    assert r.json()["text"] == "a cobbled square at dawn"


def test_upstream_error_returns_502(client):
    fake = MagicMock()
    fake.chat.completions.create.side_effect = RuntimeError("rate limited")
    with patch("geobard.app._client", return_value=fake):
        r = client.post("/narrate/window", json={"geojson": {}})
    assert r.status_code == 502
    assert "rate limited" in r.json()["detail"]


def test_model_override(client):
    fake = _stub_client("ok")
    with patch("geobard.app._client", return_value=fake):
        r = client.post("/narrate/window", json={
            "geojson": {}, "model": "anthropic/claude-opus-4-7",
        })
    assert r.status_code == 200
    assert r.json()["model"] == "anthropic/claude-opus-4-7"
