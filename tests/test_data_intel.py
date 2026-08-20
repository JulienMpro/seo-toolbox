"""Mocked tests for content, commerce, trends, and AI tools."""

import pytest

from seotoolbox.client import ApiError
from seotoolbox.models import AiMention
from seotoolbox.tools import data_intel as data


class FakeClient:
    def __init__(self, results): self.results, self.calls = results, []
    def get_result(self, path, payload): self.calls.append((path, payload)); return self.results


def test_content_tools():
    client = FakeClient([{"items": [{
        "url": "https://a.test/page",
        "domain": "a.test",
        "url_rank": 12,
        "domain_rank": 34,
        "score": 2,
        "spam_score": 1,
        "content_info": {"page_title": "A page"},
    }]}])
    mention = data.brand_mentions("brand", client=client)[0]
    assert mention == {
        "url": "https://a.test/page",
        "domain": "a.test",
        "rank": 12,
        "relevance": 2,
        "spam_score": 1,
        "title": "A page",
    }
    assert "page_type" not in client.calls[0][1]
    assert data.phrase_trends("brand", FakeClient([{"trends": [{"date": "2026-01", "count": 3}]}]))[0]["value"] == 3
    assert data.content_summary("a.test", FakeClient([{"target": "a.test", "pages_count": 4}]))[0]["pages"] == 4


def test_amazon_tools():
    product = {"data_asin": "A", "title": "Chair", "rating": {"value": 4.5, "votes_count": 2}}
    assert data.amazon_products("chair", client=FakeClient([product]))[0]["asin"] == "A"
    kw = {"keyword_data": {"keyword": "chair", "keyword_info": {"search_volume": 8}}, "ranked_serp_element": {"serp_item": {"rank_absolute": 2}}}
    assert data.amazon_product_keywords("A", client=FakeClient([kw]))[0]["position"] == 2
    assert data.amazon_competitors("A", client=FakeClient([{"asin": "B"}]))[0]["asin"] == "B"
    assert data.amazon_sellers("A", client=FakeClient([{"seller_name": "Shop"}]))[0]["seller"] == "Shop"
    assert data.amazon_asin("A", FakeClient([{"title": "Chair"}]))[0]["title"] == "Chair"


def test_trend_tools():
    trend = FakeClient([{"interest_over_time": [{"date": "2026-01-01", "value": 7}]}])
    assert data.google_trends("seo", client=trend)[0]["interest"] == 7
    assert data.trends_by_region("seo", client=FakeClient([{"location_name": "Paris", "value": 9}]))[0]["region"] == "Paris"
    assert data.trends_demography("seo", client=FakeClient([{"age": "18-24", "value": 5}]))[0]["segment"] == "18-24"


def test_ai_tools(monkeypatch):
    assert data.llm_response_extract("seo", client=FakeClient([{"response": "Answer"}])).startswith("Answer")
    assert data.llm_volume("seo\ngeo", FakeClient([{"keyword": "seo", "search_volume": 3}]))[0]["volume"] == 3
    monkeypatch.setattr(data.geo, "mentions", lambda *args: [AiMention("seo", "chatgpt", "brand.test", 2, 1)])
    result = data.brand_visibility_ia("brand", "seo", "chatgpt", client=FakeClient([]))[0]
    assert result["mentioned"] is True and result["visibility_score"] == .5


@pytest.mark.parametrize(
    ("function", "argument", "endpoint", "mcp_tool"),
    [
        (data.llm_response_extract, "seo", "ai_optimization/llm_response/live", "ai_optimization_llm_response"),
        (data.llm_volume, "seo", "ai_optimization/keyword_data/search_volume/live", "ai_optimization_keyword_data_search_volume"),
    ],
)
def test_llm_rest_404_explains_mcp_alternative(function, argument, endpoint, mcp_tool):
    client = FakeClient([])
    client.get_result = lambda path, payload: (_ for _ in ()).throw(ApiError("HTTP 404 Not Found"))

    with pytest.raises(ValueError) as exc_info:
        function(argument, client=client)

    message = str(exc_info.value)
    assert f"REST endpoint '{endpoint}' not exposed (HTTP 404)." in message
    assert f"tool '{mcp_tool}'" in message
