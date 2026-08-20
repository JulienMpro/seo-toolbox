"""Live Google SERP analysis backed by DataForSEO."""

from __future__ import annotations

from typing import Any

from .client import DataForSEOClient
from .keywords import _country
from .models import SerpFeatures, SerpResult

ENDPOINTS = {"live": "serp/google/organic/live/advanced", "locations": "serp/locations"}


def _raw(keyword: str, country: str, limit: int, device: str,
         client: DataForSEOClient | None) -> list[dict[str, Any]]:
    payload = {"keyword": keyword, "limit": limit, "device": device, **_country(country)}
    return (client or DataForSEOClient()).get_result(ENDPOINTS["live"], payload)


def live(keyword: str, country: str = "US", limit: int = 20, device: str = "desktop",
         client: DataForSEOClient | None = None) -> list[SerpResult]:
    """Return normalized organic results from a live Google SERP."""
    output = []
    for result in _raw(keyword, country, limit, device, client):
        items = result.get("items") if isinstance(result.get("items"), list) else []
        for item in items:
            if isinstance(item, dict) and item.get("type") == "organic":
                output.append(SerpResult(item.get("rank_absolute", item.get("rank_group")), item.get("url"),
                                         item.get("domain"), item.get("title"), item.get("description"),
                                         item.get("type")))
                if len(output) >= limit:
                    return output
    return output


def features(keyword: str, country: str = "US", client: DataForSEOClient | None = None) -> SerpFeatures:
    """Return sorted, deduplicated non-organic SERP feature types."""
    found: set[str] = set()
    for result in _raw(keyword, country, 100, "desktop", client):
        items = result.get("items") if isinstance(result.get("items"), list) else []
        for item in items:
            if isinstance(item, dict) and item.get("type") and item.get("type") != "organic":
                found.add(str(item["type"]))
        se_results = result.get("se_results")
        if isinstance(se_results, dict):
            found.update(str(key) for key, value in se_results.items() if value and key not in {"organic", "paid"})
        elif isinstance(se_results, list):
            found.update(str(value) for value in se_results if value not in {"organic", "paid"})
    return SerpFeatures(keyword, sorted(found))


def locations(country_code: str, client: DataForSEOClient | None = None) -> list[dict[str, Any]]:
    """Return location codes and names for a country."""
    results = (client or DataForSEOClient()).get_result(ENDPOINTS["locations"], {"country_iso_code": country_code.upper()})
    output = []
    for result in results:
        values = result.get("items") if isinstance(result.get("items"), list) else [result]
        for item in values:
            if isinstance(item, dict):
                output.append({"code": item.get("location_code"), "name": item.get("location_name")})
    return output
