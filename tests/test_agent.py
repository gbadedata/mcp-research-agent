import os

from research_agent.agent import ResearchAgent
from research_agent.llm import MockLLM, make_response, text_block, tool_use_block
from research_agent.store import Store

SAMPLE = "file://" + os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "examples", "sample_page.html"))


def test_agent_runs_tool_loop_and_saves():
    script = [
        make_response([tool_use_block("1", "fetch_url", {"url": SAMPLE})], "tool_use"),
        make_response([
            tool_use_block("2", "save_item", {"source": "Feed", "title": "A",
                                              "url": "https://x.com/a", "summary": "s"}),
            tool_use_block("3", "save_item", {"source": "Feed", "title": "B",
                                              "url": "https://x.com/b", "summary": "s"}),
        ], "tool_use"),
        make_response([text_block("Digest: two items found.")], "end_turn"),
    ]
    store = Store()
    result = ResearchAgent(MockLLM(script), store).run("collect and summarise")
    assert result["items_saved"] == 2
    assert "Digest" in result["digest"]
    assert [s["tool"] for s in result["transcript"]] == ["fetch_url", "save_item", "save_item"]


def test_agent_surfaces_tool_errors_and_continues():
    script = [
        make_response([tool_use_block("1", "does_not_exist", {})], "tool_use"),
        make_response([text_block("done")], "end_turn"),
    ]
    result = ResearchAgent(MockLLM(script), Store()).run("go")
    assert result["digest"] == "done"
    assert result["transcript"][0]["result"].get("error")     # error captured, loop continued


def test_agent_stops_at_max_steps():
    script = [make_response([tool_use_block("1", "list_items", {})], "tool_use")]
    result = ResearchAgent(MockLLM(script), Store(), max_steps=3).run("go")
    assert result.get("stopped") == "max_steps"
    assert result["steps"] == 3
