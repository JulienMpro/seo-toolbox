"""SERP term extraction and real-page on-page content scoring."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter

import httpx
from bs4 import BeautifulSoup

from . import serp
from .audit import DEFAULT_USER_AGENT, _extract
from .models import ContentScore, TermFreq

STOPWORDS = {"de", "du", "des", "le", "la", "les", "un", "une", "et", "ou", "en", "a", "au", "aux",
             "pour", "par", "sur", "dans", "avec", "the", "of", "to", "and", "or", "in", "on", "for", "a",
             "an", "is", "are", "with", "your", "you"}


def _normalized(text: str) -> str:
    return "".join(char for char in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(char))


def keyword_in_text(keyword: str, text: str) -> bool:
    """Match a phrase accent- and case-insensitively with normalized whitespace."""
    needle = " ".join(_normalized(keyword).split())
    haystack = " ".join(_normalized(text).split())
    return bool(needle) and needle in haystack


def serp_terms(keyword: str, country: str, limit: int = 10, ngram_size: int = 2) -> list[TermFreq]:
    if ngram_size < 1:
        raise ValueError("ngram_size must be at least 1")
    results = serp.live(keyword, country, limit)
    words: list[str] = []
    for result in results:
        tokens = re.findall(r"[a-z0-9]+", _normalized(f"{result.title or ''} {result.description or ''}"))
        words.extend(token for token in tokens if token not in STOPWORDS and len(token) > 1)
    counts = Counter(" ".join(words[index:index + ngram_size]) for index in range(len(words) - ngram_size + 1))
    return [TermFreq(term, count) for term, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])) if count >= 2]


def content_score(url: str, keyword: str, country: str = "FR") -> ContentScore:
    """Fetch an HTML page and score only directly verified on-page criteria."""
    del country  # Kept for a stable country-aware CLI/API signature.
    response = httpx.get(url, timeout=15, headers={"User-Agent": DEFAULT_USER_AGENT}, follow_redirects=True)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if "html" not in content_type.lower():
        raise ValueError("URL did not return HTML content")
    fields = _extract(response.text, str(response.url))
    soup = BeautifulSoup(response.text, "html.parser")
    for node in soup(["script", "style", "noscript"]):
        node.decompose()
    body = soup.body.get_text(" ", strip=True) if soup.body else soup.get_text(" ", strip=True)
    title, meta, h1 = str(fields.get("title") or ""), str(fields.get("meta_description") or ""), str(fields.get("h1") or "")
    keyword_words = [word for word in _normalized(keyword).split() if word]
    title_kw = keyword_in_text(keyword, title) or any(keyword_in_text(word, title) for word in keyword_words)
    checks = [("title present", bool(title), 15), ("keyword in title", title_kw, 10),
              ("meta description present", bool(meta), 15), ("H1 present", bool(h1), 10),
              ("keyword in H1", keyword_in_text(keyword, h1), 10),
              ("at least 300 words", len(re.findall(r"\b\w+\b", body, re.UNICODE)) >= 300, 15),
              ("keyword in body", keyword_in_text(keyword, body), 15),
              ("canonical present", bool(fields.get("canonical")), 10)]
    return ContentScore(url, sum(points for _, ok, points in checks if ok), checks)
