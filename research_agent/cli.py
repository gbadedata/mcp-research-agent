"""Command-line entry point.

  python -m research_agent.cli demo                     # offline: MockLLM drives the loop, no API key
  python -m research_agent.cli run --url https://... --url https://...   # real agent (needs ANTHROPIC_API_KEY)
  python -m research_agent.cli serve                    # start the MCP server (stdio)
  python -m research_agent.cli digest --db research_agent.db
  python -m research_agent.cli tools
"""
from __future__ import annotations

import argparse
import os
import sys

SAMPLE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "examples", "sample_page.html"))


def _cmd_tools(_args):
    from .agent import TOOL_SCHEMAS
    print("Tools exposed to the agent and over MCP:\n")
    for tool in TOOL_SCHEMAS:
        required = ", ".join(tool["input_schema"].get("required", []))
        print(f"  {tool['name']:14s} {tool['description']}")
        print(f"                 required: {required or 'none'}\n")


def _cmd_serve(_args):
    from .mcp_server import mcp
    mcp.run()


def _cmd_digest(args):
    from .digest import build_digest
    from .store import Store
    print(build_digest(Store(args.db), limit=args.limit))


def _cmd_demo(args):
    """Run the full agent loop offline: a MockLLM issues the tool calls, but the fetches
    and saves are real, so the printed digest reflects what was actually collected."""
    from .agent import ResearchAgent
    from .digest import build_digest
    from .llm import MockLLM, make_response, text_block, tool_use_block
    from .store import Store

    url = "file://" + SAMPLE
    script = [
        make_response([tool_use_block("c1", "fetch_url", {"url": url})], "tool_use"),
        make_response([
            tool_use_block("c2", "save_item", {
                "source": "Sample Feed", "title": "Anthropic ships new agent tooling",
                "url": "https://example.com/agents", "summary": "New tooling for building agents."}),
            tool_use_block("c3", "save_item", {
                "source": "Sample Feed", "title": "MCP adoption grows",
                "url": "https://example.com/mcp", "summary": "More clients adopt the Model Context Protocol."}),
        ], "tool_use"),
        make_response([text_block(
            "I fetched the source, saved the two notable items, and here is the digest.")], "end_turn"),
    ]

    store = Store(args.db)
    agent = ResearchAgent(MockLLM(script), store)
    result = agent.run("Collect notable items from the sample source and write a digest.")
    print("Agent finished in", result["steps"], "steps, tool calls:",
          [s["tool"] for s in result["transcript"]])
    print("\n" + build_digest(store))


def _cmd_run(args):
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Set ANTHROPIC_API_KEY to run the live agent. To see the loop with no key, use:\n"
              "  python -m research_agent.cli demo", file=sys.stderr)
        return 1
    from .agent import ResearchAgent
    from .digest import build_digest
    from .llm import AnthropicLLM
    from .store import Store

    sources = "\n".join(args.url)
    goal = (f"Fetch each of these sources, save the notable items with a one-line summary, "
            f"then write a short digest:\n{sources}")
    store = Store(args.db)
    agent = ResearchAgent(AnthropicLLM(), store, max_steps=args.max_steps)
    result = agent.run(goal)
    print(result["digest"])
    print("\n" + "-" * 60)
    print(build_digest(store))
    return 0


def _cmd_initdb(args):
    from .store import Store
    Store(args.db)
    print(f"Initialised database at {args.db}")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="research_agent")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("tools", help="list the tools").set_defaults(func=_cmd_tools)
    sub.add_parser("serve", help="run the MCP server (stdio)").set_defaults(func=_cmd_serve)

    pd = sub.add_parser("demo", help="run the agent loop offline with a MockLLM (no API key)")
    pd.add_argument("--db", default=":memory:")
    pd.set_defaults(func=_cmd_demo)

    pr = sub.add_parser("run", help="run the live agent (needs ANTHROPIC_API_KEY)")
    pr.add_argument("--url", action="append", default=[], required=True, help="source URL (repeatable)")
    pr.add_argument("--db", default="research_agent.db")
    pr.add_argument("--max-steps", type=int, default=8)
    pr.set_defaults(func=_cmd_run)

    pg = sub.add_parser("digest", help="print a deterministic digest of stored items")
    pg.add_argument("--db", default="research_agent.db")
    pg.add_argument("--limit", type=int, default=10)
    pg.set_defaults(func=_cmd_digest)

    pi = sub.add_parser("init-db", help="create the database")
    pi.add_argument("--db", default="research_agent.db")
    pi.set_defaults(func=_cmd_initdb)

    args = p.parse_args(argv)
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
