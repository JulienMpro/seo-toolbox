"""Mocked tests for the backlink mini-tools."""

from unittest.mock import patch

from seotoolbox.models import Anchor, Backlink, BacklinkSummary, NewLost, ReferringDomain
from seotoolbox.tools import link_tools


class FakeClient:
    """Return deterministic endpoint results without network access."""

    responses = {}
    calls = []

    def get_result(self, path, payload):
        self.calls.append((path, payload))
        return self.responses.get(path, [])


def test_distribution_quality_and_comparison_tools(tmp_path):
    toxic = Backlink("from", "to", "anchor", "bad.test", spam_score=80)
    with patch.object(link_tools.backlink_service, "anchors", return_value=[Anchor("brand", backlinks=3), Anchor("url", backlinks=1)]), \
         patch.object(link_tools.backlink_service, "backlinks", return_value=[toxic]), \
         patch.object(link_tools.backlink_service, "summary", return_value=BacklinkSummary(10, 4, 50, 2)), \
         patch.object(link_tools.backlink_service, "disavow_file", return_value=tmp_path / "disavow.txt"):
        assert link_tools.anchor_distribution("a.test")[0]["percent"] == 75
        assert link_tools.toxic_links("a.test")[0]["spam_score"] == 80
        assert link_tools.disavow_generator("a.test", output=str(tmp_path / "disavow.txt"))[0]["domain"] == "bad.test"
        assert len(link_tools.link_profile_compare("a.test\nb.test")) == 2
        assert link_tools.dofollow_ratio("a.test")[0]["count"] is None


def test_dofollow_ratio_uses_referring_page_totals():
    summary = BacklinkSummary(referring_pages=100, referring_pages_nofollow=25)
    with patch.object(link_tools.backlink_service, "summary", return_value=summary):
        assert link_tools.dofollow_ratio("a.test") == [
            {"type": "dofollow", "count": 75, "percent": 75.0},
            {"type": "nofollow", "count": 25, "percent": 25.0},
        ]


def test_disavow_generator_passes_public_limit():
    with patch.object(link_tools.backlink_service, "backlinks", return_value=[]) as fetch:
        assert link_tools.disavow_generator("a.test", limit=2) == []
        fetch.assert_called_once_with("a.test", 2)


def test_wrapped_backlink_operations():
    with patch.object(link_tools.backlink_service, "gap", return_value=[{"domain": "ref.test", "links_to_competitor": 2, "rank": 10}]), \
         patch.object(link_tools.backlink_service, "referring_domains", return_value=[ReferringDomain("ref.test", 4, rank=20)]), \
         patch.object(link_tools.backlink_service, "new_lost", return_value=[NewLost("2026-01-01", 2, 1, 1, 0)]), \
         patch.object(link_tools.backlink_service, "networks", return_value=[{"ip": "192.0.2.1", "referring_domains": 3, "backlinks": 8}]), \
         patch.object(link_tools.backlink_service, "bulk_ranks", return_value=[{"target": "a.test", "rank": 90}]):
        assert link_tools.link_gap("a.test", "b.test")[0]["domain"] == "ref.test"
        assert link_tools.referring_domains_analysis("a.test")[0]["rank"] == 20
        assert link_tools.new_lost_links("a.test")[0]["new_rd"] == 1
        assert link_tools.pbn_detection("a.test")[0]["network_address"] == "192.0.2.1"
        assert link_tools.authority_score("a.test\nmissing.test")[1]["rank"] is None


def test_direct_backlink_endpoints_are_normalized():
    FakeClient.calls = []
    FakeClient.responses = {
        "backlinks/timeseries_summary/live": [{"items": [{"date": "2026-01-01", "backlinks": 10, "referring_domains": 3}]}],
        "backlinks/domain_pages_summary/live": [{"items": [{"page": "https://a.test/x", "backlinks": 5, "referring_domains": 2}]}],
    }
    with patch.object(link_tools, "DataForSEOClient", FakeClient):
        assert link_tools.link_profile_evolution("a.test")[0]["total_backlinks"] == 10
        assert FakeClient.calls[0][1]["group_range"] == "day"
        assert link_tools.most_linked_pages("a.test")[0]["page"] == "https://a.test/x"
