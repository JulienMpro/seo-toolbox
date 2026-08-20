"""Tests for local technical SEO checkers."""

import httpx
from bs4 import BeautifulSoup

from seotoolbox.tools import checkers


class Response:
    def __init__(self, text="", status=200, headers=None, url="https://x.test/"):
        self.text, self.status_code, self.headers = text, status, headers or {}
        self.url = httpx.URL(url)

    def raise_for_status(self):
        if self.status_code >= 400:
            request = httpx.Request("GET", self.url)
            raise httpx.HTTPStatusError("failure", request=request, response=httpx.Response(self.status_code, request=request))


def test_url_and_indexation_checkers():
    syntax = checkers.url_syntax("HTTPS://Example.COM/a?b=2&a=1\nwrong")
    assert syntax[0]["normalized"] == "https://example.com/a/?a=1&b=2"
    assert syntax[1]["valid"] is False
    indexed = checkers.indexation_checker("https://x.test/a", "https://x.test/a\nhttps://x.test/b")
    assert [row["status"] for row in indexed] == ["indexed", "not indexed"]


def test_html_checkers(monkeypatch):
    html = """<title>Hello</title><meta name="description" content="Desc">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="canonical" href="/"><link rel="alternate" hreflang="fr" href="/">
    <meta property="og:title" content="Hello"><meta property="og:description" content="Desc">
    <meta property="og:image" content="image.jpg"><meta name="twitter:card" content="summary">
    <h1>Different</h1><img src="http://bad.test/i.png">
    <script type="application/ld+json">{"@context":"https://schema.org","@type":"Organization","name":"X"}</script>"""
    monkeypatch.setattr(checkers.httpx, "get", lambda url, **kwargs: Response(html, url=url))
    assert checkers.canonical_checker("https://x.test/")[0]["self_canonical"] is True
    assert checkers.viewport_checker("https://x.test/")[0]["responsive_hint"] is True
    assert checkers.og_validator("https://x.test/")[0]["twitter_card"] is True
    assert checkers.mixed_content("https://x.test/")[0]["resource"].startswith("http://")
    assert checkers.schema_validator("https://x.test/")[0]["valid"] is True
    assert checkers.title_meta_validator(url="https://x.test/")[-1]["message"] == "VALID"


def test_hreflang_checker_normalizes_www_scheme_and_trailing_slash(monkeypatch):
    pages = {
        "http://example.test/fr/": '<link rel="alternate" hreflang="en" href="https://www.example.test/en">',
        "https://www.example.test/en": '<link rel="alternate" hreflang="fr" href="https://example.test/fr">',
    }
    monkeypatch.setattr(
        checkers,
        "_page",
        lambda url: (BeautifulSoup(pages[url], "html.parser"), None),
    )

    rows = checkers.hreflang_checker("http://example.test/fr/\nhttps://www.example.test/en")

    assert [row["reciprocal"] for row in rows] == [True, True]


def test_hreflang_checker_reports_unknown_and_false_reciprocity(monkeypatch):
    pages = {
        "https://example.test/fr": '<link rel="alternate" hreflang="en" href="https://example.test/en">',
        "https://example.test/en": '<link rel="alternate" hreflang="de" href="https://example.test/de">',
    }
    monkeypatch.setattr(
        checkers,
        "_page",
        lambda url: (BeautifulSoup(pages[url], "html.parser"), None),
    )

    rows = checkers.hreflang_checker("https://example.test/fr\nhttps://example.test/en")

    assert rows[0]["reciprocal"] is False
    assert rows[1]["reciprocal"] is None


def test_hreflang_checker_preserves_page_error(monkeypatch):
    monkeypatch.setattr(checkers, "_page", lambda url: (None, "connection failed"))

    assert checkers.hreflang_checker("https://example.test/fr") == [{
        "url": "https://example.test/fr",
        "lang": None,
        "target": None,
        "reciprocal": None,
        "error": "connection failed",
    }]


def test_redirect_sitemap_status_and_robots(monkeypatch):
    calls = []
    def get(url, **kwargs):
        calls.append(url)
        if url.endswith("robots.txt"):
            return Response("User-agent: googlebot\nDisallow: /private", url=url)
        if url.endswith("sitemap.xml"):
            return Response("<urlset><url><loc>https://x.test/</loc></url></urlset>", url=url)
        if url.endswith("/start"):
            return Response(status=301, headers={"location": "/final"}, url=url)
        return Response(url=url)
    monkeypatch.setattr(checkers.httpx, "get", get)
    assert checkers.http_status_bulk("https://x.test/")[0]["status"] == 200
    assert checkers.redirect_chain("https://x.test/start")[-1]["note"] == "final"
    assert checkers.sitemap_validator("https://x.test/sitemap.xml")[0]["valid"] is True
    assert checkers.robots_checker("https://x.test/private")[0]["allowed"] is False
