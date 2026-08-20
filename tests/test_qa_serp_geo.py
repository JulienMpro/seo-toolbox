"""Regression tests for the SERP/GEO QA batch (all network calls are mocked)."""

import inspect
from datetime import date, timedelta

from seotoolbox.tools import REGISTRY
from seotoolbox.tools import data_intel as data
from seotoolbox.tools import serp_tools
from seotoolbox.tools import youtube_tools as youtube


class FakeClient:
    def __init__(self, results):
        self.results = results
        self.calls = []

    def get_result(self, path, payload):
        self.calls.append((path, payload))
        return self.results


TOOLS = """amazon_asin amazon_competitors amazon_product_keywords amazon_products amazon_sellers
brand_mentions competitor_keywords content_summary features_matrix google_trends intent_analysis keyword_gap
keyword_suggestions_tool paa_extractor phrase_trends rank_bulk serp_compare serp_countries serp_devices
serp_features serp_history serp_snapshot top_searches trends_by_region trends_demography youtube_comments
youtube_keywords youtube_transcript youtube_video_info brand_visibility_ia llm_response_extract llm_volume""".split()


def test_all_batch_registry_specs_match_signatures_and_returns():
    assert len(TOOLS) == 32
    for name in TOOLS:
        spec = REGISTRY[name]
        signature = inspect.signature(spec.fn)
        assert [arg.name for arg in spec.args] == [
            parameter for parameter in signature.parameters if parameter != "client"
        ]
        assert spec.returns in {"str", "table"}


def test_intent_analysis_localizes_payload_and_has_honest_columns(monkeypatch):
    calls = []
    monkeypatch.setattr(serp_tools.keyword_service, "intent",
                        lambda words, language_name: calls.append((words, language_name)) or [])
    assert serp_tools.intent_analysis("plombier paris", "FR") == []
    assert calls == [(["plombier paris"], "French")]


def test_paa_maps_expanded_element_snippet(monkeypatch):
    monkeypatch.setattr(serp_tools.serp, "_raw", lambda *args: [{"items": [{
        "type": "people_also_ask", "items": [{
            "title": "Pourquoi ?", "expanded_element": [{"text": "Parce que."}],
        }],
    }]}])
    assert serp_tools.paa_extractor("question", "FR") == [
        {"question": "Pourquoi ?", "snippet": "Parce que."},
    ]


def test_youtube_endpoints_and_required_market_payloads():
    cases = [
        (youtube.youtube_video_info, ("https://youtu.be/abcdefghi",), "serp/youtube/video_info/live/advanced"),
        (youtube.youtube_comments, ("abcdefghi",), "serp/youtube/video_comments/live/advanced"),
        (youtube.youtube_transcript, ("abcdefghi",), "serp/youtube/video_subtitles/live/advanced"),
    ]
    for function, args, endpoint in cases:
        client = FakeClient([])
        function(*args, client=client)
        assert client.calls[0] == (endpoint, {"video_id": "abcdefghi", "location_code": 2840, "language_code": "en"})


def test_verified_content_amazon_and_trends_mappings_preserve_zero():
    phrase = data.phrase_trends("marque", FakeClient([{"date": "2026-01", "total_count": 0, "rank": 4}]))
    assert phrase == [{"date": "2026-01", "citations": 0, "rank": 4}]

    competitors = FakeClient([{"items": [{"asin": "B", "avg_position": 0}]}])
    assert data.amazon_competitors("A", 3, competitors) == [{"asin": "B", "avg_position": 0}]
    assert competitors.calls[0][1] == {
        "asin": "A", "location_code": 2840, "language_code": "en", "limit": 3,
    }

    product = {"items": [{"data_asin": "A", "title": "Chair", "price_from": 0,
                           "image_url": "https://img.test/a.jpg",
                           "rating": {"value": 0, "votes_count": 0}}]}
    assert data.amazon_asin("A", FakeClient([product]))[0] == {
        "asin": "A", "title": "Chair", "price": 0, "image": "https://img.test/a.jpg",
        "description": None, "rating": 0, "reviews": 0,
    }

    products_client = FakeClient([])
    data.amazon_products("chair", 7, products_client)
    assert products_client.calls[0][1]["depth"] == 7
    assert "limit" not in products_client.calls[0][1]

    sellers_client = FakeClient([])
    data.amazon_sellers("A", 7, sellers_client)
    assert "limit" not in sellers_client.calls[0][1]

    empty_seller = FakeClient([{"items": [{"seller_name": None, "price": None, "stock": None}]}])
    assert data.amazon_sellers("A", client=empty_seller) == []


