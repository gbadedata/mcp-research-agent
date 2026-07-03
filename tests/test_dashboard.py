from fastapi.testclient import TestClient

from research_agent.dashboard import create_app
from research_agent.store import Store


def _client_with_items():
    store = Store()
    store.add_item("Feed", "Agents and tools", "https://x.com/a", "a summary about agents")
    store.add_item("Feed", "MCP note", "https://x.com/b", "about MCP")
    return TestClient(create_app(store))


def test_api_items():
    r = _client_with_items().get("/api/items")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2 and len(body["items"]) == 2


def test_api_digest():
    r = _client_with_items().get("/api/digest")
    assert r.status_code == 200
    assert "Agents and tools" in r.json()["digest"]


def test_index_html_lists_items():
    r = _client_with_items().get("/")
    assert r.status_code == 200
    assert "Research Agent" in r.text
    assert "Agents and tools" in r.text and "https://x.com/a" in r.text
