---
name: research-digest
description: >
  Collect information from a set of web sources, store the notable items (deduplicated),
  and produce a short digest. Use when asked to monitor sources, gather links on a topic,
  or turn a list of pages into a brief.
tools:
  - fetch_url
  - save_item
  - list_items
  - search_items
---

# Research Digest

A skill for turning web sources into a stored, deduplicated digest. It follows the
SKILL.md convention shared by OpenClaw and Claude Code (metadata and instructions in the
front matter, guidance below), and the tools it declares are served by the
`mcp-research-agent` MCP server in this repository.

## When to use

- "Monitor these pages and tell me what is new."
- "Gather the key links on <topic> and summarise them."
- "Turn this list of URLs into a short brief."

## How to run it

1. For each source URL, call `fetch_url` to get the title, cleaned text, and outbound links.
2. Decide which items are worth keeping. For each, call `save_item` with a one-sentence
   `summary`. Duplicates (same URL) are ignored automatically, so re-running is safe.
3. Optionally call `list_items` or `search_items` to review what has been collected.
4. Write the digest as short bullet points: title, source, one line each.

## Guidance

- Prefer a few high-signal items over many low-signal ones.
- Keep summaries to a single sentence.
- If a fetch fails, note it and continue with the other sources rather than stopping.
- If the task does not actually need a model (for example, just re-render what is already
  stored), the deterministic `digest` command in this repo does that with no LLM call.

## Wiring

Register the server with an MCP-capable client (Claude Desktop, Claude Code, or another
agent runtime). See the repository README for the exact configuration.
