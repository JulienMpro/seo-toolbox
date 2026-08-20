import httpx

from seotoolbox.audit import analyze, crawl_site, robots_allows
from seotoolbox.models import CrawlResult


def response(url, status=200, text="", headers=None):
    return httpx.Response(status, text=text, headers=headers or {}, request=httpx.Request("GET", url))


def test_robots_allows_star_disallow():
    robots = "User-agent: *\nDisallow: /private\n"
    assert not robots_allows("https://example.com/private/a", robots)
    assert robots_allows("https://example.com/public", robots)


def test_crawl_uses_sitemap_and_extracts_html(monkeypatch):
    def fake_get(url, **kwargs):
        if url.endswith("robots.txt"):
            return response(url, text="Sitemap: https://example.com/map.xml")
        if url.endswith("map.xml"):
            return response(url, text="<urlset><url><loc>https://example.com/a</loc></url></urlset>")
        return response(url, text="<html><head><title>A</title><meta name='description' content='D'><link rel='canonical' href='/a'></head><body><h1>H</h1></body></html>", headers={"content-type": "text/html"})
    monkeypatch.setattr("seotoolbox.audit.httpx.get", fake_get)
    results = crawl_site("https://example.com", max_pages=5)
    assert len(results) == 1
    assert results[0].title == "A"
    assert results[0].canonical == "https://example.com/a"


def test_analyze_detects_errors_duplicates_and_on_page_issues():
    results = [
        CrawlResult("https://example.com/a", 200, title="Same", meta_description="D", h1="H", content_length=10, content_type="text/html"),
        CrawlResult("https://example.com/b", 200, title="Same", meta_description="D", h1="H", canonical="https://example.com/b", noindex=True, content_length=20, content_type="text/html"),
        CrawlResult("https://example.com/c", 500),
        CrawlResult("https://example.com/d", None),
        CrawlResult("https://example.com/e", 404),
    ]
    report = analyze(results)
    types = [issue.type for issue in report.issues]
    assert "duplicate_title" in types
    assert "missing_canonical" in types
    assert "noindex" in types
    assert types.count("error") == 3
    assert report.stats["avg_content_length"] == 15
