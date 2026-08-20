"""Local business listings and Google local-pack ranks."""

from __future__ import annotations

from typing import Any

from .client import DataForSEOClient
from .models import LocalListing, LocalRank
from . import serp

ENDPOINT = "business_data/business_listings/search/live"
COUNTRIES = {"FR": "France", "GB": "United Kingdom", "US": "United States", "DE": "Germany",
             "ES": "Spain", "IT": "Italy", "BE": "Belgium", "CH": "Switzerland", "CA": "Canada"}


def map_country_location(country: str) -> str:
    """Map an ISO country code to a DataForSEO country location name."""
    code = country.upper()
    if code not in COUNTRIES:
        raise ValueError(f"Unsupported country code: {country}")
    return COUNTRIES[code]


def map_city_location(city: str, country: str) -> str:
    """Build the conventional DataForSEO city and country location name."""
    return f"{city.strip().title()}, {map_country_location(country)}"


def listings(query: str, city: str, country: str = "FR", limit: int = 20,
             client: DataForSEOClient | None = None) -> list[LocalListing]:
    # Business Listings is a database search endpoint (not a Google live SERP
    # task): city/country are expressed as documented filters.
    payload = {"title": query, "filters": [["address_info.city", "=", city.strip().title()], "and",
                                             ["address_info.country_code", "=", country.upper()]],
               "limit": limit}
    results = (client or DataForSEOClient()).get_result(ENDPOINT, payload)
    output: list[LocalListing] = []
    for result in results:
        items = result.get("items") if isinstance(result.get("items"), list) else []
        for item in items:
            if not isinstance(item, dict):
                continue
            coords = item.get("coordinates") if isinstance(item.get("coordinates"), dict) else {}
            category = item.get("category")
            if not category and isinstance(item.get("category_ids"), list):
                category = item["category_ids"][0] if item["category_ids"] else None
            output.append(LocalListing(item.get("title"), item.get("address"), item.get("phone"), category,
                                       item.get("rating", {}).get("value") if isinstance(item.get("rating"), dict) else item.get("rating"),
                                       item.get("rating", {}).get("votes_count") if isinstance(item.get("rating"), dict) else item.get("reviews_count"),
                                       item.get("place_id"), coords.get("latitude", item.get("latitude")),
                                       coords.get("longitude", item.get("longitude"))))
            if len(output) >= limit:
                return output
    return output


def local_rank(keyword: str, city: str, country: str = "FR", limit: int = 10,
               client: DataForSEOClient | None = None) -> list[LocalRank]:
    """Return businesses in the locally targeted SERP local pack."""
    output: list[LocalRank] = []
    results = serp._raw(keyword, country, limit, "desktop", client, map_city_location(city, country))
    for result in results:
        for item in result.get("items", []) if isinstance(result.get("items"), list) else []:
            if not isinstance(item, dict) or item.get("type") != "local_pack":
                continue
            pack_items = item.get("items") if isinstance(item.get("items"), list) else [item]
            for business in pack_items:
                if not isinstance(business, dict):
                    continue
                rating = business.get("rating")
                output.append(LocalRank(keyword, city, business.get("rank_absolute", business.get("rank_group")),
                                        business.get("title"), business.get("address"),
                                        rating.get("value") if isinstance(rating, dict) else rating,
                                        rating.get("votes_count") if isinstance(rating, dict) else business.get("reviews_count")))
                if len(output) >= limit:
                    return output
    return output
