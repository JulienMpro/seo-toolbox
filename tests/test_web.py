"""Tests for the local FastAPI demonstration UI."""

import asyncio
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

from api.main import app
from seotoolbox.tools import ArgSpec, REGISTRY, ToolSpec, list_tools
from seotoolbox.models import (
    AiMention, AuditReport, BacklinkSummary, CrawlResult, Issue, KeywordIdea,
    ReferringDomain, SerpResult,
)

class _SyncASGITransport(httpx.BaseTransport):
    """Run ASGI requests without Starlette 1.0's blocking portal regression."""

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        async def send() -> tuple[int, httpx.Headers, bytes, dict]:
            transport = httpx.ASGITransport(app=app)
            response = await transport.handle_async_request(request)
            content = await response.aread()
            await transport.aclose()
            return response.status_code, response.headers, content, response.extensions

        status, headers, content, extensions = asyncio.run(send())
        return httpx.Response(status, headers=headers, content=content, extensions=extensions, request=request)


client = TestClient(app)
# Starlette 1.0.1's TestClient portal hangs in this CI environment. Retain the
# FastAPI TestClient API while using httpx's in-process ASGI transport directly.
client._transport = _SyncASGITransport()  # type: ignore[attr-defined]


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.5.0"}


def test_empty_pages_render() -> None:
    for route, heading in (("/", "SEO Toolbox"), ("/keywords", "Keyword Research"),
                           ("/serp", "Live SERP"), ("/geo", "AI Mentions"),
                           ("/backlinks", "Backlink Profile"), ("/audit", "Technical Audit")):
        response = client.get(route)
        assert response.status_code == 200
        assert heading in response.text


def test_tools_page_contains_registry_and_filters() -> None:
    response = client.get("/tools")
    assert response.status_code == 200
    for tool in list_tools():
        assert tool.name in response.text
    assert 'data-category="serp"' in response.text
    assert "Search by name or description" in response.text
    assert "seo tool ${tool.name}" in response.text


def test_tools_api_exposes_all_registry_metadata() -> None:
    response = client.get("/api/tools")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 165
    assert [item["name"] for item in payload] == [tool.name for tool in list_tools()]
    assert set(payload[0]) == {"name", "category", "description", "returns", "args"}
    assert all(arg["type"] in {"str", "int", "float", "bool"} for item in payload for arg in item["args"])
    assert "fn" not in payload[0]


def test_run_text_tool() -> None:
    response = client.post("/api/tools/strip_accents/run", json={"value": "héllo"})
    assert response.status_code == 200
    assert response.json() == {"returns": "str", "output": "hello"}


