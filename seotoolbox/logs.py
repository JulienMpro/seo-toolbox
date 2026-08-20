"""Streaming parser and analyzer for common and combined HTTP access logs."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from .models import LogEntry, LogReport

LOG_RE = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ \[(?P<date>[^]]+)\] "(?P<method>\S+) (?P<path>\S+)(?: [^"]+)?" '
    r'(?P<status>\d{3}) (?:\d+|-)\s*(?:"[^"]*"\s*"(?P<ua>[^"]*)")?'
)
BOT_NAMES = ("googlebot", "bingbot", "duckduckbot", "yandex")


def parse_log(path: str | Path, bot_filter: str | None = None) -> list[LogEntry]:
    """Parse valid common/combined log lines, optionally filtering user agents."""
    entries: list[LogEntry] = []
    needle = bot_filter.casefold() if bot_filter else None
    with Path(path).open(encoding="utf-8", errors="replace") as stream:
        for line in stream:
            match = LOG_RE.match(line.rstrip("\n"))
            if not match:
                continue
            values = match.groupdict()
            ua = values.get("ua") or ""
            if needle and needle not in ua.casefold():
                continue
            entries.append(LogEntry(values["ip"], values["date"], values["method"], values["path"],
                                    int(values["status"]), ua))
    return entries


def analyze_logs(entries: list[LogEntry]) -> LogReport:
    """Aggregate status families, URLs, IPs, bots and problematic endpoints."""
    families = Counter((entry.status // 100) * 100 for entry in entries)
    urls = Counter(entry.path for entry in entries)
    ips = Counter(entry.ip for entry in entries)
    bot_days = Counter(entry.date.split(":", 1)[0] for entry in entries
                       if any(bot in entry.ua.casefold() for bot in BOT_NAMES))
    problems = Counter((entry.status, entry.path) for entry in entries
                       if entry.status == 404 or 500 <= entry.status < 600)
    return LogReport(len(entries), dict(sorted(families.items())), urls.most_common(20), ips.most_common(20),
                     sorted(bot_days.items()), [(status, url, count) for (status, url), count in
                                                sorted(problems.items(), key=lambda value: (-value[1], value[0]))])
