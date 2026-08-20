"""Content, commerce, trends, and AI intelligence mini-tools."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from .. import geo
from ..client import ApiError, DataForSEOClient
from ..keywords import _country
from . import ArgSpec as A, ToolSpec, register


def _items(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for result in results:
        nested = result.get("items")
        out.extend(x for x in nested if isinstance(x, dict)) if isinstance(nested, list) else out.append(result)
    return out


def _call(path: str, payload: dict[str, Any], client: DataForSEOClient | None) -> list[dict[str, Any]]:
    return _items((client or DataForSEOClient()).get_result(path, payload))


def brand_mentions(keyword: str, limit: int = 10, client: DataForSEOClient | None = None) -> list[dict[str, Any]]:
    """Find pages containing a phrase or brand mention."""
    rows = []
    for item in _call("content_analysis/search/live", {"keyword": keyword, "limit": limit}, client)[:limit]:
        content_info = item.get("content_info")
        if not isinstance(content_info, dict):
            content_info = {}
        rows.append({
            "url": item.get("url"),
            "domain": item.get("domain"),
            "rank": item.get("url_rank") or item.get("domain_rank"),
            "relevance": item.get("score"),
            "spam_score": item.get("spam_score"),
            "title": content_info.get("title") or content_info.get("page_title") or "N/D",
        })
    return rows


def phrase_trends(keyword: str, client: DataForSEOClient | None = None) -> list[dict[str, Any]]:
    """Return a phrase's citation trend over time."""
    rows = []
    for item in _call("content_analysis/phrase_trends/live", {"keyword": keyword}, client):
        series = item.get("metrics") or item.get("trends") or item.get("history") or item.get("items")
        if isinstance(series, dict): series = [{"date": key, "value": value} for key, value in series.items()]
        for point in series if isinstance(series, list) else [item]:
            if isinstance(point, dict): rows.append({"date": point.get("date") or point.get("year_month"), "value": point.get("value") or point.get("count")})
    return rows


def content_summary(keyword: str, client: DataForSEOClient | None = None) -> list[dict[str, Any]]:
    """Return aggregate citation metrics for a content-analysis keyword."""
    rows = _call("content_analysis/summary/live", {"keyword": keyword}, client)
    return [{"total_count": x.get("total_count", "N/D"),
             "rank": x.get("rank", "N/D"),
             "top_domains": x.get("top_domains", "N/D"),
             "sentiment_connotations": x.get("sentiment_connotations", "N/D"),
             "connotation_types": x.get("connotation_types", "N/D"),
             "page_types": x.get("page_types", "N/D"),
             "countries": x.get("countries", "N/D"),
             "languages": x.get("languages", "N/D")} for x in rows]


def amazon_products(keyword: str, limit: int = 10, client: DataForSEOClient | None = None) -> list[dict[str, Any]]:
    """Search Amazon products by keyword."""
    payload = {"keyword": keyword, "location_code": 2840, "language_code": "en_US", "limit": limit}
    rows = []
    for x in _call("merchant/amazon/products/live/advanced", payload, client)[:limit]:
        rating = x.get("rating") if isinstance(x.get("rating"), dict) else {}
        rows.append({"title": x.get("title"), "price": x.get("price_from") or x.get("price") or x.get("price_current"),
                     "rating": rating.get("value") if rating else x.get("rating_value"),
                     "reviews": rating.get("votes_count") if rating else x.get("reviews_count"),
                     "asin": x.get("asin") or x.get("data_asin")})
    return rows


def amazon_product_keywords(asin: str, limit: int = 20, client: DataForSEOClient | None = None) -> list[dict[str, Any]]:
    """List keywords for which an Amazon product ranks."""
    rows = []
    payload = {"asin": asin, "location_name": "United States", "language_code": "en", "limit": limit}
    for x in _call("dataforseo_labs/amazon/ranked_keywords/live", payload, client)[:limit]:
        data = x.get("keyword_data") if isinstance(x.get("keyword_data"), dict) else x
        info = data.get("keyword_info") if isinstance(data.get("keyword_info"), dict) else {}
        ranked = x.get("ranked_serp_element") if isinstance(x.get("ranked_serp_element"), dict) else {}
        serp = ranked.get("serp_item") if isinstance(ranked.get("serp_item"), dict) else ranked
        rows.append({"keyword": data.get("keyword"), "position": serp.get("rank_absolute") or x.get("position"), "volume": info.get("search_volume") or data.get("search_volume")})
    return rows


