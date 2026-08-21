"""Data-driven presentation hints for the mini-tools web UI."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, get_type_hints

from . import REGISTRY, ToolSpec


ARCHETYPES = frozenset(
    {"converter", "compare", "list", "single", "checker", "analyzer",
     "calculator", "checklist", "generator", "schema"}
)


@dataclass
class ToolUI:
    archetype: str
    labels: dict[str, str] = field(default_factory=dict)
    widgets: dict[str, str] = field(default_factory=dict)
    choices: dict[str, list[str]] = field(default_factory=dict)
    placeholders: dict[str, str] = field(default_factory=dict)
    examples: dict[str, str] = field(default_factory=dict)
    syntax: str = "plain"
    result_mode: str = "table"
    badge_columns: dict[str, dict] = field(default_factory=dict)
    best_highlight: bool = False
    serp_style: bool = False
    result_labels: dict[str, str] = field(default_factory=dict)


def _names(value: str) -> set[str]:
    return set(value.split())


# Every registered name is deliberately assigned here. Grouping keeps the mapping
# reviewable without duplicating 165 nearly-identical constructor calls.
_BY_ARCHETYPE = {
    "converter": _names("""url_encode url_decode text_to_slug list_to_urls md_to_html
        html_to_md csv_json case_convert strip_accents date_convert bytes_human tokenize
        dedupe_list html_entities jsonld_minify extract_emails extract_urls count_text
        tz_convert"""),
    "compare": _names("sitemap_diff keyword_rank_change indexation_checker text_diff"),
    "list": _names("""serp_compare rank_bulk intent_analysis keyword_gap features_matrix
        llm_volume keyword_prioritization difficulty_score topic_clusters intent_mix
        traffic_potential competitor_benchmark link_profile_compare authority_score
        prospect_emails domain_compare cannibalization competitor_keywords"""),
    "single": _names("""paa_extractor serp_features serp_devices serp_countries serp_history
        keyword_suggestions_tool top_searches content_length_target keyword_expansion
        content_brief faq_generator llm_response_extract brand_visibility_ia brand_mentions
        phrase_trends content_summary google_trends trends_by_region trends_demography
        youtube_keywords youtube_video_info youtube_comments youtube_transcript amazon_products
        amazon_product_keywords amazon_competitors amazon_sellers amazon_asin anchor_distribution
        dofollow_ratio disavow_generator toxic_links link_gap referring_domains_analysis
        new_lost_links link_profile_evolution most_linked_pages pbn_detection broken_link_building
        whois_lite technology_detection instant_audit check_http meta_raw_extractor serp_snapshot
        jsonld_extract"""),
    "checker": _names("""http_status_bulk redirect_chain robots_checker sitemap_validator
        canonical_checker hreflang_checker schema_validator viewport_checker og_validator
        mixed_content url_syntax hreflang_reciprocity title_meta_validator
        canonical_hreflang_check lighthouse_cwv jsonld_validate"""),
    "analyzer": _names("""keyword_density co_occurrence ngrams readability thin_content
        entity_extractor keyword_extractor page_similarity heading_checker title_meta_analyzer
        internal_anchors internal_link_score merge_candidates content_length tfidf_analysis
        content_audit"""),
    "calculator": _names("""roi_seo traffic_projection position_value ctr_curve ads_equivalent
        conversion_rate implicit_cpc cac_ltv crawl_time sitemap_split backlink_value content_cost
        time_to_rank opportunity_cost organic_revenue seo_projection"""),
    "checklist": {"eeat_score"},
    "generator": _names("""redirect_generator robots_generator sitemap_generator meta_generator
        hreflang_generator anchor_generator title_variants meta_variants internal_link_generator
        breadcrumb_generator snippet_generator canonical_generator og_generator prompt_generator
        redirect_map_generator semantic_silo editorial_calendar effort_impact lorem_seo"""),
    "schema": _names("""jsonld_article jsonld_faq jsonld_localbusiness jsonld_product
        jsonld_breadcrumb jsonld_review jsonld_event jsonld_organization jsonld_howto
        jsonld_jobposting"""),
}


_LABELS = {
    "value": "Input", "text": "Text", "text1": "Text 1", "text2": "Text 2",
    "before": "Before", "after": "After", "indexed": "Indexed export",
    "urls": "URLs (one per line)", "url": "URL", "keywords": "Keywords (one per line)",
    "keyword": "Keyword", "domains": "Domains (one per line)", "domain": "Domain",
    "competitors": "Competitors (one per line)", "pages": "Pages (one per line)",
    "paths": "Paths (one per line)", "data": "Audit data", "qa": "Questions and answers",
    "actions": "Actions (one per line)", "country": "Country", "lang": "Language",
    "language": "Language", "limit": "Result limit", "days": "Days",
    "months": "Months", "strategy": "Strategy", "engine": "Engine",
    "mode": "Mode", "input_format": "Input format", "output_format": "Output format",
    "source": "Source timezone", "target": "Target timezone", "budget": "Budget (€)",
    "basket": "Average order value (€)", "margin": "Margin (%)",
    "conversion": "Conversion rate (%)", "growth": "Monthly growth (%)",
    "traffic": "Monthly visits", "volume": "Monthly searches", "cpc": "CPC (€)",
    "cost": "Cost (€)", "rate": "Rate (€ per word)", "clicks": "Clicks",
    "visits": "Visits", "customers": "Customers", "ltv": "Lifetime value (€)",
    "words": "Words", "pages": "Pages", "position": "Position",
    "current_ctr": "Current CTR (%)", "target_ctr": "Target CTR (%)",
    "urls_per_second": "URLs per second", "daily_budget_pct": "Daily budget (%)",
    "referral_traffic": "Monthly referral visits", "authority": "Authority score",
    "kd": "Keyword difficulty", "age": "Domain age (months)",
    "value_per_visit": "Value per visit (€)", "current_traffic": "Current monthly visits",
}

_TEXTAREAS = _names("""value text text1 text2 before after indexed urls keywords domains
    competitors pages paths data qa steps same_as actions old new content description""")
_CHOICES = {
    "country": ["FR", "GB", "US", "DE", "ES", "IT", "BE", "CH", "CA"],
    "lang": ["fr", "en"], "language": ["fr", "en"],
    "strategy": ["mobile", "desktop"], "engine": ["chatgpt", "perplexity", "gemini"],
    "case_convert.mode": ["upper", "lower", "title", "sentence"],
    "csv_json.mode": ["csv2json", "json2csv"],
    "html_entities.mode": ["encode", "decode"],
    "jsonld_minify.mode": ["minify", "beautify"],
    "snippet_generator.type": ["paragraph", "list", "table"],
    "date_convert.input_format": ["iso", "epoch", "fr", "sitemap"],
    "date_convert.output_format": ["iso", "epoch", "fr", "sitemap"],
}


def _humanize(name: str) -> str:
    return _LABELS.get(name, name.replace("_", " ").capitalize())


def _base_ui(name: str, archetype: str) -> ToolUI:
    spec = REGISTRY[name]
    hints = get_type_hints(spec.fn)
    labels = {arg.name: _humanize(arg.name) for arg in spec.args}
    widgets: dict[str, str] = {}
    choices: dict[str, list[str]] = {}
    for arg in spec.args:
        choice = _CHOICES.get(f"{name}.{arg.name}") or _CHOICES.get(arg.name)
        if choice:
            widgets[arg.name], choices[arg.name] = "select", choice
        elif hints.get(arg.name) in {int, float}:
            widgets[arg.name] = "number"
        elif hints.get(arg.name) is bool or arg.is_flag:
            widgets[arg.name] = "checkbox"
        elif arg.name in _TEXTAREAS and (archetype in {"converter", "compare", "analyzer"} or arg.name.endswith("s")):
            widgets[arg.name] = "textarea"
        else:
            widgets[arg.name] = "text"
    mode = "cards" if archetype in {"calculator", "checklist"} else "table"
    if archetype in {"generator", "schema"} and spec.returns == "str":
        mode = "code"
    if archetype == "converter":
        mode = "code"
    return ToolUI(archetype, labels, widgets, choices, result_mode=mode)


TOOL_UI: dict[str, ToolUI] = {
    name: _base_ui(name, archetype)
    for archetype, names in _BY_ARCHETYPE.items()
    for name in names
}

# Focused overrides for behavior that cannot be inferred from the signature.
for _name in ("sitemap_diff", "keyword_rank_change", "indexation_checker"):
    TOOL_UI[_name].result_mode = "sets"
TOOL_UI["text_diff"].result_mode = "diff"
TOOL_UI["text_diff"].result_labels = {"first": "Text 1", "second": "Text 2"}
TOOL_UI["sitemap_diff"].result_labels = {"first": "Before", "second": "After"}
TOOL_UI["keyword_rank_change"].result_labels = {"first": "Before", "second": "After"}
TOOL_UI["indexation_checker"].result_labels = {"first": "Indexed export", "second": "URLs"}
TOOL_UI["thin_content"].labels["text"] = "Value is a URL"
TOOL_UI["tz_convert"].placeholders.update({"source": "Europe/Paris", "target": "America/New_York"})
for _name in ("serp_compare", "features_matrix", "competitor_benchmark", "link_profile_compare", "domain_compare"):
    TOOL_UI[_name].best_highlight = True
for _name in ("paa_extractor", "keyword_suggestions_tool", "amazon_products", "brand_mentions"):
    TOOL_UI[_name].serp_style = True
for _name in ("http_status_bulk", "redirect_chain", "robots_checker", "sitemap_validator",
              "canonical_checker", "hreflang_checker", "schema_validator", "viewport_checker",
              "og_validator", "mixed_content", "url_syntax", "hreflang_reciprocity",
              "title_meta_validator", "canonical_hreflang_check", "lighthouse_cwv", "jsonld_validate"):
    TOOL_UI[_name].badge_columns = {"status": {"ok": ["ok", "valid", "200", "pass"], "warn": ["warn", "redirect"], "err": ["error", "invalid", "fail", "404", "500"]}}

_SYNTAX = {
    "robots_generator": "text", "sitemap_generator": "xml", "hreflang_generator": "plain",
    "breadcrumb_generator": "plain", "og_generator": "plain", "redirect_generator": "htaccess",
    "redirect_map_generator": "htaccess",
}
for _name, _syntax in _SYNTAX.items():
    TOOL_UI[_name].syntax = _syntax
for _name in _BY_ARCHETYPE["schema"]:
    TOOL_UI[_name].syntax = "json"

_missing = set(REGISTRY) - set(TOOL_UI)
_extra = set(TOOL_UI) - set(REGISTRY)
if _missing or _extra:  # Fail at import time when registry and UI drift apart.
    raise RuntimeError(f"Tool UI mapping mismatch: missing={sorted(_missing)}, extra={sorted(_extra)}")


def ui_for(name: str) -> ToolUI:
    return TOOL_UI[name]


def similar_tools(name: str, limit: int = 8) -> list[ToolSpec]:
    spec = REGISTRY[name]
    archetype = ui_for(name).archetype
    candidates = [tool for tool in REGISTRY.values() if tool.category == spec.category and tool.name != name]
    return sorted(candidates, key=lambda tool: (ui_for(tool.name).archetype != archetype, tool.name))[:limit]


def serialize_ui(spec: ToolSpec) -> dict[str, Any]:
    """Return JSON-safe UI metadata, including a widget description per argument."""
    ui = ui_for(spec.name)
    data = asdict(ui)
    data["args"] = [
        {
            "name": arg.name,
            "label": ui.labels.get(arg.name, _humanize(arg.name)),
            "widget": ui.widgets.get(arg.name, "text"),
            "choices": ui.choices.get(arg.name, []),
            "placeholder": ui.placeholders.get(arg.name) or ui.examples.get(arg.name) or arg.help,
        }
        for arg in spec.args
    ]
    return data
