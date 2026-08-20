"""Focused zero-network regressions for the checker/link QA batch."""

from datetime import date, timedelta
from unittest.mock import patch

from bs4 import BeautifulSoup

import httpx

from seotoolbox import backlinks
from seotoolbox.models import ReferringDomain
from seotoolbox.tools import checkers, link_tools, netlinking_extra


def test_hreflang_reciprocity_is_unknown_when_batched_target_fetch_failed(monkeypatch):
    source = BeautifulSoup(
        '<link rel="alternate" hreflang="en" href="https://www.example.test/en/">',
        "html.parser",
    )
    monkeypatch.setattr(
        checkers,
        "_page",
        lambda url: (source, None) if url.endswith("/fr") else (None, "timeout"),
    )

    rows = checkers.hreflang_checker(
        "http://example.test/fr\nhttps://example.test/en"
    )

    assert rows[0]["reciprocal"] is None
    assert rows[1]["reciprocal"] is None
    spec = checkers.register.__globals__["REGISTRY"]["hreflang_checker"]
    assert all(word in spec.description for word in ("scheme", "www", "trailing-slash"))


def test_failed_viewport_fetch_does_not_report_false(monkeypatch):
    monkeypatch.setattr(checkers, "_page", lambda _url: (None, "timeout"))

    row = checkers.viewport_checker("https://example.test")[0]

    assert row["present"] is None
    assert row["device_width"] is None
    assert row["responsive_hint"] is None


def test_indexation_checker_normalizes_equivalent_url_forms():
    rows = checkers.indexation_checker(
        "https://example.test/page/",
        "https://example.test/page",
    )

    assert rows == [{
        "url": "https://example.test/page",
        "status": "indexed",
        "source_status": "indexed",
    }]


def test_hreflang_reciprocity_normalizes_equivalent_target_forms(monkeypatch):
    pages = {
        "http://example.test/fr/": '<link rel="alternate" hreflang="en" href="https://www.example.test/en">',
        "https://example.test/en": '<link rel="alternate" hreflang="fr" href="https://example.test/fr">',
    }
    monkeypatch.setattr(
        checkers,
        "_page",
        lambda url: (BeautifulSoup(pages[url], "html.parser"), None),
    )

    rows = checkers.hreflang_reciprocity(
        "fr|http://example.test/fr/\nen|https://example.test/en"
    )

    assert [row["ok"] for row in rows] == [True, True]


def test_referring_domain_lost_date_is_not_labeled_last_seen():
    item = ReferringDomain("ref.test", 4, first_seen="2025-01-01", last_seen="2026-01-01")
    with patch.object(link_tools.backlink_service, "referring_domains", return_value=[item]):
        row = link_tools.referring_domains_analysis("example.test")[0]

    assert row["lost_date"] == "2026-01-01"
    assert "last_seen" not in row


def test_direct_backlink_payloads_and_verified_response_mapping():
    calls = []

    class FakeClient:
        def get_result(self, path, payload):
            calls.append((path, payload))
            if path == "backlinks/timeseries_summary/live":
                return [{"items": [{"date": "2026-08-01", "backlinks": 10,
                                     "referring_domains": 3}]}]
            return [{"items": [{"page": "https://example.test/a", "backlinks": 5,
                                 "referring_domains": 2}]}]

    with patch.object(link_tools, "DataForSEOClient", FakeClient):
        evolution = link_tools.link_profile_evolution("example.test", 30)
        pages = link_tools.most_linked_pages("example.test", 7)

    assert calls[0] == (
        "backlinks/timeseries_summary/live",
        {"target": "example.test", "date_from": (date.today() - timedelta(days=30)).isoformat(),
         "date_to": date.today().isoformat(), "group_range": "day"},
    )
    assert calls[1] == (
        "backlinks/domain_pages_summary/live",
        {"target": "example.test", "limit": 7},
    )
    assert evolution == [{"date": "2026-08-01", "total_backlinks": 10,
                          "total_referring_domains": 3}]
    assert pages == [{"page": "https://example.test/a", "backlinks": 5,
                      "referring_domains": 2}]


def test_summary_preserves_verified_link_types_for_dofollow_ratio():
    class FakeClient:
        def get_result(self, path, payload):
            assert path == "backlinks/summary/live"
            assert payload == {"target": "example.test"}
            return [{"backlinks": 10, "referring_domains": 4, "backlinks_spam_score": 7,
                     "referring_links_types": {"dofollow": 6, "nofollow": 2}}]

    summary = backlinks.summary("example.test", FakeClient())
    with patch.object(link_tools.backlink_service, "summary", return_value=summary):
        rows = link_tools.dofollow_ratio("example.test")

    assert rows == [
        {"type": "dofollow", "count": 6, "percent": 75.0},
        {"type": "nofollow", "count": 2, "percent": 25.0},
    ]


def test_public_page_fetch_failures_are_explicit(monkeypatch):
    class Response:
        status_code = 200
        text = "<urlset><url><loc>https://example.test/dead</loc></url></urlset>"

    calls = 0

    def get(_url, **_kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return Response()
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(netlinking_extra.httpx, "get", get)
    broken = netlinking_extra.broken_link_building("example.test")
    assert broken[0]["status"] is None
    assert broken[0]["similar_page"].startswith("check failed:")

    monkeypatch.setattr(
        netlinking_extra.httpx,
        "get",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(httpx.ConnectError("offline")),
    )
    email = netlinking_extra.prospect_emails("https://example.test")[0]
    assert email == {"url": "https://example.test", "email": None,
                     "email_domain": None, "error": "offline"}
