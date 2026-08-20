"""Keyword research operations backed exclusively by DataForSEOClient."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

from .client import ApiError, DataForSEOClient, DataForSEOError
from .models import IntentInfo, KeywordIdea, KeywordOverview, KeywordRanked

ENDPOINTS = {
    "ideas": "dataforseo_labs/google/keyword_ideas/live",
    "overview": "dataforseo_labs/google/keyword_overview/live",
    "difficulty": "dataforseo_labs/google/bulk_keyword_difficulty/live",
    "suggestions": "dataforseo_labs/google/keyword_suggestions/live",
    "related": "dataforseo_labs/google/related_keywords/live",
    "intent": "dataforseo_labs/google/search_intent/live",
    "gap": "dataforseo_labs/google/domain_intersection/live",
    "for_site": "dataforseo_labs/google/keywords_for_site/live",
}

COUNTRIES = {
    "FR": {"language_code": "fr", "location_name": "France"},
    "GB": {"language_code": "en", "location_code": 2826},
    "UK": {"language_code": "en", "location_code": 2826},
    "US": {"language_code": "en", "location_code": 2840},
    "CA": {"language_code": "en", "location_code": 2124},
    "BE": {"language_code": "fr", "location_name": "Belgium"},
    "CH": {"language_code": "fr", "location_name": "Switzerland"},
    "DE": {"language_code": "de", "location_name": "Germany"},
    "ES": {"language_code": "es", "location_name": "Spain"},
    "IT": {"language_code": "it", "location_name": "Italy"},
}


def _country(country: str) -> dict[str, Any]:
    code = country.upper()
    if code not in COUNTRIES:
        supported = ", ".join(sorted(COUNTRIES))
        raise ValueError(f"Unsupported country '{country}'. Supported values: {supported}")
    return dict(COUNTRIES[code])


def _items(results: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flatten the common result/items envelope used by Labs endpoints."""
    output: list[dict[str, Any]] = []
    for result in results:
        nested = result.get("items")
        if isinstance(nested, list):
            output.extend(item for item in nested if isinstance(item, dict))
        elif "keyword" in result or "keyword_data" in result:
            output.append(result)
    return output


def _keyword(item: dict[str, Any]) -> str | None:
    data = item.get("keyword_data") or {}
    value = item.get("keyword") or (data.get("keyword") if isinstance(data, dict) else None)
    return str(value) if value else None


def _metrics(item: dict[str, Any]) -> dict[str, Any]:
    data = item.get("keyword_data") if isinstance(item.get("keyword_data"), dict) else item
    info = data.get("keyword_info") if isinstance(data.get("keyword_info"), dict) else {}
    props = data.get("keyword_properties") if isinstance(data.get("keyword_properties"), dict) else {}
    intent_data = data.get("search_intent_info") if isinstance(data.get("search_intent_info"), dict) else {}
    keyword_intent = data.get("keyword_intent") if isinstance(data.get("keyword_intent"), dict) else {}
    serp = data.get("serp_info") if isinstance(data.get("serp_info"), dict) else {}
    return {
        "volume": info.get("search_volume", data.get("search_volume")),
        "cpc": info.get("cpc", data.get("cpc")),
        "competition": info.get("competition", data.get("competition")),
        "difficulty": props.get("keyword_difficulty", data.get("keyword_difficulty")),
        "search_intent": intent_data.get("main_intent") or keyword_intent.get("label") or data.get("search_intent"),
        "serp_features": serp.get("serp_item_types", data.get("serp_features")),
    }


def overview(
    keywords: list[str], country: str = "US", client: DataForSEOClient | None = None
) -> list[KeywordOverview]:
    clean = [keyword.strip() for keyword in keywords if keyword.strip()]
    if not clean:
        return []
    api = client or DataForSEOClient()
    payload = {"keywords": clean, **_country(country)}
    found: dict[str, dict[str, Any]] = {}
    for item in _items(api.get_result(ENDPOINTS["overview"], payload)):
        keyword = _keyword(item)
        if keyword:
            found[keyword.casefold()] = _metrics(item)
    return [
        KeywordOverview(keyword=keyword, **found.get(keyword.casefold(), {}))
        for keyword in clean
    ]


def ideas(
    seed: str, country: str = "US", limit: int = 50, client: DataForSEOClient | None = None
) -> list[KeywordIdea]:
    api = client or DataForSEOClient()
    payload = {"keywords": [seed], "limit": limit, **_country(country)}
    raw = _items(api.get_result(ENDPOINTS["ideas"], payload))[:limit]
    base: list[KeywordIdea] = []
    for item in raw:
        keyword = _keyword(item)
        if keyword:
            base.append(KeywordIdea(keyword=keyword, **_metrics(item)))
    words = [item.keyword for item in base]
    if not words:
        return []
    try:
        enriched = {item.keyword.casefold(): item for item in overview(words, country, api)}
        for item in base:
            detail = enriched.get(item.keyword.casefold())
            if detail:
                item.volume, item.cpc, item.competition = detail.volume, detail.cpc, detail.competition
    except (ApiError, DataForSEOError):
        pass
    try:
        difficulty_payload = {"keywords": words, **_country(country)}
        for raw_item in _items(api.get_result(ENDPOINTS["difficulty"], difficulty_payload)):
            keyword = _keyword(raw_item)
            if keyword:
                match = next((item for item in base if item.keyword.casefold() == keyword.casefold()), None)
                if match:
                    match.difficulty = _metrics(raw_item)["difficulty"]
    except (ApiError, DataForSEOError):
        pass
    return base


