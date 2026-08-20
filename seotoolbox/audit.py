"""Small, dependency-light technical SEO spider and issue analyzer."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse

import httpx

from .models import AuditReport, CrawlResult, Issue

DEFAULT_USER_AGENT = "seotoolbox/0.3 (+https://github.com/JulienMpro/seo-toolbox)"


def robots_allows(url: str, robots_txt: str) -> bool:
    """Apply basic User-agent: * Disallow rules to a URL."""
    path = urlparse(url).path or "/"
    active = False
    rules: list[str] = []
    for raw_line in robots_txt.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        name, value = (part.strip() for part in line.split(":", 1))
        if name.lower() == "user-agent":
            active = value == "*"
        elif active and name.lower() == "disallow" and value:
            rules.append(value)
    return not any(path.startswith(rule) for rule in rules)


def _internal(url: str, origin: str) -> bool:
    parsed, base = urlparse(url), urlparse(origin)
    return parsed.scheme in {"http", "https"} and parsed.netloc.lower() == base.netloc.lower()


def _sitemap_urls(xml_text: str) -> tuple[list[str], bool]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return [], False
    urls = [node.text.strip() for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "loc" and node.text]
    return urls, root.tag.rsplit("}", 1)[-1] == "sitemapindex"


def _extract(html: str, base_url: str) -> dict[str, object]:
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.get_text(" ", strip=True) if soup.title else None
        description = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
        h1 = soup.find("h1")
        canonical = soup.find("link", attrs={"rel": lambda value: value and "canonical" in value})
        robots = soup.find("meta", attrs={"name": re.compile("^robots$", re.I)})
        return {
            "title": title,
            "meta_description": description.get("content", "").strip() or None if description else None,
            "h1": h1.get_text(" ", strip=True) or None if h1 else None,
            "canonical": urljoin(base_url, canonical.get("href", "")) or None if canonical else None,
            "noindex": bool(robots and "noindex" in robots.get("content", "").lower()),
        }
    except ImportError:
        def text(pattern: str) -> str | None:
            match = re.search(pattern, html, re.I | re.S)
            return re.sub(r"<[^>]+>", "", match.group(1)).strip() or None if match else None
        def attribute(tag: str, marker: str, name: str) -> str | None:
            for match in re.finditer(fr"<{tag}\b[^>]*>", html, re.I):
                raw = match.group(0)
                if re.search(marker, raw, re.I):
                    value = re.search(fr"\b{name}\s*=\s*[\"']([^\"']*)", raw, re.I)
                    if value:
                        return value.group(1).strip() or None
            return None
        canonical = attribute("link", r"\brel\s*=\s*[\"'][^\"']*canonical", "href")
        robots = attribute("meta", r"\bname\s*=\s*[\"']robots[\"']", "content")
        description = attribute("meta", r"\bname\s*=\s*[\"']description[\"']", "content")
        return {"title": text(r"<title[^>]*>(.*?)</title>"), "meta_description": description,
                "h1": text(r"<h1[^>]*>(.*?)</h1>"),
                "canonical": urljoin(base_url, canonical) if canonical else None,
                "noindex": bool(robots and "noindex" in robots.lower())}


def _fetch_page(url: str, timeout: float, headers: dict[str, str]) -> CrawlResult:
    try:
        response = httpx.get(url, timeout=timeout, headers=headers, follow_redirects=False)
        content_type = response.headers.get("content-type", "").split(";", 1)[0] or None
        fields: dict[str, object] = {}
        if content_type and ("html" in content_type or "xhtml" in content_type):
            fields = _extract(response.text, url)
        location = response.headers.get("location")
        return CrawlResult(url=url, status=response.status_code,
                           redirect_url=urljoin(url, location) if location else None,
                           content_length=len(response.content), content_type=content_type, **fields)
    except httpx.HTTPError:
        return CrawlResult(url=url)


def crawl_site(start_url: str, max_pages: int = 200, timeout: float = 10,
               user_agent: str = DEFAULT_USER_AGENT, workers: int = 10) -> list[CrawlResult]:
    """Discover sitemap URLs and fetch same-origin pages concurrently."""
    if max_pages < 1:
        return []
    parsed = urlparse(start_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("A valid http(s) URL is required")
    origin = f"{parsed.scheme}://{parsed.netloc}"
    headers = {"User-Agent": user_agent}
    robots_text = ""
    sitemap_candidates: list[str] = []
    try:
        response = httpx.get(urljoin(origin, "/robots.txt"), timeout=timeout, headers=headers)
        if response.status_code < 400:
            robots_text = response.text
            sitemap_candidates = re.findall(r"^\s*Sitemap:\s*(\S+)", robots_text, re.I | re.M)
    except httpx.HTTPError:
        pass
    sitemap_candidates.extend([urljoin(origin, "/sitemap.xml"), urljoin(origin, "/sitemap_index.xml")])
    queue = list(dict.fromkeys(sitemap_candidates))
    seen_maps: set[str] = set()
    discovered: list[str] = []
    while queue and len(discovered) < max_pages:
        sitemap = queue.pop(0)
        if sitemap in seen_maps or not _internal(sitemap, origin):
            continue
        seen_maps.add(sitemap)
        try:
            response = httpx.get(sitemap, timeout=timeout, headers=headers)
            if response.status_code >= 400:
                continue
            urls, is_index = _sitemap_urls(response.text)
            if is_index:
                queue.extend(urls)
            else:
                discovered.extend(url for url in urls if _internal(url, origin))
        except httpx.HTTPError:
            continue
    urls = list(dict.fromkeys(discovered))[:max_pages]
    if not urls:
        urls = [start_url]
    if robots_text:
        urls = [url for url in urls if robots_allows(url, robots_text)]
    with ThreadPoolExecutor(max_workers=max(1, min(workers, 10))) as executor:
        return list(executor.map(lambda url: _fetch_page(url, timeout, headers), urls))


def analyze(results: list[CrawlResult]) -> AuditReport:
    """Build a typed technical SEO issue report from crawl results."""
    issues: list[Issue] = []
    result_by_url = {result.url: result for result in results}
    fields = (("title", "missing_title", "duplicate_title"),
              ("meta_description", "missing_meta", "duplicate_meta"),
              ("h1", "missing_h1", "duplicate_h1"))
    duplicates: dict[str, dict[str, list[str]]] = {}
    for field, _, _ in fields:
        grouped: dict[str, list[str]] = defaultdict(list)
        for result in results:
            value = getattr(result, field)
            if value:
                grouped[str(value).strip().lower()].append(result.url)
        duplicates[field] = grouped
    for result in results:
        if result.status is None:
            issues.append(Issue(result.url, "error", "error", "Request failed or timed out"))
        elif result.status >= 400:
            issues.append(Issue(result.url, "error", "error", f"HTTP {result.status}"))
        if result.status and 300 <= result.status < 400:
            message = f"HTTP {result.status} redirects to {result.redirect_url or 'N/D'}"
            target = result_by_url.get(result.redirect_url or "")
            if target and target.status and 300 <= target.status < 400:
                message += f" (chain to {target.redirect_url or 'N/D'})"
            issues.append(Issue(result.url, "redirect", "warning", message))
        if result.status and 200 <= result.status < 300 and result.content_type and "html" in result.content_type:
            for field, missing_type, duplicate_type in fields:
                value = getattr(result, field)
                if not value:
                    issues.append(Issue(result.url, missing_type, "warning", f"Missing {field.replace('_', ' ')}"))
                elif len(duplicates[field][str(value).strip().lower()]) > 1:
                    issues.append(Issue(result.url, duplicate_type, "warning", f"Duplicate {field.replace('_', ' ')}"))
            if not result.canonical:
                issues.append(Issue(result.url, "missing_canonical", "warning", "Missing canonical URL"))
            if result.noindex:
                issues.append(Issue(result.url, "noindex", "info", "Page is marked noindex"))
    lengths = [result.content_length for result in results if result.content_length is not None]
    status_codes = Counter(str(result.status) if result.status is not None else "N/D" for result in results)
    return AuditReport(len(results), issues, {"status_codes": dict(status_codes),
                                               "avg_content_length": sum(lengths) / len(lengths) if lengths else None})
