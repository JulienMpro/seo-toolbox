"""Additional local on-page extraction and comparison tools."""

from __future__ import annotations

import re
from collections import Counter
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from . import ArgSpec, ToolSpec, register
from . import analyzers

HEADERS = {"User-Agent": "seotoolbox/0.3"}
STOPWORDS = set("a an and are as at au aux avec ce ces dans de des du en est et for from il in is it la le les of on or par pour que qui sur the this to un une with".split())


def _fetch(url: str) -> tuple[BeautifulSoup | None, str | None]:
    try:
        response = httpx.get(url, timeout=15, follow_redirects=True, headers=HEADERS)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser"), None
    except httpx.HTTPError as exc:
        return None, str(exc)


def canonical_hreflang_check(url: str) -> list[dict]:
    """Check reciprocal membership between a page canonical and its hreflang targets."""
    soup, error = _fetch(url)
    if not soup:
        return [{"element": "fetch", "value": "N/D", "status": f"alert: {error}"}]
    canonical_tag = soup.find("link", rel=lambda value: value and "canonical" in value)
    canonical = urljoin(url, str(canonical_tag.get("href"))) if canonical_tag and canonical_tag.get("href") else None
    hreflangs = [(str(tag.get("hreflang") or "N/D"), urljoin(url, str(tag.get("href"))))
                 for tag in soup.find_all("link", rel=lambda value: value and "alternate" in value)
                 if tag.get("hreflang") and tag.get("href")]
    targets = {target for _, target in hreflangs}
    canonical_ok = bool(canonical and (not targets or canonical in targets))
    rows = [{"element": "canonical", "value": canonical or "N/D", "status": "ok" if canonical_ok else "alert"}]
    rows.extend({"element": f"hreflang {lang}", "value": target,
                 "status": "ok" if canonical and canonical in targets else "alert"} for lang, target in hreflangs)
    if not hreflangs:
        rows.append({"element": "hreflang", "value": "N/D", "status": "alert"})
    return rows


def merge_candidates(urls: str) -> list[dict]:
    """Find page pairs above 80% cosine similarity, fetching at most ten URLs."""
    values = [line.strip() for line in urls.splitlines() if line.strip()]
    if len(values) > 10:
        raise ValueError("merge_candidates accepts at most 10 URLs")
    rows = []
    for row in analyzers.page_similarity("\n".join(values)):
        score = row.get("similarity_pct")
        if score is not None and score > 80:
            pair = row["pair"].split(" ↔ ", 1)
            rows.append({"url_a": pair[0], "url_b": pair[1], "similarity": score, "suggestion": "merge"})
    return rows


def meta_raw_extractor(url: str) -> list[dict]:
    """Extract raw title, meta, social, heading, and visible-word fields from one page."""
    soup, error = _fetch(url)
    if not soup:
        return [{"element": "fetch", "value": f"N/D ({error})"}]
    def meta(**attrs):
        tag = soup.find("meta", attrs=attrs)
        return str(tag.get("content", "")).strip() if tag else None
    canonical = soup.find("link", rel=lambda value: value and "canonical" in value)
    fields = [
        ("title", soup.title.get_text(" ", strip=True) if soup.title else None),
        ("meta description", meta(name=re.compile("^description$", re.I))), ("robots", meta(name=re.compile("^robots$", re.I))),
        ("canonical", urljoin(url, str(canonical.get("href"))) if canonical and canonical.get("href") else None),
        ("og:title", meta(property="og:title")), ("og:description", meta(property="og:description")), ("og:image", meta(property="og:image")),
        ("H1", " | ".join(tag.get_text(" ", strip=True) for tag in soup.find_all("h1")) or None),
        ("H2", " | ".join(tag.get_text(" ", strip=True) for tag in soup.find_all("h2")[:10]) or None),
        ("word count", len(re.findall(r"[^\W_]+", soup.get_text(" ", strip=True), re.UNICODE))),
    ]
    return [{"element": key, "value": value or "N/D"} for key, value in fields]


def keyword_extractor(text: str, limit: int = 20) -> list[dict]:
    """Rank candidate unigrams and bigrams by frequency after basic stopword removal."""
    if limit < 1:
        raise ValueError("limit must be positive")
    tokens = [token.casefold() for token in re.findall(r"[^\W_]+", text, re.UNICODE)]
    clean = [token for token in tokens if token not in STOPWORDS and len(token) > 1]
    unigrams = Counter(clean)
    bigrams = Counter(" ".join(pair) for pair in zip(clean, clean[1:]))
    candidates = ([(key, "unigram", count) for key, count in unigrams.items()] +
                  [(key, "bigram", count) for key, count in bigrams.items() if count > 1])
    candidates.sort(key=lambda item: (-item[2], item[1], item[0]))
    return [{"keyword": key, "type": kind, "frequency": count} for key, kind, count in candidates[:limit]]


def A(name: str, required: bool = True, default: str | None = None) -> ArgSpec:
    return ArgSpec(name, required, default, name.replace("_", " ").capitalize() + ".")


register(ToolSpec("canonical_hreflang_check", canonical_hreflang_check, "Check canonical and hreflang coherence.", "checkers", [A("url")], "table"))
register(ToolSpec("merge_candidates", merge_candidates, "Find near-duplicate merge candidates (maximum 10 URLs).", "analyzers", [A("urls")], "table"))
register(ToolSpec("meta_raw_extractor", meta_raw_extractor, "Extract raw on-page metadata.", "misc", [A("url")], "table"))
register(ToolSpec("keyword_extractor", keyword_extractor, "Extract frequent keyword candidates and bigrams.", "analyzers", [A("text"), A("limit", False, "20")], "table"))