def _keyword_list(
    endpoint: str, seed_key: str, seed: str, country: str, limit: int, client: DataForSEOClient | None
) -> list[KeywordIdea]:
    api = client or DataForSEOClient()
    payload = {seed_key: seed, "limit": limit, **_country(country)}
    output: list[KeywordIdea] = []
    for item in _items(api.get_result(endpoint, payload))[:limit]:
        keyword = _keyword(item)
        if keyword:
            output.append(KeywordIdea(keyword=keyword, **_metrics(item)))
    return output


def suggestions(seed: str, country: str = "US", limit: int = 30, client: DataForSEOClient | None = None) -> list[KeywordIdea]:
    return _keyword_list(ENDPOINTS["suggestions"], "keyword", seed, country, limit, client)


def related(keyword: str, country: str = "US", limit: int = 30, client: DataForSEOClient | None = None) -> list[KeywordIdea]:
    return _keyword_list(ENDPOINTS["related"], "keyword", keyword, country, limit, client)


def intent(
    keywords: list[str], language_name: str = "English", client: DataForSEOClient | None = None
) -> list[IntentInfo]:
    """Classify keywords by search intent in the requested language."""
    clean = [keyword.strip() for keyword in keywords if keyword.strip()]
    if not clean:
        return []
    api = client or DataForSEOClient()
    found: dict[str, str | None] = {}
    payload = {"keywords": clean, "language_name": language_name}
    for item in _items(api.get_result(ENDPOINTS["intent"], payload)):
        keyword = _keyword(item)
        if keyword:
            found[keyword.casefold()] = _metrics(item)["search_intent"]
    return [IntentInfo(keyword=word, intent=found.get(word.casefold())) for word in clean]


def _ranked(item: dict[str, Any]) -> KeywordRanked | None:
    keyword = _keyword(item)
    if not keyword:
        return None
    metrics = _metrics(item)
    ranked = item.get("ranked_serp_element") if isinstance(item.get("ranked_serp_element"), dict) else {}
    serp_item = ranked.get("serp_item") if isinstance(ranked.get("serp_item"), dict) else {}
    if not serp_item and isinstance(item.get("first_domain_serp_element"), dict):
        serp_item = item["first_domain_serp_element"]
    return KeywordRanked(
        keyword=keyword,
        position=serp_item.get("rank_absolute", item.get("position")),
        url=serp_item.get("url", item.get("url")),
        volume=metrics["volume"], difficulty=metrics["difficulty"], cpc=metrics["cpc"],
        search_intent=metrics["search_intent"],
    )


def keywords_for_site(domain: str, country: str = "US", limit: int = 50, client: DataForSEOClient | None = None) -> list[KeywordRanked]:
    api = client or DataForSEOClient()
    payload = {"target": domain, "limit": limit, "include_serp_info": True, **_country(country)}
    return [ranked for item in _items(api.get_result(ENDPOINTS["for_site"], payload))[:limit] if (ranked := _ranked(item))]


def gap(domain: str, competitors: list[str], country: str = "US", limit: int = 50, client: DataForSEOClient | None = None) -> list[KeywordRanked]:
    api = client or DataForSEOClient()
    unique: dict[str, KeywordRanked] = {}
    for competitor in competitors:
        payload = {
            "target1": domain, "target2": competitor, "intersections": False,
            "include_serp_info": True, "limit": limit, **_country(country),
        }
        for item in _items(api.get_result(ENDPOINTS["gap"], payload)):
            ranked = _ranked(item)
            if ranked:
                unique.setdefault(ranked.keyword.casefold(), ranked)
            if len(unique) >= limit:
                break
    return list(unique.values())[:limit]


def _bigrams(value: str) -> set[str]:
    normalized = re.sub(r"\s+", " ", re.sub(r"[^\w]+", " ", value.casefold())).strip()
    padded = f" {normalized} "
    return {padded[index:index + 2] for index in range(len(padded) - 1)}


def cluster(keywords: list[str], threshold: float = 0.4) -> list[list[str]]:
    """Greedily cluster keywords using Dice similarity over character bigrams."""
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")
    clusters: list[list[str]] = []
    signatures: list[set[str]] = []
    for keyword in (word.strip() for word in keywords if word.strip()):
        signature = _bigrams(keyword)
        best_index, best_score = -1, -1.0
        for index, representative in enumerate(signatures):
            denominator = len(signature) + len(representative)
            score = 2 * len(signature & representative) / denominator if denominator else 1.0
            if score > best_score:
                best_index, best_score = index, score
        if best_index >= 0 and best_score >= threshold:
            clusters[best_index].append(keyword)
        else:
            clusters.append([keyword])
            signatures.append(signature)
    return clusters
