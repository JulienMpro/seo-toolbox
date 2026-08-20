"""Domain rank tracking operations backed by DataForSEO."""

from __future__ import annotations

from typing import Any

from .client import DataForSEOClient
from .keywords import _country, _items, _keyword, _metrics
from .models import RankHistory, RankPosition, SerpCompetitor

ENDPOINTS = {
    "domain": "dataforseo_labs/google/domain_rank_overview/live",
    "history": "dataforseo_labs/google/historical_rank_overview/live",
    "competitors": "dataforseo_labs/google/serp_competitors/live",
}


def domain_rank(keywords: list[str], domain: str, country: str = "US", limit: int = 50,
                client: DataForSEOClient | None = None) -> list[RankPosition]:
    """Return current organic positions for a domain and keyword set."""
    clean = [word.strip() for word in keywords if word.strip()]
    if not clean:
        return []
    payload = {"target": domain, "keywords": clean, "limit": limit, **_country(country)}
    output: list[RankPosition] = []
    for item in _items((client or DataForSEOClient()).get_result(ENDPOINTS["domain"], payload))[:limit]:
        keyword = _keyword(item)
        if not keyword:
            continue
        ranked = item.get("ranked_serp_element") if isinstance(item.get("ranked_serp_element"), dict) else {}
        serp = ranked.get("serp_item") if isinstance(ranked.get("serp_item"), dict) else ranked
        metrics = _metrics(item)
        output.append(RankPosition(keyword, serp.get("rank_absolute", serp.get("position")),
                                   serp.get("url"), serp.get("type", ranked.get("se_type")),
                                   metrics["volume"], metrics["difficulty"]))
    return output


def rank_history(keywords: list[str], domain: str, country: str, date_from: str, date_to: str,
                 client: DataForSEOClient | None = None) -> list[RankHistory]:
    """Return historical positions, tolerating the API's alternate series shapes."""
    clean = [word.strip() for word in keywords if word.strip()]
    if not clean:
        return []
    payload = {"target": domain, "keywords": clean, "date_from": date_from, "date_to": date_to,
               **_country(country)}
    output: list[RankHistory] = []
    for item in _items((client or DataForSEOClient()).get_result(ENDPOINTS["history"], payload)):
        keyword = _keyword(item)
        series = item.get("history") or item.get("positions") or item.get("items")
        if isinstance(series, list):
            for point in series:
                if isinstance(point, dict) and keyword:
                    output.append(RankHistory(keyword, point.get("date"), point.get("position", point.get("rank_absolute"))))
        elif keyword:
            output.append(RankHistory(keyword, item.get("date"), item.get("position", item.get("rank_absolute"))))
    return output


def serp_competitors(domain: str, country: str = "US", limit: int = 20,
                     client: DataForSEOClient | None = None) -> list[SerpCompetitor]:
    """Return domains competing in the same search results."""
    payload = {"target": domain, "limit": limit, **_country(country)}
    output = []
    for item in _items((client or DataForSEOClient()).get_result(ENDPOINTS["competitors"], payload))[:limit]:
        name = item.get("domain") or item.get("target")
        if name:
            output.append(SerpCompetitor(str(name), item.get("avg_position"), item.get("median_position"),
                                         item.get("keywords_count"), item.get("et_visibility", item.get("visibility"))))
    return output
