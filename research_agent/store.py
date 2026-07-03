"""SQLite persistence for collected items.

A deliberately small store: one table, deduplicated on URL, so the agent can be run
repeatedly against the same sources without piling up duplicates. Defaults to an
in-memory database, which keeps the tests hermetic.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone


class Store:
    def __init__(self, path: str = ":memory:"):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._init()

    def _init(self) -> None:
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS items (
                   id         INTEGER PRIMARY KEY AUTOINCREMENT,
                   source     TEXT NOT NULL,
                   title      TEXT NOT NULL,
                   url        TEXT NOT NULL UNIQUE,
                   summary    TEXT NOT NULL DEFAULT '',
                   created_at TEXT NOT NULL
               )"""
        )
        self.conn.commit()

    def add_item(self, source: str, title: str, url: str, summary: str = "") -> int | None:
        """Insert an item. Returns the new id, or None if the URL was already stored."""
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO items (source, title, url, summary, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (source, title, url, summary, datetime.now(timezone.utc).isoformat(timespec="seconds")),
        )
        self.conn.commit()
        return cur.lastrowid if cur.rowcount else None

    def list_items(self, limit: int = 20) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM items ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def search_items(self, query: str, limit: int = 20) -> list[dict]:
        like = f"%{query}%"
        rows = self.conn.execute(
            "SELECT * FROM items WHERE title LIKE ? OR summary LIKE ? "
            "ORDER BY id DESC LIMIT ?", (like, like, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]

    def close(self) -> None:
        self.conn.close()
