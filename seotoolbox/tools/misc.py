"""Miscellaneous local SEO utilities."""

from __future__ import annotations

import difflib
import re
import socket
import time
from datetime import datetime
from urllib.parse import urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx

from . import ArgSpec, ToolSpec, register


def check_http(url: str) -> list[dict]:
    """Fetch a URL and report resolution, response metadata, and elapsed time."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname: raise ValueError("url must be an absolute HTTP(S) URL")
    started = time.perf_counter()
    response = httpx.get(url, timeout=15, follow_redirects=True)
    elapsed = (time.perf_counter() - started) * 1000
    return [{"url": str(response.url), "ip": socket.gethostbyname(parsed.hostname), "status": response.status_code, "server": response.headers.get("server"), "content_type": response.headers.get("content-type"), "content_length": response.headers.get("content-length"), "cache_control": response.headers.get("cache-control"), "elapsed_ms": round(elapsed, 2)}]


def extract_emails(value: str) -> str:
    """Extract unique email addresses from text."""
    emails = re.findall(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])", value)
    return "\n".join(sorted(set(emails), key=str.casefold))


def extract_urls(value: str) -> str:
    """Extract unique absolute HTTP(S) URLs from plain text or HTML."""
    urls = re.findall(r"https?://[^\s<>\"']+", value)
    return "\n".join(sorted({url.rstrip(".,);]") for url in urls}))


def text_diff(text1: str, text2: str, mode: str = "unified") -> str:
    """Compare two texts as unified or side-by-side line differences."""
    left, right = text1.splitlines(), text2.splitlines()
    if mode == "unified": return "\n".join(difflib.unified_diff(left, right, fromfile="text1", tofile="text2", lineterm=""))
    if mode == "side-by-side":
        width = max([len(line) for line in left] + [5])
        return "\n".join(f"{a:<{width}} | {b}" for a, b in zip(left + [""] * max(0, len(right)-len(left)), right + [""] * max(0, len(left)-len(right))))
    raise ValueError("mode must be unified or side-by-side")


def count_text(value: str) -> str:
    """Count characters, non-space characters, words, and lines."""
    words = re.findall(r"[^\W_]+(?:[-'][^\W_]+)*", value, re.UNICODE)
    lines = len(value.splitlines()) if value else 0
    return f"Characters: {len(value)}; without spaces: {sum(not char.isspace() for char in value)}; words: {len(words)}; lines: {lines}"


_LOREM = "Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua".split()


def lorem_seo(paragraphs: int = 1, words: int = 50, keywords: str = "") -> str:
    """Generate deterministic placeholder paragraphs with optional SEO terms."""
    if paragraphs <= 0 or words <= 0: raise ValueError("paragraphs and words must be positive")
    extras = [item.strip() for item in keywords.split(",") if item.strip()]
    pool = _LOREM + extras
    result = []
    for paragraph in range(paragraphs):
        selected = [pool[(paragraph * words + index) % len(pool)] for index in range(words)]
        result.append(" ".join(selected).capitalize() + ".")
    return "\n\n".join(result)


def tz_convert(value: str, source: str, target: str) -> str:
    """Convert a local ISO date-time between IANA time zones."""
    try: converted = datetime.fromisoformat(value).replace(tzinfo=ZoneInfo(source)).astimezone(ZoneInfo(target))
    except ZoneInfoNotFoundError as exc: raise ValueError(f"unknown timezone: {exc.args[0]}") from exc
    except ValueError as exc: raise ValueError("value must be an ISO date-time such as 2026-08-20T14:30") from exc
    return converted.isoformat()


def A(name: str, required: bool = True, default: str | None = None) -> ArgSpec: return ArgSpec(name, required, default, name.replace("_", " ").capitalize() + ".")
register(ToolSpec("check_http", check_http, "Check a URL's IP, headers, status, and latency.", "misc", [A("url")], "table"))
register(ToolSpec("extract_emails", extract_emails, "Extract unique email addresses from text.", "misc", [A("value")]))
register(ToolSpec("extract_urls", extract_urls, "Extract unique URLs from text or HTML.", "misc", [A("value")]))
register(ToolSpec("text_diff", text_diff, "Compare two texts with a readable diff.", "misc", [A("text1"), A("text2"), A("mode", False, "unified")]))
register(ToolSpec("count_text", count_text, "Count text characters, words, and lines.", "misc", [A("value")]))
register(ToolSpec("lorem_seo", lorem_seo, "Generate parameterized SEO placeholder text.", "misc", [A("paragraphs", False, "1"), A("words", False, "50"), A("keywords", False, "")]))
register(ToolSpec("tz_convert", tz_convert, "Convert local time between IANA time zones.", "misc", [A("value"), A("source"), A("target")]))
