"""Local technical SEO validators and URL checkers."""

from __future__ import annotations

import csv
import io
import json
import re
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

from . import ArgSpec, ToolSpec, register
from .schema import _JSONLDParser, jsonld_validate


def _lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def _valid_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"invalid HTTP(S) URL: {url}")


def _page(url: str) -> tuple[BeautifulSoup | None, str | None]:
    _valid_url(url)
    try:
        response = httpx.get(url, timeout=15, follow_redirects=True, headers={"User-Agent": "seotoolbox/0.3"})
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser"), None
    except httpx.HTTPError as exc:
        return None, str(exc)


def http_status_bulk(urls: str) -> list[dict]:
    """Fetch URLs concurrently without following redirects."""
    values = _lines(urls)
    def check(url: str) -> dict:
        try:
            _valid_url(url); started = time.perf_counter()
            response = httpx.get(url, timeout=15, follow_redirects=False, headers={"User-Agent": "seotoolbox/0.3"})
            elapsed = round((time.perf_counter() - started) * 1000, 2)
            location = response.headers.get("location")
            return {"url": url, "status": response.status_code, "time_ms": elapsed, "redirect": urljoin(url, location) if location else None, "error": None}
        except (ValueError, httpx.HTTPError) as exc:
            return {"url": url, "status": None, "time_ms": None, "redirect": None, "error": str(exc)}
    with ThreadPoolExecutor(max_workers=min(10, max(1, len(values)))) as executor:
        return list(executor.map(check, values))


def redirect_chain(url: str) -> list[dict]:
    """Follow and report up to ten redirect hops, detecting loops."""
    _valid_url(url); current = url; seen = set(); rows = []
    for hop in range(11):
        if current in seen:
            rows.append({"hop": hop, "url": current, "status": None, "location": None, "note": "redirect loop"}); break
        seen.add(current)
        try: response = httpx.get(current, timeout=15, follow_redirects=False, headers={"User-Agent": "seotoolbox/0.3"})
        except httpx.HTTPError as exc:
            rows.append({"hop": hop, "url": current, "status": None, "location": None, "note": str(exc)}); break
        location = response.headers.get("location")
        target = urljoin(current, location) if location else None
        rows.append({"hop": hop, "url": current, "status": response.status_code, "location": target, "note": "final" if not (300 <= response.status_code < 400 and target) else None})
        if not (300 <= response.status_code < 400 and target): break
        if hop == 10: rows[-1]["note"] = "maximum 10 redirects exceeded"; break
        current = target
    return rows


def robots_checker(url: str, user_agent: str = "googlebot") -> list[dict]:
    """Check a URL against its origin robots.txt and report the matching rule."""
    _valid_url(url); parsed = urlparse(url); robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        response = httpx.get(robots_url, timeout=15, follow_redirects=True, headers={"User-Agent": "seotoolbox/0.3"})
        response.raise_for_status()
    except httpx.HTTPError as exc:
        return [{"url": url, "ua": user_agent, "allowed": None, "rule": None, "error": str(exc)}]
    parser = RobotFileParser(); parser.set_url(robots_url); parser.parse(response.text.splitlines())
    allowed = parser.can_fetch(user_agent, url); path = parsed.path or "/"; active = False; matched = None
    for raw in response.text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if ":" not in line: continue
        name, value = (part.strip() for part in line.split(":", 1))
        if name.casefold() == "user-agent": active = value.casefold() in {"*", user_agent.casefold()}
        elif active and name.casefold() in {"allow", "disallow"} and value and path.startswith(value.rstrip("$")): matched = f"{name}: {value}"
    return [{"url": url, "ua": user_agent, "allowed": allowed, "rule": matched, "error": None}]


