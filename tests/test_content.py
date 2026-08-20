import httpx

from seotoolbox import content
from seotoolbox.models import SerpResult


def test_keyword_matching_ignores_case_and_accents():
    assert content.keyword_in_text("plombier à Paris", "PLOMBIER A PARIS disponible")


def test_serp_terms_counts_repeated_ngrams(monkeypatch):
    monkeypatch.setattr(content.serp, "live", lambda *args: [
        SerpResult(title="Plombier Paris urgence", description="Plombier Paris devis"),
        SerpResult(title="Meilleur plombier Paris", description="Plombier Paris urgence")])
    terms = content.serp_terms("plombier", "FR")
    assert terms[0].term == "plombier paris" and terms[0].frequency == 4


def test_content_score_uses_real_html(monkeypatch):
    body = "plombier paris " + "mot " * 300
    html = f"<html><head><title>Plombier Paris</title><meta name='description' content='D'><link rel='canonical' href='/p'></head><body><h1>plombier paris</h1>{body}</body></html>"
    response = httpx.Response(200, text=html, headers={"content-type": "text/html"}, request=httpx.Request("GET", "https://x/p"))
    monkeypatch.setattr(content.httpx, "get", lambda *args, **kwargs: response)
    assert content.content_score("https://x/p", "plombier paris").score == 100
