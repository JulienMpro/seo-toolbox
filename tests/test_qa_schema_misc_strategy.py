"""Focused zero-network QA coverage for the schema, misc, and strategy batch."""

from __future__ import annotations

import inspect
import json
from types import SimpleNamespace

import pytest

from seotoolbox.models import BacklinkSummary, IntentInfo, KeywordIdea, KeywordOverview, KeywordRanked
from seotoolbox.tools import REGISTRY, domain_intel, misc, onpage_extra, schema, strategy


NAMES = """jsonld_article jsonld_breadcrumb jsonld_event jsonld_extract jsonld_faq
jsonld_howto jsonld_jobposting jsonld_localbusiness jsonld_organization jsonld_product
jsonld_review jsonld_validate check_http count_text domain_compare extract_emails extract_urls
instant_audit lorem_seo meta_raw_extractor technology_detection text_diff tz_convert whois_lite
competitor_benchmark content_audit difficulty_score editorial_calendar effort_impact intent_mix
keyword_prioritization semantic_silo seo_projection topic_clusters traffic_potential""".split()


class FakeClient:
    def __init__(self, results):
        self.results = results
        self.calls = []

    def get_result(self, path, payload):
        self.calls.append((path, payload))
        return self.results


def test_all_35_tools_are_registered_with_coherent_signatures():
    assert len(NAMES) == 35
    for name in NAMES:
        spec = REGISTRY[name]
        parameters = inspect.signature(spec.fn).parameters
        assert [arg.name for arg in spec.args] == [key for key in parameters if key != "client"]
        assert spec.returns in {"str", "table"}


def test_all_jsonld_generators_parse_and_preserve_french_content():
    outputs = [
        schema.jsonld_article("Guide de l'été", "Élodie", "2026-08-20"),
        schema.jsonld_breadcrumb("Accueil > Événements"),
        schema.jsonld_event("Conférence SEO", "2026-09-01", description="À Paris"),
        schema.jsonld_faq("Quel délai ?|Deux jours"),
        schema.jsonld_howto("Faire du café", "Moudre les grains\nVerser l'eau"),
        schema.jsonld_jobposting("Rédacteur SEO", "Écrire en français", "Société Exemple"),
        schema.jsonld_localbusiness("Café Été", "10 rue de l'Église, Paris", phone="+33102030405"),
        schema.jsonld_organization("Société Française", same_as="https://example.fr"),
        schema.jsonld_product("Thé vert", description="Cultivé en France", price=12, rating_value=4.5, review_count=8),
        schema.jsonld_review("Thé vert", "André", 5, "Très bon"),
    ]
    expected_types = {"Article", "BreadcrumbList", "Event", "FAQPage", "HowTo", "JobPosting", "LocalBusiness", "Organization", "Product", "Review"}
    parsed = [json.loads(value) for value in outputs]
    assert {value["@type"] for value in parsed} == expected_types
    assert all(value["@context"] == "https://schema.org" for value in parsed)
    assert "Élodie" in outputs[0] and "Écrire en français" in outputs[5]
    assert all(schema.jsonld_validate(value)[-1]["message"] == "VALID" for value in outputs)


def test_product_rejects_incomplete_or_invalid_aggregate_rating():
    with pytest.raises(ValueError, match="provided together"):
        schema.jsonld_product("Produit", rating_value=4.5)
    with pytest.raises(ValueError, match="between 0 and 5"):
        schema.jsonld_product("Produit", rating_value=6, review_count=1)
    with pytest.raises(ValueError, match="non-negative"):
        schema.jsonld_product("Produit", price=-1)
    with pytest.raises(ValueError, match="between 1 and 5"):
        schema.jsonld_review("Produit", "Alice", 6)
    with pytest.raises(ValueError, match="non-negative"):
        schema.jsonld_event("Événement", "2026-09-01", offers_price=-1)
    with pytest.raises(ValueError, match="non-negative"):
        schema.jsonld_jobposting("SEO", "Description", "Société", salary=-1)