def test_empty_items_envelopes_do_not_become_misleading_rows():
    envelope = [{"asin": "A", "items_count": 0, "items": None}]
    assert data.amazon_competitors("A", client=FakeClient(envelope)) == []
    assert data.amazon_product_keywords("A", client=FakeClient(envelope)) == []
    assert data.amazon_sellers("A", client=FakeClient(envelope)) == []
    assert youtube.youtube_comments("abcdefghi", client=FakeClient(envelope)) == []


def test_phrase_trends_supplies_required_date_range():
    client = FakeClient([])
    data.phrase_trends("marque", client)
    payload = client.calls[0][1]
    assert payload == {"keyword": "marque", "date_from": (date.today() - timedelta(days=30)).isoformat(),
                       "date_to": date.today().isoformat()}


def test_verified_trends_nested_shapes_and_endpoints():
    region_client = FakeClient([{"items": [{"type": "google_trends_map", "data": [
        {"geo_name": "Île-de-France", "values": [0]},
    ]}]}])
    assert data.trends_by_region("seo", "FR", region_client) == [
        {"region": "Île-de-France", "interest": 0},
    ]
    assert region_client.calls[0][0] == "keywords_data/google_trends/explore/live"
    assert region_client.calls[0][1]["item_types"] == ["google_trends_map"]

    demographic = {"items": [{"demography": {
        "age": [{"keyword": "seo", "values": [{"type": "18-24", "value": 0}]}],
        "gender": [{"keyword": "seo", "values": [{"type": "female", "value": 70}]}],
    }}]}
    demo_client = FakeClient([demographic])
    assert data.trends_demography("seo", "US", demo_client) == [
        {"dimension": "age", "segment": "18-24", "value": 0},
        {"dimension": "gender", "segment": "female", "value": 70},
    ]
    assert demo_client.calls[0][0] == "keywords_data/dataforseo_trends/demography/live"
    assert demo_client.calls[0][1] == {"keywords": ["seo"], "location_code": 2840}


def test_trends_presets_and_youtube_organic_omits_rejected_depth_field():
    trends_client = FakeClient([])
    data.google_trends("seo", "FR", "past_12_months", trends_client)
    assert trends_client.calls[0][1]["time_range"] == "past_12_months"
    assert "date_from" not in trends_client.calls[0][1]

    youtube_client = FakeClient([])
    youtube.youtube_keywords("seo", 7, youtube_client)
    assert "depth" not in youtube_client.calls[0][1]
    assert "limit" not in youtube_client.calls[0][1]


def test_keyword_gap_maps_first_domain_position():
    item = {"keyword_data": {"keyword": "seo", "keyword_info": {"search_volume": 10}},
            "first_domain_serp_element": {"rank_absolute": 3, "url": "https://example.test"}}
    ranked = __import__("seotoolbox.keywords", fromlist=["_ranked"])._ranked(item)
    assert ranked.position == 3
    assert ranked.url == "https://example.test"


def test_brand_visibility_does_not_match_brand_as_arbitrary_substring(monkeypatch):
    from seotoolbox.models import AiMention
    monkeypatch.setattr(data.geo, "mentions", lambda *args: [
        AiMention("seo", "chatgpt", "walmart.com", 1, 1),
        AiMention("seo", "chatgpt", "art.example", 2, 1),
    ])
    result = data.brand_visibility_ia("art", "seo", "chatgpt")[0]
    assert result["domain"] == "art.example"
