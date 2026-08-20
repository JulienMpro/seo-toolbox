"""Small SERP and keyword tools backed by existing DataForSEO services."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, timedelta
from typing import Any

from .. import keywords as keyword_service
from .. import ranktracker, serp
from ..client import DataForSEOClient
from ..keywords import _country
from . import ArgSpec, ToolSpec, register


COUNTRY_MARKETS = {
    "FR": ("France", "fr"), "GB": ("United Kingdom", "en"),
    "US": ("United States", "en"), "DE": ("Germany", "de"),
    "ES": ("Spain", "es"), "IT": ("Italy", "it"),
    "BE": ("Belgium", "fr"), "CH": ("Switzerland", "fr"),
}


def _values(value: str) -> list[str]:
    """Split newline- or comma-separated values and preserve their order."""
    return [part.strip() for line in value.splitlines() for part in line.split(",") if part.strip()]


def _row(value: Any) -> dict[str, Any]:
    if is_dataclass(value):
        return asdict(value)
    return value if isinstance(value, dict) else {}


def _market(country: str) -> tuple[str, str]:
    code = country.upper()
    if code not in COUNTRY_MARKETS:
        raise ValueError(f"Unsupported country '{country}'. Supported values: {', '.join(COUNTRY_MARKETS)}")
    return COUNTRY_MARKETS[code]


def serp_compare(keywords: str, country: str = "FR") -> list[dict[str, Any]]:
    """Compare the top five organic results and features for several keywords."""
    words = _values(keywords)
    if len(words) < 2:
        raise ValueError("keywords must contain at least two values")
    rows = []
    for word in words:
        features = serp.features(word, country).features or []
        for result in serp.live(word, country, 5):
            item = _row(result)
            rows.append({"keyword": word, "rank": item.get("rank"), "domain": item.get("domain"),
                         "title": item.get("title"), "features": ", ".join(features) or None})
    return rows


def paa_extractor(keyword: str, country: str = "FR") -> list[dict[str, Any]]:
    """Extract People Also Ask questions and snippets from a live SERP."""
    rows = []
    for result in serp._raw(keyword, country, 100, "desktop", None):
        items = result.get("items") if isinstance(result.get("items"), list) else []
        for item in items:
            if not isinstance(item, dict) or item.get("type") != "people_also_ask":
                continue
            nested = item.get("items") if isinstance(item.get("items"), list) else [item]
            for question in nested:
                if isinstance(question, dict):
                    expanded = question.get("expanded_element")
                    if isinstance(expanded, list):
                        expanded = next((value for value in expanded if isinstance(value, dict)), {})
                    if not isinstance(expanded, dict):
                        expanded = {}
                    rows.append({"question": question.get("title"),
                                 "snippet": question.get("text") or expanded.get("text") or expanded.get("snippet")})
    return rows


def serp_features(keyword: str, country: str = "FR") -> list[dict[str, Any]]:
    """Report whether common SERP features are present."""
    present = set(serp.features(keyword, country).features or [])
    common = ["featured_snippet", "people_also_ask", "local_pack", "ai_overview", "top_stories",
              "shopping", "images", "videos", "related_searches"]
    ordered = common + sorted(present - set(common))
    return [{"feature": feature, "present": "✅" if feature in present else "❌"} for feature in ordered]


def serp_devices(keyword: str, country: str = "FR") -> list[dict[str, Any]]:
    """Compare desktop and mobile organic domains by position."""
    desktop = serp.live(keyword, country, 10, "desktop")
    mobile = serp.live(keyword, country, 10, "mobile")
    size = max(len(desktop), len(mobile))
    return [{"position": index + 1,
             "desktop_domain": _row(desktop[index]).get("domain") if index < len(desktop) else None,
             "mobile_domain": _row(mobile[index]).get("domain") if index < len(mobile) else None}
            for index in range(size)]


def serp_countries(keyword: str, countries: str = "FR,GB,US") -> list[dict[str, Any]]:
    """Compare top organic domains and feature counts across markets."""
    rows = []
    for country in _values(countries):
        location, _language = _market(country)
        results = serp.live(keyword, country, 5, location_name=location)
        domains = [_row(item).get("domain") for item in results if _row(item).get("domain")]
        features = serp.features(keyword, country).features or []
        rows.append({"country": country.upper(), "top_domains": domains or None, "feature_count": len(features)})
    return rows


def serp_history(keyword: str, country: str = "FR", days: int = 30) -> list[dict[str, Any]]:
    """Return normalized historical top-ten organic positions."""
    if days <= 0:
        raise ValueError("days must be positive")
    today = date.today()
    payload = {"keyword": keyword, "date_from": (today - timedelta(days=days)).isoformat(),
               "date_to": today.isoformat(), "limit": 10, **_country(country)}
    results = DataForSEOClient().get_result("dataforseo_labs/google/historical_serps/live", payload)
    rows = []
    for result in results:
        nested_items = result.get("items")
        items = nested_items if isinstance(nested_items, list) else ([] if "items" in result else [result])
        for item in items:
            if not isinstance(item, dict):
                continue
            day = item.get("date") or item.get("datetime")
            nested = item.get("items") or item.get("serp_items") or item.get("organic")
            nested = nested if isinstance(nested, list) else [item]
            for entry in nested[:10]:
                if isinstance(entry, dict):
                    rows.append({"date": day, "position": entry.get("rank_absolute", entry.get("position")),
                                 "domain": entry.get("domain")})
    return rows


def rank_bulk(domain: str, keywords: str, country: str = "FR") -> list[dict[str, Any]]:
    """Return a domain's positions and keyword metrics in bulk."""
    return [{"keyword": row.get("keyword"), "position": row.get("position"), "url": row.get("url"),
             "volume": row.get("volume"), "kd": row.get("difficulty")}
            for item in ranktracker.domain_rank(_values(keywords), domain, country)
            if (row := _row(item))]


