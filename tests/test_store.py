from research_agent.store import Store


def test_add_and_count():
    s = Store()
    assert s.add_item("src", "Title A", "https://x.com/a", "sum") is not None
    assert s.count() == 1


def test_dedupe_on_url():
    s = Store()
    first = s.add_item("src", "Title", "https://x.com/a")
    dup = s.add_item("src", "Title again", "https://x.com/a")
    assert first is not None and dup is None      # second insert is a duplicate URL
    assert s.count() == 1


def test_list_orders_newest_first():
    s = Store()
    s.add_item("src", "one", "https://x.com/1")
    s.add_item("src", "two", "https://x.com/2")
    items = s.list_items()
    assert items[0]["title"] == "two" and items[1]["title"] == "one"


def test_search_matches_title_and_summary():
    s = Store()
    s.add_item("src", "MCP servers", "https://x.com/mcp", "protocol details")
    s.add_item("src", "Something else", "https://x.com/other", "about MCP too")
    assert len(s.search_items("MCP")) == 2
    assert len(s.search_items("servers")) == 1
