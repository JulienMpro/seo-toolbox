"""Tests for local SEO generators."""

import xml.etree.ElementTree as ET

from seotoolbox.tools import generators


def test_redirect_and_robots_generators():
    assert "Redirect 301 /old /new" in generators.redirect_generator("/old", "/new")
    assert "Sitemap: https://x.test/sitemap.xml" in generators.robots_generator(sitemap="https://x.test/sitemap.xml")


def test_sitemap_escapes_urls():
    value = generators.sitemap_generator("https://x.test/?a=1&b=2", "2026-08-20")
    ET.fromstring(value)
    assert "&amp;" in value


def test_meta_hreflang_and_variants():
    rows = generators.meta_generator("plombier", "{kw} | {brand}", brand="ACME")
    assert rows[0]["value"] == "plombier | ACME"
    assert 'hreflang="x-default"' in generators.hreflang_generator("fr:https://x.fr/,en:https://x.com/")
    assert len(generators.title_variants("SEO", 8)) == 8
    assert len(generators.meta_variants("Une offre", 7)) == 7


def test_links_breadcrumb_snippet_canonical_and_og():
    rows = generators.internal_link_generator("SEO|/seo\nAccueil|/", "SEO")
    assert rows[0]["target_page"] == "/seo"
    assert "BreadcrumbList" in generators.breadcrumb_generator("Accueil > SEO")
    assert "1. Premier" in generators.snippet_generator("Premier\nSecond", "list")
    assert generators.canonical_generator("http://www.x.test/a/?utm=x", True, True, True, "utm")[-1]["url"] == "https://x.test/a"
    assert "twitter:card" in generators.og_generator("T", "D", "https://x.test/i.jpg")
