"""Tests for dedicated, data-driven mini-tool pages."""

from fastapi.testclient import TestClient
import pytest

from api.main import _serialize_tool, app
from seotoolbox.tools import REGISTRY
from seotoolbox.tools.ui import ARCHETYPES, TOOL_UI, similar_tools, ui_for


client = TestClient(app)


def test_ui_mapping_complete() -> None:
    assert set(TOOL_UI) == set(REGISTRY)
    assert all(ui.archetype in ARCHETYPES for ui in TOOL_UI.values())


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


def test_serialize_ui() -> None:
    payload = _serialize_tool(REGISTRY["text_to_slug"])
    assert payload["archetype"] == "converter"
    assert payload["labels"]["value"] == "Input"
    assert payload["widgets"]["value"] == "textarea"
    assert payload["ui"]["archetype"] == "converter"
    assert payload["args"][0]["widget"] == "textarea"


def test_focused_ui_overrides() -> None:
    assert ui_for("thin_content").labels["text"] == "Value is a URL"
    assert ui_for("date_convert").widgets["input_format"] == "select"
    assert ui_for("date_convert").choices["input_format"] == ["iso", "epoch", "fr", "sitemap"]
    assert ui_for("date_convert").choices["output_format"] == ["iso", "epoch", "fr", "sitemap"]
    assert ui_for("tz_convert").placeholders == {
        "source": "Europe/Paris",
        "target": "America/New_York",
    }
