"""Exhaustive, zero-network conformance checks for all mini-tool pages."""

from __future__ import annotations

import asyncio
import json
import re
from collections import Counter

import httpx
import pytest
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from api.main import app
from seotoolbox.tools import REGISTRY
from seotoolbox.tools.ui import similar_tools, ui_for


CTAS = {
    "converter": "Convert", "compare": "Compare", "list": "Run", "single": "Run",
    "checker": "Check", "analyzer": "Analyze", "calculator": "Calculate",
    "checklist": "Calculate score", "generator": "Generate", "schema": "Generate JSON-LD",
}
VALID_WIDGETS = {"textarea", "select", "text", "number", "checkbox"}
LIST_INPUTS = {"urls", "paths", "qa", "steps", "content"}
BATCH_LIST_INPUTS = {
    "keywords", "urls", "domains", "competitors", "pages", "actions",
    "old", "new", "paths", "data",
}
PRIMARY_INPUTS = {"domain", "url", "keyword", "video", "asin", "brand", "value", "seed", "question", "item", "category"}
COMPOUND_SINGLE_INPUTS = {
    "brand_visibility_ia": {"brand", "keyword"},
    "link_gap": {"domain", "competitor"},
}


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


def _page(name: str) -> tuple[BeautifulSoup, dict]:
    response = client.get(f"/tools/{name}")
    assert response.status_code == 200
    soup = BeautifulSoup(response.text, "html.parser")
    node = soup.select_one("#tool-data")
    assert node is not None
    return soup, json.loads(node.get_text())


@pytest.mark.parametrize("name", sorted(REGISTRY))
def test_tool_page_conformance(name: str) -> None:
    spec = REGISTRY[name]
    soup, data = _page(name)
    text = soup.get_text(" ", strip=True)
    assert name in text
    assert spec.description in text
    assert soup.select_one("#tool-form") is not None
    submit = soup.select_one("#tool-form button[type=submit]")
    # CTA copy is now tool-specific and comes from the serialized ToolUI metadata.
    assert submit is not None and submit.get_text(strip=True) == ui_for(name).cta
    assert soup.select_one('nav[aria-label="Breadcrumb"]') is not None
    assert "Example command" in text
    assert data["archetype"] == ui_for(name).archetype
    for arg in data["args"]:
        assert arg["label"].strip()
        assert arg["widget"] in VALID_WIDGETS
        assert arg["placeholder"] is not None and str(arg["placeholder"]).strip()
        if arg["widget"] == "select":
            assert arg["choices"]
    ids = [node["id"] for node in soup.select("[id]")]
    assert len(ids) == len(set(ids))
    related = similar_tools(name)
    section = next((h.parent for h in soup.find_all("h2") if h.get_text(strip=True) == "Related tools"), None)
    assert (section is not None) == bool(related)
    if section:
        links = [a.get("href") for a in section.select('a[href^="/tools/"]')]
        assert links
        assert all(link.removeprefix("/tools/") in REGISTRY for link in links)


