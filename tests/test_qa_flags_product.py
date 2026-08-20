"""Regression tests for product honesty flags and localization."""

import math

import pytest

from seotoolbox.tools import REGISTRY, business_calc, calculators, generators, reliquats, strategy


def test_cannibalization_uses_live_serp_and_only_emits_multi_url_keywords(monkeypatch):
    calls = []

    def live(keyword, country, limit):
        calls.append((keyword, country, limit))
        if keyword == "multi":
            return [
                {"url": "https://example.com/b", "domain": "example.com", "rank_absolute": 8},
                {"url": "https://other.test/", "domain": "other.test", "rank_absolute": 2},
                {"url": "https://example.com/a", "domain": "example.com", "rank_absolute": 3},
                {"url": "https://example.com/c", "domain": "example.com", "rank_absolute": 12},
            ]
        return [{"url": "https://example.com/only", "domain": "example.com", "rank_absolute": 1}]

    monkeypatch.setattr(reliquats.serp, "live", live)
    assert reliquats.cannibalization("www.example.com", "multi\nsingle", "FR") == [
        {"keyword": "multi", "url": "https://example.com/a", "rank": 3},
        {"keyword": "multi", "url": "https://example.com/b", "rank": 8},
        {"keyword": "multi", "url": "https://example.com/c", "rank": 12},
    ]
    assert calls == [("multi", "FR", 100), ("single", "FR", 100)]


def test_tfidf_uses_normalized_tf_and_smoothed_idf(monkeypatch):
    monkeypatch.setattr(reliquats.serp, "live", lambda *args: [{"url": "https://a.test", "rank": 1}])
    monkeypatch.setattr(reliquats, "_fetch", lambda url: (reliquats.BeautifulSoup("beta gamma", "html.parser"), None))
    rows = reliquats.tfidf_analysis("topic", "alpha alpha beta")
    alpha = next(row for row in rows if row["document"] == "input" and row["term"] == "alpha")
    beta = next(row for row in rows if row["document"] == "input" and row["term"] == "beta")
    assert alpha["tf"] == pytest.approx(2 / 3, abs=1e-6)
    assert alpha["idf"] == pytest.approx(math.log(3), abs=1e-6)
    assert alpha["tfidf"] == pytest.approx(2 / 3 * math.log(3), abs=1e-6)
    assert beta["tf"] == pytest.approx(1 / 3, abs=1e-6)
    assert beta["idf"] == pytest.approx(math.log(2), abs=1e-6)
    assert rows == sorted(rows, key=lambda row: (-row["tfidf"], row["term"], row["document"]))


def test_heuristic_tools_are_explicitly_labeled():
    assert "not an official metric" in REGISTRY["backlink_value"].description
    assert "heuristic estimate" in calculators.backlink_value(50, 100, 1)
    eeat = calculators.eeat_score(author=True)
    assert "not a Google score" in eeat and "author: yes" in eeat and "bio: no" in eeat
    assert "verdict" not in eeat
    rows = business_calc.time_to_rank(50, 30, 24)
    assert all("non-predictive" in row["note"] for row in rows)
    assert "not calibrated data" in REGISTRY["time_to_rank"].description


def test_generators_support_french_and_english_and_expose_language_arg():
    assert "voir plus" in str(generators.anchor_generator("plombier Paris", language="fr"))
    assert "learn more" in str(generators.anchor_generator("London plumber", language="en"))
    assert generators.title_variants("SEO", 1, "fr")[0]["title"].startswith("Pourquoi")
    assert generators.title_variants("SEO", 1, "en")[0]["title"].startswith("Why")
    assert generators.meta_variants("une offre", 1, "fr")[0]["description"].startswith("Découvrez")
    assert generators.meta_variants("an offer", 1, "en")[0]["description"].startswith("Discover")
    for name in ("anchor_generator", "title_variants", "meta_variants"):
        arg = REGISTRY[name].args[-1]
        assert (arg.name, arg.default) == ("language", "fr")
        assert arg.help
    with pytest.raises(ValueError, match="fr or en"):
        generators.title_variants("SEO", language="de")


def test_intent_mix_maps_country_to_provider_language(monkeypatch):
    calls = []

    def intent(words, language_name):
        calls.append(language_name)
        return []

    monkeypatch.setattr(strategy.keyword_service, "intent", intent)
    strategy.intent_mix("audit SEO", "France")
    strategy.intent_mix("SEO audit", "US")
    assert calls == ["French", "English"]
    assert REGISTRY["intent_mix"].args[-1].default == "FR"
