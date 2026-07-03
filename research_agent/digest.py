"""A plain, no-LLM digest of what has been collected.

The role values reaching for the simplest thing that works, so this is here for when an
LLM is not warranted: it renders the stored items directly. It also gives the CLI something
useful to do with no API key.
"""
from __future__ import annotations

from .store import Store


def build_digest(store: Store, limit: int = 10) -> str:
    items = store.list_items(limit)
    if not items:
        return "No items collected yet."
    lines = [f"Research digest ({len(items)} of {store.count()} items):", ""]
    for it in items:
        summary = f" {it['summary']}" if it["summary"] else ""
        lines.append(f"- {it['title']} [{it['source']}]{summary}\n  {it['url']}")
    return "\n".join(lines)