def sitemap_validator(url: str) -> list[dict]:
    """Validate sitemap XML and list invalid location entries."""
    _valid_url(url)
    try:
        response = httpx.get(url, timeout=15, follow_redirects=True); response.raise_for_status()
    except httpx.HTTPError as exc:
        return [{"valid": False, "url_count": None, "sitemap_index": None, "error": str(exc)}]
    try: root = ET.fromstring(response.text)
    except ET.ParseError as exc: return [{"valid": False, "url_count": 0, "sitemap_index": None, "error": f"invalid XML: {exc}"}]
    root_name = root.tag.rsplit("}", 1)[-1]; is_index = root_name == "sitemapindex"
    locations = [node.text.strip() if node.text else "" for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "loc"]
    invalid = [value or "(empty)" for value in locations if urlparse(value).scheme not in {"http", "https"} or not urlparse(value).netloc]
    rows = [{"valid": root_name in {"urlset", "sitemapindex"} and not invalid, "url_count": len(locations), "sitemap_index": is_index, "error": None if root_name in {"urlset", "sitemapindex"} else f"unexpected root: {root_name}"}]
    rows += [{"valid": False, "url_count": None, "sitemap_index": is_index, "error": f"invalid loc: {value}"} for value in invalid]
    return rows


def canonical_checker(urls: str) -> list[dict]:
    """Check canonical presence, self-reference, and cross-domain conflicts."""
    rows = []
    for url in _lines(urls):
        soup, error = _page(url); tag = soup.find("link", rel=lambda value: value and "canonical" in value) if soup else None
        canonical = urljoin(url, str(tag.get("href", ""))) if tag and tag.get("href") else None
        rows.append({"url": url, "canonical": canonical, "present": bool(canonical) if soup else None, "self_canonical": _normalized(canonical) == _normalized(url) if canonical else False if soup else None, "conflict": urlparse(canonical).netloc.casefold() != urlparse(url).netloc.casefold() if canonical else False if soup else None, "error": error})
    return rows


def _hreflangs(soup: BeautifulSoup, base: str) -> dict[str, str]:
    return {str(tag.get("hreflang", "")).casefold(): urljoin(base, str(tag.get("href", ""))) for tag in soup.find_all("link", href=True) if tag.get("hreflang") and "alternate" in (tag.get("rel") or [])}


def hreflang_checker(urls: str) -> list[dict]:
    """List hreflang links and check reciprocal references within the batch."""
    values = _lines(urls); pages = {}
    for url in values:
        soup, error = _page(url); pages[url] = (_hreflangs(soup, url) if soup else {}, error)
    rows = []
    for url, (links, error) in pages.items():
        if not links: rows.append({"url": url, "lang": None, "target": None, "reciprocal": None, "error": error or "no hreflang"})
        for lang, target in links.items():
            reciprocal = target in pages and url in pages[target][0].values()
            rows.append({"url": url, "lang": lang, "target": target, "reciprocal": reciprocal, "error": None})
    return rows


def schema_validator(url: str) -> list[dict]:
    """Extract and validate every JSON-LD block on a page."""
    _valid_url(url)
    try: response = httpx.get(url, timeout=15, follow_redirects=True); response.raise_for_status()
    except httpx.HTTPError as exc: return [{"index": None, "type": None, "valid": None, "errors": str(exc)}]
    parser = _JSONLDParser(); parser.feed(response.text); rows = []
    for index, block in enumerate(parser.blocks, 1):
        try: data = json.loads(block); type_name = data.get("@type") if isinstance(data, dict) else "unknown"
        except json.JSONDecodeError: type_name = "invalid JSON"
        checks = jsonld_validate(block); invalid = [row["message"] for row in checks if not row["ok"] and row["check"] != "verdict"]
        rows.append({"index": index, "type": type_name, "valid": not invalid, "errors": "; ".join(invalid) or None})
    return rows or [{"index": None, "type": None, "valid": False, "errors": "no JSON-LD blocks"}]


def viewport_checker(urls: str) -> list[dict]:
    """Check viewport metadata for responsive-design hints."""
    rows = []
    for url in _lines(urls):
        soup, error = _page(url); tag = soup.find("meta", attrs={"name": re.compile(r"^viewport$", re.I)}) if soup else None
        content = str(tag.get("content", "")) if tag else ""
        rows.append({"url": url, "present": bool(tag) if soup else None, "device_width": "width=device-width" in content.casefold().replace(" ", ""), "responsive_hint": bool(tag and "width=device-width" in content.casefold().replace(" ", "")), "error": error})
    return rows


