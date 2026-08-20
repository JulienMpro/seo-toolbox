"""Local prospecting helpers that only fetch public web pages."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from urllib.parse import urljoin, urlparse

import httpx

from .. import audit, serp
from . import ArgSpec, ToolSpec, register
from .misc import extract_emails

HEADERS = {"User-Agent": "seotoolbox/0.3"}


def _urls(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def broken_link_building(domain: str, keyword: str = "") -> list[dict]:
    """Check at most 100 URLs from a domain sitemap and suggest relevant SERP pages."""
    base = domain if urlparse(domain).scheme else "https://" + domain
    sitemap_url = urljoin(base, "/sitemap.xml")
    try:
        response = httpx.get(sitemap_url, timeout=15, follow_redirects=True, headers=HEADERS)
        if response.status_code >= 400:
            return [{"url_404": "N/D", "status": "N/D", "similar_page": "No sitemap available"}]
        urls, is_index = audit._sitemap_urls(response.text)
        if is_index:
            nested = []
            for location in urls[:10]:
                child = httpx.get(location, timeout=15, follow_redirects=True, headers=HEADERS)
                if child.status_code < 400:
                    nested.extend(audit._sitemap_urls(child.text)[0])
            urls = nested
        if not urls:
            return [{"url_404": "N/D", "status": "N/D", "similar_page": "No sitemap available"}]
    except httpx.HTTPError:
        return [{"url_404": "N/D", "status": "N/D", "similar_page": "No sitemap available"}]
    suggestions = []
    if keyword:
        for item in serp.live(keyword, "FR", 10):
            row = asdict(item) if is_dataclass(item) else item
            if row.get("url"):
                suggestions.append(row["url"])
    rows = []
    for url in urls[:100]:
        try:
            status = httpx.get(url, timeout=15, follow_redirects=False, headers=HEADERS).status_code
        except httpx.HTTPError as exc:
            status = None
            rows.append({"url_404": url, "status": None, "similar_page": f"check failed: {exc}"})
        if status == 404:
            rows.append({"url_404": url, "status": 404, "similar_page": suggestions[0] if suggestions else "N/D"})
    return rows


def prospect_emails(urls: str) -> list[dict]:
    """Extract public emails from at most ten pages, deduplicated by email domain; never send mail."""
    values = _urls(urls)
    if len(values) > 10:
        raise ValueError("prospect_emails accepts at most 10 URLs")
    rows, domains = [], set()
    for url in values:
        try:
            response = httpx.get(url, timeout=15, follow_redirects=True, headers=HEADERS)
            response.raise_for_status()
            emails = _urls(extract_emails(response.text))
        except httpx.HTTPError as exc:
            rows.append({"url": url, "email": None, "email_domain": None, "error": str(exc)})
            continue
        for email in emails:
            domain = email.rsplit("@", 1)[-1].casefold()
            if domain not in domains:
                domains.add(domain)
                rows.append({"url": url, "email": email, "email_domain": domain, "error": None})
    return rows


def A(name: str, required: bool = True, default: str | None = None) -> ArgSpec:
    return ArgSpec(name, required, default, name.replace("_", " ").capitalize() + ".")


register(ToolSpec("broken_link_building", broken_link_building, "Find 404s in a competitor sitemap (maximum 100 URLs).", "links", [A("domain"), A("keyword", False, "")], "table"))
register(ToolSpec("prospect_emails", prospect_emails, "Extract public emails from prospect pages (maximum 10 URLs).", "links", [A("urls")], "table"))
