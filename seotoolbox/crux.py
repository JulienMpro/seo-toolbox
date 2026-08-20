"""PageSpeed Insights and Chrome UX field metric helpers."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import httpx

from .models import CruxMetric

PSI_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


def _field_metric(data: dict[str, Any], *names: str) -> dict[str, Any] | None:
    metrics = data.get("loadingExperience", {}).get("metrics", {})
    for name in names:
        value = metrics.get(name)
        if isinstance(value, dict):
            return {"percentile": value.get("percentile"), "category": value.get("category", "").lower() or None}
    return None


def page_speed(url: str, strategy: str = "mobile", api_key: str | None = None) -> CruxMetric:
    """Return Lighthouse score and available PSI field metrics for one URL."""
    if strategy not in {"mobile", "desktop"}:
        raise ValueError("strategy must be mobile or desktop")
    params = {"url": url, "strategy": strategy}
    key = api_key if api_key is not None else os.getenv("PSI_API_KEY")
    if key:
        params["key"] = key
    response = httpx.get(PSI_URL, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    score = data.get("lighthouseResult", {}).get("categories", {}).get("performance", {}).get("score")
    category = data.get("loadingExperience", {}).get("overall_category")
    return CruxMetric(url, category.lower() if isinstance(category, str) else None,
                      _field_metric(data, "LARGEST_CONTENTFUL_PAINT_MS"),
                      _field_metric(data, "CUMULATIVE_LAYOUT_SHIFT_SCORE"),
                      _field_metric(data, "INTERACTION_TO_NEXT_PAINT", "FIRST_INPUT_DELAY_MS"),
                      round(score * 100) if isinstance(score, (int, float)) else None)


def crux_report(urls: list[str], strategy: str = "mobile") -> list[CruxMetric]:
    """Fetch PSI metrics concurrently for at most ten URLs."""
    selected = urls[:10]
    with ThreadPoolExecutor(max_workers=max(1, len(selected))) as executor:
        return list(executor.map(lambda url: page_speed(url, strategy), selected))
