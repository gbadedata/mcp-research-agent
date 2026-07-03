import os

from research_agent.store import Store
from research_agent.tools import fetch_url, list_items, save_item, search_items

SAMPLE = "file://" + os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "examples", "sample_page.html"))


def test_fetch_url_parses_title_text_links():
    out = fetch_url(SAMPLE)
    assert out["status"] == 200
    assert "Sample Feed" in out["title"]
    assert "Model Context Protocol" in out["text"]
    assert "https://example.com/agents" in out["links"]
    # script/style content should be stripped (none here) and text collapsed
    assert "  " not in out["text"]


def test_fetch_url_respects_max_chars():
    out = fetch_url(SAMPLE, max_chars=20)
    assert len(out["text"]) <= 20


def test_save_item_and_dedupe():
    s = Store()
    first = save_item(s, "Feed", "T", "https://x.com/a", "s")
    dup = save_item(s, "Feed", "T", "https://x.com/a", "s")
    assert first["saved"] is True and dup["saved"] is False
    assert dup["reason"] == "duplicate url"


def test_list_and_search_tools():
    s = Store()
    save_item(s, "Feed", "MCP note", "https://x.com/mcp", "protocol")
    assert list_items(s)["total"] == 1
    assert len(search_items(s, "MCP")["items"]) == 1