def amazon_competitors(asin: str, limit: int = 20, client: DataForSEOClient | None = None) -> list[dict[str, Any]]:
    """Find products competing with an Amazon ASIN."""
    return [{"asin": x.get("asin") or x.get("product_asin"), "title": x.get("title"),
             "relevance": x.get("relevance") or x.get("avg_position")}
            for x in _call("dataforseo_labs/amazon/product_competitors/live", {"asin": asin, "limit": limit}, client)[:limit]]


def amazon_sellers(asin: str, limit: int = 20, client: DataForSEOClient | None = None) -> list[dict[str, Any]]:
    """List Amazon sellers and current offers for an ASIN."""
    payload = {"asin": asin, "location_code": 2840, "language_code": "en_US", "limit": limit}
    return [{"seller": x.get("seller_name") or x.get("seller"), "price": x.get("price") or x.get("price_current"),
             "stock": x.get("stock") or x.get("availability")} for x in _call("merchant/amazon/sellers/live/advanced", payload, client)[:limit]]


def amazon_asin(asin: str, client: DataForSEOClient | None = None) -> list[dict[str, Any]]:
    """Return detailed Amazon product data for an ASIN."""
    rows = _call("merchant/amazon/asin/live/advanced", {"asin": asin, "location_code": 2840, "language_code": "en_US"}, client)
    x = rows[0] if rows else {}
    return [{"asin": asin, "title": x.get("title"), "price": x.get("price") or x.get("price_current"),
             "images": x.get("images"), "description": x.get("description"), "rating": x.get("rating") or x.get("rating_value"),
             "reviews": x.get("reviews_count")}]


def _trend_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for item in rows:
        series = item.get("interest_over_time") or item.get("items") or item.get("data")
        if isinstance(series, dict): series = [{"date": key, "value": value} for key, value in series.items()]
        for point in series if isinstance(series, list) else [item]:
            if isinstance(point, dict):
                stamp = point.get("timestamp")
                day = point.get("date") or point.get("time")
                if not day and isinstance(stamp, (int, float)):
                    day = datetime.fromtimestamp(stamp, UTC).date().isoformat()
                value = point.get("value") if "value" in point else point.get("interest", point.get("values"))
                out.append({"date": day, "interest": value})
    return out


def google_trends(keyword: str, country: str = "FR", time_range: str = "", client: DataForSEOClient | None = None) -> list[dict[str, Any]]:
    """Return Google Trends interest over time."""
    location = _country(country)
    requested = (time_range or f"{date.today().year}-01-01 {date.today().isoformat()}").split()
    payload = {"keywords": [keyword], "date_from": requested[0], "date_to": requested[-1], **location}
    return _trend_rows(_call("keywords_data/google_trends/explore/live", payload, client))


def trends_by_region(keyword: str, country: str = "FR", client: DataForSEOClient | None = None) -> list[dict[str, Any]]:
    """Return keyword interest by subregion."""
    rows = _call("keywords_data/google_trends/subregion_interests/live", {"keywords": [keyword], **_country(country)}, client)
    return [{"region": x.get("region") or x.get("location_name"), "interest": x.get("value") or x.get("interest") or x.get("values")} for x in rows]


def trends_demography(keyword: str, country: str = "FR", client: DataForSEOClient | None = None) -> list[dict[str, Any]]:
    """Return DFS Trends demographic interest segments."""
    rows = _call("keywords_data/dfs_trends/demography/live", {"keywords": [keyword], **_country(country)}, client)
    return [{"segment": x.get("segment") or x.get("age") or x.get("gender"), "value": x.get("value") or x.get("interest") or x.get("values")} for x in rows]


def llm_response_extract(keyword: str, engine: str = "chatgpt", client: DataForSEOClient | None = None) -> str:
    """Return an LLM answer when available; this capability is currently MCP-only."""
    path = "ai_optimization/llm_response/live"
    try:
        rows = _call(path, {"keyword": keyword, "engines": [engine]}, client)
    except ApiError as exc:
        if "404" in str(exc):
            raise ValueError(
                f"REST endpoint '{path}' not exposed (HTTP 404). This capability is available "
                "via the DataForSEO MCP server (tool 'ai_optimization_llm_response')."
            ) from exc
        raise
    x = rows[0] if rows else {}
    value = x.get("response") or x.get("answer") or x.get("text") or x.get("content")
    if isinstance(value, dict): value = value.get("text") or value.get("content")
    return f"{str(value)[:2000] if value else 'N/D'}\n\nSource: DataForSEO {engine}"


