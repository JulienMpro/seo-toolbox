import httpx
import pytest

from seotoolbox import ga4
from seotoolbox import google_auth


def test_oauth_helper_uses_exact_token_url(monkeypatch):
    for name, value in (("GSC_CLIENT_ID", "id"), ("GSC_CLIENT_SECRET", "secret"),
                        ("GSC_REFRESH_TOKEN", "refresh")):
        monkeypatch.setenv(name, value)
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured["data"] = kwargs["data"]
        return httpx.Response(200, json={"access_token": "token"},
                              request=httpx.Request("POST", url))

    monkeypatch.setattr(google_auth.httpx, "post", fake_post)
    assert google_auth.get_access_token() == "token"
    assert captured["url"] == "https://oauth2.googleapis.com/token"
    assert captured["data"]["grant_type"] == "refresh_token"


def test_run_report_exact_url_payload_and_normalization(monkeypatch):
    captured = {}

    def fake_post(url, **kwargs):
        captured.update(url=url, **kwargs)
        return httpx.Response(200, json={"rows": [{
            "dimensionValues": [{"value": "20260819"}],
            "metricValues": [{"value": "12"}, {"value": "3.5"}],
        }]}, request=httpx.Request("POST", url))

    monkeypatch.setattr(ga4.httpx, "post", fake_post)
    rows = ga4.run_report("123", "2026-08-01", "2026-08-20", ["date"],
                          ["sessions", "engagementRate"], 10, "token")
    assert captured["url"] == "https://analyticsdata.googleapis.com/v1beta/properties/123:runReport"
    assert captured["json"] == {
        "dateRanges": [{"startDate": "2026-08-01", "endDate": "2026-08-20"}],
        "dimensions": [{"name": "date"}],
        "metrics": [{"name": "sessions"}, {"name": "engagementRate"}],
        "limit": 10,
    }
    assert rows[0].dimensions == ["20260819"]
    assert rows[0].metrics == [12.0, 3.5]


def test_run_report_propagates_property_error(monkeypatch):
    url = "https://analyticsdata.googleapis.com/v1beta/properties/bad:runReport"
    monkeypatch.setattr(ga4.httpx, "post", lambda *args, **kwargs: httpx.Response(
        404, json={"error": {"message": "Property not found"}},
        request=httpx.Request("POST", url)))
    with pytest.raises(ValueError, match=r"GA4 API request failed \(404\): Property not found"):
        ga4.run_report("bad", "2026-08-01", "2026-08-20", [], ["sessions"], 10, "token")


def test_run_report_explains_invalid_token(monkeypatch):
    url = "https://analyticsdata.googleapis.com/v1beta/properties/123:runReport"
    monkeypatch.setattr(ga4.httpx, "post", lambda *args, **kwargs: httpx.Response(
        401, json={"error": {"message": "Invalid Credentials"}},
        request=httpx.Request("POST", url)))
    with pytest.raises(ValueError, match="invalid or expired access token"):
        ga4.run_report("123", "2026-08-01", "2026-08-20", [], ["sessions"], 10, "bad")


def test_convenience_reports_reuse_shared_oauth(monkeypatch):
    calls = []
    monkeypatch.setattr(ga4, "get_access_token", lambda: "shared-token")
    monkeypatch.setattr(ga4, "run_report", lambda *args: calls.append(args) or [])
    ga4.daily_traffic("123", 28)
    ga4.traffic_by_source("123", 7, 5)
    ga4.top_pages("123", 14, 8)
    assert calls[0][3:6] == (["date"], ["sessions", "totalUsers", "engagedSessions"], 10000)
    assert calls[1][3:6] == (["sessionDefaultChannelGroup"], ["sessions", "totalUsers"], 5)
    assert calls[2][3:6] == (["pagePath"], ["sessions", "totalUsers", "engagementRate"], 8)
    assert all(call[-1] == "shared-token" for call in calls)
