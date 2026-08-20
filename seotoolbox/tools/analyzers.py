"""Local on-page content and site-structure analyzers."""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict, deque
from itertools import combinations
from urllib.parse import urljoin, urlparse, urlunparse

import httpx
from bs4 import BeautifulSoup

from . import ArgSpec, ToolSpec, register

_WORD_RE = re.compile(r"[^\W_]+(?:[-'][^\W_]+)*", re.UNICODE)
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "is", "it", "of", "on", "or", "that", "the", "this", "to", "with",
    "à", "au", "aux", "avec", "ce", "ces", "dans", "de", "des", "du", "elle", "en", "et", "est", "il", "la", "le", "les", "ou", "par", "pour", "que", "qui", "sur", "un", "une",
}


def _words(text: str) -> list[str]:
    return [word.casefold() for word in _WORD_RE.findall(text)]


def _lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def _valid_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"invalid HTTP(S) URL: {url}")


def _fetch(url: str) -> tuple[BeautifulSoup | None, str | None]:
    _valid_url(url)
    try:
        response = httpx.get(url, timeout=15, follow_redirects=True, headers={"User-Agent": "seotoolbox/0.3"})
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser"), None
    except httpx.HTTPError as exc:
        return None, str(exc)


def keyword_density(text: str, keyword: str) -> list[dict]:
    """Measure keyword occurrences and density for each paragraph and overall."""
    phrase = _words(keyword)
    if not phrase:
        raise ValueError("keyword must contain at least one word")
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()] or ([text] if text else [])
    rows = []
    total_words = total_occurrences = 0
    for index, paragraph in enumerate(paragraphs, 1):
        tokens = _words(paragraph)
        occurrences = sum(tokens[pos:pos + len(phrase)] == phrase for pos in range(max(0, len(tokens) - len(phrase) + 1)))
        total_words += len(tokens)
        total_occurrences += occurrences
        rows.append({"paragraph": index, "occurrences": occurrences, "density_pct": round(occurrences / len(tokens) * 100, 2) if tokens else 0.0})
    rows.append({"paragraph": "TOTAL", "occurrences": total_occurrences, "density_pct": round(total_occurrences / total_words * 100, 2) if total_words else 0.0})
    return rows


def co_occurrence(text: str, keyword: str, limit: int = 20) -> list[dict]:
    """Count non-stopword terms occurring in sentences or paragraphs containing a keyword."""
    if limit < 1:
        raise ValueError("limit must be positive")
    needle = keyword.casefold().strip()
    if not needle:
        raise ValueError("keyword must not be empty")
    units = re.split(r"(?:\n\s*\n)|(?<=[.!?])\s+", text)
    counts: Counter[str] = Counter()
    keyword_words = set(_words(keyword))
    for unit in units:
        if needle in unit.casefold():
            counts.update(word for word in _words(unit) if word not in _STOPWORDS and word not in keyword_words)
    return [{"term": term, "frequency": frequency} for term, frequency in counts.most_common(limit)]


def ngrams(text: str, n: int = 2, limit: int = 20) -> list[dict]:
    """Return the most frequent contiguous word n-grams."""
    if n < 1 or limit < 1:
        raise ValueError("n and limit must be positive")
    tokens = _words(text)
    counts = Counter(" ".join(tokens[index:index + n]) for index in range(max(0, len(tokens) - n + 1)))
    return [{"n_gram": value, "frequency": count} for value, count in counts.most_common(limit)]


def _syllables(word: str, lang: str) -> int:
    """Approximate syllables via vowel groups, with English silent-e handling."""
    cleaned = re.sub(r"[^a-zàâäéèêëîïôöùûüÿœæ]", "", word.casefold())
    groups = re.findall(r"[aeiouyàâäéèêëîïôöùûüÿœæ]+", cleaned)
    count = len(groups)
    if lang == "en" and len(cleaned) > 2 and cleaned.endswith("e") and not cleaned.endswith(("le", "ye")) and count > 1:
        count -= 1
    return max(1, count) if cleaned else 0


def readability(text: str, lang: str = "fr") -> list[dict]:
    """Compute approximate Flesch ease and grade scores for French or English."""
    if lang not in {"fr", "en"}:
        raise ValueError("lang must be fr or en")
    words = _words(text)
    sentences = [part for part in re.split(r"[.!?]+", text) if _words(part)]
    if not words:
        raise ValueError("text must contain words")
    sentence_count = max(1, len(sentences))
    syllables = sum(_syllables(word, lang) for word in words)
    asl, asw = len(words) / sentence_count, syllables / len(words)
    # Kandel-Moles adapts Reading Ease to French; the grade-style score uses
    # the standard FK coefficients as a useful comparable approximation.
    ease = (207 - 1.015 * asl - 73.6 * asw) if lang == "fr" else (206.835 - 1.015 * asl - 84.6 * asw)
    grade = 0.39 * asl + 11.8 * asw - 15.59
    verdict = "very easy" if ease >= 80 else "easy" if ease >= 60 else "medium" if ease >= 40 else "difficult" if ease >= 20 else "very difficult"
    return [{"metric": "Flesch Reading Ease", "score": round(ease, 2), "verdict": verdict}, {"metric": "Flesch-Kincaid Grade", "score": round(grade, 2), "verdict": verdict}]


