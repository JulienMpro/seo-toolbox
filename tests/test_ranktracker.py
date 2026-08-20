from seotoolbox import ranktracker


class FakeClient:
    def __init__(self, response): self.response, self.calls = response, []
    def get_result(self, path, payload): self.calls.append((path, payload)); return self.response


def test_domain_rank_normalizes_nested_serp():
    client = FakeClient([{"items": [{"keyword_data": {"keyword": "seo", "keyword_info": {"search_volume": 10}},
        "ranked_serp_element": {"serp_item": {"rank_absolute": 3, "url": "https://x.test", "type": "organic"}}}]}])
    result = ranktracker.domain_rank(["seo"], "x.test", "FR", 5, client)
    assert result[0].position == 3
    assert result[0].volume == 10
    assert client.calls[0][1]["location_name"] == "France"


def test_rank_history_flattens_points():
    client = FakeClient([{"items": [{"keyword": "seo", "history": [{"date": "2026-01-01", "position": 4}]}]}])
    assert ranktracker.rank_history(["seo"], "x.test", "US", "2026-01-01", "2026-01-02", client)[0].position == 4
