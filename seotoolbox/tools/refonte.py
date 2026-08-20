"""Local migration, ranking comparison, and SERP archival tools."""

from __future__ import annotations

import csv
import html
import io
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from .. import serp
from . import ArgSpec, ToolSpec, register


def _lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def _normalized_path(url: str) -> str:
    path = urlparse(url).path.rstrip("/") or "/"
    stem = path.rsplit("/", 1)[-1]
    if "." in stem:
        path = path[: path.rfind(".")]
    return path.casefold().replace("-", " ").replace("_", " ")


def redirect_map_generator(old: str, new: str = "") -> str:
    """Match old and new URLs and render a migration table plus htaccess rules."""
    old_urls, new_urls, explicit = [], _lines(new), {}
    for line in _lines(old):
        if "|" in line:
            left, right = (part.strip() for part in line.split("|", 1))
            old_urls.append(left)
            if right:
                new_urls.append(right)
                explicit[left] = right
        else:
            old_urls.append(line)
    if not old_urls:
        raise ValueError("old must contain at least one URL")
    exact = {_normalized_path(url): url for url in new_urls}
    rows, rules = [], []
    for source in old_urls:
        key = _normalized_path(source)
        target, status = explicit.get(source) or exact.get(key), "exact"
        if not target and new_urls:
            scores = [(SequenceMatcher(None, key, _normalized_path(candidate)).ratio(), candidate) for candidate in new_urls]
            score, candidate = max(scores)
            if score >= 0.6:
                target, status = candidate, "approximate"
        if not target:
            status = "404 to create"
        rows.append((source, target or "N/D", status))
        if target:
            rules.append(f"Redirect 301 {urlparse(source).path or '/'} {target}")
    table = ["| old | new | match |", "| --- | --- | --- |", *[f"| {a} | {b} | {c} |" for a, b, c in rows]]
    return "\n".join([*table, "", "# Redirect map", *rules])


def sitemap_diff(before: str, after: str) -> list[dict]:
    """Compare two newline-separated sitemap URL sets."""
    a, b = set(_lines(before)), set(_lines(after))
    rows = ([{"status": "new", "url": url} for url in sorted(b - a)] +
            [{"status": "removed", "url": url} for url in sorted(a - b)] +
            [{"status": "unchanged", "url": url} for url in sorted(a & b)])
    rows.append({"status": "TOTAL", "url": f"new={len(b-a)}, removed={len(a-b)}, unchanged={len(a&b)}"})
    return rows


def _positions(value: str) -> dict[str, int]:
    rows = csv.DictReader(io.StringIO(value.strip()))
    if not rows.fieldnames or not {"keyword", "position"} <= {name.strip().lower() for name in rows.fieldnames}:
        raise ValueError("CSV must contain keyword,position headers")
    result = {}
    for row in rows:
        normalized = {str(key).strip().lower(): value for key, value in row.items()}
        try:
            result[str(normalized["keyword"]).strip()] = int(normalized["position"])
        except (TypeError, ValueError):
            raise ValueError("positions must be integers") from None
    return result


def keyword_rank_change(before: str, after: str) -> list[dict]:
    """Compare two keyword-position CSV snapshots (positive delta means improvement)."""
    a, b = _positions(before), _positions(after)
    rows, counts = [], {"gained": 0, "lost": 0, "stable": 0, "new": 0, "gone": 0}
    for keyword in a.keys() | b.keys():
        old, new = a.get(keyword), b.get(keyword)
        delta = old - new if old is not None and new is not None else None
        state = "new" if old is None else "gone" if new is None else "gained" if delta > 0 else "lost" if delta < 0 else "stable"
        counts[state] += 1
        rows.append({"keyword": keyword, "before": old, "after": new, "delta": delta, "status": state})
    rows.sort(key=lambda row: (row["delta"] is None, -(row["delta"] or 0), row["keyword"]))
    rows.append({"keyword": "TOTAL", "before": None, "after": None, "delta": None, "status": ", ".join(f"{k}={v}" for k, v in counts.items())})
    return rows


def serp_snapshot(keyword: str, country: str = "FR", output: str = "data/serp-snapshots/") -> str:
    """Save a dated, standalone HTML snapshot of normalized live SERP results."""
    results = serp.live(keyword, country, 100)
    features = serp.features(keyword, country).features or []
    now = datetime.now(timezone.utc)
    target = Path(output)
    if output.endswith(("/", "\\")) or target.suffix.lower() != ".html":
        slug = "-".join(keyword.casefold().split()) or "serp"
        target = target / f"{now:%Y%m%d-%H%M%S}-{slug}.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    cards = []
    for item in results:
        row = asdict(item) if is_dataclass(item) else item
        cards.append(f"<article><b>{html.escape(str(row.get('rank') or 'N/D'))}. {html.escape(str(row.get('title') or 'N/D'))}</b><br><a href=\"{html.escape(str(row.get('url') or ''))}\">{html.escape(str(row.get('url') or 'N/D'))}</a><p>{html.escape(str(row.get('description') or 'N/D'))}</p></article>")
    language = {"FR": "fr", "DE": "de", "ES": "es", "IT": "it"}.get(country.upper(), "en")
    document = f"<!doctype html><html lang='{language}'><meta charset='utf-8'><title>SERP — {html.escape(keyword)}</title><body><h1>{html.escape(keyword)} ({html.escape(country)})</h1><p>{now.isoformat()}</p><p>Features: {html.escape(', '.join(features) or 'N/D')}</p>{''.join(cards) or '<p>N/D</p>'}</body></html>"
    target.write_text(document, encoding="utf-8")
    return str(target)


def A(name: str, required: bool = True, default: str | None = None) -> ArgSpec:
    return ArgSpec(name, required, default, name.replace("_", " ").capitalize() + ".")


register(ToolSpec("redirect_map_generator", redirect_map_generator, "Build a migration redirect map and htaccess rules.", "generators", [A("old"), A("new", False, "")]))
register(ToolSpec("sitemap_diff", sitemap_diff, "Compare two sitemap URL lists.", "checkers", [A("before"), A("after")], "table"))
register(ToolSpec("keyword_rank_change", keyword_rank_change, "Compare two keyword ranking CSV snapshots.", "analyzers", [A("before"), A("after")], "table"))
register(ToolSpec("serp_snapshot", serp_snapshot, "Archive a live SERP as standalone HTML.", "serp", [A("keyword"), A("country", False, "FR"), A("output", False, "data/serp-snapshots/")]))