def page_similarity(urls: str) -> list[dict]:
    """Compare visible page text with cosine similarity."""
    values = _lines(urls)
    if len(values) < 2:
        raise ValueError("provide at least two URLs, one per line")
    vectors: dict[str, Counter[str] | None] = {}
    errors: dict[str, str | None] = {}
    for url in values:
        soup, error = _fetch(url)
        vectors[url] = Counter(_words(soup.get_text(" ", strip=True))) if soup else None
        errors[url] = error
    pairs = [(values[0], value) for value in values[1:]] if len(values) > 5 else list(combinations(values, 2))
    rows = []
    for left, right in pairs:
        a, b = vectors[left], vectors[right]
        if a is None or b is None:
            rows.append({"pair": f"{left} ↔ {right}", "similarity_pct": None, "error": errors[left] or errors[right]})
            continue
        dot = sum(count * b.get(word, 0) for word, count in a.items())
        denominator = math.sqrt(sum(v * v for v in a.values()) * sum(v * v for v in b.values()))
        rows.append({"pair": f"{left} ↔ {right}", "similarity_pct": round(dot / denominator * 100, 2) if denominator else 0.0, "error": None})
    return rows


def heading_checker(urls: str) -> list[dict]:
    """Check H1 count, hierarchy jumps, and heading lengths."""
    rows = []
    for url in _lines(urls):
        soup, error = _fetch(url)
        if not soup:
            rows.append({"url": url, "h1": None, "h1_ok": None, "h2_count": None, "errors": error})
            continue
        headings = soup.find_all(re.compile(r"^h[1-6]$"))
        h1s = [tag.get_text(" ", strip=True) for tag in headings if tag.name == "h1"]
        issues = []
        if not h1s: issues.append("missing H1")
        if len(h1s) > 1: issues.append("multiple H1")
        levels = [int(tag.name[1]) for tag in headings]
        if any(current > previous + 1 for previous, current in zip(levels, levels[1:])): issues.append("heading level jump")
        long = [f"{tag.name.upper()}={len(tag.get_text(' ', strip=True))}" for tag in headings if len(tag.get_text(" ", strip=True)) > 70]
        if long: issues.append("long headings: " + ", ".join(long))
        rows.append({"url": url, "h1": " | ".join(h1s) or None, "h1_ok": len(h1s) == 1, "h2_count": sum(tag.name == "h2" for tag in headings), "errors": "; ".join(issues) or None})
    return rows


def _pixel_width(value: str) -> int:
    return round(sum(3.5 if char in " ilI.,'" else 9 if char in "MW@%" else 7 for char in value))


def title_meta_analyzer(urls: str) -> list[dict]:
    """Analyze title and description lengths, truncation, and batch duplicates."""
    pages = []
    for url in _lines(urls):
        soup, error = _fetch(url)
        title = soup.title.get_text(" ", strip=True) if soup and soup.title else ""
        meta_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)}) if soup else None
        meta = str(meta_tag.get("content", "")).strip() if meta_tag else ""
        pages.append((url, title, meta, error))
    title_counts = Counter(title.casefold() for _, title, _, _ in pages if title)
    meta_counts = Counter(meta.casefold() for _, _, meta, _ in pages if meta)
    return [{"url": url, "title_len": len(title) if title else None, "title_ok": bool(title) and _pixel_width(title) <= 600, "meta_len": len(meta) if meta else None, "meta_ok": bool(meta) and len(meta) <= 155, "duplicate": bool(title and title_counts[title.casefold()] > 1 or meta and meta_counts[meta.casefold()] > 1), "truncated": bool(title and _pixel_width(title) > 600 or meta and len(meta) > 155), "error": error} for url, title, meta, error in pages]


def thin_content(value: str, text: bool = False) -> list[dict]:
    """Score thin-content risk from raw text or a fetched HTML page."""
    if text:
        content, paragraphs, images, links, headings = value, len([p for p in re.split(r"\n\s*\n", value) if p.strip()]), 0, 0, 0
    else:
        soup, error = _fetch(value)
        if not soup:
            return [{"criterion": "fetch", "value": None, "points": None, "score": None, "error": error}]
        content = soup.get_text(" ", strip=True)
        paragraphs, images, links, headings = len(soup.find_all("p")), len(soup.find_all("img")), len(soup.find_all("a")), len(soup.find_all(re.compile(r"^h[1-6]$")))
    words = len(_words(content))
    criteria = [("words", words, 50 if words < 150 else 25 if words < 300 else 0), ("paragraphs", paragraphs, 15 if paragraphs < 2 else 0), ("images", images, 10 if images == 0 else 0), ("links", links, 10 if links == 0 else 0), ("headings", headings, 15 if headings == 0 else 0)]
    score = sum(points for _, _, points in criteria)
    return [{"criterion": name, "value": amount, "points": points, "score": score} for name, amount, points in criteria]


