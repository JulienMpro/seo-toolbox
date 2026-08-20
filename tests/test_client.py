import httpx
import pytest

from seotoolbox.client import DataForSEOClient, DataForSEOError


def success(items=None):
    return {"tasks": [{"status_code": 20000, "result": items or []}]}


def test_second_identical_call_uses_cache(tmp_path):
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(200, json=success([{"items": [{"keyword": "seo"}]}]))

    client = DataForSEOClient(
        username="user", password="pass", cache_path=tmp_path / "cache.db",
        transport=httpx.MockTransport(handler), sleep=lambda _: None,
    )
    first = client.post("example/live", {"keyword": "seo"})
    second = client.post("example/live", {"keyword": "seo"})

    assert first == second
    assert calls == 1


def test_business_error_is_raised(tmp_path):
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"tasks": [{
            "status_code": 40101, "status_message": "Invalid credentials", "result": None
        }]})
    )
    client = DataForSEOClient(
        username="user", password="pass", cache_path=tmp_path / "cache.db", transport=transport
    )

    with pytest.raises(DataForSEOError, match="Invalid credentials"):
        client.get_result("example/live", {})


def test_retries_server_errors(tmp_path):
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        if calls < 3:
            return httpx.Response(500, json={"message": "temporary"})
        return httpx.Response(200, json=success([{"keyword": "seo"}]))

    client = DataForSEOClient(
        username="user", password="pass", cache_path=tmp_path / "cache.db",
        transport=httpx.MockTransport(handler), sleep=lambda _: None,
    )

    assert client.get_result("example/live", {}) == [{"keyword": "seo"}]
    assert calls == 3


def test_flattens_results_from_multiple_tasks(tmp_path):
    response = {"tasks": [
        {"status_code": 20000, "result": [{"keyword": "one"}]},
        {"status_code": 20000, "result": [{"keyword": "two"}]},
    ]}
    client = DataForSEOClient(
        username="user", password="pass", cache_path=tmp_path / "cache.db",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=response)),
    )

    assert client.get_result("example/live", {}) == [{"keyword": "one"}, {"keyword": "two"}]