def intent_analysis(keywords: str, country: str = "FR") -> list[dict[str, Any]]:
    """Classify the intent of several keywords."""
    rows = []
    language = {"fr": "French", "en": "English", "de": "German", "es": "Spanish", "it": "Italian"}[_market(country)[1]]
    for item in keyword_service.intent(_values(keywords), language_name=language):
        row = _row(item)
        rows.append({"keyword": row.get("keyword"), "intent": row.get("intent") or "N/D"})
    return rows


def keyword_gap(domain: str, competitors: str, country: str = "FR", limit: int = 50) -> list[dict[str, Any]]:
    """Find domain keywords absent from the supplied competitors."""
    return [{"keyword": row.get("keyword"), "volume": row.get("volume"),
             "domain_position": row.get("position")}
            for item in keyword_service.gap(domain, _values(competitors), country, limit)
            if (row := _row(item))]


def competitor_keywords(domain: str, country: str = "FR", limit: int = 50) -> list[dict[str, Any]]:
    """List the keywords for which a competitor ranks."""
    return [{"keyword": row.get("keyword"), "position": row.get("position"), "volume": row.get("volume")}
            for item in keyword_service.keywords_for_site(domain, country, limit) if (row := _row(item))]


def keyword_suggestions_tool(keyword: str, country: str = "FR", limit: int = 30) -> list[dict[str, Any]]:
    """Merge and deduplicate keyword suggestions and related terms."""
    found: dict[str, dict[str, Any]] = {}
    for source, values in (("suggestion", keyword_service.suggestions(keyword, country, limit)),
                           ("related", keyword_service.related(keyword, country, limit))):
        for item in values:
            word = _row(item).get("keyword")
            if word:
                found.setdefault(str(word).casefold(), {"keyword": word, "source": source})
    return list(found.values())[:limit]


