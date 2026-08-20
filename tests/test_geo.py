from seotoolbox import geo


class FakeClient:
    def __init__(self, response): self.response, self.calls = response, []
    def get_result(self, path, payload): self.calls.append((path, payload)); return self.response


def test_mentions_payload_and_normalization():
    client = FakeClient([{"items": [{"engine": "chatgpt", "domain": "x.test", "rank": 2, "mention_count": 5}]}])
    result = geo.mentions("seo", ["chatgpt"], "FR", client)
    assert result[0].keyword == "seo"
    assert result[0].mention_count == 5
    assert client.calls[0][1]["target"] == [{"keyword": "seo", "search_filter": "include"}]
    assert client.calls[0][1]["platform"] == "chat_gpt"


def test_top_pages_preserves_missing_values():
    client = FakeClient([{"items": [{"keyword": "seo", "url": "https://x.test"}]}])
    result = geo.top_pages(["seo"], None, 10, client)
    assert result[0].rank is None
    assert result[0].page_url == "https://x.test"


def test_mentions_aggregates_current_source_shape():
    client = FakeClient([{"items": [{"sources": [{"domain": "x.test", "position": 3},
                                                     {"domain": "x.test", "position": 1}]}]}])
    result = geo.mentions("seo", ["chatgpt"], "US", client)
    assert result[0].domain == "x.test"
    assert result[0].rank == 1
    assert result[0].mention_count == 2
