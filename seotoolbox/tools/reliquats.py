"""Remaining catalogue tools backed by SERP, keyword, rank, and PSI services."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import asdict, is_dataclass
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from .. import crux, keywords, serp
from ..client import ApiError, DataForSEOError
from . import ArgSpec, ToolSpec, register
from .serp_tools import paa_extractor

_WORD = re.compile(r"[^\W_]+(?:[-'][^\W_]+)*", re.UNICODE)
_STOP = {"a", "au", "aux", "avec", "ce", "ces", "dans", "de", "des", "du", "en", "et", "est", "la", "le", "les", "ou", "par", "pour", "que", "qui", "sur", "un", "une", "the", "and", "for", "from", "that", "this", "with"}


def _lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def _row(value: Any) -> dict[str, Any]:
    return asdict(value) if is_dataclass(value) else value if isinstance(value, dict) else {}


def _fetch(url: str) -> tuple[BeautifulSoup | None, str | None]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None, "invalid URL"
    try:
        response = httpx.get(url, timeout=15, follow_redirects=True, headers={"User-Agent": "seotoolbox/0.5"})
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser"), None
    except httpx.HTTPError as exc:
        return None, str(exc)


def _visible(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "noscript", "svg"]): tag.decompose()
    return soup.get_text(" ", strip=True)


def _length_rows(keyword: str, country: str) -> list[dict[str, Any]]:
    """Fetch top-ten pages locally; failures remain N/D and never affect the mean."""
    rows = []
    try: results = serp.live(keyword, country, 10)
    except (ApiError, DataForSEOError): results = []
    for result in results:
        item = _row(result); soup, _error = _fetch(item.get("url") or "")
        rows.append({"rank": item.get("rank"), "url": item.get("url"), "words": len(_WORD.findall(_visible(soup))) if soup else None})
    return rows


def content_length_target(keyword: str, country: str = "FR") -> list[dict[str, Any]]:
    """Recommend the mean word count of fetchable top-ten organic pages (light local HTML parsing)."""
    rows = _length_rows(keyword, country)
    values = [row["words"] for row in rows if row["words"] is not None]
    rows.append({"rank": "TARGET", "url": None, "words": round(sum(values) / len(values)) if values else None})
    return rows


def keyword_expansion(seed: str, country: str = "FR", limit: int = 30) -> list[dict[str, Any]]:
    """Merge long-tail keyword ideas and suggestions without inventing metrics."""
    if limit < 1: raise ValueError("limit must be positive")
    found: dict[str, dict[str, Any]] = {}
    for source, operation in (("ideas", keywords.ideas), ("suggestions", keywords.suggestions)):
        items = operation(seed, country, limit)
        for item in items:
            row = _row(item); word = row.get("keyword")
            if word and word.casefold() not in found:
                found[word.casefold()] = {"keyword": word, "volume": row.get("volume"), "source": source}
    return list(found.values())[:limit]


def faq_generator(keyword: str, country: str = "FR") -> list[dict[str, Any]]:
    """Return deduplicated live People Also Ask questions only."""
    live = paa_extractor(keyword, country)
    rows, seen = [], set()
    for item in live:
        question = item.get("question")
        if question and question.casefold() not in seen:
            seen.add(question.casefold()); rows.append({"question": question, "source": "PAA"})
    return rows


def content_brief(keyword: str, country: str = "FR") -> str:
    """Build a factual brief from live titles, PAA, headings, page lengths, and frequent terms."""
    results = serp.live(keyword, country, 10)
    questions = [row["question"] for row in faq_generator(keyword, country)]
    headings, terms, lengths = [], Counter(), []
    for result in results[:5]:
        item = _row(result); soup, _error = _fetch(item.get("url") or "")
        if not soup: continue
        headings.extend(tag.get_text(" ", strip=True) for tag in soup.find_all(["h2", "h3"]))
        text = _visible(soup); lengths.append(len(_WORD.findall(text)))
        terms.update(word.casefold() for word in _WORD.findall(text) if len(word) > 3 and word.casefold() not in _STOP)
    titles = [(_row(item).get("title")) for item in results if _row(item).get("title")]
    target = round(sum(lengths) / len(lengths)) if lengths else None
    show = lambda values: "\n".join(f"- {value}" for value in values) if values else "N/D"
    if country.upper() == "FR":
        return f"# Brief de contenu : {keyword}\n\nTitre suggéré (modèle du premier résultat) : {titles[0] if titles else 'N/D'}\n\n## H2/H3 suggérés\n{show(headings[:12])}\n\n## Questions\n{show(questions[:10])}\n\n## Longueur cible\n{target if target is not None else 'N/D'} mots (moyenne des cinq premières pages accessibles)\n\n## Termes fréquents\n{show([word for word, _ in terms.most_common(15)])}"
    return f"# Content brief: {keyword}\n\nSuggested title (top-result pattern): {titles[0] if titles else 'N/D'}\n\n## Suggested H2/H3\n{show(headings[:12])}\n\n## Questions\n{show(questions[:10])}\n\n## Target length\n{target if target is not None else 'N/D'} words (mean of fetchable top-five pages)\n\n## Frequent terms\n{show([word for word, _ in terms.most_common(15)])}"


def cannibalization(domain: str, keywords: str, country: str = "FR") -> list[dict[str, Any]]:
    """Return every target-domain URL when at least two rank in the same live SERP."""
    target = domain.strip().casefold().rstrip(".")
    if "://" in target:
        target = (urlparse(target).hostname or "").casefold().rstrip(".")
    if target.startswith("www."):
        target = target[4:]
    if not target:
        raise ValueError("domain must not be empty")
    rows = []
    for word in _lines(keywords):
        try: results = serp.live(word, country, 100)
        except (ApiError, DataForSEOError): results = []
        matches: dict[str, int | None] = {}
        for result in results:
            item = _row(result)
            url = item.get("url")
            hostname = str(item.get("domain") or (urlparse(url).hostname if url else "")).casefold().rstrip(".")
            if hostname.startswith("www."):
                hostname = hostname[4:]
            if url and hostname == target:
                rank = item.get("rank_absolute", item.get("rank"))
                if url not in matches or (rank is not None and (matches[url] is None or rank < matches[url])):
                    matches[url] = rank
        if len(matches) >= 2:
            ordered = sorted(matches.items(), key=lambda pair: (pair[1] is None, pair[1] or 0, pair[0]))
            rows.extend({"keyword": word, "url": url, "rank": rank} for url, rank in ordered)
    return rows


def content_length(urls: str) -> list[dict[str, Any]]:
    """Count visible words, paragraphs, images, and H2 headings with lightweight BeautifulSoup parsing."""
    rows = []
    for url in _lines(urls):
        soup, error = _fetch(url)
        rows.append({"url": url, "words": len(_WORD.findall(_visible(soup))) if soup else None, "paragraphs": len(soup.find_all("p")) if soup else None, "images": len(soup.find_all("img")) if soup else None, "h2": len(soup.find_all("h2")) if soup else None, "error": error})
    return rows


def tfidf_analysis(keyword: str, text: str, country: str = "FR") -> list[dict[str, Any]]:
    """Calculate normalized TF-IDF across the supplied text and fetchable live top-five pages."""
    own = text
    if text.startswith(("http://", "https://")):
        soup, _error = _fetch(text); own = _visible(soup) if soup else ""
    documents: list[tuple[str, list[str]]] = [("input", [word.casefold() for word in _WORD.findall(own)])]
    try: results = serp.live(keyword, country, 5)
    except (ApiError, DataForSEOError): results = []
    for index, result in enumerate(results, 1):
        item = _row(result)
        soup, _error = _fetch(item.get("url") or "")
        if not soup: continue
        documents.append((item.get("url") or f"serp_{index}", [word.casefold() for word in _WORD.findall(_visible(soup))]))
    document_frequency = Counter(term for _, tokens in documents for term in set(tokens))
    document_count = len(documents)
    rows = []
    for document, tokens in documents:
        counts = Counter(tokens)
        for term, frequency in counts.items():
            tf = frequency / len(tokens)
            idf = math.log(1 + document_count / document_frequency[term])
            rows.append({"term": term, "document": document, "tf": round(tf, 6), "idf": round(idf, 6), "tfidf": round(tf * idf, 6)})
    return sorted(rows, key=lambda row: (-row["tfidf"], row["term"], row["document"]))


def lighthouse_cwv(url: str, strategy: str = "mobile") -> list[dict[str, Any]]:
    """Return Lighthouse performance and available CrUX field metrics from PageSpeed Insights."""
    metric = crux.page_speed(url, strategy)
    rows = [{"metric": "Lighthouse performance", "value": metric.performance_score, "status": metric.overall_category}]
    for name in ("lcp", "cls", "inp"):
        value = getattr(metric, name)
        rows.append({"metric": name.upper(), "value": value.get("percentile") if value else None, "status": value.get("category") if value else None})
    return rows


A = lambda name, required=True, default=None: ArgSpec(name, required, default)
register(ToolSpec("content_length_target", content_length_target, "Derive a content-length target from the live top ten.", "calculators", [A("keyword"), A("country", False, "FR")], "table"))
register(ToolSpec("keyword_expansion", keyword_expansion, "Expand a seed with live long-tail keywords.", "generators", [A("seed"), A("country", False, "FR"), A("limit", False, "30")], "table"))
register(ToolSpec("content_brief", content_brief, "Generate a live SERP-based content brief.", "generators", [A("keyword"), A("country", False, "FR")]))
register(ToolSpec("faq_generator", faq_generator, "Return live People Also Ask questions without invented fallbacks.", "generators", [A("keyword"), A("country", False, "FR")], "table"))
register(ToolSpec("cannibalization", cannibalization, "Detect competing ranking pages for each query.", "analyzers", [A("domain"), A("keywords"), A("country", False, "FR")], "table"))
register(ToolSpec("content_length", content_length, "Measure structural content length for URLs.", "analyzers", [A("urls")], "table"))
register(ToolSpec("tfidf_analysis", tfidf_analysis, "Calculate normalized TF-IDF across the input and live top-five pages.", "analyzers", [A("keyword"), A("text"), A("country", False, "FR")], "table"))
register(ToolSpec("lighthouse_cwv", lighthouse_cwv, "Report Lighthouse and Core Web Vitals metrics.", "checkers", [A("url"), A("strategy", False, "mobile")], "table"))
