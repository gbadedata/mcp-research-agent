"""Tests for the headless-browser fetcher.

A real browser binary cannot be downloaded in every environment, so these mock Playwright:
they verify the wrapper drives a browser correctly and parses the rendered HTML, and that
the tool degrades gracefully when Playwright is absent.
"""
import research_agent.tools as tools

RENDERED = ("<html><head><title>Rendered SPA</title></head>"
            "<body><p>Hello from JavaScript</p>"
            "<a href='https://example.com/x'>link</a></body></html>")


class _FakePage:
    def goto(self, url, **kw):
        self.url = url

    def content(self):
        return RENDERED


class _FakeBrowser:
    def __init__(self):
        self.closed = False

    def new_page(self, **kw):
        return _FakePage()

    def close(self):
        self.closed = True


class _FakeChromium:
    def launch(self, **kw):
        return _FakeBrowser()


class _FakePW:
    def __init__(self):
        self.chromium = _FakeChromium()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_fetch_rendered_parses_rendered_html(monkeypatch):
    monkeypatch.setattr(tools, "sync_playwright", lambda: _FakePW())
    out = tools.fetch_rendered("https://example.com/spa")
    assert out["title"] == "Rendered SPA"
    assert "Hello from JavaScript" in out["text"]
    assert "https://example.com/x" in out["links"]
    assert out["rendered"] is True


def test_fetch_rendered_without_playwright(monkeypatch):
    monkeypatch.setattr(tools, "sync_playwright", None)
    out = tools.fetch_rendered("https://example.com/spa")
    assert "error" in out and "playwright" in out["error"].lower()
