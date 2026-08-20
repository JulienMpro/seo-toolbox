"""YouTube SERP mini-tools backed by DataForSEO."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from ..client import DataForSEOClient
from . import ArgSpec as A, ToolSpec, register


def _items(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for result in results:
        nested = result.get("items")
        if isinstance(nested, list):
            output.extend(x for x in nested if isinstance(x, dict))
        elif "items" not in result:
            output.append(result)
    return output


def _video_id(value: str) -> str:
    match = re.search(r"(?:v=|youtu\.be/|shorts/)([\w-]{6,})", value)
    return match.group(1) if match else value.strip()


def _first(item: dict[str, Any], *keys: str) -> Any:
    """Return the first present field while preserving valid zero values."""
    return next((item[key] for key in keys if key in item), None)


def youtube_keywords(keyword: str, limit: int = 10, client: DataForSEOClient | None = None) -> list[dict[str, Any]]:
    """List organic YouTube results for a keyword."""
    payload = {"keyword": keyword, "location_code": 2840, "language_code": "en"}
    rows = []
    for item in _items((client or DataForSEOClient()).get_result("serp/youtube/organic/live/advanced", payload))[:limit]:
        rows.append({"rank": item.get("rank_absolute") or item.get("rank_group"), "title": item.get("title"),
                     "channel": _first(item, "channel_name", "channel"), "views": _first(item, "views_count", "views"),
                     "duration": item.get("duration"), "url": item.get("url")})
    return rows


def youtube_video_info(video: str, client: DataForSEOClient | None = None) -> list[dict[str, Any]]:
    """Return metadata and engagement for one YouTube video."""
    item = next(iter(_items((client or DataForSEOClient()).get_result(
        "serp/youtube/video_info/live/advanced",
        {"video_id": _video_id(video), "location_code": 2840, "language_code": "en"}))), {})
    return [{"title": item.get("title"), "channel": _first(item, "channel_name", "channel"),
             "views": _first(item, "views_count", "views"), "likes": _first(item, "likes_count", "likes"),
             "comments": _first(item, "comments_count", "comments"), "duration": item.get("duration"),
             "date": item.get("publication_date") or item.get("date") }]


def youtube_comments(video: str, limit: int = 20, client: DataForSEOClient | None = None) -> list[dict[str, Any]]:
    """Return viewer comments for a YouTube video."""
    rows = []
    for item in _items((client or DataForSEOClient()).get_result(
            "serp/youtube/video_comments/live/advanced",
            {"video_id": _video_id(video), "location_code": 2840, "language_code": "en"}))[:limit]:
        rows.append({"author": item.get("author_name") or item.get("author"), "text": item.get("text"),
                     "likes": _first(item, "likes_count", "likes"), "date": item.get("publication_date") or item.get("date")})
    return rows


def youtube_transcript(video: str, n: int = 2, limit: int = 10, client: DataForSEOClient | None = None) -> str:
    """Return a transcript followed by its most frequent word n-grams."""
    parts = []
    for item in _items((client or DataForSEOClient()).get_result(
            "serp/youtube/video_subtitles/live/advanced",
            {"video_id": _video_id(video), "location_code": 2840, "language_code": "en"})):
        value = item.get("text") or item.get("transcript") or item.get("subtitle")
        if isinstance(value, str): parts.append(value)
        elif isinstance(value, list): parts.extend(str(x.get("text")) for x in value if isinstance(x, dict) and x.get("text"))
    text = " ".join(parts)
    words = re.findall(r"[\w'-]+", text.casefold())
    counts = Counter(" ".join(words[i:i + n]) for i in range(max(0, len(words) - n + 1)))
    suffix = "\n\nTop n-grams:\n" + "\n".join(f"{gram}: {count}" for gram, count in counts.most_common(limit))
    return (text or "N/D") + suffix


register(ToolSpec("youtube_keywords", youtube_keywords, "Search organic YouTube video results.", "serp", [A("keyword", True), A("limit", False, "10")], "table"))
register(ToolSpec("youtube_video_info", youtube_video_info, "Show metadata for a YouTube video.", "serp", [A("video", True)], "table"))
register(ToolSpec("youtube_comments", youtube_comments, "Extract YouTube comments for voice-of-customer analysis.", "serp", [A("video", True), A("limit", False, "20")], "table"))
register(ToolSpec("youtube_transcript", youtube_transcript, "Extract a YouTube transcript and top n-grams.", "serp", [A("video", True), A("n", False, "2"), A("limit", False, "10")]))
