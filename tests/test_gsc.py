import httpx
import pytest

from seotoolbox.gsc import get_access_token, list_properties, search_analytics


def test_credentials_are_required(monkeypatch):
    for name in ("GSC_CLIENT_ID", "GSC_CLIENT_SECRET", "GSC_REFRESH_TOKEN"):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(ValueError, match="GSC credentials missing"):
        get_access_token()


def test_refresh_and_properties(monkeypatch):
    monkeypatch.setenv("GSC_CLIENT_ID", "id")
    monkeypatch.setenv("GSC_CLIENT_SECRET", "secret")
    monkeypatch.setenv("GSC_REFRESH_TOKEN", "refresh")
    monkeypatch.setattr("seotoolbox.gsc.httpx.post", lambda url, **kwargs: httpx.Response(
        200, json={"access_token": "token"}, request=httpx.Request("POST", url)))
    assert get_access_token() == "token"
    monkeypatch.setattr("seotoolbox.gsc.httpx.get", lambda url, **kwargs: httpx.Response(
        200, json={"siteEntry": [{"siteUrl": "sc-domain:example.com"}]}, request=httpx.Request("GET", url)))
    assert list_properties("token") == ["sc-domain:example.com"]


def test_search_analytics_normalizes_rows(monkeypatch):
    captured = {}
    def fake_post(url, **kwargs):
        captured.update(kwargs["json"])
        return httpx.Response(200, json={"rows": [{"keys": ["seo"], "clicks": 4, "impressions": 10,
                                                     "ctr": .4, "position": 2.5}]},
                              request=httpx.Request("POST", url))
    monkeypatch.setattr("seotoolbox.gsc.httpx.post", fake_post)
    rows = search_analytics("sc-domain:example.com", "2026-01-01", "2026-01-02", ["query"], 20, "token")
    assert rows[0].keys == ["seo"]
    assert captured["rowLimit"] == 20