def llm_volume(keywords: str, client: DataForSEOClient | None = None) -> list[dict[str, Any]]:
    """Return LLM query volumes when available; this capability is currently MCP-only."""
    clean = [x.strip() for x in keywords.splitlines() if x.strip()]
    path = "ai_optimization/keyword_data/search_volume/live"
    try:
        rows = _call(path, {"keywords": clean}, client)
    except ApiError as exc:
        if "404" in str(exc):
            raise ValueError(
                f"REST endpoint '{path}' not exposed (HTTP 404). This capability is available "
                "via the DataForSEO MCP server (tool 'ai_optimization_keyword_data_search_volume')."
            ) from exc
        raise
    return [{"keyword": x.get("keyword"), "volume": x.get("search_volume") or x.get("volume")}
            for x in rows]


def brand_visibility_ia(brand: str, keyword: str, engines: str = "chatgpt,perplexity,gemini", country: str = "US", client: DataForSEOClient | None = None) -> list[dict[str, Any]]:
    """Measure whether a brand appears among cited domains for each AI engine."""
    rows = []
    for engine in [x.strip() for x in engines.split(",") if x.strip()]:
        mentions = geo.mentions(keyword, [engine], country, client)
        matches = [x for x in mentions if x.domain and brand.casefold() in x.domain.casefold()]
        best = min((x.rank for x in matches if isinstance(x.rank, int)), default=None)
        rows.append({"engine": engine, "mentioned": bool(matches), "domain": matches[0].domain if matches else None,
                     "rank": best, "visibility_score": (1 / best if best else (1 if matches else 0))})
    return rows


SERP = "serp"
register(ToolSpec("brand_mentions", brand_mentions, "Find web pages mentioning a phrase or brand.", SERP, [A("keyword", True), A("limit", False, "10")], "table"))
register(ToolSpec("phrase_trends", phrase_trends, "Show phrase citation trends over time.", SERP, [A("keyword", True)], "table"))
register(ToolSpec("content_summary", content_summary, "Summarize citation metrics for a content keyword.", SERP, [A("keyword", True)], "table"))
register(ToolSpec("amazon_products", amazon_products, "Search Amazon products.", SERP, [A("keyword", True), A("limit", False, "10")], "table"))
register(ToolSpec("amazon_product_keywords", amazon_product_keywords, "List ranking keywords for an Amazon ASIN.", SERP, [A("asin", True), A("limit", False, "20")], "table"))
register(ToolSpec("amazon_competitors", amazon_competitors, "Find competing Amazon products.", SERP, [A("asin", True), A("limit", False, "20")], "table"))
register(ToolSpec("amazon_sellers", amazon_sellers, "List Amazon sellers for an ASIN.", SERP, [A("asin", True), A("limit", False, "20")], "table"))
register(ToolSpec("amazon_asin", amazon_asin, "Show details for an Amazon ASIN.", SERP, [A("asin", True)], "table"))
register(ToolSpec("google_trends", google_trends, "Show Google Trends interest over time.", SERP, [A("keyword", True), A("country", False, "FR"), A("time_range", False, "")], "table"))
register(ToolSpec("trends_by_region", trends_by_region, "Show trends interest by subregion.", SERP, [A("keyword", True), A("country", False, "FR")], "table"))
register(ToolSpec("trends_demography", trends_demography, "Show trends interest by demographic segment.", SERP, [A("keyword", True), A("country", False, "FR")], "table"))
register(ToolSpec("llm_response_extract", llm_response_extract, "Extract a live structured LLM response.", "geo", [A("keyword", True), A("engine", False, "chatgpt")]))
register(ToolSpec("llm_volume", llm_volume, "Show LLM search volumes for keywords.", "geo", [A("keywords", True)], "table"))
register(ToolSpec("brand_visibility_ia", brand_visibility_ia, "Measure brand visibility in AI citations.", "geo", [A("brand", True), A("keyword", True), A("engines", False, "chatgpt,perplexity,gemini"), A("country", False, "US")], "table"))
