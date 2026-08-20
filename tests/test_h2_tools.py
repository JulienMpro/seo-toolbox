"""Zero-network tests for the H2 local consulting tools."""

from pathlib import Path

from seotoolbox.models import SerpFeatures, SerpResult
from seotoolbox.tools import business_calc, ia_tools, netlinking_extra, onpage_extra, refonte


def test_migration_and_rank_comparisons():
    rendered = refonte.redirect_map_generator("https://x.fr/vieux-produit", "https://x.fr/produit")
    assert "approximate" in rendered and "Redirect 301" in rendered
    assert "https://x.fr/new" in refonte.redirect_map_generator("https://x.fr/old|https://x.fr/new")
    diff = refonte.sitemap_diff("https://x/a\nhttps://x/b", "https://x/b\nhttps://x/c")
    assert diff[-1]["url"] == "new=1, removed=1, unchanged=1"
    ranks = refonte.keyword_rank_change("keyword,position\na,5\nb,2", "keyword,position\na,2\nc,3")
    assert ranks[0]["keyword"] == "a" and ranks[0]["delta"] == 3


def test_serp_snapshot(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(refonte.serp, "live", lambda *a: [SerpResult(1, "https://a", "a", "Title", "Desc")])
    monkeypatch.setattr(refonte.serp, "features", lambda *a: SerpFeatures("kw", ["images"]))
    target = refonte.serp_snapshot("kw", output=str(tmp_path))
    assert Path(target).exists() and "Title" in Path(target).read_text()


def test_business_calculators_and_prompts():
    assert business_calc.time_to_rank(40, 30, 24)[-1]["value"] == 4.7
    assert business_calc.opportunity_cost(1000, 2, 5, 30)[-1]["value"] == 440
    assert business_calc.organic_revenue(1000, 2, 100, 10)[-1]["value"] == 2200
    assert len(ia_tools.prompt_generator("geo", "plomberie Paris")) == 3


def test_onpage_extractors(monkeypatch):
    html = "<title>T</title><meta name='description' content='D'><link rel='canonical' href='/fr'><link rel='alternate' hreflang='fr' href='/fr'><meta property='og:title' content='OG'><h1>One</h1><h2>Two</h2><p>plombier paris plombier paris</p>"
    soup = onpage_extra.BeautifulSoup(html, "html.parser")
    monkeypatch.setattr(onpage_extra, "_fetch", lambda url: (soup, None))
    assert onpage_extra.canonical_hreflang_check("https://x/fr")[0]["status"] == "ok"
    assert onpage_extra.meta_raw_extractor("https://x/fr")[0]["value"] == "T"
    assert onpage_extra.keyword_extractor("plombier paris plombier paris", 3)[0]["frequency"] == 2
    monkeypatch.setattr(onpage_extra.analyzers, "page_similarity", lambda urls: [{"pair": "a ↔ b", "similarity_pct": 90, "error": None}])
    assert onpage_extra.merge_candidates("a\nb")[0]["suggestion"] == "merge"


def test_prospect_email_and_broken_links(monkeypatch):
    class Response:
        def __init__(self, text="", status=200): self.text, self.status_code = text, status
        def raise_for_status(self): return None
    monkeypatch.setattr(netlinking_extra.httpx, "get", lambda url, **kw: Response("Contact A@EXAMPLE.COM"))
    assert netlinking_extra.prospect_emails("https://x")[0]["email_domain"] == "example.com"
    monkeypatch.setattr(netlinking_extra.httpx, "get", lambda url, **kw: Response("<urlset><url><loc>https://x/missing</loc></url></urlset>") if url.endswith("sitemap.xml") else Response(status=404))
    assert netlinking_extra.broken_link_building("x")[0]["status"] == 404