@pytest.mark.parametrize("name", sorted(REGISTRY))
def test_tool_archetype_conformance(name: str) -> None:
    _, data = _page(name)
    args = data["args"]
    archetype = data["archetype"]
    textareas = [arg for arg in args if arg["widget"] == "textarea"]
    required = [arg for arg in args if arg["required"]]
    if archetype == "converter":
        main = [arg for arg in textareas if arg["name"] in {"value", "text"}]
        assert len(main) == 1 and len(textareas) == 1
        assert all(arg["widget"] == "select" for arg in args if "mode" in arg["name"])
    elif archetype == "compare":
        assert len(textareas) == 2
        assert {arg["name"] for arg in textareas} in ({"before", "after"}, {"text1", "text2"}, {"indexed", "urls"})
    elif archetype == "checker":
        url_args = [arg for arg in args if arg["name"] in {"url", "urls"}]
        assert url_args
        assert all(arg["widget"] == ("textarea" if arg["name"] == "urls" else "text") for arg in url_args)
    elif archetype == "analyzer":
        scalar_text_inputs = [
            arg for arg in args
            if arg["widget"] == "text" and arg["name"] in {"text", "value", "data"}
        ]
        assert textareas or scalar_text_inputs
    elif archetype == "calculator":
        assert all(arg["widget"] == "number" for arg in args)
    elif archetype == "checklist":
        assert all(arg["widget"] == "checkbox" for arg in args)
    elif archetype in {"generator", "schema"}:
        assert all(arg["widget"] != "textarea" or arg["name"] in LIST_INPUTS or arg["name"].endswith("s") for arg in required)
        assert all("_" not in arg["label"] for arg in args)
    elif archetype == "single":
        if name in COMPOUND_SINGLE_INPUTS:
            assert {arg["name"] for arg in required} == COMPOUND_SINGLE_INPUTS[name]
            assert all(arg["widget"] == "text" for arg in required)
            return
        candidates = required or args
        primary = [arg for arg in candidates if arg["name"] in PRIMARY_INPUTS and arg["widget"] != "select"]
        assert len(primary) == 1
        assert all(arg in primary for arg in required)
    elif archetype == "list":
        batch_inputs = [
            arg for arg in textareas
            if arg["name"] in BATCH_LIST_INPUTS
            or (arg["name"] == "value" and "one per line" in arg["label"].lower())
        ]
        assert batch_inputs


# Deliberately explicit: every entry below is implemented without HTTP or DataForSEO.
LOCAL_TOOLS = {
    "url_encode", "url_decode", "text_to_slug", "list_to_urls", "md_to_html", "html_to_md",
    "csv_json", "case_convert", "strip_accents", "date_convert", "bytes_human", "tokenize",
    "dedupe_list", "html_entities", "jsonld_minify", "extract_emails", "extract_urls", "count_text",
    "tz_convert", "text_diff", "sitemap_diff", "keyword_rank_change", "indexation_checker",
    "keyword_density", "co_occurrence", "ngrams", "readability", "thin_content", "entity_extractor",
    "keyword_extractor", "url_syntax", "title_meta_validator", "jsonld_validate",
    "time_to_rank", "opportunity_cost", "organic_revenue", "roi_seo", "traffic_projection",
    "position_value", "ctr_curve", "ads_equivalent", "conversion_rate", "implicit_cpc", "cac_ltv",
    "crawl_time", "sitemap_split", "eeat_score", "backlink_value", "content_cost", "seo_projection",
    "redirect_generator", "robots_generator", "sitemap_generator", "meta_generator", "hreflang_generator",
    "anchor_generator", "title_variants", "meta_variants", "internal_link_generator",
    "breadcrumb_generator", "snippet_generator", "canonical_generator", "og_generator",
    "prompt_generator", "redirect_map_generator", "editorial_calendar", "semantic_silo", "effort_impact",
    "lorem_seo", "jsonld_article", "jsonld_faq", "jsonld_localbusiness", "jsonld_product",
    "jsonld_breadcrumb", "jsonld_review", "jsonld_event", "jsonld_organization", "jsonld_howto",
    "jsonld_jobposting",
}