def test_schema_validation_and_full_extraction_are_honest(monkeypatch):
    assert schema.jsonld_validate("not json")[-1]["message"] == "INVALID"

    long_value = json.dumps({"@context": "https://schema.org", "@type": "Article", "headline": "é" * 300})
    html = f'<script type="application/ld+json">{long_value}</script>'
    response = SimpleNamespace(text=html, raise_for_status=lambda: None)
    monkeypatch.setattr(schema.httpx, "get", lambda *args, **kwargs: response)
    row = schema.jsonld_extract("https://example.fr")[0]
    assert row["type"] == "Article" and json.loads(row["jsonld"])["headline"] == "é" * 300
    with pytest.raises(ValueError, match="absolute"):
        schema.jsonld_extract("example.fr")


def test_local_misc_tools_with_french_english_and_edges():
    assert misc.extract_emails("Écrire à a@example.fr, then b@example.com.") == "a@example.fr\nb@example.com"
    assert misc.extract_urls("Voir https://example.fr/été, then https://example.com/x.") == "https://example.com/x\nhttps://example.fr/été"
    assert "words: 4" in misc.count_text("audit SEO d'été\nEnglish")
    assert "+nouveau" in misc.text_diff("ancien", "nouveau")
    assert "left" in misc.text_diff("gauche", "left", "side-by-side")
    assert len(misc.lorem_seo(2, 7, "référencement,SEO").split("\n\n")) == 2
    with pytest.raises(ValueError):
        misc.lorem_seo(0)
    assert misc.tz_convert("2026-08-20T12:00", "UTC", "Europe/Paris").startswith("2026-08-20T14:00")
    with pytest.raises(ValueError, match="unknown timezone"):
        misc.tz_convert("2026-08-20T12:00", "UTC", "Mars/Olympus")


def test_http_misc_tools_are_fully_mocked(monkeypatch):
    response = SimpleNamespace(url="https://example.fr/", status_code=200, headers={"content-type": "text/html"})
    monkeypatch.setattr(misc.httpx, "get", lambda *args, **kwargs: response)
    monkeypatch.setattr(misc.socket, "gethostbyname", lambda host: "192.0.2.10")
    assert misc.check_http("https://example.fr")[0]["ip"] == "192.0.2.10"
    with pytest.raises(ValueError):
        misc.check_http("ftp://example.fr")

    soup = onpage_extra.BeautifulSoup("<title>Été</title><meta name='description' content='Page française'><h1>Bonjour</h1>", "html.parser")
    monkeypatch.setattr(onpage_extra, "_fetch", lambda url: (soup, None))
    fields = {row["element"]: row["value"] for row in onpage_extra.meta_raw_extractor("https://example.fr")}
    assert fields["title"] == "Été" and fields["meta description"] == "Page française"


def test_dataforseo_misc_payloads_and_verified_mappings(monkeypatch):
    whois_client = FakeClient([{"registrar": "AFNIC", "created_datetime": "2020-01-01", "name_servers": ["ns1"]}])
    assert domain_intel.whois_lite("example.fr", whois_client)[0]["value"] == "AFNIC"
    assert whois_client.calls == [("domain_analytics/whois/overview/live", {"domain": "example.fr"})]

    tech_client = FakeClient([{"technologies": [{"name": "CMS", "categories": ["WordPress"]}]}])
    assert domain_intel.technology_detection("example.fr", tech_client) == [{"group": "CMS", "technologies": ["WordPress"]}]
    assert tech_client.calls[0] == ("domain_analytics/technologies/domain_technologies/live", {"target": "example.fr"})

    audit_client = FakeClient([{"page_meta": {"title": "Accueil", "description": "Bonjour"}, "status_code": 200}])
    audit = domain_intel.instant_audit("https://example.fr", audit_client)
    assert audit[0]["value"] == "Accueil" and audit[-1]["value"] == 200
    assert audit_client.calls == [("on_page/instant_pages", {"url": "https://example.fr"})]

    monkeypatch.setattr(domain_intel.backlinks, "bulk_ranks", lambda targets, client: [{"target": targets[0], "rank": 80}])
    monkeypatch.setattr(domain_intel.backlinks, "summary", lambda domain, client: BacklinkSummary(100, 20, 70, 3))
    monkeypatch.setattr(domain_intel.keywords, "keywords_for_site", lambda domain, country, limit, client: [KeywordRanked("référencement", position=4)])
    row = domain_intel.domain_compare("example.fr", "FR", FakeClient([]))[0]
    assert row == {"domain": "example.fr", "rank": 80, "backlinks": 100, "referring_domains": 20, "spam": 3, "keyword_count": 1, "best_position": 4}


