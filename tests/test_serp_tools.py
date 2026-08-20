"""Mocked tests for the SERP mini-tools."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from seotoolbox.models import IntentInfo, KeywordIdea, KeywordRanked, RankPosition, SerpFeatures, SerpResult
from seotoolbox.tools import serp_tools


class FakeClient:
    """Return deterministic endpoint results without network access."""

    responses = {}

    def get_result(self, path, payload):
        return self.responses.get(path, [])


def test_serp_comparison_extractors_and_matrix():
    organic = [SerpResult(1, "https://a.test", "a.test", "A")]
    with patch.object(serp_tools.serp, "live", return_value=organic), \
         patch.object(serp_tools.serp, "features", return_value=SerpFeatures("kw", ["images"])):
        assert len(serp_tools.serp_compare("one\ntwo")) == 2
        assert serp_tools.serp_devices("one")[0]["desktop_domain"] == "a.test"
        assert serp_tools.serp_countries("one", "FR")[0]["feature_count"] == 1
        assert serp_tools.features_matrix("one\ntwo")[0]["images"] == "✅"
        assert any(row["feature"] == "images" and row["present"] == "✅"
                   for row in serp_tools.serp_features("one"))
    with patch.object(serp_tools.serp, "_raw", return_value=[{"items": [{"type": "people_also_ask", "items": [{"title": "Why?", "text": "Because."}]}]}]):
        assert serp_tools.paa_extractor("one") == [{"question": "Why?", "snippet": "Because."}]


def test_keyword_tools_reuse_services():
    with patch.object(serp_tools.ranktracker, "domain_rank", return_value=[RankPosition("seo", 2, "https://a.test", volume=10, difficulty=4)]):
        assert serp_tools.rank_bulk("a.test", "seo")[0]["kd"] == 4
    with patch.object(serp_tools.keyword_service, "intent", return_value=[IntentInfo("seo", "commercial")]), \
         patch.object(serp_tools.keyword_service, "gap", return_value=[KeywordRanked("seo", 3, 10)]), \
         patch.object(serp_tools.keyword_service, "keywords_for_site", return_value=[KeywordRanked("seo", 3, 10)]), \
         patch.object(serp_tools.keyword_service, "suggestions", return_value=[KeywordIdea("seo")]), \
         patch.object(serp_tools.keyword_service, "related", return_value=[KeywordIdea("SEO"), KeywordIdea("seo tool")]):
        assert serp_tools.intent_analysis("seo")[0]["intent"] == "commercial"
        assert serp_tools.keyword_gap("a.test", "b.test")[0]["domain_position"] == 3
        assert serp_tools.competitor_keywords("b.test")[0]["volume"] == 10
        assert len(serp_tools.keyword_suggestions_tool("seo")) == 2


def test_intent_analysis_displays_missing_values():
    with patch.object(serp_tools.keyword_service, "intent", return_value=[IntentInfo("seo", None)]):
        assert serp_tools.intent_analysis("seo") == [{"keyword": "seo", "intent": "N/D"}]


def test_direct_serp_endpoints_are_normalized():
    FakeClient.responses = {
        "dataforseo_labs/google/historical_serps/live": [{"items": [{"date": "2026-01-01", "items": [{"rank_absolute": 1, "domain": "a.test"}]}]}],
        "dataforseo_labs/google/top_searches/live": [{"items": [{"keyword": "seo", "keyword_info": {"search_volume": 100}}]}],
    }
    with patch.object(serp_tools, "DataForSEOClient", FakeClient):
        assert serp_tools.serp_history("seo")[0]["domain"] == "a.test"
        assert serp_tools.top_searches()[0]["estimated_volume"] == 100
    with pytest.raises(ValueError):
        serp_tools.features_matrix("\n".join(f"kw {index}" for index in range(21)))