def og_validator(urls: str) -> list[dict]:
    """Validate essential Open Graph and Twitter metadata."""
    rows = []
    for url in _lines(urls):
        soup, error = _page(url); values = {}
        if soup:
            for key in ("og:title", "og:description", "og:image", "twitter:card"):
                tag = soup.find("meta", attrs={"property": key}) or soup.find("meta", attrs={"name": key})
                values[key] = str(tag.get("content", "")).strip() if tag else ""
        rows.append({"url": url, "og_title": bool(values.get("og:title")) if soup else None, "title_len": len(values.get("og:title", "")) or None, "og_description": bool(values.get("og:description")) if soup else None, "description_len": len(values.get("og:description", "")) or None, "og_image": bool(values.get("og:image")) if soup else None, "twitter_card": bool(values.get("twitter:card")) if soup else None, "error": error})
    return rows


def mixed_content(url: str) -> list[dict]:
    """Find insecure HTTP resources referenced by an HTTPS page."""
    _valid_url(url)
    if urlparse(url).scheme != "https": return [{"resource": None, "type": None, "error": "page is not HTTPS"}]
    soup, error = _page(url)
    if not soup: return [{"resource": None, "type": None, "error": error}]
    rows = []
    for tag in soup.find_all(True):
        for attribute in ("src", "href"):
            value = tag.get(attribute)
            if isinstance(value, str) and value.casefold().startswith("http://"):
                rows.append({"resource": value, "type": f"{tag.name}[{attribute}]", "error": None})
    return rows


def _normalized(url: str | None) -> str | None:
    if not url: return None
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname: return None
    host = parsed.hostname.casefold() + (f":{parsed.port}" if parsed.port else "")
    path = parsed.path or "/"
    if path != "/": path = path.rstrip("/") + "/"
    return urlunparse((parsed.scheme.casefold(), host, path, "", urlencode(sorted(parse_qsl(parsed.query, keep_blank_values=True))), ""))


def url_syntax(urls: str) -> list[dict]:
    """Validate and deterministically normalize URLs."""
    rows = []
    for value in _lines(urls):
        normalized = _normalized(value); error = None
        if not normalized: error = "absolute HTTP(S) URL with a host required"
        elif any(char.isspace() for char in value): normalized, error = None, "URL contains whitespace"
        rows.append({"url": value, "valid": error is None, "normalized": normalized, "error": error})
    return rows


def indexation_checker(indexed: str, urls: str) -> list[dict]:
    """Compare URLs against an indexed-list or GSC-style CSV export."""
    indexed_values: dict[str, str] = {}
    if "," in indexed.splitlines()[0] if indexed.splitlines() else False:
        reader = csv.DictReader(io.StringIO(indexed)); fields = reader.fieldnames or []
        url_field = next((field for field in fields if field.casefold() in {"url", "page"}), None)
        status_field = next((field for field in fields if "status" in field.casefold() or "index" in field.casefold()), None)
        if not url_field: raise ValueError("CSV must contain a URL or Page column")
        for row in reader: indexed_values[row.get(url_field, "").strip()] = row.get(status_field, "indexed") if status_field else "indexed"
    else:
        indexed_values = {value: "indexed" for value in _lines(indexed)}
    rows = []
    for url in _lines(urls):
        raw = indexed_values.get(url)
        status = "unknown" if raw is None and not indexed_values else "not indexed" if raw is None else "not indexed" if re.search(r"not|non|excluded|error", raw, re.I) else "indexed"
        rows.append({"url": url, "status": status, "source_status": raw})
    return rows


def hreflang_reciprocity(urls: str) -> list[dict]:
    """Ensure every lang|URL page links back to every supplied language URL."""
    entries = []
    for line in _lines(urls):
        lang, separator, url = line.partition("|")
        if not separator or not lang.strip() or not url.strip(): raise ValueError("urls must use lang|url, one per line")
        entries.append((lang.strip(), url.strip()))
    pages = {}
    for _, url in entries:
        soup, error = _page(url); pages[url] = (_hreflangs(soup, url) if soup else {}, error)
    rows = []
    for lang, url in entries:
        links, error = pages[url]; missing = [other_lang for other_lang, target in entries if target != url and links.get(other_lang.casefold()) != target]
        rows.append({"url": url, "lang": lang, "missing_returns": ", ".join(missing) or None, "ok": not missing if not error else None, "error": error})
    return rows


