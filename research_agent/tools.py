"""The tools the agent can call and the MCP server exposes.

Each tool is a plain function that returns a JSON-serialisable dict, so the exact same
implementations back both the Anthropic tool-use loop and the MCP server. `fetch_url`
handles real http(s) as well as file:// URLs; the file:// path keeps tests and the offline
demo free of any network access.
"""
from __future__ import annotations

from urllib.parse import urljoin, urlparse

import feedparser
import requests
from bs4 import BeautifulSoup

from .store import Store

try:  # optional, only needed for fetch_rendered
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

USER_AGENT = "mcp-research-agent/0.1 (+https://github.com/gbadedata/mcp-research-agent)"


def _parse_html(html: str, base_url: str, max_chars: int) -> tuple[str, str, list]:
    """Extract title, cleaned text, and outbound links from HTML. Shared by the plain and
    the browser-rendered fetchers."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    text = " ".join(soup.get_text(" ").split())[:max_chars]
    links = []
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        if href.startswith("http") and href not in links:
            links.append(href)
        if len(links) >= 20:
            break
    return title, text, links


def fetch_url(url: str, max_chars: int = 2000) -> dict:
    """Fetch a page and return its title, cleaned text, and outbound links.

    Reads static HTML only. For pages whose content is rendered by JavaScript, use
    fetch_rendered."""
    parsed = urlparse(url)
    if parsed.scheme == "file":
        with open(parsed.path, encoding="utf-8") as fh:
            html, status = fh.read(), 200
    else:
        resp = requests.get(url, timeout=15, headers={"User-Agent": USER_AGENT})
        html, status = resp.text, resp.status_code
    title, text, links = _parse_html(html, url, max_chars)
    return {"url": url, "status": status, "title": title, "text": text, "links": links}


def fetch_rendered(url: str, max_chars: int = 2000, wait_until: str = "networkidle",
                   timeout_ms: int = 15000) -> dict:
    """Fetch a page with a headless browser so JavaScript-rendered content is included.

    Requires Playwright: `pip install playwright && playwright install chromium`. If it is
    not installed, this returns an error dict rather than raising, so the rest of the
    toolkit keeps working."""
    if sync_playwright is None:
        return {"url": url, "error": "playwright not installed; "
                "run: pip install playwright && playwright install chromium"}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(user_agent=USER_AGENT)
            page.goto(url, wait_until=wait_until, timeout=timeout_ms)
            html = page.content()
        finally:
            browser.close()
    title, text, links = _parse_html(html, url, max_chars)
    return {"url": url, "status": 200, "title": title, "text": text, "links": links,
            "rendered": True}


def save_item(store: Store, source: str, title: str, url: str, summary: str = "") -> dict:
    item_id = store.add_item(source=source, title=title, url=url, summary=summary)
    return {"saved": item_id is not None, "id": item_id,
            "reason": "stored" if item_id is not None else "duplicate url"}


def list_items(store: Store, limit: int = 10) -> dict:
    return {"items": store.list_items(limit), "total": store.count()}


def search_items(store: Store, query: str, limit: int = 10) -> dict:
    return {"query": query, "items": store.search_items(query, limit)}


def fetch_feed(url: str, limit: int = 10) -> dict:
    """Parse an RSS or Atom feed and return its recent entries.

    Broadens ingestion beyond single HTML pages: many sources worth monitoring publish a
    feed. Handles file:// for offline use and tests."""
    src = urlparse(url).path if url.startswith("file://") else url
    parsed = feedparser.parse(src)
    entries = []
    for entry in parsed.entries[:limit]:
        summary = (entry.get("summary") or "")
        entries.append({
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "summary": " ".join(summary.split())[:500],
            "published": entry.get("published", entry.get("updated", "")),
        })
    return {"feed_title": parsed.feed.get("title", ""), "count": len(entries), "entries": entries}
