"""Tests for the FastAPI service. Ollama is replaced by a small fake, so no model and no network are needed."""
import json

import pytest
import requests
from fastapi.testclient import TestClient

from app import main

client = TestClient(main.app)


class FakeResponse:
    """Just enough of requests.Response for the code under test (also works as a context manager)."""

    def __init__(self, lines=None, payload=None, status=200):
        self._lines = lines or []
        self._payload = payload or {}
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error")

    def json(self):
        return self._payload

    def iter_lines(self):
        return iter(self._lines)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def ndjson(*tokens):
    return [json.dumps({"response": t}).encode() for t in tokens]


@pytest.fixture
def ollama(monkeypatch):
    """Records what the service sends to Ollama and lets a test choose the reply."""
    seen = {}

    def fake_post(url, json=None, stream=None, timeout=None):
        seen["url"], seen["payload"], seen["timeout"] = url, json, timeout
        reply = seen.get("reply") or FakeResponse(lines=ndjson("Hello", ", ", "world"))
        if isinstance(reply, Exception):
            raise reply
        return reply

    def fake_get(url, timeout=None):
        seen["get_url"] = url
        reply = seen.get("get_reply") or FakeResponse(payload={"models": [{"name": "phi3:mini"}, {"name": "qwen3:8b"}]})
        if isinstance(reply, Exception):
            raise reply
        return reply

    monkeypatch.setattr(main.requests, "post", fake_post)
    monkeypatch.setattr(main.requests, "get", fake_get)
    return seen


def test_root():
    r = client.get("/")
    assert r.status_code == 200 and "running" in r.json()["message"]


def test_health_lists_models(ollama):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True and r.json()["models"] == ["phi3:mini", "qwen3:8b"]
    assert ollama["get_url"].endswith("/api/tags")


def test_health_is_502_when_ollama_is_down(ollama):
    ollama["get_reply"] = requests.ConnectionError("connection refused")
    r = client.get("/health")
    assert r.status_code == 502 and r.json()["ok"] is False and "refused" in r.json()["error"]


def test_models_returns_names_and_raw(ollama):
    r = client.get("/models")
    assert r.status_code == 200
    assert r.json()["names"] == ["phi3:mini", "qwen3:8b"] and "raw" in r.json()


def test_models_error_is_502(ollama):
    ollama["get_reply"] = requests.ConnectionError("boom")
    r = client.get("/models")
    assert r.status_code == 502 and "Ollama error" in r.json()["detail"]


def test_chat_post_joins_the_streamed_tokens(ollama):
    r = client.post("/chat", json={"prompt": "hi"})
    assert r.status_code == 200
    assert r.json()["response"] == "Hello, world"
    assert ollama["url"].endswith("/api/generate")


def test_chat_post_sends_the_documented_defaults(ollama):
    client.post("/chat", json={"prompt": "hi"})
    p = ollama["payload"]
    assert p["model"] == "phi3:mini" and p["prompt"] == "hi" and p["think"] is False
    assert p["options"] == {"temperature": 0.7, "top_p": 0.9, "num_predict": 512}


def test_chat_maps_max_tokens_to_num_predict_and_passes_think(ollama):
    client.post("/chat", json={"prompt": "x", "model": "qwen3:8b", "max_tokens": 64, "temperature": 0.2, "top_p": 0.5, "think": True})
    p = ollama["payload"]
    assert p["model"] == "qwen3:8b" and p["think"] is True
    assert p["options"] == {"temperature": 0.2, "top_p": 0.5, "num_predict": 64}


def test_chat_get_works_like_post(ollama):
    r = client.get("/chat", params={"prompt": "hi", "max_tokens": 10})
    assert r.status_code == 200 and r.json()["max_tokens"] == 10 and ollama["payload"]["options"]["num_predict"] == 10


def test_chat_requires_a_prompt():
    assert client.get("/chat").status_code == 422
    assert client.post("/chat", json={}).status_code == 422


def test_chat_skips_blank_and_broken_lines(ollama):
    ollama["reply"] = FakeResponse(lines=[b"", b"not json", *ndjson("ok"), b'{"done": true}'])
    assert client.get("/chat", params={"prompt": "x"}).json()["response"] == "ok"


def test_chat_timeout_is_504(ollama):
    ollama["reply"] = requests.Timeout("slow")
    r = client.get("/chat", params={"prompt": "x"})
    assert r.status_code == 504


def test_chat_ollama_error_is_502(ollama):
    ollama["reply"] = FakeResponse(status=500)
    r = client.get("/chat", params={"prompt": "x"})
    assert r.status_code == 502


def test_stream_is_plain_text_tokens(ollama):
    r = client.get("/stream", params={"prompt": "x"})
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/plain")
    assert r.text == "Hello, world"


def test_stream_reports_a_timeout_inside_the_stream(ollama):
    ollama["reply"] = requests.Timeout("slow")
    assert "Timeout talking to Ollama" in client.get("/stream", params={"prompt": "x"}).text


def test_playground_is_html_with_a_model_selector():
    r = client.get("/playground")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/html")
    assert 'id="model"' in r.text


def test_cors_allows_any_origin():
    r = client.get("/", headers={"Origin": "http://example.com"})
    assert r.headers.get("access-control-allow-origin") in ("*", "http://example.com")
