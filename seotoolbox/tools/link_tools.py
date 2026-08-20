"""Small backlink tools backed by existing DataForSEO services."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from .. import backlinks as backlink_service
from ..client import DataForSEOClient
from . import ArgSpec, ToolSpec, register


def _values(value: str) -> list[str]:
    return [part.strip() for line in value.splitlines() for part in line.split(",") if part.strip()]


def _row(value: Any) -> dict[str, Any]:
    if is_dataclass(value):
        return asdict(value)
    return value if isinstance(value, dict) else {}


def _items(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for result in results:
        nested = result.get("items")
        output.extend(item for item in nested if isinstance(item, dict)) if isinstance(nested, list) else output.append(result)
    return output


def _percent(value: int | float | None, total: int | float) -> float | None:
    return round(value * 100 / total, 2) if value is not None and total else None


def anchor_distribution(domain: str, limit: int = 50) -> list[dict[str, Any]]:
    """Return backlink counts and shares by anchor text."""
    values = [_row(item) for item in backlink_service.anchors(domain, limit)]
    total = sum(row.get("backlinks") or 0 for row in values)
    return [{"anchor": row.get("anchor"), "backlinks": row.get("backlinks"),
             "percent": _percent(row.get("backlinks"), total)} for row in values]


def dofollow_ratio(domain: str) -> list[dict[str, Any]]:
    """Return dofollow and nofollow counts when exposed by the summary model."""
    summary = _row(backlink_service.summary(domain))
    types = summary.get("referring_links_types")
    types = types if isinstance(types, dict) else {}
    dofollow = types.get("dofollow", summary.get("dofollow"))
    nofollow = types.get("nofollow", summary.get("nofollow"))
    total = (dofollow or 0) + (nofollow or 0)
    return [{"type": "dofollow", "count": dofollow, "percent": _percent(dofollow, total)},
            {"type": "nofollow", "count": nofollow, "percent": _percent(nofollow, total)}]


def disavow_generator(domain: str, spam_threshold: float = 60, output: str = "") -> list[dict[str, Any]]:
    """List toxic referring domains and optionally write a disavow file."""
    links = backlink_service.backlinks(domain, 1000)
    domains = sorted({_row(item).get("domain_from") for item in links
                      if _row(item).get("domain_from") and _row(item).get("spam_score") is not None
                      and _row(item)["spam_score"] >= spam_threshold})
    destination = None
    if output:
        destination = str(backlink_service.disavow_file(domain, Path(output), spam_threshold))
    return [{"domain": value, "output": destination} for value in domains]


def toxic_links(domain: str, spam_threshold: float = 60, limit: int = 50) -> list[dict[str, Any]]:
    """List backlinks whose spam score reaches the supplied threshold."""
    rows = []
    for item in backlink_service.backlinks(domain, limit):
        row = _row(item)
        score = row.get("spam_score", row.get("backlink_spam_score", row.get("backlinks_spam_score")))
        if score is not None and score >= spam_threshold:
            rows.append({"url_from": row.get("url_from"), "url_to": row.get("url_to"),
                         "anchor": row.get("anchor"), "spam_score": score})
    return rows


def link_gap(domain: str, competitor: str, limit: int = 50) -> list[dict[str, Any]]:
    """Return referring domains available to a competitor but not the target."""
    return backlink_service.gap(domain, competitor, limit)


def referring_domains_analysis(domain: str, limit: int = 50) -> list[dict[str, Any]]:
    """Return referring-domain link, date, rank, and spam metrics."""
    return [{"domain": row.get("domain"), "links": row.get("referring_links"),
             "first_seen": row.get("first_seen"), "lost_date": row.get("last_seen"),
             "rank": row.get("rank"), "spam": row.get("spam_score")}
            for item in backlink_service.referring_domains(domain, limit) if (row := _row(item))]


def new_lost_links(domain: str, days: int = 30) -> list[dict[str, Any]]:
    """Return daily new and lost backlink and referring-domain totals."""
    return [{"date": row.get("date"), "new_backlinks": row.get("new_backlinks"),
             "lost_backlinks": row.get("lost_backlinks"), "new_rd": row.get("new_referring_domains"),
             "lost_rd": row.get("lost_referring_domains")}
            for item in backlink_service.new_lost(domain, days) if (row := _row(item))]


def link_profile_evolution(domain: str, days: int = 90) -> list[dict[str, Any]]:
    """Return live backlink and referring-domain totals over time."""
    if days <= 0:
        raise ValueError("days must be positive")
    today = date.today()
    payload = {"target": domain, "date_from": (today - timedelta(days=days)).isoformat(),
               "date_to": today.isoformat()}
    # Prefer the absolute timeseries endpoint; cumulative new/lost values have no
    # trustworthy starting baseline and would manufacture totals.
    results = DataForSEOClient().get_result("backlinks/timeseries_summary/live", payload)
    rows = []
    for item in _items(results):
        rows.append({"date": item.get("date"), "total_backlinks": item.get("backlinks"),
                     "total_referring_domains": item.get("referring_domains")})
    return rows


def link_profile_compare(domains: str) -> list[dict[str, Any]]:
    """Compare backlink profile totals for at least two domains."""
    values = _values(domains)
    if len(values) < 2:
        raise ValueError("domains must contain at least two values")
    rows = []
    for domain in values:
        summary = _row(backlink_service.summary(domain))
        rows.append({"domain": domain, "backlinks": summary.get("backlinks"),
                     "referring_domains": summary.get("referring_domains"), "rank": summary.get("rank"),
                     "spam": summary.get("spam_score")})
    return rows


def most_linked_pages(domain: str, limit: int = 50) -> list[dict[str, Any]]:
    """Return the target's most-linked pages."""
    payload = {"target": domain, "limit": limit}
    results = DataForSEOClient().get_result("backlinks/domain_pages_summary/live", payload)
    rows = []
    for item in _items(results)[:limit]:
        page = item.get("page") or item.get("url") or item.get("target")
        rows.append({"page": page, "backlinks": item.get("backlinks"),
                     "referring_domains": item.get("referring_domains")})
    return rows


