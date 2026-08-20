"""Mocked, zero-network tests for remaining catalogue tools."""

from seotoolbox.models import CruxMetric, KeywordIdea, RankPosition, SerpResult
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
    monkeypatch.setattr(reliquats.ranktracker, "domain_rank", lambda *args: [RankPosition("x", 3, "https://a"), RankPosition("x", 5, "https://b")])
    assert reliquats.cannibalization("example.com", "x")[0]["risk"] == "high"


def test_lighthouse(monkeypatch):
    monkeypatch.setattr(reliquats.crux, "page_speed", lambda *args: CruxMetric("https://a", "good", {"percentile": 1000, "category": "good"}, None, None, 92))
    rows = reliquats.lighthouse_cwv("https://a")
    assert rows[0]["value"] == 92 and rows[1]["status"] == "good"
