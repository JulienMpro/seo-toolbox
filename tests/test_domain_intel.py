"""Mocked tests for domain intelligence tools."""

from types import SimpleNamespace

from seotoolbox.tools import domain_intel


class FakeClient:
    def __init__(self, results): self.results, self.calls = results, []
    def get_result(self, path, payload): self.calls.append((path, payload)); return self.results


def test_whois_and_technology_and_audit():
    whois = domain_intel.whois_lite("example.com", FakeClient([{"domain": "example.com", "registrar": "Registrar", "epp_status_codes": ["ok"]}]))
    assert whois[0]["value"] == "Registrar" and whois[-1]["value"] == ["ok"]
    tech = domain_intel.technology_detection("example.com", FakeClient([{"technologies": {"cms": {"content_management": ["WordPress"]}}}]))
    assert tech == [{"group": "cms", "category": "content_management", "technology": "WordPress"}]
    audit = domain_intel.instant_audit("https://example.com", FakeClient([{"page_meta": {"title": "Page"}, "status_code": 200}]))
    assert audit[0]["status"] == "ok" and audit[1]["status"] == "absent"


def test_domain_compare_reuses_wrappers(monkeypatch):
    monkeypatch.setattr(domain_intel.backlinks, "bulk_ranks", lambda targets, client: [{"target": targets[0], "rank": 9}])
    monkeypatch.setattr(domain_intel.backlinks, "summary", lambda domain, client: SimpleNamespace(rank=None, backlinks=10, referring_domains=3, spam_score=1))
    monkeypatch.setattr(domain_intel.keywords, "keywords_for_site", lambda *args: [SimpleNamespace(position=4)])
    row = domain_intel.domain_compare("a.test", client=FakeClient([]))[0]
    assert row["rank"] == 9 and row["best_position"] == 4