def top_searches(country: str = "FR", category: str = "", limit: int = 50) -> list[dict[str, Any]]:
    """Return the market's top searches from DataForSEO Labs."""
    payload: dict[str, Any] = {"limit": limit, **_country(country)}
    if category:
        try:
            payload["category_code"] = int(category)
        except ValueError:
            raise ValueError("category must be a numeric DataForSEO category code") from None
    results = DataForSEOClient().get_result("dataforseo_labs/google/top_searches/live", payload)
    rows = []
    for result in results:
        items = result.get("items") if isinstance(result.get("items"), list) else [result]
        for item in items:
            if isinstance(item, dict):
                data = item.get("keyword_data") if isinstance(item.get("keyword_data"), dict) else item
                info = data.get("keyword_info") if isinstance(data.get("keyword_info"), dict) else {}
                rows.append({"rank": item.get("rank", len(rows) + 1), "keyword": data.get("keyword"),
                             "estimated_volume": info.get("search_volume", data.get("search_volume"))})
    return rows[:limit]


def features_matrix(keywords: str, country: str = "FR") -> list[dict[str, Any]]:
    """Build a feature-presence matrix for up to twenty keywords."""
    words = _values(keywords)
    if len(words) > 20:
        raise ValueError("features_matrix accepts at most 20 keywords")
    found = [(word, set(serp.features(word, country).features or [])) for word in words]
    columns = sorted(set().union(*(features for _, features in found))) if found else []
    return [{"keyword": word, **{feature: "✅" if feature in features else "❌" for feature in columns}}
            for word, features in found]


def A(name: str, required: bool = True, default: str | None = None) -> ArgSpec:
    return ArgSpec(name, required, default, name.replace("_", " ").capitalize() + ".")


register(ToolSpec("serp_compare", serp_compare, "Compare organic results for several keywords.", "serp", [A("keywords"), A("country", False, "FR")], "table"))
register(ToolSpec("paa_extractor", paa_extractor, "Extract People Also Ask questions and snippets.", "serp", [A("keyword"), A("country", False, "FR")], "table"))
register(ToolSpec("serp_features", serp_features, "Show the features present in a SERP.", "serp", [A("keyword"), A("country", False, "FR")], "table"))
register(ToolSpec("serp_devices", serp_devices, "Compare desktop and mobile organic results.", "serp", [A("keyword"), A("country", False, "FR")], "table"))
register(ToolSpec("serp_countries", serp_countries, "Compare a keyword across several countries.", "serp", [A("keyword"), A("countries", False, "FR,GB,US")], "table"))
register(ToolSpec("serp_history", serp_history, "Show historical organic positions.", "serp", [A("keyword"), A("country", False, "FR"), A("days", False, "30")], "table"))
register(ToolSpec("rank_bulk", rank_bulk, "Check a domain's positions for several keywords.", "serp", [A("domain"), A("keywords"), A("country", False, "FR")], "table"))
register(ToolSpec("intent_analysis", intent_analysis, "Classify search intent for several keywords.", "serp", [A("keywords"), A("country", False, "FR")], "table"))
register(ToolSpec("keyword_gap", keyword_gap, "Find keywords missing from competitor profiles.", "serp", [A("domain"), A("competitors"), A("country", False, "FR"), A("limit", False, "50")], "table"))
register(ToolSpec("competitor_keywords", competitor_keywords, "List a competitor's ranking keywords.", "serp", [A("domain"), A("country", False, "FR"), A("limit", False, "50")], "table"))
register(ToolSpec("keyword_suggestions_tool", keyword_suggestions_tool, "Merge suggested and related keywords.", "serp", [A("keyword"), A("country", False, "FR"), A("limit", False, "30")], "table"))
register(ToolSpec("top_searches", top_searches, "List a market's top searches.", "serp", [A("country", False, "FR"), A("category", False, ""), A("limit", False, "50")], "table"))
register(ToolSpec("features_matrix", features_matrix, "Compare SERP features across keywords.", "serp", [A("keywords"), A("country", False, "FR")], "table"))
