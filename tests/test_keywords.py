from seotoolbox import keywords


class FakeClient:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def get_result(self, path, payload):
        self.calls.append((path, payload))
        response = self.responses.get(path, [])
        if isinstance(response, Exception):
            raise response
        return response


def item(keyword, volume=None, difficulty=None):
    return {
        "keyword_data": {
            "keyword": keyword,
            "keyword_info": {"search_volume": volume, "cpc": 2.3, "competition": 0.4},
            "keyword_properties": {"keyword_difficulty": difficulty},
            "search_intent_info": {"main_intent": "commercial"},
        }
    }


def test_overview_maps_country_payload_and_missing_result():
    client = FakeClient({keywords.ENDPOINTS["overview"]: [{"items": [item("seo", 100, 42)]}]})

    result = keywords.overview(["seo", "missing"], "FR", client)

    assert client.calls[0][1] == {
        "keywords": ["seo", "missing"], "language_code": "fr", "location_name": "France"
    }
    assert result[0].volume == 100
    assert result[0].difficulty == 42
    assert result[1].volume is None


def test_ideas_normalizes_and_enriches_in_batches():
    client = FakeClient({
        keywords.ENDPOINTS["ideas"]: [{"items": [item("seo tool"), item("seo audit")]}],
        keywords.ENDPOINTS["overview"]: [{"items": [item("seo tool", 50), item("seo audit", 80)]}],
        keywords.ENDPOINTS["difficulty"]: [{"items": [item("seo tool", difficulty=31)]}],
    })

    result = keywords.ideas("seo", "US", 2, client)

    assert [value.keyword for value in result] == ["seo tool", "seo audit"]
    assert result[0].volume == 50
    assert result[0].difficulty == 31
    assert result[1].difficulty is None
    assert client.calls[0][1]["keywords"] == ["seo"]
    assert client.calls[0][1]["limit"] == 2


def test_intent_sends_required_language_name():
    client = FakeClient({keywords.ENDPOINTS["intent"]: [{"items": [{
        "keyword": "seo", "keyword_intent": {"label": "commercial", "probability": 0.9}
    }]}]})

    result = keywords.intent(["seo"], client=client)

    assert result[0].intent == "commercial"
    assert client.calls[0][1] == {"keywords": ["seo"], "language_name": "English"}


def test_keywords_for_site_handles_missing_fields():
    client = FakeClient({keywords.ENDPOINTS["for_site"]: [{"items": [{"keyword_data": {"keyword": "seo"}}]}]})

    result = keywords.keywords_for_site("example.com", "GB", 5, client)

    assert result[0].keyword == "seo"
    assert result[0].position is None
    assert client.calls[0][1]["target"] == "example.com"
    assert client.calls[0][1]["include_serp_info"] is True


def test_keywords_for_site_optionally_returns_provider_total():
    client = FakeClient({keywords.ENDPOINTS["for_site"]: [{
        "total_count": 5000, "items": [item("seo"), item("audit seo")],
    }]})

    ranked, total = keywords.keywords_for_site(
        "example.com", client=client, return_total=True)

    assert len(ranked) == 2
    assert total == 5000

    missing_client = FakeClient({keywords.ENDPOINTS["for_site"]: [{
        "items": [item("seo")],
    }]})
    _, missing_total = keywords.keywords_for_site(
        "example.com", client=missing_client, return_total=True)
    assert missing_total is None


def test_gap_calls_each_competitor_and_deduplicates():
    client = FakeClient({keywords.ENDPOINTS["gap"]: [{"items": [item("unique kw", 10)]}]})

    result = keywords.gap("mine.test", ["one.test", "two.test"], "US", 10, client)

    assert [value.keyword for value in result] == ["unique kw"]
    assert len(client.calls) == 2
    assert all(call[1]["intersections"] is False for call in client.calls)


def test_cluster_uses_bigram_similarity():
    result = keywords.cluster(["seo tool", "seo tools", "plumber paris"], threshold=0.6)

    assert result == [["seo tool", "seo tools"], ["plumber paris"]]
