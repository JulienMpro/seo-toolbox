from seotoolbox import serp


class FakeClient:
    def __init__(self, response): self.response, self.calls = response, []
    def get_result(self, path, payload): self.calls.append((path, payload)); return self.response


def test_live_keeps_only_organic_results():
    client = FakeClient([{"items": [{"type": "people_also_ask"}, {"type": "organic", "rank_absolute": 1,
        "url": "https://x.test", "domain": "x.test", "title": "X"}]}])
    result = serp.live("seo", "FR", 10, "desktop", client)
    assert len(result) == 1
    assert result[0].rank == 1
    assert client.calls[0][1]["language_code"] == "fr"


def test_features_are_sorted_and_deduplicated():
    client = FakeClient([{"items": [{"type": "people_also_ask"}, {"type": "ai_overview"},
        {"type": "people_also_ask"}, {"type": "organic"}], "se_results": ["organic", "local_pack"]}])
    assert serp.features("seo", "US", client).features == ["ai_overview", "local_pack", "people_also_ask"]


def test_locations_normalizes_code_and_name():
    client = FakeClient([{"location_code": 2250, "location_name": "France"}])
    assert serp.locations("fr", client) == [{"code": 2250, "name": "France"}]
