"""Focused QA coverage for every generator and converter in this audit batch."""

import inspect
import json

import pytest

from seotoolbox.client import DataForSEOError
from seotoolbox.tools import REGISTRY, converters, generators, ia_tools, refonte, reliquats


GENERATOR_NAMES = {
    "anchor_generator", "breadcrumb_generator", "canonical_generator", "content_brief",
    "faq_generator", "hreflang_generator", "internal_link_generator", "keyword_expansion",
    "meta_generator", "meta_variants", "og_generator", "prompt_generator",
    "redirect_generator", "redirect_map_generator", "robots_generator", "sitemap_generator",
    "snippet_generator", "title_variants",
}
CONVERTER_NAMES = {
    "bytes_human", "case_convert", "csv_json", "date_convert", "dedupe_list",
    "html_entities", "html_to_md", "jsonld_minify", "list_to_urls", "md_to_html",
    "strip_accents", "text_to_slug", "tokenize", "url_decode", "url_encode",
}


def test_registry_contracts_for_entire_batch():
    for name in GENERATOR_NAMES | CONVERTER_NAMES:
        spec = REGISTRY[name]
        signature = inspect.signature(spec.fn)
        assert [arg.name for arg in spec.args] == list(signature.parameters)
        assert spec.returns in {"str", "table"}


def test_all_local_generators_french_and_english_smoke():
    anchors = generators.anchor_generator("plombier Paris")
    assert "guide plombier" in str(anchors)
    assert not {"brand", "naked"} & {row["type"] for row in anchors}
    assert "BreadcrumbList" in generators.breadcrumb_generator("Accueil > Plomberie")
    assert generators.canonical_generator("http://www.x.fr/a/?utm=x", True, True, True, "utm")[-1]["url"] == "https://x.fr/a"
    assert 'hreflang="fr"' in generators.hreflang_generator("fr:https://x.fr\nen:https://x.com")
    assert generators.internal_link_generator("Plomberie|/plomberie\nHome|/", "plomberie")
    assert generators.meta_generator("plombier", "{kw} | {brand}", brand="ACME")[0]["value"] == "plombier | ACME"
    assert len(generators.meta_variants("Service de plomberie")) == 5
    assert "twitter:card" in generators.og_generator("Plombier", "Dépannage", "https://x.fr/i.jpg")
    assert "Redirect 301" in generators.redirect_generator("/ancien", "/nouveau")
    assert "Disallow: /prive" in generators.robots_generator(disallow="/prive")
    assert "https://x.com/a" in generators.sitemap_generator("https://x.com/a")
    assert "1. Premier" in generators.snippet_generator("Premier\nSecond", "list")
    assert len(generators.title_variants("Plomberie Paris")) == 8
    assert "Redirect 301" in refonte.redirect_map_generator("https://x.fr/old|https://x.fr/new")
    assert ia_tools.prompt_generator("meta", "plomberie à Paris")[0]["prompt"].startswith("Propose")


def test_faq_uses_only_live_paa_and_deduplicates(monkeypatch):
    monkeypatch.setattr(reliquats, "paa_extractor", lambda *args: [
        {"question": "Quel est le prix ?"}, {"question": "quel est le prix ?"},
    ])
    assert reliquats.faq_generator("plombier") == [{"question": "Quel est le prix ?", "source": "PAA"}]


def test_faq_and_keyword_expansion_propagate_dataforseo_errors(monkeypatch):
    error = DataForSEOError("service unavailable")

    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(reliquats, "paa_extractor", fail)
    with pytest.raises(DataForSEOError):
        reliquats.faq_generator("plombier")
    monkeypatch.setattr(reliquats.keywords, "ideas", fail)
    with pytest.raises(DataForSEOError):
        reliquats.keyword_expansion("plombier")


def test_keyword_expansion_mapping_and_content_brief_localization(monkeypatch):
    monkeypatch.setattr(reliquats.keywords, "ideas", lambda *a: [{"keyword": "plombier paris", "volume": 10}])
    monkeypatch.setattr(reliquats.keywords, "suggestions", lambda *a: [{"keyword": "Plombier Paris", "volume": 20}, {"keyword": "urgence plombier", "volume": None}])
    assert reliquats.keyword_expansion("plombier") == [
        {"keyword": "plombier paris", "volume": 10, "source": "ideas"},
        {"keyword": "urgence plombier", "volume": None, "source": "suggestions"},
    ]
    monkeypatch.setattr(reliquats.serp, "live", lambda *a: [])
    monkeypatch.setattr(reliquats, "paa_extractor", lambda *a: [{"question": "Quel tarif ?"}])
    assert "# Brief de contenu : plombier" in reliquats.content_brief("plombier", "FR")
    assert "## Longueur cible" in reliquats.content_brief("plombier", "FR")
    assert "# Content brief: plumber" in reliquats.content_brief("plumber", "US")


def test_all_converters_french_and_english_and_edges():
    encoded = converters.url_encode("https://x.fr/été à Paris")
    assert converters.url_decode(encoded) == "https://x.fr/été à Paris"
    assert converters.strip_accents("Crème brûlée") == "Creme brulee"
    assert converters.text_to_slug("Cœur d'été") == "coeur-d-ete"
    assert converters.text_to_slug("Été à Paris !") == "ete-a-paris"
    assert converters.list_to_urls("Été à Paris\nHello World", "/", "/") == "/ete-a-paris/\n/hello-world/"
    assert "<strong>gras</strong>" in converters.md_to_html("**gras**")
    assert converters.html_to_md("<h1>Titre</h1><p><strong>Gras</strong></p>") == "# Titre\n\n**Gras**"
    assert converters.case_convert("éCOLE", "sentence") == "École"
    assert converters.date_convert("20/08/2026", "fr", "iso") == "2026-08-20"
    assert converters.date_convert("1970-01-01", "iso", "timestamp") == "0"
    assert converters.bytes_human("0") == "0.00 octets (0 octets)"
    assert converters.tokenize("Le SEO et the Content") == "content\nseo"
    assert converters.dedupe_list("Été\nhello\nÉté") == "hello\nÉté"
    assert converters.html_entities("été & tea") == "été &amp; tea"
    assert converters.jsonld_minify('{"@type": "Article", "name": "Été"}') == '{"@type":"Article","name":"Été"}'


def test_csv_json_handles_accents_and_heterogeneous_objects():
    records = json.loads(converters.csv_json("nom,ville\nÉlodie,Paris"))
    assert records == [{"nom": "Élodie", "ville": "Paris"}]
    rendered = converters.csv_json('[{"a": 1}, {"b": 2}]', "json2csv")
    assert rendered.splitlines()[0] == "a,b"
    assert "1," in rendered and ",2" in rendered


@pytest.mark.parametrize("call", [
    lambda: generators.sitemap_generator(""),
    lambda: generators.canonical_generator("relative/path"),
    lambda: generators.snippet_generator("sans séparateur", "table"),
    lambda: converters.bytes_human("-1"),
    lambda: converters.csv_json("[]", "unknown"),
    lambda: converters.date_convert("2026-99-99", "iso", "fr"),
])
def test_clear_invalid_inputs_raise(call):
    with pytest.raises(ValueError):
        call()
