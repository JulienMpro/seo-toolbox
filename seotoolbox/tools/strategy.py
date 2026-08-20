"""Planning and strategy mini-tools using local rules and existing services."""

from __future__ import annotations

import csv
import io
import math
from collections import Counter
from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from .. import backlinks, keywords as keyword_service
from ..client import ApiError, DataForSEOError
from . import ArgSpec, ToolSpec, register


def _lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def _md(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "N/D"
    headers = list(rows[0])
    show = lambda value: "N/D" if value is None or value == "" else str(value).replace("|", "\\|")
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |", *["| " + " | ".join(show(row.get(key)) for key in headers) + " |" for row in rows]])


def editorial_calendar(keywords: str, frequency: int = 4, start_date: str = "") -> str:
    """Schedule prioritized content at an even monthly cadence."""
    if frequency < 1:
        raise ValueError("frequency must be positive")
    start = date.fromisoformat(start_date) if start_date else date.today()
    parsed = []
    for line in _lines(keywords):
        parts = [part.strip() for part in line.split("|")]
        parsed.append((parts + ["N/D", "N/D"])[0:3])
    parsed.sort(key=lambda item: ({"P1": 1, "P2": 2, "P3": 3}.get(item[1].upper(), 9), item[0].casefold()))
    rows = [{"date": (start + timedelta(days=round(index * 30.4375 / frequency))).isoformat(), "keyword": word, "priority": priority, "type": kind} for index, (word, priority, kind) in enumerate(parsed)]
    priorities, types = Counter(row["priority"] for row in rows), Counter(row["type"] for row in rows)
    stats = ", ".join(f"{key}: {value}" for key, value in sorted(priorities.items())) + "; " + ", ".join(f"{key}: {value}" for key, value in sorted(types.items()))
    return _md(rows) + f"\n\nDistribution — {stats or 'N/D'}"


def seo_projection(current_traffic: float, growth: float = 5, months: int = 12, value_per_visit: float = 0) -> list[dict[str, Any]]:
    """Project compounding monthly traffic and its estimated visit value."""
    if current_traffic < 0 or months < 1 or value_per_visit < 0 or growth <= -100:
        raise ValueError("traffic/value must be non-negative, months positive, and growth greater than -100")
    rows, cumulative = [], 0.0
    for month in range(1, months + 1):
        traffic = current_traffic * (1 + growth / 100) ** month
        revenue = traffic * value_per_visit
        cumulative += revenue
        rows.append({"month": month, "traffic": round(traffic), "estimated_revenue_eur": round(revenue, 2), "cumulative_eur": round(cumulative, 2)})
    return rows


def _safe(call, default):
    try:
        return call()
    except (ApiError, DataForSEOError, OSError):
        return default


def keyword_prioritization(keywords: str, country: str = "FR") -> list[dict[str, Any]]:
    """Score keywords from available metrics, without fabricating missing data."""
    words = _lines(keywords)
    overview = _safe(lambda: keyword_service.overview(words, country), [])
    intents = _safe(lambda: keyword_service.intent(words), [])
    metrics = {item.keyword.casefold(): item for item in overview}
    intent_map = {item.keyword.casefold(): item.intent for item in intents}
    volumes = [item.volume for item in overview if item.volume is not None]
    cpcs = [item.cpc for item in overview if item.cpc is not None]
    max_volume, max_cpc = max(volumes, default=0), max(cpcs, default=0)
    intent_weight = {"transactional": 100, "commercial": 80, "navigational": 50, "informational": 40}
    rows = []
    for word in words:
        item, intent = metrics.get(word.casefold()), intent_map.get(word.casefold())
        volume, kd, cpc = (item.volume, item.difficulty, item.cpc) if item else (None, None, None)
        if volume is None and kd is None and cpc is None:
            score = None
        else:
            components = []
            if volume is not None:
                components.append((.35, math.log1p(volume) / math.log1p(max_volume) * 100 if max_volume else 0))
            if kd is not None:
                components.append((.25, 100 - kd))
            if cpc is not None:
                components.append((.15, cpc / max_cpc * 100 if max_cpc else 0))
            if intent is not None:
                components.append((.25, intent_weight.get(intent.casefold(), 30)))
            # Rebalance the documented weights over available components. In
            # particular, a missing intent uses 35/75, 25/75, and 15/75 for
            # volume, difficulty, and CPC respectively.
            total_weight = sum(weight for weight, _ in components)
            score = round(sum(weight * value for weight, value in components) / total_weight)
        verdict = None if score is None else ("high" if score >= 70 else "medium" if score >= 40 else "low")
        rows.append({"keyword": word, "volume": volume, "KD": kd, "CPC": cpc, "intent": intent or "N/D", "score": score, "verdict": verdict})
    return rows


def difficulty_score(keywords: str, country: str = "FR") -> list[dict[str, Any]]:
    """Return provider keyword difficulty and a readable level."""
    words = _lines(keywords)
    found = {item.keyword.casefold(): item.difficulty for item in _safe(lambda: keyword_service.overview(words, country), [])}
    return [{"keyword": word, "KD": (kd := found.get(word.casefold())), "level": None if kd is None else "easy" if kd < 30 else "medium" if kd < 60 else "difficult"} for word in words]


def topic_clusters(keywords: str, country: str = "FR") -> list[dict[str, Any]]:
    """Enrich seeds with related terms, cluster by bigram similarity, and select volume leaders."""
    seeds, expanded = _lines(keywords), []
    for seed in seeds:
        expanded.append(seed)
        expanded.extend(item.keyword for item in _safe(lambda seed=seed: keyword_service.related(seed, country, 5), []))
    expanded = list(dict.fromkeys(expanded))
    volumes = {item.keyword.casefold(): item.volume for item in _safe(lambda: keyword_service.overview(expanded, country), [])}
    rows = []
    for index, group in enumerate(keyword_service.cluster(expanded), 1):
        pillar = max(group, key=lambda word: volumes.get(word.casefold()) or -1)
        rows.append({"cluster": index, "keywords": ", ".join(group), "suggested_pillar": pillar})
    return rows


def semantic_silo(keywords: str, country: str = "FR") -> str:
    """Build a deterministic pillar/subpage tree using specificity and volume."""
    words = _lines(keywords)
    if not words:
        return "N/D"
    volumes = {item.keyword.casefold(): item.volume for item in _safe(lambda: keyword_service.overview(words, country), [])}
    pillar = min(words, key=lambda word: (len(word.split()), -(volumes.get(word.casefold()) or 0)))
    rows = [{"page": pillar, "type": "pillar", "links_to": ", ".join(word for word in words if word != pillar) or None}]
    rows += [{"page": word, "type": "subpage", "links_to": pillar} for word in words if word != pillar]
    tree = pillar + "\n" + "\n".join(f"  └─ {word}" for word in words if word != pillar)
    return tree + "\n\n" + _md(rows)


def traffic_potential(domain: str, keywords: str, country: str = "FR") -> str:
    """Estimate potential visits using a conservative 5% CTR (positions 3–10 model)."""
    words = _lines(keywords)
    found = {item.keyword.casefold(): item.volume for item in _safe(lambda: keyword_service.overview(words, country), [])}
    rows, total = [], 0.0
    for word in words:
        volume = found.get(word.casefold())
        traffic = round(volume * .05, 1) if volume is not None else None
        total += traffic or 0
        rows.append({"keyword": word, "volume": volume, "estimated_traffic": traffic})
    return _md(rows) + f"\n\nTotal potential for {domain}: {round(total, 1)} visits/month (5% CTR)."


def intent_mix(keywords: str) -> str:
    """Summarize provider search-intent classifications."""
    words = _lines(keywords)
    values = _safe(lambda: keyword_service.intent(words), [])
    counts = Counter(item.intent or "N/D" for item in values)
    if len(values) < len(words): counts["N/D"] += len(words) - len(values)
    rows = [{"intent": key, "count": count, "percent": round(count / len(words) * 100, 1) if words else 0} for key, count in sorted(counts.items())]
    dominant = max(counts, key=counts.get) if counts else "N/D"
    return _md(rows) + f"\n\nVerdict: dominant intent is {dominant}."


def effort_impact(actions: str) -> str:
    """Place actions in a conventional effort-impact matrix."""
    rows = []
    for line in _lines(actions):
        parts = [part.strip() for part in line.split("|")]
        if len(parts) != 3: raise ValueError("each action must use action|effort|impact")
        effort, impact = int(parts[1]), int(parts[2])
        if effort not in range(1, 6) or impact not in range(1, 6): raise ValueError("effort and impact must be between 1 and 5")
        quadrant = "quick win" if impact >= 4 and effort <= 2 else "major project" if impact >= 4 else "fill-in" if effort <= 2 else "deprioritize"
        rows.append({"action": parts[0], "effort": effort, "impact": impact, "quadrant": quadrant})
    wins = [row["action"] for row in rows if row["quadrant"] == "quick win"]
    return _md(rows) + "\n\nQuick wins: " + (", ".join(wins) or "N/D")


def content_audit(data: str) -> list[dict[str, Any]]:
    """Audit GSC rows: keep top-10 traffic, improve impressions, merge weak pages, remove zero-demand pages."""
    path = Path(data)
    source = path.read_text(encoding="utf-8-sig") if "\n" not in data and path.is_file() else data
    if "|" in source and "," not in source.splitlines()[0]:
        parsed = [dict(zip(("url", "clicks", "impressions", "position"), line.split("|"))) for line in _lines(source)]
    else:
        parsed = list(csv.DictReader(io.StringIO(source)))
    rows = []
    for item in parsed:
        url = item.get("url") or item.get("page")
        try: clicks, impressions, position = float(item.get("clicks", 0)), float(item.get("impressions", 0)), float(item.get("position", 0))
        except (TypeError, ValueError):
            rows.append({"url": url, "clicks": None, "impressions": None, "position": None, "verdict": None, "action": None}); continue
        if clicks > 0 and 0 < position <= 10: verdict, action = "keep", "maintain and refresh"
        elif impressions >= 100 and (position > 10 or clicks == 0): verdict, action = "improve", "optimize title, content, and links"
        elif impressions > 0: verdict, action = "merge", "consolidate with a stronger related page"
        else: verdict, action = "remove", "remove or noindex after business review"
        rows.append({"url": url, "clicks": clicks, "impressions": impressions, "position": position, "verdict": verdict, "action": action})
    return rows


def competitor_benchmark(domains: str, country: str = "FR") -> list[dict[str, Any]]:
    """Compare ranked-keyword and backlink KPIs, returning N/D fields on provider failure."""
    rows = []
    for domain in _lines(domains):
        ranked = _safe(lambda domain=domain: keyword_service.keywords_for_site(domain, country, 1000), [])
        summary = _safe(lambda domain=domain: backlinks.summary(domain), None)
        positions = [item.position for item in ranked if item.position is not None]
        rows.append({"domain": domain, "ranked_keywords": len(ranked) if ranked else None, "average_position": round(sum(positions) / len(positions), 1) if positions else None, "backlinks": summary.backlinks if summary else None, "referring_domains": summary.referring_domains if summary else None, "rank": summary.rank if summary else None})
    return rows


A = lambda name, required=True, default=None, help="": ArgSpec(name, required, default, help)
register(ToolSpec("editorial_calendar", editorial_calendar, "Schedule a prioritized editorial calendar.", "strategy", [A("keywords"), A("frequency", False, "4"), A("start_date", False, "")]))
register(ToolSpec("seo_projection", seo_projection, "Project compounding SEO traffic and value.", "strategy", [A("current_traffic"), A("growth", False, "5"), A("months", False, "12"), A("value_per_visit", False, "0")], "table"))
register(ToolSpec("keyword_prioritization", keyword_prioritization, "Prioritize keywords from live SEO metrics.", "strategy", [A("keywords"), A("country", False, "FR")], "table"))
register(ToolSpec("difficulty_score", difficulty_score, "Retrieve keyword difficulty levels.", "strategy", [A("keywords"), A("country", False, "FR")], "table"))
register(ToolSpec("topic_clusters", topic_clusters, "Build enriched thematic keyword clusters.", "strategy", [A("keywords"), A("country", False, "FR")], "table"))
register(ToolSpec("semantic_silo", semantic_silo, "Build a pillar and subpage semantic silo.", "strategy", [A("keywords"), A("country", False, "FR")]))
register(ToolSpec("traffic_potential", traffic_potential, "Estimate keyword traffic potential at a documented CTR.", "strategy", [A("domain"), A("keywords"), A("country", False, "FR")]))
register(ToolSpec("intent_mix", intent_mix, "Summarize the search-intent mix.", "strategy", [A("keywords")]))
register(ToolSpec("effort_impact", effort_impact, "Classify actions in an effort-impact matrix.", "strategy", [A("actions")]))
register(ToolSpec("content_audit", content_audit, "Classify GSC pages for content action.", "strategy", [A("data")], "table"))
register(ToolSpec("competitor_benchmark", competitor_benchmark, "Benchmark domain SEO and backlink KPIs.", "strategy", [A("domains"), A("country", False, "FR")], "table"))
