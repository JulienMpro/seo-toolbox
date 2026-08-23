"""Tests for dedicated, data-driven mini-tool pages."""

import asyncio

import httpx
from fastapi.testclient import TestClient
import pytest

from api.main import _serialize_tool, app
from seotoolbox.tools import REGISTRY
from seotoolbox.tools.ui import ARCHETYPES, TOOL_UI, similar_tools, ui_for


class _SyncASGITransport(httpx.BaseTransport):
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
client._transport = _SyncASGITransport()  # type: ignore[attr-defined]


def test_ui_mapping_complete() -> None:
    assert set(TOOL_UI) == set(REGISTRY)
    assert all(ui.archetype in ARCHETYPES for ui in TOOL_UI.values())
    assert all(ui.display_name and "_" not in ui.display_name for ui in TOOL_UI.values())


@pytest.mark.parametrize(
    ("name", "display_name"),
    [
        ("brand_visibility_ia", "Brand Visibility IA"),
        ("list_to_urls", "List to URLs"),
        ("time_to_rank", "Time to Rank"),
        ("trends_by_region", "Trends by Region"),
    ],
)
def test_display_names(name: str, display_name: str) -> None:
    assert TOOL_UI[name].display_name == display_name


def test_list_and_single_ctas_are_verbal() -> None:
    focused = [ui for ui in TOOL_UI.values() if ui.archetype in {"list", "single"}]
    assert len(focused) == 64
    assert all(ui.cta and ui.cta != "Run" and len(ui.cta.split()) <= 3 for ui in focused)


def test_no_api_metadata_is_registry_scoped() -> None:
    no_api = {name for name, ui in TOOL_UI.items() if ui.no_api}
    assert no_api
    assert no_api <= set(REGISTRY)


def test_similar_tools() -> None:
    name = "serp_compare"
    related = similar_tools(name, limit=5)
    assert len(related) <= 5
    assert all(tool.name != name for tool in related)
    assert all(tool.category == REGISTRY[name].category for tool in related)
    flags = [TOOL_UI[tool.name].archetype == TOOL_UI[name].archetype for tool in related]
    assert flags == sorted(flags, reverse=True)


@pytest.mark.parametrize(
    "name",
    [
        "text_to_slug", "sitemap_diff", "serp_compare", "paa_extractor",
        "http_status_bulk", "keyword_density", "roi_seo", "eeat_score",
        "redirect_generator", "jsonld_article", "text_diff", "lighthouse_cwv",
    ],
)
def test_tool_page_ok(name: str) -> None:
    response = client.get(f"/tools/{name}")
    assert response.status_code == 200
    assert name in response.text
    assert "Related tools" in response.text
    assert "/api/tools/" in response.text


def test_tool_page_unknown() -> None:
    response = client.get("/tools/does_not_exist")
    assert response.status_code == 404
    assert "Tool not found" in response.text
    assert "does not exist" in response.text


def test_tools_grid_no_modal() -> None:
    response = client.get("/tools")
    assert response.status_code == 200
    assert "tool-modal" not in response.text
    assert 'data-category="checkers"' in response.text
    assert 'id="tools-directory"' in response.text
    assert '/static/tools.js' in response.text


def test_command_palette_is_available_globally() -> None:
    for path in ("/", "/tools", "/keywords"):
        response = client.get(path)
        assert 'id="command-palette"' in response.text
        assert 'data-palette-open' in response.text
        assert '/static/catalog.js' in response.text


def test_serialize_ui() -> None:
    payload = _serialize_tool(REGISTRY["text_to_slug"])
    assert payload["archetype"] == "converter"
    assert payload["labels"]["value"] == "Input"
    assert payload["widgets"]["value"] == "textarea"
    assert payload["ui"]["archetype"] == "converter"
    assert payload["display_name"] == "Text to Slug"
    assert payload["cta"] == "Convert"
    assert payload["no_api"] is True
    assert payload["args"][0]["widget"] == "textarea"


def test_focused_ui_overrides() -> None:
    assert ui_for("thin_content").labels["text"] == "Value is a URL"
    assert ui_for("date_convert").widgets["input_format"] == "select"
    assert ui_for("date_convert").choices["input_format"] == ["iso", "timestamp", "fr", "lastmod"]
    assert ui_for("date_convert").choices["output_format"] == ["iso", "timestamp", "fr", "lastmod"]
    assert ui_for("tz_convert").placeholders["source"] == "Europe/Paris"
    assert ui_for("tz_convert").placeholders["target"] == "America/New_York"
