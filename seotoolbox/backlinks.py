"""Backlink analysis and disavow operations backed by DataForSEO."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Any

from .client import DataForSEOClient
from .models import Anchor, Backlink, BacklinkCompetitor, BacklinkSummary, NewLost, ReferringDomain

ENDPOINTS = {
    "summary": "backlinks/summary/live", "backlinks": "backlinks/backlinks/live",
    "referring_domains": "backlinks/referring_domains/live", "anchors": "backlinks/anchors/live",
    "networks": "backlinks/referring_networks/live",
    "new_lost": "backlinks/timeseries_new_lost_summary/live",
    "competitors": "backlinks/competitors/live",
    "bulk_ranks": "backlinks/bulk_ranks/live",
}


def _items(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for result in results:
        nested = result.get("items")
        if isinstance(nested, list):
            output.extend(item for item in nested if isinstance(item, dict))
        else:
            output.append(result)
    return output


def _first(item: dict[str, Any], *keys: str) -> Any:
    """Return the first present API field, including false and zero values."""
    for key in keys:
        if key in item:
            return item[key]
    return None


def summary(target: str, client: DataForSEOClient | None = None) -> BacklinkSummary:
    """Return aggregate live backlink metrics."""
    items = _items((client or DataForSEOClient()).get_result(ENDPOINTS["summary"], {"target": target}))
    item = items[0] if items else {}
    return BacklinkSummary(
        backlinks=item.get("backlinks"),
        referring_domains=item.get("referring_domains"),
        rank=item.get("rank"),
        spam_score=item.get("backlinks_spam_score"),
        broken_backlinks=item.get("broken_backlinks"),
        crawled_pages=item.get("crawled_pages"),
        first_seen=item.get("first_seen"),
        lost_date=item.get("lost_date"),
        external_links_count=item.get("external_links_count"),
        internal_links_count=item.get("internal_links_count"),
        referring_pages=item.get("referring_pages"),
        referring_links_types=item.get("referring_links_types") if isinstance(item.get("referring_links_types"), dict) else None,
        referring_pages_nofollow=item.get("referring_pages_nofollow"),
    )


def backlinks(target: str, limit: int = 30, client: DataForSEOClient | None = None) -> list[Backlink]:
    """List live backlinks for a target."""
    payload = {"target": target, "limit": limit}
    return [Backlink(item.get("url_from"), item.get("url_to"), item.get("anchor"), item.get("domain_from"),
                     item.get("first_seen"), item.get("last_seen"), item.get("is_new"), item.get("is_lost"),
                     _first(item, "backlink_spam_score", "backlinks_spam_score", "spam_score"))
            for item in _items((client or DataForSEOClient()).get_result(ENDPOINTS["backlinks"], payload))[:limit]]


def referring_domains(target: str, limit: int = 20, client: DataForSEOClient | None = None) -> list[ReferringDomain]:
    """List referring domains and their quality metrics."""
    payload = {"target": target, "limit": limit}
    output = []
    for item in _items((client or DataForSEOClient()).get_result(ENDPOINTS["referring_domains"], payload))[:limit]:
        domain = item.get("domain") or item.get("domain_from")
        if domain:
            output.append(ReferringDomain(
                str(domain),
                _first(item, "referring_links", "backlinks"),
                item.get("external_links"),
                item.get("first_seen"),
                _first(item, "last_seen", "lost_date"),
                item.get("rank"),
                _first(item, "backlinks_spam_score", "spam_score"),
            ))
    return output


def anchors(target: str, limit: int = 20, client: DataForSEOClient | None = None) -> list[Anchor]:
    """Return anchor text distribution."""
    payload = {"target": target, "limit": limit}
    return [Anchor(str(item.get("anchor")), item.get("referring_domains"), item.get("backlinks"),
                   item.get("external_links"))
            for item in _items((client or DataForSEOClient()).get_result(ENDPOINTS["anchors"], payload))[:limit]
            if item.get("anchor") is not None]


def networks(target: str, limit: int = 20, client: DataForSEOClient | None = None) -> list[dict[str, Any]]:
    """Return referring network aggregates as supplied by the API."""
    return _items((client or DataForSEOClient()).get_result(
        ENDPOINTS["networks"], {"target": target, "limit": limit}))[:limit]


def new_lost(target: str, days: int = 30, client: DataForSEOClient | None = None) -> list[NewLost]:
    """Return daily new and lost link totals for the requested trailing period."""
    date_to = date.today()
    payload = {"target": target, "date_from": (date_to - timedelta(days=days)).isoformat(),
               "date_to": date_to.isoformat(), "group_range": "day"}
    output = []
    for item in _items((client or DataForSEOClient()).get_result(ENDPOINTS["new_lost"], payload)):
        day = item.get("date")
        if day:
            output.append(NewLost(str(day), item.get("new_backlinks"), item.get("lost_backlinks"),
                                  item.get("new_referring_domains"), item.get("lost_referring_domains")))
    return output


def gap(target: str, competitor: str, limit: int = 20,
        client: DataForSEOClient | None = None) -> list[dict[str, Any]]:
    """Return competitor referring domains which do not link to the target."""
    api = client or DataForSEOClient()
    target_items = _items(api.get_result(
        ENDPOINTS["referring_domains"], {"target": target, "limit": limit}))
    competitor_items = _items(api.get_result(
        ENDPOINTS["referring_domains"], {"target": competitor, "limit": limit}))
    target_domains = {
        str(item["domain_from"]).casefold()
        for item in target_items if isinstance(item.get("domain_from"), str)
    }
    rows = [
        {"domain": item["domain_from"],
         "links_to_competitor": item.get("referring_links"),
         "rank": item.get("rank")}
        for item in competitor_items
        if isinstance(item.get("domain_from"), str)
        and item["domain_from"].casefold() not in target_domains
    ]
    rows.sort(key=lambda row: (
        row["links_to_competitor"] if isinstance(row["links_to_competitor"], (int, float)) else -1,
        row["rank"] if isinstance(row["rank"], (int, float)) else -1,
    ), reverse=True)
    return rows[:limit]


def competitors(target: str, limit: int = 10, client: DataForSEOClient | None = None) -> list[BacklinkCompetitor]:
    """Return backlink competitors for a target."""
    output = []
    for item in _items((client or DataForSEOClient()).get_result(
            ENDPOINTS["competitors"], {"target": target, "limit": limit}))[:limit]:
        domain = item.get("domain") or item.get("target")
        if domain:
            output.append(BacklinkCompetitor(str(domain), item.get("backlinks"),
                                              item.get("referring_domains"), item.get("rank")))
    return output


def bulk_ranks(targets: list[str], client: DataForSEOClient | None = None) -> list[dict[str, Any]]:
    """Return rank scores for several targets."""
    return _items((client or DataForSEOClient()).get_result(ENDPOINTS["bulk_ranks"], {"targets": targets}))


def disavow_file(target: str, path: str | Path, max_spam: float = 60,
                 client: DataForSEOClient | None = None) -> Path:
    """Write unique toxic referring domains in Google Disavow format."""
    candidates = backlinks(target, 1000, client)
    domains = sorted({item.domain_from for item in candidates
                      if item.domain_from and item.spam_score is not None and item.spam_score >= max_spam})
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("".join(f"domain:{domain}\n" for domain in domains), encoding="utf-8")
    return destination
