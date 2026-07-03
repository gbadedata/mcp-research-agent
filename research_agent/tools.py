"""The tools the agent can call and the MCP server exposes.

Each tool is a plain function that returns a JSON-serialisable dict, so the exact same
implementations back both the Anthropic tool-use loop and the MCP server. `fetch_url`
handles real http(s) as well as file:// URLs; the file:// path keeps tests and the offline
demo free of any network access.
"""
from __future__ import annotations

from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .store import Store

USER_AGENT = "mcp-research-agent/0.1 (+https://github.com/gbadedata/mcp-research-agent)"


def fetch_url(url: str, max_chars: int = 2000) -> dict:
    """Fetch a page and return its title, cleaned text, and outbound links."""
    parsed = urlparse(url)
    if parsed.scheme == "file":
        with open(parsed.path, encoding="utf-8") as fh:
            html, status = fh.read(), 200
    else:
        resp = requests.get(url, timeout=15, headers={"User-Agent": USER_AGENT})
        html, status = resp.text, resp.status_code

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    text = " ".join(soup.get_text(" ").split())[:max_chars]
    links = []
    for a in soup.find_all("a", href=True):
        href = urljoin(url, a["href"])
        if href.startswith("http") and href not in links:
            links.append(href)
        if len(links) >= 20:
            break
    return {"url": url, "status": status, "title": title, "text": text, "links": links}


def save_item(store: Store, source: str, title: str, url: str, summary: str = "") -> dict:
    item_id = store.add_item(source=source, title=title, url=url, summary=summary)
    return {"saved": item_id is not None, "id": item_id,
            "reason": "stored" if item_id is not None else "duplicate url"}


def list_items(store: Store, limit: int = 10) -> dict:
    return {"items": store.list_items(limit), "total": store.count()}


def search_items(store: Store, query: str, limit: int = 10) -> dict:
    return {"query": query, "items": store.search_items(query, limit)}
