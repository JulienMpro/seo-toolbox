"""Google Search Console OAuth and Search Analytics connector."""

from __future__ import annotations

from datetime import date, timedelta
from urllib.parse import quote

import httpx

from .google_auth import get_access_token
from .models import GscRow


def list_properties(access_token: str) -> list[str]:
    """List Search Console property URLs available to the token."""
    response = httpx.get("https://www.googleapis.com/webmasters/v3/sites",
                         headers={"Authorization": f"Bearer {access_token}"}, timeout=20)
    response.raise_for_status()
    return [item["siteUrl"] for item in response.json().get("siteEntry", []) if item.get("siteUrl")]


def search_analytics(property: str, start_date: str, end_date: str, dimensions: list[str],
                     row_limit: int, access_token: str) -> list[GscRow]:
    """Query Search Analytics; public v3 provides no equivalent Coverage endpoint."""
    endpoint = f"https://www.googleapis.com/webmasters/v3/sites/{quote(property, safe='')}/searchAnalytics/query"
    response = httpx.post(endpoint, headers={"Authorization": f"Bearer {access_token}"}, json={
        "startDate": start_date, "endDate": end_date, "dimensions": dimensions, "rowLimit": row_limit}, timeout=30)
    response.raise_for_status()
    return [GscRow(list(row.get("keys", [])), row.get("clicks"), row.get("impressions"),
                   row.get("ctr"), row.get("position")) for row in response.json().get("rows", [])]


def _dates(days: int) -> tuple[str, str]:
    end = date.today()
    return (end - timedelta(days=days)).isoformat(), end.isoformat()


def top_queries(property: str, days: int = 28, limit: int = 20) -> list[GscRow]:
    """Return the top query rows for a property."""
    start, end = _dates(days)
    return search_analytics(property, start, end, ["query"], limit, get_access_token())


def top_pages(property: str, days: int = 28, limit: int = 20) -> list[GscRow]:
    """Return the top page rows for a property."""
    start, end = _dates(days)
    return search_analytics(property, start, end, ["page"], limit, get_access_token())


def query_performance(property: str, query: str, days: int = 28) -> list[GscRow]:
    """Return rows for one query when filtering the API response locally."""
    start, end = _dates(days)
    rows = search_analytics(property, start, end, ["query"], 25000, get_access_token())
    return [row for row in rows if row.keys and row.keys[0] == query]
