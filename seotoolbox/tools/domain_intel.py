"""Domain intelligence mini-tools backed by live DataForSEO endpoints."""

from __future__ import annotations

from typing import Any

from .. import backlinks, keywords
from ..client import DataForSEOClient
from . import ArgSpec as A, ToolSpec, register


def _items(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for result in results:
        nested = result.get("items")
        if isinstance(nested, list):
            output.extend(item for item in nested if isinstance(item, dict))
        else:
            output.append(result)
    return output


def whois_lite(domain: str, client: DataForSEOClient | None = None) -> list[dict[str, Any]]:
    """Return the principal public WHOIS fields for a domain."""
    items = _items((client or DataForSEOClient()).get_result(
        "domain_analytics/whois/overview/live",
        {"filters": [["domain", "=", domain]], "limit": 1}))
    item = next((value for value in items if value.get("domain") == domain), {})
    fields = (("registrar", "registrar"), ("created", "created_datetime"),
              ("expires", "expiration_datetime"), ("updated", "updated_datetime"),
              ("status", "epp_status_codes"))
    return [{"field": label, "value": item.get(key)} for label, key in fields]


def technology_detection(domain: str, client: DataForSEOClient | None = None) -> list[dict[str, Any]]:
    """Return detected technology groups for a domain or URL."""
    rows: list[dict[str, Any]] = []
    for item in _items((client or DataForSEOClient()).get_result(
            "domain_analytics/technologies/domain_technologies/live", {"target": domain})):
        technologies = item.get("technologies")
        if not isinstance(technologies, dict):
            continue
        for group, categories in technologies.items():
            if not isinstance(categories, dict):
                continue
            for category, names in categories.items():
                if not isinstance(names, list):
                    continue
                rows.extend({"group": group, "category": category, "technology": name}
                            for name in names if isinstance(name, str))
    return rows


def domain_compare(domains: str, country: str = "US", client: DataForSEOClient | None = None) -> list[dict[str, Any]]:
    """Compare authority, backlink, and ranking-keyword metrics across domains."""
    targets = [value.strip() for value in domains.splitlines() if value.strip()]
    api = client or DataForSEOClient()
    ranks = backlinks.bulk_ranks(targets, api)
    rank_by_domain = {str(item.get("target") or item.get("domain")): item.get("rank") for item in ranks}
    rows = []
    for domain in targets:
        summary = backlinks.summary(domain, api)
        ranked = keywords.keywords_for_site(domain, country, 1000, api)
        positions = [item.position for item in ranked if isinstance(item.position, (int, float))]
        rows.append({"domain": domain, "rank": rank_by_domain.get(domain, summary.rank),
                     "backlinks": summary.backlinks, "referring_domains": summary.referring_domains,
                     "spam": summary.spam_score, "keyword_count": len(ranked),
                     "best_position": min(positions) if positions else None})
    return rows


def instant_audit(url: str, client: DataForSEOClient | None = None) -> list[dict[str, Any]]:
    """Inspect essential on-page metadata using the instant-pages endpoint."""
    item = next(iter(_items((client or DataForSEOClient()).get_result(
        "on_page/instant_pages", {"url": url}))), {})
    meta = item.get("page_meta") if isinstance(item.get("page_meta"), dict) else item.get("meta")
    if not isinstance(meta, dict):
        meta = {}
    values = {"title": item.get("title") or meta.get("title"),
              "description": item.get("description") or meta.get("description"),
              "canonical": item.get("canonical") or meta.get("canonical"),
              "hreflang": item.get("hreflang") or meta.get("hreflang"),
              "robots": item.get("robots") or meta.get("robots"),
              "open_graph": item.get("og") or meta.get("og") or meta.get("social_media_tags"),
              "status_code": item.get("status_code")}
    return [{"element": key, "value": value, "status": "ok" if value not in (None, "", [], {}) else "absent"}
            for key, value in values.items()]


register(ToolSpec("whois_lite", whois_lite, "Show essential WHOIS data for a domain.", "misc", [A("domain", True)], "table"))
register(ToolSpec("technology_detection", technology_detection, "Detect a site's technology stack.", "misc", [A("domain", True)], "table"))
register(ToolSpec("domain_compare", domain_compare, "Compare domain authority and search KPIs.", "misc", [A("domains", True), A("country", False, "US")], "table"))
register(ToolSpec("instant_audit", instant_audit, "Audit essential metadata for one URL instantly.", "misc", [A("url", True)], "table"))
