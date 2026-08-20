"""QA coverage for every analyzer and calculator in the assigned batch."""

from dataclasses import dataclass
import inspect

from bs4 import BeautifulSoup
import pytest

from seotoolbox.tools import REGISTRY
from seotoolbox.tools import analyzers as a
from seotoolbox.tools import business_calc as b
from seotoolbox.tools import calculators as c
from seotoolbox.tools import onpage_extra as o
from seotoolbox.tools import refonte as r
from seotoolbox.tools import reliquats as q


ANALYZERS = {
    "cannibalization", "co_occurrence", "content_length", "entity_extractor",
    "heading_checker", "internal_anchors", "internal_link_score", "keyword_density",
    "keyword_extractor", "keyword_rank_change", "merge_candidates", "ngrams",
    "page_similarity", "readability", "tfidf_analysis", "thin_content",
    "title_meta_analyzer",
}
CALCULATORS = {
    "ads_equivalent", "backlink_value", "cac_ltv", "content_cost",
    "content_length_target", "conversion_rate", "crawl_time", "ctr_curve",
    "eeat_score", "implicit_cpc", "opportunity_cost", "organic_revenue",
    "position_value", "roi_seo", "sitemap_split", "time_to_rank",
    "traffic_projection",
}


def soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def test_registry_signatures_and_table_contracts():
    for name in ANALYZERS | CALCULATORS:
        spec = REGISTRY[name]
        assert list(inspect.signature(spec.fn).parameters) == [arg.name for arg in spec.args]
        assert spec.returns in {"str", "table"}


def test_local_text_analyzers_fr_en_and_empty():
    assert a.keyword_density("Été à Paris.\n\nÉté indien.", "été")[-1]["occurrences"] == 2
    assert a.keyword_density("", "SEO") == [{"paragraph": "TOTAL", "occurrences": 0, "density_pct": 0.0}]
    assert a.co_occurrence("SEO local à Lyon. SEO local utile.", "seo")[0] == {"term": "local", "frequency": 2}
    assert a.co_occurrence("Une baseologie locale.", "seo") == []
    assert a.ngrams("café bio café bio", 2, 1)[0]["frequency"] == 2
    assert a.readability("Ce texte est simple. Il est clair.", "fr")[0]["verdict"] in {"très facile", "facile", "moyen", "difficile", "très difficile"}
    assert a.readability("This sentence is clear. It is short.", "en")[0]["verdict"] in {"very easy", "easy", "medium", "difficult", "very difficult"}
    entities = a.entity_extractor("Jean Dupont vit à Paris. Jane Doe works in New York. ACME ACME.")
    assert {row["entity"] for row in entities if row["type"] == "Location"} >= {"Paris", "New York"}
    thin = a.thin_content("Un café.", text=True)
    assert thin[0]["score"] == 100 and thin[2]["points"] is None
    assert o.keyword_extractor("café durable café durable", 5)[0]["keyword"] == "café durable"


def test_local_page_analyzers_with_mocked_fetch(monkeypatch):
    pages = {
        "https://ex.test/": "<title>Café durable</title><meta name='description' content='Conseils'><h1>Café</h1><h3>Saut</h3><p>café durable</p><a href='/en'>English guide</a>",
        "https://ex.test/en": "<title>Café durable</title><h1>Guide</h1><p>cafe sustainable</p><a href='/'>Accueil</a>",
    }
    monkeypatch.setattr(a, "_fetch", lambda url: (soup(pages[url]), None))
    urls = "https://ex.test/\nhttps://ex.test/en"
    assert isinstance(a.page_similarity(urls), list)
    assert "jump" in a.heading_checker("https://ex.test/")[0]["errors"]
    assert a.title_meta_analyzer(urls)[0]["duplicate"] is True
    assert a.internal_anchors(urls)[0]["kind"] == "anchor"
    assert a.internal_link_score(urls)[1]["depth"] == 1
    monkeypatch.setattr(o.analyzers, "page_similarity", lambda value: [{"pair": "a ↔ b", "similarity_pct": 81.0, "error": None}])
    assert o.merge_candidates("a\nb")[0]["suggestion"] == "merge"


def test_unknown_page_states_are_not_false_claims(monkeypatch):
    monkeypatch.setattr(a, "_fetch", lambda url: (soup(""), None))
    row = a.page_similarity("https://a.test\nhttps://b.test")[0]
    assert row["similarity_pct"] is None and row["error"] == "no visible text"
    monkeypatch.setattr(a, "_fetch", lambda url: (None, "timeout"))
    meta = a.title_meta_analyzer("https://a.test")[0]
    assert meta["title_ok"] is None and meta["meta_ok"] is None and meta["duplicate"] is None