def _pixel_width(value: str) -> int:
    return round(sum(3.5 if char in " ilI.,'" else 9 if char in "MW@%" else 7 for char in value))


def title_meta_validator(url: str = "", title: str = "", meta: str = "") -> list[dict]:
    """Validate one page title and description, fetched or supplied directly."""
    h1 = ""; error = None
    if url:
        soup, error = _page(url)
        if soup:
            title = soup.title.get_text(" ", strip=True) if soup.title else ""
            tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
            meta = str(tag.get("content", "")).strip() if tag else ""
            first_h1 = soup.find("h1"); h1 = first_h1.get_text(" ", strip=True) if first_h1 else ""
    elif not title and not meta: raise ValueError("provide --url or --title/--meta")
    checks = [("title present", bool(title), "present" if title else "missing"), ("title width", bool(title) and _pixel_width(title) <= 600, f"{len(title)} chars / {_pixel_width(title)} px"), ("meta present", bool(meta), "present" if meta else "missing"), ("meta length", bool(meta) and len(meta) <= 155, f"{len(meta)} chars"), ("title unique vs H1", not h1 or title.casefold() != h1.casefold(), "different" if not h1 or title.casefold() != h1.casefold() else "same as H1")]
    rows = [{"check": name, "ok": ok if not error else None, "message": error or message} for name, ok, message in checks]
    rows.append({"check": "verdict", "ok": all(ok for _, ok, _ in checks) if not error else None, "message": "VALID" if not error and all(ok for _, ok, _ in checks) else "INVALID" if not error else error})
    return rows


def A(name: str, required: bool = True, default: str | None = None) -> ArgSpec:
    return ArgSpec(name, required, default, name.replace("_", " ").capitalize() + ".")


register(ToolSpec("http_status_bulk", http_status_bulk, "Check HTTP status and latency in bulk.", "checkers", [A("urls")], "table"))
register(ToolSpec("redirect_chain", redirect_chain, "Trace a redirect chain and detect loops.", "checkers", [A("url")], "table"))
register(ToolSpec("robots_checker", robots_checker, "Check robots.txt access for a user agent.", "checkers", [A("url"), A("user_agent", False, "googlebot")], "table"))
register(ToolSpec("sitemap_validator", sitemap_validator, "Validate sitemap XML and locations.", "checkers", [A("url")], "table"))
register(ToolSpec("canonical_checker", canonical_checker, "Check canonical tags in bulk.", "checkers", [A("urls")], "table"))
register(ToolSpec("hreflang_checker", hreflang_checker, "Check hreflang tags and reciprocity.", "checkers", [A("urls")], "table"))
register(ToolSpec("schema_validator", schema_validator, "Validate JSON-LD blocks on a page.", "checkers", [A("url")], "table"))
register(ToolSpec("viewport_checker", viewport_checker, "Check responsive viewport metadata.", "checkers", [A("urls")], "table"))
register(ToolSpec("og_validator", og_validator, "Validate Open Graph and Twitter metadata.", "checkers", [A("urls")], "table"))
register(ToolSpec("mixed_content", mixed_content, "Find insecure resources on an HTTPS page.", "checkers", [A("url")], "table"))
register(ToolSpec("url_syntax", url_syntax, "Validate and normalize URL syntax.", "checkers", [A("urls")], "table"))
register(ToolSpec("indexation_checker", indexation_checker, "Compare URLs with an indexation export.", "checkers", [A("indexed"), A("urls")], "table"))
register(ToolSpec("hreflang_reciprocity", hreflang_reciprocity, "Check multilingual hreflang return links.", "checkers", [A("urls")], "table"))
register(ToolSpec("title_meta_validator", title_meta_validator, "Validate one title and meta description.", "checkers", [A("url", False, ""), A("title", False, ""), A("meta", False, "")], "table"))
