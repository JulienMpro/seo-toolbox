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
    display_name: str = ""
    cta: str = ""
    no_api: bool = False
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


_DISPLAY_OVERRIDES = {
    "amazon_asin": "Amazon ASIN",
    "brand_visibility_ia": "Brand Visibility IA",
    "bytes_human": "Human-readable Bytes",
    "cac_ltv": "CAC / LTV",
    "canonical_hreflang_check": "Canonical / Hreflang Check",
    "check_http": "Check HTTP",
    "csv_json": "CSV ↔ JSON",
    "ctr_curve": "CTR Curve",
    "eeat_score": "E-E-A-T Score",
    "faq_generator": "FAQ Generator",
    "html_entities": "HTML Entities",
    "html_to_md": "HTML to Markdown",
    "http_status_bulk": "HTTP Status Bulk",
    "implicit_cpc": "Implicit CPC",
    "jsonld_article": "JSON-LD Article",
    "jsonld_breadcrumb": "JSON-LD Breadcrumb",
    "jsonld_event": "JSON-LD Event",
    "jsonld_extract": "JSON-LD Extract",
    "jsonld_faq": "JSON-LD FAQ",
    "jsonld_howto": "JSON-LD HowTo",
    "jsonld_jobposting": "JSON-LD JobPosting",
    "jsonld_localbusiness": "JSON-LD LocalBusiness",
    "jsonld_minify": "JSON-LD Minify",
    "jsonld_organization": "JSON-LD Organization",
    "jsonld_product": "JSON-LD Product",
    "jsonld_review": "JSON-LD Review",
    "jsonld_validate": "JSON-LD Validate",
    "list_to_urls": "List to URLs",
    "llm_response_extract": "LLM Response Extract",
    "llm_volume": "LLM Search Volume",
    "lighthouse_cwv": "Lighthouse CWV",
    "lorem_seo": "Lorem SEO",
    "md_to_html": "Markdown to HTML",
    "ngrams": "N-grams",
    "og_generator": "OG Generator",
    "og_validator": "OG Validator",
    "paa_extractor": "PAA Extractor",
    "pbn_detection": "PBN Detection",
    "roi_seo": "SEO ROI",
    "serp_compare": "SERP Compare",
    "serp_countries": "SERP Countries",
    "serp_devices": "SERP Devices",
    "serp_features": "SERP Features",
    "serp_history": "SERP History",
    "serp_snapshot": "SERP Snapshot",
    "seo_projection": "SEO Projection",
    "sitemap_diff": "Sitemap Diff",
    "tfidf_analysis": "TF-IDF Analysis",
    "url_decode": "URL Decode",
    "url_encode": "URL Encode",
    "url_syntax": "URL Syntax",
    "whois_lite": "WHOIS Lite",
}


def _display_name(name: str) -> str:
    """Human-facing tool name; keep this deterministic and registry independent."""
    if name in _DISPLAY_OVERRIDES:
        return _DISPLAY_OVERRIDES[name]
    words = name.split("_")
    small_words = {"to", "by", "of", "and", "for", "in", "on", "at", "a", "an", "the"}
    display = " ".join(
        word.lower() if index and word.lower() in small_words else word.capitalize()
        for index, word in enumerate(words)
    )
    return display.replace("Co Occurrence", "Co-occurrence")