def test_rank_change_fr_en_and_empty():
    rows = r.keyword_rank_change("keyword,position\ncafé,8\nseo,3", "keyword,position\ncafé,4\nseo,3")
    assert rows[0]["keyword"] == "café" and rows[0]["delta"] == 4
    assert r.keyword_rank_change("keyword,position\n", "keyword,position\n")[-1]["keyword"] == "TOTAL"


@dataclass
class Rank:
    url: str
    position: int


def test_reliquat_analyzers_and_target_are_fully_mocked(monkeypatch):
    html = "<html><p>Café durable et local.</p><h2>Guide</h2><img src='x'></html>"
    monkeypatch.setattr(q, "_fetch", lambda url: (soup(html), None) if url.startswith("http") else (None, "invalid URL"))
    monkeypatch.setattr(q.serp, "live", lambda keyword, country, limit: [{"rank": 1, "url": "https://ex.test/"}])
    monkeypatch.setattr(q.ranktracker, "domain_rank", lambda *args: [Rank("https://ex.test/a", 4), Rank("https://ex.test/b", 9)])
    assert q.content_length("https://ex.test/")[0] == {"url": "https://ex.test/", "words": 5, "paragraphs": 1, "images": 1, "h2": 1, "error": None}
    assert q.content_length_target("café", "FR")[-1]["words"] == 5
    assert q.tfidf_analysis("café", "Le café est local", "FR")[0]["term"]
    assert q.cannibalization("ex.test", "café\ncoffee", "FR")[0]["risk"] == "high"


def test_fetch_failure_is_honest(monkeypatch):
    monkeypatch.setattr(q, "_fetch", lambda url: (None, "timeout"))
    monkeypatch.setattr(q.serp, "live", lambda *args: [])
    row = q.content_length("https://ex.test/")[0]
    assert row["words"] is None and row["error"] == "timeout"
    assert q.content_length_target("coffee", "US") == [{"rank": "TARGET", "url": None, "words": None}]


def test_all_calculators_realistic_zero_and_boundaries():
    assert isinstance(c.roi_seo(1000, 80, 35, 2, 2, 500, 3), list)
    assert c.traffic_projection(0, 10)[0]["estimated_traffic"] == 0
    assert "€" in c.position_value(1000, 1.5, 3, 8)
    assert isinstance(c.ctr_curve(1, "mobile"), list)
    assert "€0.00" in c.ads_equivalent(0, 2)
    assert "0.00%" in c.conversion_rate(10, 0)
    assert "€0.00" in c.implicit_cpc(0, 10)
    assert "infinite" in c.cac_ltv(0, 10, 500)
    assert "0.00 s" in c.crawl_time(0, 2)
    assert "Sitemap files: 0" in c.sitemap_split(0)
    assert "0/100" in c.eeat_score()
    assert "€0.00" in c.backlink_value(0, 0, 0)
    assert "€0.00" in c.content_cost(0, 0, 1)
    assert isinstance(b.time_to_rank(50, 30, 24), list)
    assert b.opportunity_cost(0, 0, 1, 0)[-1]["value"] == 0
    assert b.organic_revenue(0, 0, 0, -100)[0]["value"] == 0


@pytest.mark.parametrize("call", [
    lambda: c.traffic_projection(1, 1, growth=-101),
    lambda: c.roi_seo(1, 1, 1, 1, growth=-101),
    lambda: c.position_value(-1, 1, 1, 2),
    lambda: c.position_value(1, 1, -1, 2),
    lambda: c.ads_equivalent(-1, 1),
    lambda: c.implicit_cpc(-1, 1),
    lambda: c.cac_ltv(-1, 1, 1),
    lambda: c.crawl_time(-1, 1),
    lambda: c.backlink_value(1, -1, 1),
    lambda: c.content_cost(1, 1, 0),
    lambda: b.time_to_rank(-1, 1, 1),
    lambda: b.opportunity_cost(-1, 1, 1),
    lambda: b.opportunity_cost(1, 1, 0),
    lambda: b.organic_revenue(1, 1, 1, -101),
    lambda: b.organic_revenue(1, 101, 1),
])
def test_negative_values_are_rejected(call):
    with pytest.raises(ValueError):
        call()