def test_run_table_tool_returns_dict_rows() -> None:
    response = client.post(
        "/api/tools/sitemap_diff/run",
        json={"before": "https://example.com/a", "after": "https://example.com/b"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["returns"] == "table"
    assert payload["output"][0] == {"status": "new", "url": "https://example.com/b"}


def test_run_tool_rejects_missing_and_unknown_arguments() -> None:
    missing = client.post("/api/tools/strip_accents/run", json={})
    assert missing.status_code == 400
    assert "missing required" in missing.json()["error"]
    unknown = client.post("/api/tools/strip_accents/run", json={"value": "ok", "fn": "bad"})
    assert unknown.status_code == 400
    assert unknown.json() == {"error": "unknown argument: fn"}


def test_run_unknown_tool() -> None:
    response = client.post("/api/tools/not_a_tool/run", json={})
    assert response.status_code == 404
    assert response.json() == {"error": "unknown tool"}


def test_run_tool_coerces_integer_and_boolean(monkeypatch) -> None:
    def typed(count: int, enabled: bool = False) -> str:
        return f"{count}:{enabled}"

    spec = ToolSpec(
        "typed_test", typed, "Test typed arguments.", "misc",
        [ArgSpec("count", True), ArgSpec("enabled", False, is_flag=True)],
    )
    monkeypatch.setitem(REGISTRY, spec.name, spec)
    response = client.post(
        "/api/tools/typed_test/run", json={"count": "10", "enabled": "yes"}
    )
    assert response.status_code == 200
    assert response.json() == {"returns": "str", "output": "10:True"}


def test_run_tool_runtime_error_is_json(monkeypatch) -> None:
    spec = REGISTRY["strip_accents"]

    def fail(value: str) -> str:
        raise OSError("runtime unavailable")

    monkeypatch.setattr(spec, "fn", fail)
    response = client.post("/api/tools/strip_accents/run", json={"value": "hello"})
    assert response.status_code == 500
    assert response.json() == {"error": "runtime unavailable"}


def test_navigation_and_extended_audit_limits() -> None:
    response = client.get("/audit")
    assert 'Tools <span class="nav-badge">165</span>' in response.text
    assert '/tools#calculators' in response.text
    for limit in (5, 10, 25, 50, 100, 250, 500, 1000):
        assert f">{limit}</option>" in response.text


def test_table_export_helpers_are_available_on_every_page() -> None:
    response = client.get("/keywords")
    assert 'aria-label="Copy table"' in response.text
    assert 'aria-label="Download CSV"' in response.text
    assert "const BOM = '\\ufeff'" in response.text
    assert "function tableCsv(table)" in response.text
    assert ".join(';')" in response.text
    assert ".join('\\r\\n')" in response.text
    assert "function tableTsv(table)" in response.text
    assert "return value.replace(/[\\t\\r\\n]+/g, ' ');" in response.text
    assert ".join('\\t')" in response.text
    assert ").join('\\n');" in response.text
    assert "copyText(tableTsv(table))" in response.text
    assert "copyText(tableCsv(table))" not in response.text
    assert "if (value === 'N/D') value = '';" in response.text


@patch("api.main.keywords.ideas", return_value=[KeywordIdea("seo tools", 100, 22, 1.5, search_intent="commercial")])
def test_keywords_results(mock_ideas) -> None:
    response = client.get("/keywords", params={"seed": "seo", "country": "FR", "limit": 5})
    assert response.status_code == 200
    assert "seo tools" in response.text
    assert 'class="exportable" data-export-name="keyword-results"' in response.text
    mock_ideas.assert_called_once_with("seo", "FR", 5)


@patch("api.main.serp.live", return_value=[SerpResult(1, "https://example.com", "example.com", "Example", "Description", "organic")])
def test_serp_results(mock_live) -> None:
    response = client.get("/serp", params={"keyword": "seo", "country": "US", "limit": 10})
    assert response.status_code == 200
    assert "Example" in response.text
    assert 'class="exportable" data-export-name="serp-results"' in response.text
    mock_live.assert_called_once_with("seo", "US", 10)


@patch("api.main.geo.mentions", return_value=[AiMention("seo", "chatgpt", "example.com", 2, 3)])
def test_geo_results(mock_mentions) -> None:
    response = client.get("/geo", params={"keyword": "seo", "engine": "chatgpt"})
    assert response.status_code == 200
    assert "example.com" in response.text
    assert 'class="exportable" data-export-name="ai-mentions"' in response.text
    mock_mentions.assert_called_once_with("seo", ["chatgpt"], limit=50)


@patch("api.main.backlinks.referring_domains", return_value=[ReferringDomain("referrer.com", 4, rank=55)])
@patch("api.main.backlinks.summary", return_value=BacklinkSummary(100, 12, 60, 3.5))
def test_backlink_results(mock_summary, mock_referring) -> None:
    response = client.get("/backlinks", params={"domain": "example.com"})
    assert response.status_code == 200
    assert "referrer.com" in response.text
    assert 'class="exportable" data-export-name="referring-domains"' in response.text
    mock_summary.assert_called_once_with("example.com")
    mock_referring.assert_called_once_with("example.com", limit=10)


@patch("api.main.audit.crawl_site", return_value=[CrawlResult("https://example.com", 200)])
@patch("api.main.audit.analyze", return_value=AuditReport(1, [Issue("https://example.com", "missing_title", "warning", "Missing title")], {"status_codes": {"200": 1}}))
def test_audit_results(mock_analyze, mock_crawl) -> None:
    response = client.get("/audit", params={"url": "https://example.com", "limit": 5})
    assert response.status_code == 200
    assert "Missing title" in response.text
    assert 'class="exportable" data-export-name="audit-issues"' in response.text
    mock_crawl.assert_called_once_with("https://example.com", max_pages=5)


@patch("api.main.audit.crawl_site", return_value=[CrawlResult("https://example.com", 200)])
@patch("api.main.audit.analyze", return_value=AuditReport(1, [], {"status_codes": {"200": 1}}))
@patch("api.main.backlinks.summary", return_value=BacklinkSummary(100, 12, 60, 3.5))
def test_dashboard_quick_check(mock_summary, mock_analyze, mock_crawl) -> None:
    response = client.get("/", params={"domain": "example.com"})
    assert response.status_code == 200
    assert "Quick profile for example.com" in response.text
    mock_crawl.assert_called_once_with("https://example.com", max_pages=10)


@patch("api.main.keywords.ideas", side_effect=RuntimeError("API unavailable"))
def test_api_error_is_rendered(_mock_ideas) -> None:
    response = client.get("/keywords", params={"seed": "seo"})
    assert response.status_code == 200
    assert "API unavailable" in response.text
