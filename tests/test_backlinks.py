from seotoolbox import backlinks


class FakeClient:
    def __init__(self, responses): self.responses, self.calls = responses, []
    def get_result(self, path, payload): self.calls.append((path, payload)); return self.responses.get(path, [])


def test_summary_and_list_mapping():
    client = FakeClient({
        backlinks.ENDPOINTS["summary"]: [{"backlinks": 9, "rank": 50}],
        backlinks.ENDPOINTS["backlinks"]: [{"items": [{"domain_from": "bad.test", "backlink_spam_score": 70}]}],
    })
    assert backlinks.summary("x.test", client).backlinks == 9
    assert backlinks.backlinks("x.test", 3, client)[0].spam_score == 70
    assert client.calls[1][1] == {"target": "x.test", "limit": 3}


def test_summary_maps_real_api_keys():
    client = FakeClient({backlinks.ENDPOINTS["summary"]: [{
        "backlinks": 100,
        "referring_domains": 10,
        "rank": 5,
        "backlinks_spam_score": 20,
        "broken_backlinks": 3,
        "crawled_pages": 200,
        "first_seen": "2020-01-01 00:00:00 +00:00",
        "lost_date": None,
        "external_links_count": 400,
        "internal_links_count": 500,
        "referring_pages": 80,
        "referring_links_types": {"dofollow": 60, "nofollow": 40},
        "referring_pages_nofollow": None,
    }]})

    result = backlinks.summary("x.test", client)

    assert result.to_dict() == {
        "backlinks": 100,
        "referring_domains": 10,
        "rank": 5,
        "spam_score": 20,
        "broken_backlinks": 3,
        "crawled_pages": 200,
        "first_seen": "2020-01-01 00:00:00 +00:00",
        "lost_date": None,
        "external_links_count": 400,
        "internal_links_count": 500,
        "referring_pages": 80,
        "referring_links_types": {"dofollow": 60, "nofollow": 40},
        "referring_pages_nofollow": None,
    }


def test_disavow_writes_unique_toxic_domains(tmp_path):
    client = FakeClient({backlinks.ENDPOINTS["backlinks"]: [{"items": [
        {"domain_from": "bad.test", "backlink_spam_score": 70},
        {"domain_from": "bad.test", "backlinks_spam_score": 80},
        {"domain_from": "good.test", "backlink_spam_score": 10}]}]})
    path = backlinks.disavow_file("x.test", tmp_path / "disavow.txt", 60, client)
    assert path.read_text() == "domain:bad.test\n"


def test_new_lost_uses_iso_dates():
    client = FakeClient({backlinks.ENDPOINTS["new_lost"]: [{"items": [{"date": "2026-01-01", "new_backlinks": 2}]}]})
    assert backlinks.new_lost("x.test", 30, client)[0].new_backlinks == 2
    assert len(client.calls[0][1]["date_from"]) == 10
    assert client.calls[0][1]["group_range"] == "day"


def test_referring_domains_and_anchors_map_documented_keys():
    client = FakeClient({
        backlinks.ENDPOINTS["referring_domains"]: [{"items": [{
            "domain": "source.test", "backlinks": 12, "first_seen": "2020-01-01",
            "lost_date": "2026-01-01", "rank": 42, "backlinks_spam_score": 7,
        }]}],
        backlinks.ENDPOINTS["anchors"]: [{"items": [{
            "anchor": "example", "referring_domains": 4, "backlinks": 8, "external_links": 2,
        }]}],
    })

    domain = backlinks.referring_domains("x.test", client=client)[0]
    anchor = backlinks.anchors("x.test", client=client)[0]

    assert (domain.domain, domain.referring_links, domain.last_seen, domain.spam_score) == (
        "source.test", 12, "2026-01-01", 7)
    assert (anchor.anchor, anchor.referring_domains, anchor.backlinks, anchor.external_links) == (
        "example", 4, 8, 2)
