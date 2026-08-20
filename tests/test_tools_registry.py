"""Tests for the mini-tool registry and dynamic CLI dispatcher."""

from typer.testing import CliRunner

from seotoolbox.cli import app
from seotoolbox.tools import REGISTRY, list_tools


runner = CliRunner()


def test_registry_contract():
    # The roadmap has 13 calculators, 15 converter command names (encode and
    # decode are separate), and 7 miscellaneous tools.
    assert len(REGISTRY) == 129
    assert len(REGISTRY) == len(set(REGISTRY))
    assert all(tool.description and tool.args for tool in REGISTRY.values())
    assert len(list_tools("calculators")) == 14
    assert len(list_tools("generators")) == 16
    assert len(list_tools("schema")) == 12
    assert len(list_tools("analyzers")) == 14
    assert len(list_tools("checkers")) == 15
    assert len(list_tools("serp")) == 13
    assert len(list_tools("links")) == 12
    assert len(list_tools("strategy")) == 11
    assert {"content_length_target", "keyword_expansion", "content_brief", "faq_generator",
            "cannibalization", "content_length", "tfidf_analysis", "lighthouse_cwv"} <= set(REGISTRY)


def test_dispatcher_string_and_table_tools():
    slug = runner.invoke(app, ["tool", "text_to_slug", "--value", "Plombier Paris 16e — Urgence !"])
    assert slug.exit_code == 0
    assert "plombier-paris-16e-urgence" in slug.stdout
    table = runner.invoke(app, ["tool", "ctr_curve", "--position", "1"])
    assert table.exit_code == 0
    assert "28.5" in table.stdout


def test_dispatcher_help_list_and_errors():
    help_result = runner.invoke(app, ["tool", "roi_seo", "--help"])
    assert help_result.exit_code == 0
    assert "--budget" in help_result.stdout
    assert runner.invoke(app, ["tools", "list"]).exit_code == 0
    unknown = runner.invoke(app, ["tool", "inconnu"])
    assert unknown.exit_code == 1
    assert "unknown tool" in unknown.stdout
