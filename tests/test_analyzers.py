"""Tests for local on-page analyzers."""

import httpx

from seotoolbox.tools import analyzers


class Response:
    def __init__(self, text: str, url: str = "https://x.test/"):
        self.text = text
        self.url = httpx.URL(url)
        self.status_code = 200

    def raise_for_status(self):
        return None


def test_text_analyzers():
    density = analyzers.keyword_density("SEO local SEO.\n\nSEO technique.", "seo")
    assert density[-1] == {"paragraph": "TOTAL", "occurrences": 3, "density_pct": 60.0}
    assert analyzers.ngrams("seo local seo local", 2, 1) == [{"n_gram": "seo local", "frequency": 2}]
    assert analyzers.co_occurrence("SEO local à Paris. Autre phrase.", "seo")[0]["term"] == "local"
    assert analyzers.readability("This is short. It is easy.", "en")[0]["metric"] == "Flesch Reading Ease"


def test_entities_and_thin_content():
    entities = analyzers.entity_extractor("Jean Dupont vit à Paris. ACME vend ACME. Contact a@b.fr le 2026-08-20.")
    assert {row["type"] for row in entities} >= {"Person", "Location", "Brand", "Email", "Date"}
    assert analyzers.thin_content("Quelques mots.", text=True)[0]["score"] == 100


def test_page_analyzers(monkeypatch):
    pages = {
        "https://x.test/": "<title>Accueil</title><meta name='description' content='Description'><h1>Accueil</h1><h3>Saut</h3><a href='/b'>Page B</a>",
        "https://x.test/b": "<title>Accueil</title><h1>Page B</h1><a href='/'>Accueil</a>",
    }
    monkeypatch.setattr(analyzers.httpx, "get", lambda url, **kwargs: Response(pages[url], url))
    urls = "https://x.test/\nhttps://x.test/b"
    assert analyzers.page_similarity(urls)[0]["similarity_pct"] is not None
    assert "jump" in analyzers.heading_checker("https://x.test/")[0]["errors"]
    assert analyzers.title_meta_analyzer(urls)[0]["duplicate"] is True
    assert any(row["kind"] == "anchor" for row in analyzers.internal_anchors(urls))
    scores = analyzers.internal_link_score(urls)
    assert scores[1]["depth"] == 1 and scores[0]["in"] == 1