def _samples(name: str) -> dict[str, object]:
    values: dict[str, object] = {
        "value": "Hello world", "text": "Alice writes useful SEO content for Paris.",
        "text1": "before text", "text2": "after text", "before": "https://example.com/a",
        "after": "https://example.com/b", "indexed": "https://example.com/a",
        "urls": "https://example.com/a\nhttps://example.com/b", "url": "https://example.com/page",
        "keywords": "seo tools\nkeyword research", "keyword": "seo", "domains": "example.com\nexample.org",
        "domain": "example.com", "pages": "/guide|seo guide\n/tools|seo tools", "paths": "Home|/\nTools|/tools",
        "qa": "What is SEO?|Search engine optimization.", "steps": "Research\nWrite\nPublish",
        "content": "First point\nSecond point", "actions": "Technical audit|2|5\nContent plan|3|4",
        "old": "/old", "new": "/new", "title": "SEO guide", "description": "A practical SEO guide",
        "headline": "SEO guide", "author": "Alice", "date_published": "2026-01-01", "name": "Example",
        "address": "1 Main Street", "item_reviewed": "SEO Toolbox", "rating_value": 4,
        "start_date": "2026-09-01", "hiring_organization": "Example Ltd", "subject": "technical SEO",
        "template": "{kw} guide", "image": "https://example.com/image.jpg", "budget": 1000,
        "basket": 100, "margin": 40, "conversion": 2, "months": 12, "traffic": 1000,
        "volume": 1000, "cpc": 1.5, "position": 3, "ctr": 20, "current_ctr": 5,
        "target_ctr": 10, "clicks": 100, "visits": 1000, "conversions": 20, "cost": 500,
        "customers": 10, "ltv": 1000, "pages": 100, "urls_per_second": 2, "kd": 30,
        "authority": 40, "age": 24, "referral_traffic": 100, "words": 1000, "rate": 0.1,
        "current_traffic": 1000, "growth": 5, "value_per_visit": 1,
    }
    special = {
        "csv_json": {"value": "name,value\nseo,1", "mode": "csv2json"},
        "case_convert": {"value": "hello world", "mode": "title"},
        "date_convert": {"value": "2026-01-01", "input_format": "iso", "output_format": "timestamp"},
        "bytes_human": {"value": "1024"}, "jsonld_minify": {"value": '{"@type":"Thing"}'},
        "tz_convert": {"value": "2026-01-01 12:00", "source": "Europe/Paris", "target": "UTC"},
        "thin_content": {"value": "Useful local text with enough words to analyze.", "text": True},
        "title_meta_validator": {"title": "Useful SEO title", "meta": "A useful meta description for this page."},
        "jsonld_validate": {"value": '{"@context":"https://schema.org","@type":"Article","headline":"Test"}'},
        "ctr_curve": {}, "eeat_score": {"author": True, "sources": True},
        "internal_link_generator": {"pages": "SEO guide|https://example.com/guide\nSEO tools|https://example.com/tools", "keywords": "seo guide"},
        "keyword_rank_change": {"before": "keyword,position\nseo,5", "after": "keyword,position\nseo,3"},
        "sitemap_split": {"urls": 100},
        "prompt_generator": {"type": "audit", "subject": "technical SEO"},
        "jsonld_product": {"name": "Widget"}, "jsonld_review": {"item_reviewed": "Widget", "author": "Alice", "rating_value": 4},
        "jsonld_event": {"name": "SEO Day", "start_date": "2026-09-01"},
        "jsonld_howto": {"name": "Audit a site", "steps": "Crawl\nReview"},
        "jsonld_jobposting": {"title": "SEO", "description": "SEO role", "hiring_organization": "Example"},
    }
    if name in special:
        return special[name]
    return {arg.name: values[arg.name] for arg in REGISTRY[name].args if arg.required}


def test_local_run_inventory_is_complete_and_disjoint() -> None:
    assert LOCAL_TOOLS <= set(REGISTRY)
    assert len(LOCAL_TOOLS) + len(set(REGISTRY) - LOCAL_TOOLS) == 165


@pytest.mark.parametrize("name", sorted(LOCAL_TOOLS))
def test_local_tool_run_smoke(name: str) -> None:
    response = client.post(f"/api/tools/{name}/run", json=_samples(name))
    assert response.status_code == 200, response.text
    payload = response.json()
    assert "error" not in payload
    assert payload["returns"] in {"str", "table"}
    assert payload["output"] is not None


def test_conformance_inventory_counts() -> None:
    archetypes = Counter(ui_for(name).archetype for name in REGISTRY)
    assert sum(archetypes.values()) == 165
    assert len(LOCAL_TOOLS) > 0
    assert len(set(REGISTRY) - LOCAL_TOOLS) > 0
