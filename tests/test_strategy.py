"""Tests for planning and strategy mini-tools."""

from seotoolbox.models import BacklinkSummary, IntentInfo, KeywordOverview, KeywordRanked
from seotoolbox.tools import strategy


def test_local_strategy_tools():
    calendar = strategy.editorial_calendar("beta|P2|guide\nalpha|P1|article", 4, "2026-01-01")
    assert "2026-01-01" in calendar and "alpha" in calendar and "Distribution" in calendar
    assert strategy.seo_projection(100, 10, 2, 2)[1]["traffic"] == 121
    assert "quick" in strategy.effort_impact("fix titles|1|5")
    audit = strategy.content_audit("/a|10|200|4\n/b|0|300|20\n/c|0|0|0")
    assert [row["verdict"] for row in audit] == ["keep", "improve", "remove"]


def test_keyword_strategy_with_mocked_services(monkeypatch):
    monkeypatch.setattr(strategy.keyword_service, "overview", lambda words, country: [
        KeywordOverview(word, volume=1000 - index * 100, cpc=2, difficulty=20 + index * 10)
        for index, word in enumerate(words)
    ])
    monkeypatch.setattr(strategy.keyword_service, "intent", lambda words: [IntentInfo(word, "commercial") for word in words])
    rows = strategy.keyword_prioritization("alpha\nbeta", "FR")
    assert all(row["score"] is not None for row in rows)
    assert strategy.difficulty_score("alpha", "FR")[0]["level"] == "easy"
    assert "commercial" in strategy.intent_mix("alpha\nbeta")


def test_keyword_prioritization_scores_metrics_without_intent(monkeypatch):
    monkeypatch.setattr(strategy.keyword_service, "overview", lambda words, country: [
        KeywordOverview(words[0], volume=500, cpc=2, difficulty=30)
    ])
    monkeypatch.setattr(strategy.keyword_service, "intent", lambda words: [IntentInfo(words[0], None)])

    row = strategy.keyword_prioritization("alpha", "FR")[0]

    assert row["intent"] == "N/D"
    assert row["score"] is not None


def test_keyword_prioritization_does_not_score_without_numeric_data(monkeypatch):
    monkeypatch.setattr(strategy.keyword_service, "overview", lambda words, country: [KeywordOverview(words[0])])
    monkeypatch.setattr(strategy.keyword_service, "intent", lambda words: [IntentInfo(words[0], None)])

    row = strategy.keyword_prioritization("alpha", "FR")[0]

    assert row["score"] is None
    assert row["verdict"] is None
    assert "N/D" in strategy.intent_mix("alpha")


def test_benchmark_and_clusters(monkeypatch):
    monkeypatch.setattr(strategy.keyword_service, "related", lambda seed, country, limit: [])
    monkeypatch.setattr(strategy.keyword_service, "overview", lambda words, country: [KeywordOverview(word, volume=10) for word in words])
    assert strategy.topic_clusters("red shoes\nblue hats")
    monkeypatch.setattr(strategy.keyword_service, "keywords_for_site", lambda domain, country, limit: [KeywordRanked("x", position=4)])
    monkeypatch.setattr(strategy.backlinks, "summary", lambda domain: BacklinkSummary(10, 2, 3))
    assert strategy.competitor_benchmark("example.com")[0]["backlinks"] == 10