# List/single tools need a literal, honest verb + object CTA (never generic "Run").
_CTA_OVERRIDES = {
    "anchor_distribution": "Analyze anchors", "amazon_asin": "Inspect ASIN",
    "amazon_competitors": "Find competitors", "amazon_product_keywords": "Find keywords",
    "amazon_products": "Find products", "amazon_sellers": "Find sellers",
    "authority_score": "Score authority", "brand_mentions": "Find mentions",
    "brand_visibility_ia": "Measure visibility", "broken_link_building": "Find opportunities",
    "cannibalization": "Find conflicts", "check_http": "Check response",
    "competitor_benchmark": "Benchmark competitors", "competitor_keywords": "Find keywords",
    "content_brief": "Build brief", "content_length_target": "Set target",
    "content_summary": "Summarize content", "difficulty_score": "Score difficulty",
    "disavow_generator": "Build disavow", "dofollow_ratio": "Measure ratio",
    "domain_compare": "Compare domains", "faq_generator": "Generate FAQs",
    "features_matrix": "Compare features", "google_trends": "Explore trends",
    "intent_analysis": "Classify intent", "intent_mix": "Analyze intent",
    "instant_audit": "Audit page",
    "jsonld_extract": "Extract JSON-LD",
    "keyword_expansion": "Expand keywords", "keyword_gap": "Find keyword gaps",
    "keyword_prioritization": "Prioritize keywords", "keyword_suggestions_tool": "Find suggestions",
    "link_gap": "Find gaps", "link_profile_compare": "Compare profiles",
    "link_profile_evolution": "Track links", "llm_response_extract": "Extract response",
    "llm_volume": "Check volume", "most_linked_pages": "Find top pages",
    "meta_raw_extractor": "Extract metadata",
    "new_lost_links": "Track changes", "paa_extractor": "Extract questions",
    "pbn_detection": "Detect PBNs", "phrase_trends": "Track phrase",
    "prospect_emails": "Find emails", "rank_bulk": "Check ranks",
    "referring_domains_analysis": "Analyze domains", "serp_compare": "Compare SERPs",
    "serp_countries": "Compare countries", "serp_devices": "Compare devices",
    "serp_features": "Inspect features", "serp_history": "View history",
    "serp_snapshot": "Capture SERP", "technology_detection": "Detect technology",
    "topic_clusters": "Build clusters", "top_searches": "Find top searches",
    "toxic_links": "Find toxic links", "traffic_potential": "Estimate traffic",
    "trends_by_region": "Compare regions", "trends_demography": "Analyze audience",
    "whois_lite": "Inspect WHOIS", "youtube_comments": "Fetch comments",
    "youtube_keywords": "Find keywords", "youtube_transcript": "Fetch transcript",
    "youtube_video_info": "Inspect video",
}


# Explicitly means "no DataForSEO credits"; some entries still fetch public URLs.
_NO_API_TOOLS = frozenset({
    "ads_equivalent", "anchor_generator", "backlink_value", "breadcrumb_generator",
    "bytes_human", "cac_ltv", "canonical_generator", "canonical_hreflang_check",
    "case_convert", "check_http", "content_cost", "conversion_rate",
    "count_text", "crawl_time", "csv_json", "date_convert", "dedupe_list",
    "eeat_score", "entity_extractor", "extract_emails", "extract_urls",
    "heading_checker", "hreflang_generator", "html_entities", "html_to_md",
    "http_status_bulk", "implicit_cpc", "internal_anchors", "internal_link_generator",
    "internal_link_score", "jsonld_article", "jsonld_breadcrumb", "jsonld_event",
    "jsonld_extract", "jsonld_faq", "jsonld_howto", "jsonld_jobposting",
    "jsonld_localbusiness", "jsonld_minify", "jsonld_organization", "jsonld_product",
    "jsonld_review", "jsonld_validate", "keyword_density", "keyword_extractor",
    "list_to_urls", "lorem_seo", "md_to_html", "merge_candidates", "meta_generator",
    "meta_raw_extractor", "meta_variants", "ngrams", "og_generator", "opportunity_cost",
    "organic_revenue", "page_similarity", "position_value", "prompt_generator",
    "readability", "redirect_chain", "redirect_generator", "redirect_map_generator",
    "robots_checker", "robots_generator", "roi_seo", "schema_validator",
    "sitemap_diff", "sitemap_generator", "sitemap_split", "sitemap_validator",
    "snippet_generator", "strip_accents", "text_diff", "text_to_slug", "time_to_rank",
    "title_meta_analyzer", "title_variants", "tokenize", "traffic_projection",
    "tz_convert", "url_decode", "url_encode", "url_syntax",
})


