"""AI answer visibility operations backed by DataForSEO."""

from __future__ import annotations

from typing import Any

from .client import DataForSEOClient
from .keywords import _country
from .models import AiMention, AiTopPage

ENDPOINTS = {
    "mentions": "ai_optimization/llm_mentions/search/live",
    "aggregated": "ai_optimization/llm_mentions/aggregated_metrics/live",
    "top_pages": "ai_optimization/llm_mentions/top_pages/live",
}
DEFAULT_ENGINES = ["chatgpt", "perplexity", "gemini"]


def _items(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for result in results:
        nested = result.get("items")
        if isinstance(nested, list):
            output.extend(value for value in nested if isinstance(value, dict))
        else:
            output.append(result)
    return output


def mentions(keyword: str, engines: list[str] | None = None, country: str = "US",
             client: DataForSEOClient | None = None, limit: int | None = None) -> list[AiMention]:
    """Search tracked LLM mentions for one keyword."""
    selected = engines or DEFAULT_ENGINES
    # The current search/live contract accepts target entities and one platform.
    # Keep the public engine vocabulary while translating ChatGPT's API spelling.
    platform = "chat_gpt" if selected[0] == "chatgpt" else selected[0]
    payload: dict[str, Any] = {
        "target": [{"keyword": keyword, "search_filter": "include"}],
        "platform": platform,
        **_country(country),
    }
    if limit is not None:
        payload["limit"] = limit
    output: list[AiMention] = []
    source_counts: dict[str, tuple[int | None, int]] = {}
    for item in _items((client or DataForSEOClient()).get_result(ENDPOINTS["mentions"], payload)):
        sources = item.get("sources")
        if isinstance(sources, list):
            for source in sources:
                if not isinstance(source, dict) or not source.get("domain"):
                    continue
                domain = str(source["domain"])
                position = source.get("position")
                previous_rank, count = source_counts.get(domain, (None, 0))
                best_rank = position if previous_rank is None else (
                    min(previous_rank, position) if isinstance(position, int) else previous_rank)
                source_counts[domain] = (best_rank, count + 1)
        elif item.get("domain") or item.get("target"):
            output.append(AiMention(str(item.get("keyword") or keyword), item.get("engine") or selected[0],
                                    item.get("domain") or item.get("target"), item.get("rank"),
                                    item.get("mention_count")))
    output.extend(AiMention(keyword, selected[0], domain, rank, count)
                  for domain, (rank, count) in source_counts.items())
    return output[:limit] if limit is not None else output


def aggregated(keywords: list[str], engines: list[str] | None = None,
               client: DataForSEOClient | None = None) -> list[dict[str, Any]]:
    """Return optional aggregate fields without manufacturing a fixed schema."""
    payload = {"keywords": [word.strip() for word in keywords if word.strip()],
               "engines": engines or DEFAULT_ENGINES, "aggregation": "domain"}
    return _items((client or DataForSEOClient()).get_result(ENDPOINTS["aggregated"], payload))


def top_pages(keywords: list[str], engines: list[str] | None = None, limit: int = 20,
              client: DataForSEOClient | None = None) -> list[AiTopPage]:
    """Return the pages most often cited by tracked LLM engines."""
    clean = [word.strip() for word in keywords if word.strip()]
    payload = {"keywords": clean, "engines": engines or DEFAULT_ENGINES, "limit": limit}
    output = []
    for item in _items((client or DataForSEOClient()).get_result(ENDPOINTS["top_pages"], payload))[:limit]:
        output.append(AiTopPage(str(item.get("keyword") or (clean[0] if len(clean) == 1 else "N/D")),
                                item.get("engine"), item.get("page_url") or item.get("url"),
                                item.get("rank"), item.get("mention_count")))
    return output
