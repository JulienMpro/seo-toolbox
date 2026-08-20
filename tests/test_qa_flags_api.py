"""Regression tests for API response shapes verified live on 2026-08-20."""

from unittest.mock import patch

from seotoolbox import backlinks
from seotoolbox.tools import domain_intel, link_tools


class FakeClient:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def get_result(self, path, payload):
        self.calls.append((path, payload))
        return self.responses.get(path, [])


def test_link_gap_diffs_verified_referring_domain_shape():
    endpoint = backlinks.ENDPOINTS["referring_domains"]
    client = FakeClient({endpoint: []})
    responses = iter([
        [{"items": [{"domain_from": "shared.test", "referring_links": 1, "rank": 5}]}],
        [{"items": [
            {"domain_from": "small.test", "referring_links": 3, "rank": 80},
            {"domain_from": "shared.test", "referring_links": 100, "rank": 90},
            {"domain_from": "large.test", "referring_links": 12, "rank": 20},
        ]}],
    ])
    client.get_result = lambda path, payload: (client.calls.append((path, payload)) or next(responses))

    assert backlinks.gap("target.test", "competitor.test", 2, client) == [
        {"domain": "large.test", "links_to_competitor": 12, "rank": 20},
        {"domain": "small.test", "links_to_competitor": 3, "rank": 80},
    ]
    assert client.calls == [
        (endpoint, {"target": "target.test", "limit": 2}),
        (endpoint, {"target": "competitor.test", "limit": 2}),
    ]


def test_link_gap_tool_exposes_service_columns():
    expected = [{"domain": "ref.test", "links_to_competitor": 7, "rank": 42}]
    with patch.object(link_tools.backlink_service, "gap", return_value=expected) as service:
        assert link_tools.link_gap("target.test", "competitor.test", 5) == expected
    service.assert_called_once_with("target.test", "competitor.test", 5)


def test_pbn_detection_maps_verified_network_address():
    response = [{"network_address": "192.0.2.0/24", "referring_domains": 4, "backlinks": 9}]
    with patch.object(link_tools.backlink_service, "networks", return_value=response):
        assert link_tools.pbn_detection("example.test") == [{
            "network_address": "192.0.2.0/24", "referring_domains": 4, "backlinks": 9,
        }]


def test_whois_lite_filters_domain_and_uses_epp_status_codes():
    endpoint = "domain_analytics/whois/overview/live"
    client = FakeClient({endpoint: [{"items": [
        {"domain": "youtube.com", "registrar": "Wrong"},
        {"domain": "wikipedia.org", "registrar": "Right", "created_datetime": "2001-01-13",
         "expiration_datetime": "2031-01-13", "updated_datetime": "2026-01-01",
         "epp_status_codes": ["client transfer prohibited"]},
    ]}]})

    rows = domain_intel.whois_lite("wikipedia.org", client)

    assert [row["field"] for row in rows] == ["registrar", "created", "expires", "updated", "status"]
    assert rows[0]["value"] == "Right"
    assert rows[-1]["value"] == ["client transfer prohibited"]


def test_technology_detection_flattens_verified_nested_dict_and_ignores_non_strings():
    endpoint = "domain_analytics/technologies/domain_technologies/live"
    client = FakeClient({endpoint: [{"technologies": {
        "servers": {"web_servers": ["Apache Traffic Server", None, 42]},
        "analytics": {"tracking": ["Plausible"], "invalid": "not-a-list"},
        "invalid_group": ["ignored"],
    }}]})

    assert domain_intel.technology_detection("example.test", client) == [
        {"group": "servers", "category": "web_servers", "technology": "Apache Traffic Server"},
        {"group": "analytics", "category": "tracking", "technology": "Plausible"},
    ]


def test_link_profile_evolution_maps_verified_timeseries_items():
    endpoint = "backlinks/timeseries_summary/live"
    response = [{"date_from": "2026-01-01", "date_to": "2026-01-02", "items": [{
        "type": "backlinks_timeseries_summary", "date": "2026-01-02", "rank": 75,
        "backlinks": 120, "backlinks_nofollow": 20, "referring_domains": 30,
    }], "items_count": 1, "target": "example.test"}]
    with patch.object(link_tools, "DataForSEOClient", return_value=FakeClient({endpoint: response})):
        assert link_tools.link_profile_evolution("example.test") == [{
            "date": "2026-01-02", "total_backlinks": 120, "total_referring_domains": 30,
        }]


def test_most_linked_pages_maps_verified_domain_pages_items():
    endpoint = "backlinks/domain_pages_summary/live"
    response = [{"items": [{
        "type": "backlinks_domain_pages_summary", "url": "https://example.test/popular",
        "rank": 65, "backlinks": 50, "referring_domains": 12,
    }], "items_count": 1, "target": "example.test", "total_count": 1}]
    with patch.object(link_tools, "DataForSEOClient", return_value=FakeClient({endpoint: response})):
        assert link_tools.most_linked_pages("example.test", 10) == [{
            "page": "https://example.test/popular", "backlinks": 50, "referring_domains": 12,
        }]