_ARCHETYPE_CTAS = {
    "converter": "Convert", "compare": "Compare", "checker": "Check",
    "analyzer": "Analyze", "calculator": "Calculate", "checklist": "Calculate score",
    "generator": "Generate", "schema": "Generate JSON-LD",
}


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
        prospect_emails domain_compare cannibalization"""),
    "single": _names("""paa_extractor serp_features serp_devices serp_countries serp_history
        keyword_suggestions_tool top_searches content_length_target keyword_expansion
        content_brief faq_generator llm_response_extract brand_mentions competitor_keywords
        phrase_trends content_summary google_trends trends_by_region trends_demography
        youtube_keywords youtube_video_info youtube_comments youtube_transcript amazon_products
        amazon_product_keywords amazon_competitors amazon_sellers amazon_asin anchor_distribution
        dofollow_ratio disavow_generator toxic_links referring_domains_analysis
        new_lost_links link_profile_evolution most_linked_pages pbn_detection broken_link_building
        whois_lite technology_detection instant_audit check_http meta_raw_extractor serp_snapshot
        jsonld_extract brand_visibility_ia link_gap"""),
    "checker": _names("""http_status_bulk redirect_chain robots_checker sitemap_validator
        canonical_checker hreflang_checker schema_validator viewport_checker og_validator
        mixed_content url_syntax hreflang_reciprocity title_meta_validator
        canonical_hreflang_check lighthouse_cwv"""),
    "analyzer": _names("""keyword_density co_occurrence ngrams readability thin_content
        entity_extractor keyword_extractor page_similarity heading_checker title_meta_analyzer
        internal_anchors internal_link_score merge_candidates content_length tfidf_analysis
        content_audit jsonld_validate"""),
    "calculator": _names("""roi_seo traffic_projection position_value ads_equivalent
        conversion_rate implicit_cpc cac_ltv crawl_time sitemap_split backlink_value content_cost
        time_to_rank opportunity_cost organic_revenue seo_projection"""),
    "checklist": {"eeat_score"},
    "generator": _names("""redirect_generator robots_generator sitemap_generator meta_generator
        hreflang_generator anchor_generator title_variants meta_variants internal_link_generator
        breadcrumb_generator snippet_generator canonical_generator og_generator prompt_generator
        redirect_map_generator semantic_silo editorial_calendar effort_impact lorem_seo ctr_curve"""),
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
    "click_rate": "Click realization rate (%)", "conversions": "Conversions",
    "articles": "Articles", "user_agent": "User agent", "x_default": "Default-language URL",
    "force_https": "Force HTTPS", "remove_www": "Remove www", "remove_trailing_slash": "Remove trailing slash",
    "remove_params": "Parameters to remove", "site_name": "Site name", "time_range": "Time range",
    "spam_threshold": "Spam threshold", "same_as": "Profile URLs (one per line)",
    "date_published": "Publication date", "date_modified": "Modified date", "opening_hours": "Opening hours",
    "price_range": "Price range", "rating_value": "Rating value", "review_count": "Review count",
    "item_reviewed": "Item reviewed", "review_body": "Review text", "start_date": "Start date",
    "end_date": "End date", "location_name": "Location name", "location_address": "Location address",
    "offers_price": "Offer price", "total_time": "Total time", "hiring_organization": "Hiring organization",
    "employment_type": "Employment type", "date_posted": "Posting date", "valid_through": "Valid through",
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
    "text_diff.mode": ["unified", "side-by-side"],
    "ctr_curve.device": ["both", "desktop", "mobile"],
    "og_generator.type": ["website", "article", "product", "profile"],
    "prompt_generator.type": ["audit", "brief", "geo", "meta", "strategy", "email"],
    "jsonld_product.availability": ["InStock", "OutOfStock", "PreOrder", "Discontinued"],
    "jsonld_jobposting.employment_type": ["FULL_TIME", "PART_TIME", "CONTRACTOR", "TEMPORARY", "INTERN", "VOLUNTEER", "PER_DIEM", "OTHER"],
    "google_trends.time_range": ["", "past_day", "past_7_days", "past_30_days", "past_90_days", "past_year", "past_5_years"],
    "date_convert.input_format": ["iso", "timestamp", "fr", "lastmod"],
    "date_convert.output_format": ["iso", "timestamp", "fr", "lastmod"],
}


def _humanize(name: str) -> str:
    return _LABELS.get(name, name.replace("_", " ").capitalize())


def _placeholder(name: str, label: str, help_text: str) -> str:
    return help_text.strip() or f"Enter {label.rstrip('.').lower()}"


def _base_ui(name: str, archetype: str) -> ToolUI:
    spec = REGISTRY[name]
    hints = get_type_hints(spec.fn)
    labels = {arg.name: _humanize(arg.name) for arg in spec.args}
    placeholders = {arg.name: _placeholder(arg.name, labels[arg.name], arg.help) for arg in spec.args}
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
    return ToolUI(
        archetype=archetype, display_name=_display_name(name),
        cta=_CTA_OVERRIDES.get(name, _ARCHETYPE_CTAS.get(archetype, "")),
        no_api=name in _NO_API_TOOLS, labels=labels, widgets=widgets,
        choices=choices, placeholders=placeholders, result_mode=mode,
    )


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
TOOL_UI["jsonld_validate"].widgets["value"] = "textarea"
TOOL_UI["brand_visibility_ia"].widgets["engines"] = "text"
TOOL_UI["link_gap"].widgets["competitor"] = "text"
TOOL_UI["jsonld_faq"].widgets["qa"] = "textarea"
TOOL_UI["snippet_generator"].widgets["content"] = "textarea"
TOOL_UI["tz_convert"].placeholders.update({"source": "Europe/Paris", "target": "America/New_York"})
TOOL_UI["roi_seo"].examples.update({"budget": "2000", "basket": "300", "margin": "40", "conversion": "2", "months": "12", "traffic": "1000", "growth": "5"})
TOOL_UI["dedupe_list"].examples["value"] = "technical seo\ncontent audit\ntechnical seo\nlink building\ncontent audit"
TOOL_UI["redirect_generator"].examples.update({"old": "/old-page\n/legacy-guide", "new": "/new-page\n/updated-guide"})
TOOL_UI["jsonld_faq"].examples["qa"] = "What is a canonical URL?|A canonical URL identifies the preferred version of a page.\nWhat is a sitemap?|A sitemap lists URLs available for crawling."
TOOL_UI["http_status_bulk"].examples["urls"] = "https://example.com\nhttps://example.com/about\nhttps://www.iana.org/domains/reserved"
TOOL_UI["csv_json"].examples["value"] = "keyword,volume\ntechnical seo,900\ncontent audit,500"
TOOL_UI["keyword_density"].examples.update({"text": "A technical SEO audit finds crawl, indexation, and page quality issues. Regular SEO audits help teams prioritize fixes.", "keyword": "SEO"})
TOOL_UI["url_encode"].examples["value"] = "https://example.com/search?q=technical seo"
for _name in ("serp_compare", "features_matrix", "competitor_benchmark", "link_profile_compare", "domain_compare"):
    TOOL_UI[_name].best_highlight = True
for _name in ("paa_extractor", "keyword_suggestions_tool", "amazon_products", "brand_mentions"):
    TOOL_UI[_name].serp_style = True
for _name in ("http_status_bulk", "redirect_chain", "robots_checker", "sitemap_validator",
              "canonical_checker", "hreflang_checker", "schema_validator", "viewport_checker",
              "og_validator", "mixed_content", "url_syntax", "hreflang_reciprocity",
              "title_meta_validator", "canonical_hreflang_check", "lighthouse_cwv", "jsonld_validate"):
    TOOL_UI[_name].badge_columns = {"status": {"ok": ["ok", "valid", "200", "pass"], "warn": ["warn", "redirect"], "err": ["error", "invalid", "fail", "404", "500"]}}

_BOOL_BADGES = {"ok": ["true", "yes", "present"], "warn": [], "err": ["false", "no", "missing"]}
TOOL_UI["sitemap_validator"].badge_columns.update({"valid": _BOOL_BADGES})
TOOL_UI["canonical_checker"].badge_columns.update({
    "present": _BOOL_BADGES, "self_canonical": _BOOL_BADGES,
    "conflict": {"ok": ["false", "no"], "warn": [], "err": ["true", "yes"]},
})
TOOL_UI["og_validator"].badge_columns.update({
    key: _BOOL_BADGES for key in ("og_title", "og_description", "og_image", "twitter_card")
})
TOOL_UI["title_meta_analyzer"].badge_columns = {
    "title_ok": _BOOL_BADGES, "meta_ok": _BOOL_BADGES,
    "duplicate": {"ok": ["false", "no"], "warn": [], "err": ["true", "yes"]},
    "truncated": {"ok": ["false", "no"], "warn": [], "err": ["true", "yes"]},
}

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
            "placeholder": ui.placeholders.get(arg.name) or ui.examples.get(arg.name) or _placeholder(arg.name, ui.labels.get(arg.name, _humanize(arg.name)), arg.help),
        }
        for arg in spec.args
    ]
    return data
