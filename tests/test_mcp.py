import asyncio
import os

os.environ["RESEARCH_DB"] = ":memory:"   # keep the server's store off disk during tests

from research_agent.mcp_server import mcp  # noqa: E402


def test_mcp_exposes_expected_tools():
    tools = asyncio.run(mcp.list_tools())
    names = {t.name for t in tools}
    assert {"fetch_url", "save_item", "list_items", "search_items"} <= names
