"""Tests for Schema.org mini-tools."""

import json

from seotoolbox.tools import schema


def test_generators_produce_valid_json():
    faq = json.loads(schema.jsonld_faq("Quel prix ?|50 euros"))
    assert faq["@type"] == "FAQPage"
    assert json.loads(schema.jsonld_article("Titre", "Alice", "2026-08-20"))["headline"] == "Titre"
    assert json.loads(schema.jsonld_product("Produit", price=10))["offers"]["price"] == 10
    assert json.loads(schema.jsonld_breadcrumb("Accueil > Produits"))["itemListElement"][1]["position"] == 2


def test_validation_reports_missing_fields():
    rows = schema.jsonld_validate('{"@context":"https://schema.org","@type":"Article"}')
    assert rows[-1]["message"] == "INVALID"
    assert "headline" in rows[-2]["message"]


def test_extract(monkeypatch):
    class Response:
        text = '<script TYPE="application/ld+json">{"@type":"Article"}</script>'
        def raise_for_status(self): pass
    monkeypatch.setattr(schema.httpx, "get", lambda *args, **kwargs: Response())
    rows = schema.jsonld_extract("https://x.test")
    assert rows[0]["type"] == "Article"
