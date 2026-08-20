import httpx

from seotoolbox.crux import crux_report, page_speed


def test_page_speed_normalizes_field_data(monkeypatch):
    payload = {
        "loadingExperience": {"overall_category": "FAST", "metrics": {
            "LARGEST_CONTENTFUL_PAINT_MS": {"percentile": 2100, "category": "FAST"},
            "CUMULATIVE_LAYOUT_SHIFT_SCORE": {"percentile": 12, "category": "AVERAGE"},
            "INTERACTION_TO_NEXT_PAINT": {"percentile": 180, "category": "FAST"},
        }},
        "lighthouseResult": {"categories": {"performance": {"score": 0.91}}},
    }
    monkeypatch.setattr("seotoolbox.crux.httpx.get", lambda url, **kwargs: httpx.Response(
        200, json=payload, request=httpx.Request("GET", url)))
    metric = page_speed("https://example.com")
    assert metric.performance_score == 91
    assert metric.overall_category == "fast"
    assert metric.lcp == {"percentile": 2100, "category": "fast"}


def test_crux_report_limits_to_ten(monkeypatch):
    monkeypatch.setattr("seotoolbox.crux.page_speed", lambda url, strategy: url)
    assert len(crux_report([f"https://example.com/{i}" for i in range(12)])) == 10


def test_missing_field_data_stays_none(monkeypatch):
    monkeypatch.setattr("seotoolbox.crux.httpx.get", lambda url, **kwargs: httpx.Response(
        200, json={}, request=httpx.Request("GET", url)))
    metric = page_speed("https://example.com")
    assert metric.lcp is None
    assert metric.performance_score is None
