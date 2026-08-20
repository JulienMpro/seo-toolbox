"""Google Analytics 4 Data API connector."""

from __future__ import annotations

from datetime import date, timedelta

import httpx

from .google_auth import get_access_token
from .models import Ga4Row

REPORT_URL = "https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport"


def run_report(property_id: str, start_date: str, end_date: str,
               dimensions: list[str], metrics: list[str], row_limit: int,
               access_token: str) -> list[Ga4Row]:
    """Run a GA4 report and normalize dimension and numeric metric values."""
    if not property_id:
        raise ValueError("GA4 property ID missing")
    response = httpx.post(
        REPORT_URL.format(property_id=property_id),
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "dateRanges": [{"startDate": start_date, "endDate": end_date}],
            "dimensions": [{"name": name} for name in dimensions],
            "metrics": [{"name": name} for name in metrics],
            "limit": row_limit,
        },
        timeout=30,
    )
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        try:
            message = response.json().get("error", {}).get("message", response.text)
        except ValueError:
            message = response.text
        if response.status_code == 401:
            raise ValueError(
                f"GA4 authentication failed (invalid or expired access token): {message}"
            ) from exc
        raise ValueError(f"GA4 API request failed ({response.status_code}): {message}") from exc
    return [
        Ga4Row(
            dimensions=[value.get("value", "") for value in row.get("dimensionValues", [])],
            metrics=[float(value.get("value", 0)) for value in row.get("metricValues", [])],
        )
        for row in response.json().get("rows", [])
    ]


def _dates(days: int) -> tuple[str, str]:
    end = date.today()
    return (end - timedelta(days=days)).isoformat(), end.isoformat()


def daily_traffic(property_id: str, days: int = 28) -> list[Ga4Row]:
    """Return sessions, users, and engaged sessions by day."""
    start, end = _dates(days)
    return run_report(property_id, start, end, ["date"],
                      ["sessions", "totalUsers", "engagedSessions"], 10000,
                      get_access_token())


def traffic_by_source(property_id: str, days: int = 28, limit: int = 10) -> list[Ga4Row]:
    """Return traffic grouped by default session channel."""
    start, end = _dates(days)
    return run_report(property_id, start, end, ["sessionDefaultChannelGroup"],
                      ["sessions", "totalUsers"], limit, get_access_token())


def top_pages(property_id: str, days: int = 28, limit: int = 10) -> list[Ga4Row]:
    """Return the most visited page paths."""
    start, end = _dates(days)
    return run_report(property_id, start, end, ["pagePath"],
                      ["sessions", "totalUsers", "engagementRate"], limit,
                      get_access_token())