def entity_extractor(text: str) -> list[dict]:
    """Extract lightweight named entities using deterministic patterns."""
    found: set[tuple[str, str]] = set()
    patterns = [
        (r"\b[A-ZÀ-ÖØ-Þ][a-zà-öø-ÿ]+(?:\s+[A-ZÀ-ÖØ-Þ][a-zà-öø-ÿ]+)+\b", "Person"),
        (r"\b(?:à|de|en)\s+([A-ZÀ-ÖØ-Þ][\wÀ-ÖØ-öø-ÿ-]+(?:\s+[A-ZÀ-ÖØ-Þ][\wÀ-ÖØ-öø-ÿ-]+)*)", "Location"),
        (r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b", "Date"),
        (r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", "Email"),
        (r"https?://[^\s<>\"']+", "URL"),
    ]
    for pattern, kind in patterns:
        for match in re.finditer(pattern, text): found.add(((match.group(1) if match.lastindex else match.group(0)).rstrip(".,)"), kind))
    capitals = Counter(re.findall(r"\b[A-Z][A-Z0-9&-]{1,}\b", text))
    found.update((word, "Brand") for word, count in capitals.items() if count > 1)
    return [{"entity": entity, "type": kind} for entity, kind in sorted(found, key=lambda item: (item[1], item[0].casefold()))]


def _site_links(urls: list[str]) -> tuple[Counter[str], Counter[str], dict[str, set[str]], dict[str, str]]:
    anchors, targets, graph, errors = Counter(), Counter(), defaultdict(set), {}
    domains = {urlparse(url).netloc.casefold() for url in urls}
    known = set(urls)
    for url in urls:
        soup, error = _fetch(url)
        if not soup:
            errors[url] = error or "request failed"; continue
        for tag in soup.find_all("a", href=True):
            target = urljoin(url, str(tag["href"])).split("#", 1)[0]
            if urlparse(target).netloc.casefold() in domains:
                anchor = tag.get_text(" ", strip=True) or "(empty)"
                anchors[anchor] += 1; targets[target] += 1
                if target in known: graph[url].add(target)
    return anchors, targets, graph, errors


def internal_anchors(urls: str) -> list[dict]:
    """Aggregate internal-link anchor text and most-linked targets."""
    values = _lines(urls)
    anchors, targets, _, errors = _site_links(values)
    rows = [{"kind": "anchor", "value": value, "occurrences": count} for value, count in anchors.most_common()]
    rows += [{"kind": "target", "value": value, "occurrences": count} for value, count in targets.most_common()]
    rows += [{"kind": "error", "value": url, "occurrences": None, "error": error} for url, error in errors.items()]
    return rows


def internal_link_score(urls: str) -> list[dict]:
    """Report in-links, out-links, and BFS depth within a supplied URL set."""
    values = _lines(urls)
    if not values: raise ValueError("provide at least one URL")
    _, _, graph, errors = _site_links(values)
    incoming = Counter(target for targets in graph.values() for target in targets)
    depths = {values[0]: 0}; queue = deque([values[0]])
    while queue:
        source = queue.popleft()
        for target in graph[source]:
            if target not in depths: depths[target] = depths[source] + 1; queue.append(target)
    return [{"url": url, "in": incoming[url] if url not in errors else None, "out": len(graph[url]) if url not in errors else None, "depth": depths.get(url), "error": errors.get(url)} for url in values]


def A(name: str, required: bool = True, default: str | None = None, is_flag: bool = False) -> ArgSpec:
    return ArgSpec(name, required, default, name.replace("_", " ").capitalize() + ".", is_flag)


register(ToolSpec("keyword_density", keyword_density, "Measure keyword density by paragraph.", "analyzers", [A("text"), A("keyword")], "table"))
register(ToolSpec("co_occurrence", co_occurrence, "Find terms co-occurring with a keyword.", "analyzers", [A("text"), A("keyword"), A("limit", False, "20")], "table"))
register(ToolSpec("ngrams", ngrams, "Count frequent word n-grams.", "analyzers", [A("text"), A("n", False, "2"), A("limit", False, "20")], "table"))
register(ToolSpec("readability", readability, "Estimate French or English text readability.", "analyzers", [A("text"), A("lang", False, "fr")], "table"))
register(ToolSpec("page_similarity", page_similarity, "Compare visible text across URLs.", "analyzers", [A("urls")], "table"))
register(ToolSpec("heading_checker", heading_checker, "Check page heading structure.", "analyzers", [A("urls")], "table"))
register(ToolSpec("title_meta_analyzer", title_meta_analyzer, "Analyze page titles and descriptions in bulk.", "analyzers", [A("urls")], "table"))
register(ToolSpec("thin_content", thin_content, "Score thin-content risk for text or a URL.", "analyzers", [A("value"), A("text", False, is_flag=True)], "table"))
register(ToolSpec("entity_extractor", entity_extractor, "Extract named entities with local patterns.", "analyzers", [A("text")], "table"))
register(ToolSpec("internal_anchors", internal_anchors, "Aggregate internal anchor text and targets.", "analyzers", [A("urls")], "table"))
register(ToolSpec("internal_link_score", internal_link_score, "Score internal links and crawl depth.", "analyzers", [A("urls")], "table"))
