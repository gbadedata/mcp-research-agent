"""The model layer.

`AnthropicLLM` wraps the real Messages API. `MockLLM` returns pre-scripted responses and
ignores its inputs, which lets the whole agent loop be exercised in tests and in an offline
demo without an API key. Both expose the same `.complete(...)` call and return objects with
the same shape the Anthropic SDK uses (a `.content` list of blocks and a `.stop_reason`),
so the agent code does not know or care which one it is talking to.
"""
from __future__ import annotations

import os
from types import SimpleNamespace


def text_block(text: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=text)


def tool_use_block(block_id: str, name: str, tool_input: dict) -> SimpleNamespace:
    return SimpleNamespace(type="tool_use", id=block_id, name=name, input=tool_input)


def make_response(blocks: list, stop_reason: str) -> SimpleNamespace:
    return SimpleNamespace(content=blocks, stop_reason=stop_reason)


class AnthropicLLM:
    def __init__(self, model: str | None = None):
        from anthropic import Anthropic
        self.client = Anthropic()
        self.model = model or os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

    def complete(self, *, system, messages, tools, max_tokens: int = 1024):
        return self.client.messages.create(
            model=self.model, max_tokens=max_tokens, system=system,
            messages=messages, tools=tools,
        )


class MockLLM:
    """Deterministic stand-in that plays back a fixed list of responses."""

    def __init__(self, script: list):
        self.script = list(script)
        self.i = 0
        self.seen_messages: list = []

    def complete(self, *, system, messages, tools, max_tokens: int = 1024):
        self.seen_messages.append(messages)
        resp = self.script[min(self.i, len(self.script) - 1)]
        self.i += 1
        return resp
