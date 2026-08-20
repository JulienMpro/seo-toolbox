"""Typer command-line interface for SEO Toolbox."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from . import keywords as service
from .client import ApiError, DataForSEOError

app = typer.Typer(help="Pay-per-request SEO research tools powered by DataForSEO.")
keywords_app = typer.Typer(help="Keyword research, intent, gap, and clustering tools.")
app.add_typer(keywords_app, name="keywords")
console = Console()


def _rows(values: list[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for value in values:
        if is_dataclass(value):
            rows.append(asdict(value))
        elif isinstance(value, dict):
            rows.append(value)
        else:
            rows.append({"keyword": str(value)})
    return rows


def _display(value: Any) -> str:
    if value is None or value == "":
        return "N/D"
    if isinstance(value, list):
        return ", ".join(str(part) for part in value) if value else "N/D"
    return str(value)


def _serialize(rows: list[dict[str, Any]], output: str) -> str:
    rendered = [{key: ("N/D" if value is None or value == "" else value) for key, value in row.items()} for row in rows]
    if output == "json":
        return json.dumps(rendered, ensure_ascii=False, indent=2)
    headers = list(rows[0]) if rows else ["result"]
    if output == "csv":
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=headers)
        writer.writeheader()
        writer.writerows({key: _display(row.get(key)) for key in headers} for row in rows)
        return buffer.getvalue()
    if output == "md":
        header = "| " + " | ".join(headers) + " |"
        divider = "| " + " | ".join("---" for _ in headers) + " |"
        body = ["| " + " | ".join(_display(row.get(key)).replace("|", "\\|") for key in headers) + " |" for row in rows]
        return "\n".join([header, divider, *body])
    raise typer.BadParameter("output must be one of: table, csv, md, json")


def _emit(values: list[Any], output: str, save: Path | None = None) -> None:
    rows = _rows(values)
    if output == "table":
        headers = list(rows[0]) if rows else ["result"]
        table = Table(show_header=True, header_style="bold cyan")
        for header in headers:
            label = {"difficulty": "KD", "search_intent": "INTENT"}.get(
                header, header.replace("_", " ").upper()
            )
            table.add_column(label)
        if rows:
            for row in rows:
                table.add_row(*(_display(row.get(header)) for header in headers))
        else:
            table.add_row("N/D", *("" for _ in headers[1:]))
        if save:
            raise typer.BadParameter("--save requires --output csv, md, or json")
        console.print(table)
        return
    text = _serialize(rows, output)
    if save:
        save.parent.mkdir(parents=True, exist_ok=True)
        save.write_text(text, encoding="utf-8")
        console.print(f"Saved {len(rows)} row(s) to {save}")
    else:
        typer.echo(text)


def _run(operation: Any, output: str, save: Path | None = None) -> None:
    try:
        _emit(operation(), output.lower(), save)
    except (ApiError, DataForSEOError, ValueError) as exc:
        console.print(f"[red]Error:[/red] {exc}", highlight=False)
        raise typer.Exit(code=1) from exc


@keywords_app.command("research")
def research(seed: str, country: str = typer.Option("US"), limit: int = typer.Option(50, min=1), output: str = typer.Option("table"), save: Path | None = typer.Option(None)) -> None:
    """Find and enrich keyword ideas."""
    _run(lambda: service.ideas(seed, country, limit), output, save)


@keywords_app.command("overview")
def overview(words: str, country: str = typer.Option("US"), output: str = typer.Option("table"), save: Path | None = typer.Option(None)) -> None:
    """Retrieve metrics for comma-separated keywords."""
    _run(lambda: service.overview(words.split(","), country), output, save)


@keywords_app.command("suggestions")
def suggestions(seed: str, country: str = typer.Option("US"), limit: int = typer.Option(30, min=1), output: str = typer.Option("table"), save: Path | None = typer.Option(None)) -> None:
    """Find keyword suggestions."""
    _run(lambda: service.suggestions(seed, country, limit), output, save)


@keywords_app.command("related")
def related(word: str, country: str = typer.Option("US"), limit: int = typer.Option(30, min=1), output: str = typer.Option("table"), save: Path | None = typer.Option(None)) -> None:
    """Find semantically related keywords."""
    _run(lambda: service.related(word, country, limit), output, save)


@keywords_app.command("intent")
def intent(words: str, output: str = typer.Option("table"), save: Path | None = typer.Option(None)) -> None:
    """Classify search intent for comma-separated keywords."""
    _run(lambda: service.intent(words.split(",")), output, save)


@keywords_app.command("gap")
def gap(domain: str = typer.Option(...), competitors: str = typer.Option(...), country: str = typer.Option("US"), limit: int = typer.Option(50, min=1), output: str = typer.Option("table"), save: Path | None = typer.Option(None)) -> None:
    """Find domain keywords absent from one or more competitors."""
    _run(lambda: service.gap(domain, competitors.split(","), country, limit), output, save)


@keywords_app.command("for-site")
def for_site(domain: str = typer.Option(...), country: str = typer.Option("US"), limit: int = typer.Option(50, min=1), output: str = typer.Option("table"), save: Path | None = typer.Option(None)) -> None:
    """List keywords and positions for a domain."""
    _run(lambda: service.keywords_for_site(domain, country, limit), output, save)


@keywords_app.command("cluster")
def cluster(words: str = typer.Option(..., "--keywords"), threshold: float = typer.Option(0.4, min=0, max=1), output: str = typer.Option("table"), save: Path | None = typer.Option(None)) -> None:
    """Cluster comma-separated keywords locally by bigram similarity."""
    def operation() -> list[dict[str, Any]]:
        groups = service.cluster(words.split(","), threshold)
        return [{"cluster": index, "keywords": group} for index, group in enumerate(groups, start=1)]
    _run(operation, output, save)


if __name__ == "__main__":
    app()
