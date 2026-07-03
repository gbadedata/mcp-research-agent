"""The research agent: a standard tool-use loop.

Given a goal, the agent lets the model call tools (fetch pages, save notable items, list or
search what it has stored) and keeps feeding tool results back until the model stops asking
for tools and returns a final digest. The loop is model-agnostic: it reads `.stop_reason`
and `.content` blocks, which both the Anthropic SDK response and the MockLLM provide.
"""
from __future__ import annotations

import json

from .store import Store
from .tools import fetch_feed, fetch_url, list_items, save_item, search_items

SYSTEM = (
    "You are a research automation agent. Use the tools to read the given sources "
    "(fetch_url for a page, fetch_feed for an RSS or Atom feed), save the items worth "
    "keeping with a one-sentence summary each, then reply with a short digest of what you "
    "found as concise bullet points. Do not save duplicates. When you have written the "
    "digest, stop calling tools."
)

TOOL_SCHEMAS = [
    {
        "name": "fetch_url",
        "description": "Fetch a web page and return its title, cleaned text, and outbound links.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL to fetch (http(s) or file://)."},
                "max_chars": {"type": "integer", "description": "Max characters of text to return."},
            },
            "required": ["url"],
        },
    },
    {
        "name": "save_item",
        "description": "Save a notable item to the store. Deduplicated on URL.",
        "input_schema": {
            "type": "object",
            "properties": {
                "source": {"type": "string"},
                "title": {"type": "string"},
                "url": {"type": "string"},
                "summary": {"type": "string"},
            },
            "required": ["source", "title", "url"],
        },
    },
    {
        "name": "list_items",
        "description": "List the most recently stored items.",
        "input_schema": {
            "type": "object",
            "properties": {"limit": {"type": "integer"}},
        },
    },
    {
        "name": "search_items",
        "description": "Search stored items by keyword in title or summary.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}},
            "required": ["query"],
        },
    },
    {
        "name": "fetch_feed",
        "description": "Parse an RSS or Atom feed and return its recent entries (title, link, summary).",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Feed URL (http(s) or file://)."},
                "limit": {"type": "integer"},
            },
            "required": ["url"],
        },
    },
]


def _dispatch(store: Store) -> dict:
    return {
        "fetch_url": lambda **kw: fetch_url(**kw),
        "fetch_feed": lambda **kw: fetch_feed(**kw),
        "save_item": lambda **kw: save_item(store, **kw),
        "list_items": lambda **kw: list_items(store, **kw),
        "search_items": lambda **kw: search_items(store, **kw),
    }


def _blocks_to_dicts(content) -> list:
    out = []
    for b in content:
        if b.type == "text":
            out.append({"type": "text", "text": b.text})
        elif b.type == "tool_use":
            out.append({"type": "tool_use", "id": b.id, "name": b.name, "input": b.input})
    return out


class ResearchAgent:
    def __init__(self, llm, store: Store, max_steps: int = 8):
        self.llm = llm
        self.store = store
        self.max_steps = max_steps

    def run(self, goal: str) -> dict:
        dispatch = _dispatch(self.store)
        messages: list = [{"role": "user", "content": goal}]
        transcript: list = []
        texts: list = []

        for step in range(1, self.max_steps + 1):
            resp = self.llm.complete(system=SYSTEM, messages=messages, tools=TOOL_SCHEMAS)
            messages.append({"role": "assistant", "content": _blocks_to_dicts(resp.content)})
            tool_uses = [b for b in resp.content if b.type == "tool_use"]
            texts = [b.text for b in resp.content if b.type == "text"]

            if resp.stop_reason != "tool_use" or not tool_uses:
                return {"digest": "\n".join(texts).strip(), "steps": step,
                        "items_saved": self.store.count(), "transcript": transcript}

            results = []
            for tu in tool_uses:
                try:
                    result = dispatch[tu.name](**tu.input)
                    is_error = False
                except Exception as exc:  # surface tool errors back to the model
                    result, is_error = {"error": str(exc)}, True
                transcript.append({"tool": tu.name, "input": tu.input, "result": result})
                block = {"type": "tool_result", "tool_use_id": tu.id, "content": json.dumps(result)}
                if is_error:
                    block["is_error"] = True
                results.append(block)
            messages.append({"role": "user", "content": results})

        return {"digest": "\n".join(texts).strip(), "steps": self.max_steps,
                "items_saved": self.store.count(), "transcript": transcript,
                "stopped": "max_steps"}