def test_strategy_local_calculators_with_real_french_scenarios():
    calendar = strategy.editorial_calendar("audit SEO|P1|article\nréférencement local|P2|guide", 2, "2026-09-01")
    assert "audit SEO" in calendar and "2026-09-01" in calendar
    assert strategy.editorial_calendar("", 2, "2026-09-01") == "N/D"
    assert strategy.seo_projection(1000, 5, 2, 1)[-1]["traffic"] == 1102
    assert "quick win" in strategy.effort_impact("Corriger les titres|1|5\nRefondre le site|5|5")
    assert strategy.content_audit("/fr|10|200|4\n/en|0|300|20\n/zero|0|0|0")[-1]["verdict"] == "remove"
    very_long_inline = "/" + "é" * 5000 + "|0|0|0"
    assert strategy.content_audit(very_long_inline)[0]["verdict"] == "remove"
    assert strategy.semantic_silo("seo\nseo local paris\naudit seo") != "N/D"
    with pytest.raises(ValueError):
        strategy.seo_projection(-1)


def test_strategy_provider_tools_use_french_and_never_invent_missing_metrics(monkeypatch):
    seen = {}

    def overview(words, country):
        seen["country"] = country
        return [KeywordOverview(word, volume=100 if i == 0 else None, cpc=2 if i == 0 else None, difficulty=20 if i == 0 else None) for i, word in enumerate(words)]

    def intent(words, language_name="English"):
        seen["language"] = language_name
        return [IntentInfo(word, "commercial") for word in words]

    monkeypatch.setattr(strategy.keyword_service, "overview", overview)
    monkeypatch.setattr(strategy.keyword_service, "intent", intent)
    monkeypatch.setattr(strategy.keyword_service, "related", lambda seed, country, limit: [KeywordIdea(seed + " guide")])
    prioritized = strategy.keyword_prioritization("audit SEO\nréférencement", "FR")
    assert seen == {"country": "FR", "language": "French"}
    assert prioritized[0]["score"] is not None and prioritized[1]["score"] is None
    assert strategy.difficulty_score("audit SEO", "FR")[0]["level"] == "easy"
    assert strategy.topic_clusters("audit SEO", "FR")[0]["suggested_pillar"]
    assert "commercial" in strategy.intent_mix("audit SEO")
    assert "5.0 visits/month" in strategy.traffic_potential("example.fr", "audit SEO", "FR")

    monkeypatch.setattr(strategy.keyword_service, "overview", lambda words, country: [KeywordOverview(word) for word in words])
    assert "Total potential for example.fr: N/D" in strategy.traffic_potential("example.fr", "mot inconnu", "FR")


def test_competitor_benchmark_maps_verified_backlink_fields(monkeypatch):
    monkeypatch.setattr(strategy.keyword_service, "keywords_for_site", lambda domain, country, limit: [KeywordRanked("seo", position=3)])
    monkeypatch.setattr(strategy.backlinks, "summary", lambda domain: BacklinkSummary(backlinks=120, referring_domains=30, rank=75, spam_score=2))
    row = strategy.competitor_benchmark("example.fr", "FR")[0]
    assert row == {"domain": "example.fr", "ranked_keywords": 1, "average_position": 3.0, "backlinks": 120, "referring_domains": 30, "rank": 75}
    monkeypatch.setattr(strategy.keyword_service, "keywords_for_site", lambda domain, country, limit: [])
    assert strategy.competitor_benchmark("zero.fr", "FR")[0]["ranked_keywords"] == 0
