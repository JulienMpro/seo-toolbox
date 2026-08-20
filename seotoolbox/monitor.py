"""SQLite-backed detection of technical on-page changes between crawls."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .audit import crawl_site
from .models import CrawlResult, MonitorChange, MonitorReport

FIELDS = ("status", "title", "meta", "h1", "canonical", "noindex")


def _connect(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("CREATE TABLE IF NOT EXISTS pages (url TEXT PRIMARY KEY, status INT, title TEXT, "
                       "meta TEXT, h1 TEXT, canonical TEXT, noindex INT, content_length INT, "
                       "first_seen TEXT, last_seen TEXT)")
    return connection


def _values(page: CrawlResult) -> dict[str, Any]:
    return {"status": page.status, "title": page.title, "meta": page.meta_description, "h1": page.h1,
            "canonical": page.canonical, "noindex": int(page.noindex), "content_length": page.content_length}


def _replace(connection: sqlite3.Connection, pages: list[CrawlResult], previous: dict[str, sqlite3.Row]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    connection.execute("DELETE FROM pages")
    for page in pages:
        values = _values(page)
        first_seen = previous[page.url]["first_seen"] if page.url in previous else now
        connection.execute("INSERT INTO pages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                           (page.url, values["status"], values["title"], values["meta"], values["h1"],
                            values["canonical"], values["noindex"], values["content_length"], first_seen, now))
    connection.commit()


def init_baseline(url: str, max_pages: int = 100, db_path: str | Path = "data/monitor.db") -> int:
    """Crawl and replace a monitoring baseline; return the number stored."""
    pages = crawl_site(url, max_pages)
    with _connect(db_path) as connection:
        _replace(connection, pages, {})
    return len(pages)


def check(url: str, max_pages: int = 100, db_path: str | Path = "data/monitor.db") -> MonitorReport:
    """Compare a crawl with its baseline and atomically update that baseline."""
    pages = crawl_site(url, max_pages)
    current = {page.url: page for page in pages}
    with _connect(db_path) as connection:
        previous = {row["url"]: row for row in connection.execute("SELECT * FROM pages")}
        added = sorted(current.keys() - previous.keys())
        removed = sorted(previous.keys() - current.keys())
        changes = [MonitorChange(value, "added", None, value) for value in added]
        changes.extend(MonitorChange(value, "removed", None, None) for value in removed)
        for page_url in sorted(current.keys() & previous.keys()):
            values = _values(current[page_url])
            for field in FIELDS:
                old, new = previous[page_url][field], values[field]
                if old != new:
                    changes.append(MonitorChange(page_url, field, old, new))
        _replace(connection, pages, previous)
    return MonitorReport(changes, added, removed, len(pages))