def pbn_detection(domain: str, limit: int = 50) -> list[dict[str, Any]]:
    """Expose shared referring networks or IPs as possible PBN signals."""
    rows = []
    for item in backlink_service.networks(domain, limit):
        row = _row(item)
        network = row.get("network_address") or row.get("network") or row.get("ip") or row.get("subnet")
        rows.append({"network_address": network, "referring_domains": row.get("referring_domains"),
                     "backlinks": row.get("backlinks")})
    return rows


def authority_score(domains: str) -> list[dict[str, Any]]:
    """Return DataForSEO rank scores for several domains."""
    requested = _values(domains)
    found = {}
    for item in backlink_service.bulk_ranks(requested):
        row = _row(item)
        key = row.get("target") or row.get("domain")
        if key:
            found[str(key).casefold()] = row.get("rank")
    return [{"domain": domain, "rank": found.get(domain.casefold())} for domain in requested]


def A(name: str, required: bool = True, default: str | None = None) -> ArgSpec:
    return ArgSpec(name, required, default, name.replace("_", " ").capitalize() + ".")


register(ToolSpec("anchor_distribution", anchor_distribution, "Show anchor text distribution.", "links", [A("domain"), A("limit", False, "50")], "table"))
register(ToolSpec("dofollow_ratio", dofollow_ratio, "Show dofollow and nofollow shares.", "links", [A("domain")], "table"))
register(ToolSpec("disavow_generator", disavow_generator, "List toxic domains and optionally write a disavow file.", "links", [A("domain"), A("spam_threshold", False, "60"), A("output", False, "")], "table"))
register(ToolSpec("toxic_links", toxic_links, "List backlinks above a spam threshold.", "links", [A("domain"), A("spam_threshold", False, "60"), A("limit", False, "50")], "table"))
register(ToolSpec("link_gap", link_gap, "Find competitor referring domains missing from a target.", "links", [A("domain"), A("competitor"), A("limit", False, "50")], "table"))
register(ToolSpec("referring_domains_analysis", referring_domains_analysis, "Analyze referring-domain quality metrics.", "links", [A("domain"), A("limit", False, "50")], "table"))
register(ToolSpec("new_lost_links", new_lost_links, "Show daily gained and lost links.", "links", [A("domain"), A("days", False, "30")], "table"))
register(ToolSpec("link_profile_evolution", link_profile_evolution, "Show backlink profile totals over time.", "links", [A("domain"), A("days", False, "90")], "table"))
register(ToolSpec("link_profile_compare", link_profile_compare, "Compare backlink profiles across domains.", "links", [A("domains")], "table"))
register(ToolSpec("most_linked_pages", most_linked_pages, "List a domain's most-linked pages.", "links", [A("domain"), A("limit", False, "50")], "table"))
register(ToolSpec("pbn_detection", pbn_detection, "Find shared referring networks and IPs.", "links", [A("domain"), A("limit", False, "50")], "table"))
register(ToolSpec("authority_score", authority_score, "Return authority rank scores for domains.", "links", [A("domains")], "table"))
