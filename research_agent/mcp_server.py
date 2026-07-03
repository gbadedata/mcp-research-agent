"""An MCP server exposing the research tools.

Runs over stdio and can be registered with any MCP client (Claude Desktop, Claude Code, or
another agent runtime). The same tool implementations back the standalone agent in
`agent.py`, so nothing is duplicated. Start it with `python -m research_agent.mcp_server`
or `python -m research_agent.cli serve`.
"""
from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

from . import tools as t
from .store import Store

mcp = FastMCP("research-agent")
_store = Store(os.environ.get("RESEARCH_DB", "research_agent.db"))


@mcp.tool()
def fetch_url(url: str, max_chars: int = 2000) -> dict:
    """Fetch a web page and return its title, cleaned text, and outbound links."""
    return t.fetch_url(url, max_chars=max_chars)


@mcp.tool()
def fetch_rendered(url: str, max_chars: int = 2000) -> dict:
    """Fetch a page with a headless browser so JavaScript-rendered content is included."""
    return t.fetch_rendered(url, max_chars=max_chars)


@mcp.tool()
def save_item(source: str, title: str, url: str, summary: str = "") -> dict:
    """Save a notable item to the store. Deduplicated on URL."""
    return t.save_item(_store, source=source, title=title, url=url, summary=summary)


@mcp.tool()
def list_items(limit: int = 10) -> dict:
    """List the most recently stored items."""
    return t.list_items(_store, limit=limit)


@mcp.tool()
def search_items(query: str, limit: int = 10) -> dict:
    """Search stored items by keyword in title or summary."""
    return t.search_items(_store, query=query, limit=limit)


@mcp.tool()
def fetch_feed(url: str, limit: int = 10) -> dict:
    """Parse an RSS or Atom feed and return its recent entries."""
    return t.fetch_feed(url, limit=limit)


if __name__ == "__main__":
    mcp.run()
