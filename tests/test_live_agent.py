"""A live integration test for the agent.

Skipped unless ANTHROPIC_API_KEY is set, so the public CI stays green and free. Provide the
key (locally, or as a CI secret) to exercise the real tool-use loop end to end.
"""
import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="no ANTHROPIC_API_KEY set; live agent test skipped",
)


def test_live_agent_produces_a_digest():
    from research_agent.agent import ResearchAgent
    from research_agent.llm import AnthropicLLM
    from research_agent.store import Store

    sample = "file://" + os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "examples", "sample_page.html"))
    store = Store()
    agent = ResearchAgent(AnthropicLLM(), store, max_steps=6)
    result = agent.run(
        f"Fetch this source, save the notable items, and write a short digest: {sample}")

    assert result["digest"].strip()          # the model returned a digest
    assert result["items_saved"] >= 1        # and actually used the tools to save something
