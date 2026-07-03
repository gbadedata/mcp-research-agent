"""A small read-only dashboard and JSON API over what the agent has collected.

This gives the automation a viewable surface without turning it into a heavy service: a
JSON API (`/api/items`, `/api/digest`) and a plain HTML page at `/`. It is intentionally
read-only, so it is safe to leave running while the agent or an MCP client writes to the
same store. `create_app(store)` takes an explicit store, which keeps it testable with the
FastAPI test client and no network.
"""
from __future__ import annotations

import html

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from .digest import build_digest
from .store import Store


def create_app(store: Store) -> FastAPI:
    app = FastAPI(title="research-agent dashboard")

    @app.get("/api/items")
    def api_items(limit: int = 20):
        return {"total": store.count(), "items": store.list_items(limit)}

    @app.get("/api/digest")
    def api_digest(limit: int = 20):
        return {"digest": build_digest(store, limit)}

    @app.get("/", response_class=HTMLResponse)
    def index():
        items = store.list_items(50)
        rows = "\n".join(
            f"<li><a href='{html.escape(it['url'])}'>{html.escape(it['title'])}</a>"
            f" <span class='src'>{html.escape(it['source'])}</span>"
            f"<div class='sum'>{html.escape(it['summary'])}</div></li>"
            for it in items
        ) or "<li>No items collected yet.</li>"
        return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Research Agent</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 760px; margin: 2rem auto; color: #1a1a1a; }}
  h1 {{ color: #1f3864; }}
  .count {{ color: #5e5e5e; }}
  ul {{ list-style: none; padding: 0; }}
  li {{ padding: .75rem 0; border-bottom: 1px solid #eee; }}
  a {{ color: #1f3864; text-decoration: none; font-weight: 600; }}
  .src {{ color: #5e5e5e; font-size: .85em; }}
  .sum {{ color: #333; font-size: .95em; margin-top: .2rem; }}
</style></head>
<body>
  <h1>Research Agent</h1>
  <p class="count">{store.count()} items collected. JSON at <code>/api/items</code> and <code>/api/digest</code>.</p>
  <ul>{rows}</ul>
</body></html>"""

    return app
