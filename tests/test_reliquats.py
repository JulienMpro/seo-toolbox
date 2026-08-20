"""Mocked, zero-network tests for remaining catalogue tools."""

import httpx

from seotoolbox.models import CruxMetric, KeywordIdea, SerpResult
from seotoolbox.tools import reliquats


HTML = "<html><h2>Choose a plumber</h2><p>plumber price advice and service</p><img src='x'></html>"


def _mock_fetch(_url):
    return reliquats.BeautifulSoup(HTML, "html.parser"), None


def test_content_fetch_tools(monkeypatch):
    monkeypatch.setattr(reliquats.serp, "live", lambda *args, **kwargs: [SerpResult(1, "https://a.test", "a.test", "Best plumber")])
    monkeypatch.setattr(reliquats, "paa_extractor", lambda *args: [])
    monkeypatch.setattr(reliquats, "_fetch", _mock_fetch)
    target = reliquats.content_length_target("plumber")
    assert target[-1]["rank"] == "TARGET" and target[-1]["words"] > 0
    assert reliquats.content_length("https://a.test")[0]["h2"] == 1
    assert reliquats.tfidf_analysis("plumber", "my service")[0]["term"]
    assert "Best plumber" in reliquats.content_brief("plumber")


def test_keyword_and_rank_tools(monkeypatch):
    monkeypatch.setattr(reliquats.keywords, "ideas", lambda *args: [KeywordIdea("seed long", volume=20)])
    monkeypatch.setattr(reliquats.keywords, "suggestions", lambda *args: [KeywordIdea("seed longer", volume=10)])
    assert len(reliquats.keyword_expansion("seed")) == 2
    monkeypatch.setattr(reliquats, "paa_extractor", lambda *args: [{"question": "How?", "snippet": None}])
    assert reliquats.faq_generator("plumbing")[0]["source"] == "PAA"
    monkeypatch.setattr(reliquats.serp, "live", lambda *args: [
        {"url": "https://example.com/a", "domain": "example.com", "rank_absolute": 3},
        {"url": "https://example.com/b", "domain": "example.com", "rank_absolute": 5},
    ])
    assert reliquats.cannibalization("example.com", "x")[0]["rank"] == 3


def test_lighthouse(monkeypatch):
    monkeypatch.setattr(reliquats.crux, "page_speed", lambda *args: CruxMetric("https://a", "good", {"percentile": 1000, "category": "good"}, None, None, 92))
    rows = reliquats.lighthouse_cwv("https://a")
    assert rows[0]["value"] == 92 and rows[1]["status"] == "good"


def test_lighthouse_reports_http_failure_without_crashing(monkeypatch):
    request = httpx.Request("GET", "https://www.googleapis.com/pagespeedonline/v5/runPagespeed")
    response = httpx.Response(429, request=request)
    monkeypatch.setattr(
        reliquats.crux,
        "page_speed",
        lambda *args: (_ for _ in ()).throw(
            httpx.HTTPStatusError("rate limited", request=request, response=response)
        ),
    )

    assert reliquats.lighthouse_cwv("https://a") == [{
        "metric": "Lighthouse performance",
        "value": None,
        "status": "unavailable: rate limited",
    }]
