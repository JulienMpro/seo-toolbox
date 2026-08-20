from typer.testing import CliRunner

from seotoolbox.cli import app
from seotoolbox.models import KeywordIdea, KeywordOverview

runner = CliRunner()


def test_research_command(monkeypatch):
    monkeypatch.setattr(
        "seotoolbox.cli.service.ideas",
        lambda seed, country, limit: [KeywordIdea(keyword=seed, volume=120, difficulty=None)],
    )

    result = runner.invoke(app, ["keywords", "research", "seo", "--country", "FR", "--limit", "3"])

    assert result.exit_code == 0
    assert "seo" in result.stdout
    assert "N/D" in result.stdout


def test_overview_json_displays_missing_value(monkeypatch):
    monkeypatch.setattr(
        "seotoolbox.cli.service.overview",
        lambda words, country: [KeywordOverview(keyword=words[0], volume=None)],
    )

    result = runner.invoke(app, ["keywords", "overview", "missing", "--output", "json"])

    assert result.exit_code == 0
    assert '"volume": "N/D"' in result.stdout


def test_empty_results_display_nd(monkeypatch):
    monkeypatch.setattr("seotoolbox.cli.service.suggestions", lambda *args: [])

    result = runner.invoke(app, ["keywords", "suggestions", "nothing"])

    assert result.exit_code == 0
    assert "N/D" in result.stdout


def test_cluster_command_is_local():
    result = runner.invoke(
        app, ["keywords", "cluster", "--keywords", "seo tool,seo tools,plumber", "--output", "json"]
    )

    assert result.exit_code == 0
    assert '"cluster"' in result.stdout
