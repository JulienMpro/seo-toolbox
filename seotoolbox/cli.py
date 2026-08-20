"""Typer command-line interface for SEO Toolbox."""

from __future__ import annotations

import csv
import difflib
import io
import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, get_type_hints

import typer
import httpx
from rich.console import Console
from rich.table import Table

from . import backlinks as backlinks_service
from . import geo as geo_service
from . import keywords as service
from . import ranktracker as ranks_service
from . import serp as serp_service
from . import audit as audit_service
from . import crux as crux_service
from . import gsc as gsc_service
from . import ga4 as ga4_service
from . import local as local_service
from . import logs as logs_service
from . import monitor as monitor_service
from . import report as report_service
from . import content as content_service
from .client import ApiError, DataForSEOError
from .tools import REGISTRY, list_tools

app = typer.Typer(help="Pay-per-request SEO research tools powered by DataForSEO.")
keywords_app = typer.Typer(help="Keyword research, intent, gap, and clustering tools.")
ranks_app = typer.Typer(help="Domain rank tracking tools.")
geo_app = typer.Typer(help="AI and GEO visibility tools.")
backlinks_app = typer.Typer(help="Backlink profile and gap tools.")
serp_app = typer.Typer(help="Live SERP analysis tools.")
audit_app = typer.Typer(help="Technical crawl and Core Web Vitals tools.")
gsc_app = typer.Typer(help="Google Search Console analytics tools.")
ga4_app = typer.Typer(help="Google Analytics 4 reporting tools.")
local_app = typer.Typer(help="Local business listings and local-pack ranks.")
logs_app = typer.Typer(help="Local web server log analysis.")
monitor_app = typer.Typer(help="Crawl baseline and change monitoring.")
report_app = typer.Typer(help="White-label Markdown reporting.")
content_app = typer.Typer(help="Content terms and on-page scoring.")
tools_app = typer.Typer(help="Browse the local mini-tool catalogue.")
app.add_typer(keywords_app, name="keywords")
app.add_typer(ranks_app, name="ranks")
app.add_typer(geo_app, name="geo")
app.add_typer(backlinks_app, name="backlinks")
app.add_typer(serp_app, name="serp")
app.add_typer(audit_app, name="audit")
app.add_typer(gsc_app, name="gsc")
app.add_typer(ga4_app, name="ga4")
app.add_typer(local_app, name="local")
app.add_typer(logs_app, name="logs")
app.add_typer(monitor_app, name="monitor")
app.add_typer(report_app, name="report")
app.add_typer(content_app, name="content")
app.add_typer(tools_app, name="tools")
console = Console()


def _tool_help(name: str) -> None:
    """Render detailed help for a registered mini-tool."""
    spec = REGISTRY[name]
    console.print(f"[bold]{spec.name}[/bold] — {spec.description}")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Argument")
    table.add_column("Required")
    table.add_column("Default")
    table.add_column("Description")
    for arg in spec.args:
        table.add_row(f"--{arg.name.replace('_', '-')}", "yes" if arg.required else "no", arg.default if arg.default is not None else "N/D", arg.help or "N/D")
    console.print(table)


def _parse_tool_args(name: str, tokens: list[str]) -> dict[str, Any]:
    """Parse dynamic options according to a registered ToolSpec."""
    spec = REGISTRY[name]
    args = {arg.name: arg for arg in spec.args}
    raw: dict[str, Any] = {}
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if not token.startswith("--"):
            raise ValueError(f"unexpected argument: {token}")
        key = token[2:].replace("-", "_")
        if key not in args:
            raise ValueError(f"unknown option --{token[2:]} for {name}")
        arg = args[key]
        if arg.is_flag:
            raw[key] = True
            index += 1
        else:
            if index + 1 >= len(tokens) or tokens[index + 1].startswith("--"):
                raise ValueError(f"option --{token[2:]} requires a value")
            raw[key] = tokens[index + 1]
            index += 2
    for arg in spec.args:
        if arg.name not in raw:
            if arg.required:
                raise ValueError(f"missing required option --{arg.name.replace('_', '-')}")
            if arg.is_flag:
                raw[arg.name] = False
            elif arg.default is not None:
                raw[arg.name] = arg.default
    hints = get_type_hints(spec.fn)
    for key, value in list(raw.items()):
        target = hints.get(key, str)
        if target is bool:
            if isinstance(value, bool): continue
            normalized = value.lower()
            if normalized not in {"true", "false", "1", "0", "yes", "no"}: raise ValueError(f"--{key} must be a boolean")
            raw[key] = normalized in {"true", "1", "yes"}
        elif target in {int, float, str}:
            try: raw[key] = target(value)
            except ValueError as exc: raise ValueError(f"--{key.replace('_', '-')} must be a {target.__name__}") from exc
    return raw


@tools_app.command("list")
def tools_list(category: str | None = typer.Option(None, help="Filter by category.")) -> None:
    """List available local mini-tools."""
    rows = list_tools(category)
    if category and not rows:
        console.print(f"[red]Error:[/red] unknown or empty category: {category}")
        raise typer.Exit(code=1)
    table = Table(show_header=True, header_style="bold cyan")
    for column in ("NAME", "CATEGORY", "DESCRIPTION"): table.add_column(column)
    for spec in rows: table.add_row(spec.name, spec.category, spec.description)
    console.print(table)


@app.command("tool", context_settings={"allow_extra_args": True, "ignore_unknown_options": True, "help_option_names": []})
def run_tool(ctx: typer.Context, name: str) -> None:
    """Run a local mini-tool by name; append --help for its arguments."""
    if name not in REGISTRY:
        matches = difflib.get_close_matches(name, REGISTRY, n=3)
        suggestion = f" Did you mean: {', '.join(matches)}?" if matches else " Run 'seo tools list' to browse categories."
        console.print(f"[red]Error:[/red] unknown tool '{name}'.{suggestion}")
        raise typer.Exit(code=1)
    if "--help" in ctx.args or "-h" in ctx.args:
        _tool_help(name)
        return
    try:
        kwargs = _parse_tool_args(name, list(ctx.args))
        spec = REGISTRY[name]
        result = spec.fn(**kwargs)
        if spec.returns == "table":
            if not isinstance(result, list): raise ValueError("table tools must return a list of rows")
            _emit(result, "table")
        else:
            console.print(str(result), highlight=False, markup=False)
    except (ValueError, TypeError, httpx.HTTPError, OSError) as exc:
        console.print(f"[red]Error:[/red] {exc}", highlight=False)
        raise typer.Exit(code=1) from exc


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
    except (ApiError, DataForSEOError, ValueError, httpx.HTTPError) as exc:
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


@ranks_app.command("domain")
def ranks_domain(words: str, domain: str = typer.Option(...), country: str = typer.Option("US"), limit: int = typer.Option(50, min=1), output: str = typer.Option("table"), save: Path | None = typer.Option(None)) -> None:
    """Show current positions for comma-separated keywords."""
    _run(lambda: ranks_service.domain_rank(words.split(","), domain, country, limit), output, save)


@ranks_app.command("history")
def ranks_history(words: str, domain: str = typer.Option(...), country: str = typer.Option("US"), days: int = typer.Option(90, min=1), output: str = typer.Option("table"), save: Path | None = typer.Option(None)) -> None:
    """Show position history over a trailing number of days."""
    from datetime import date, timedelta
    end = date.today()
    _run(lambda: ranks_service.rank_history(words.split(","), domain, country, (end - timedelta(days=days)).isoformat(), end.isoformat()), output, save)


@ranks_app.command("competitors")
def ranks_competitors(domain: str = typer.Option(...), country: str = typer.Option("US"), limit: int = typer.Option(20, min=1), output: str = typer.Option("table"), save: Path | None = typer.Option(None)) -> None:
    """Show competing domains in organic results."""
    _run(lambda: ranks_service.serp_competitors(domain, country, limit), output, save)


@geo_app.command("mentions")
def geo_mentions(word: str, engine: str | None = typer.Option(None), country: str = typer.Option("US"), limit: int = typer.Option(20, min=1), output: str = typer.Option("table"), save: Path | None = typer.Option(None)) -> None:
    """Search LLM mentions for a keyword."""
    _run(lambda: geo_service.mentions(word, [engine] if engine else None, country, limit=limit), output, save)


@geo_app.command("aggregated")
def geo_aggregated(words: str, engines: str = typer.Option("chatgpt,perplexity,gemini"), output: str = typer.Option("table"), save: Path | None = typer.Option(None)) -> None:
    """Show aggregate LLM visibility metrics."""
    _run(lambda: geo_service.aggregated(words.split(","), engines.split(",")), output, save)


@geo_app.command("top-pages")
def geo_top_pages(words: str, engines: str = typer.Option("chatgpt,perplexity,gemini"), limit: int = typer.Option(20, min=1), output: str = typer.Option("table"), save: Path | None = typer.Option(None)) -> None:
    """Show pages most frequently cited by LLMs."""
    _run(lambda: geo_service.top_pages(words.split(","), engines.split(","), limit), output, save)


@backlinks_app.command("summary")
def backlinks_summary(domain: str = typer.Option(...), output: str = typer.Option("table"), save: Path | None = typer.Option(None)) -> None:
    """Show a domain's backlink profile."""
    _run(lambda: [backlinks_service.summary(domain)], output, save)


@backlinks_app.command("list")
def backlinks_list(domain: str = typer.Option(...), limit: int = typer.Option(30, min=1), output: str = typer.Option("table"), save: Path | None = typer.Option(None)) -> None:
    """List backlinks for a domain."""
    _run(lambda: backlinks_service.backlinks(domain, limit), output, save)


@backlinks_app.command("referring-domains")
def backlinks_referring_domains(domain: str = typer.Option(...), limit: int = typer.Option(20, min=1), output: str = typer.Option("table"), save: Path | None = typer.Option(None)) -> None:
    """List referring domains."""
    _run(lambda: backlinks_service.referring_domains(domain, limit), output, save)


@backlinks_app.command("anchors")
def backlinks_anchors(domain: str = typer.Option(...), limit: int = typer.Option(20, min=1), output: str = typer.Option("table"), save: Path | None = typer.Option(None)) -> None:
    """Show anchor text distribution."""
    _run(lambda: backlinks_service.anchors(domain, limit), output, save)


@backlinks_app.command("new-lost")
def backlinks_new_lost(domain: str = typer.Option(...), days: int = typer.Option(30, min=1), output: str = typer.Option("table"), save: Path | None = typer.Option(None)) -> None:
    """Show new and lost backlinks over time."""
    _run(lambda: backlinks_service.new_lost(domain, days), output, save)


@backlinks_app.command("gap")
def backlinks_gap(domain: str = typer.Option(...), competitors: str = typer.Option(...), limit: int = typer.Option(20, min=1), output: str = typer.Option("table"), save: Path | None = typer.Option(None)) -> None:
    """Show backlink intersections with competitors."""
    _run(lambda: backlinks_service.gap([domain, *competitors.split(",")], limit), output, save)


@backlinks_app.command("competitors")
def backlinks_competitors(domain: str = typer.Option(...), limit: int = typer.Option(10, min=1), output: str = typer.Option("table"), save: Path | None = typer.Option(None)) -> None:
    """Show backlink competitors."""
    _run(lambda: backlinks_service.competitors(domain, limit), output, save)


@backlinks_app.command("disavow")
def backlinks_disavow(domain: str = typer.Option(...), output: Path = typer.Option(...), max_spam: float = typer.Option(60)) -> None:
    """Export toxic domains in Google Disavow format."""
    try:
        destination = backlinks_service.disavow_file(domain, output, max_spam)
        console.print(f"Saved disavow file to {destination}")
    except (ApiError, DataForSEOError, ValueError) as exc:
        console.print(f"[red]Error:[/red] {exc}", highlight=False)
        raise typer.Exit(code=1) from exc


@serp_app.command("live")
def serp_live(word: str, country: str = typer.Option("US"), limit: int = typer.Option(20, min=1), device: str = typer.Option("desktop"), output: str = typer.Option("table"), save: Path | None = typer.Option(None)) -> None:
    """Show live organic search results."""
    _run(lambda: serp_service.live(word, country, limit, device), output, save)


@serp_app.command("features")
def serp_features(word: str, country: str = typer.Option("US"), output: str = typer.Option("table"), save: Path | None = typer.Option(None)) -> None:
    """Show detected SERP features."""
    _run(lambda: [serp_service.features(word, country)], output, save)


def _audit_report(url: str, limit: int, workers: int, issue_types: set[str] | None = None):
    report = audit_service.analyze(audit_service.crawl_site(url, limit, workers=workers))
    return [issue for issue in report.issues if issue_types is None or issue.type in issue_types]


def _audit_markdown(report: Any) -> str:
    groups = {
        "Errors": [issue for issue in report.issues if issue.type == "error"],
        "Redirects": [issue for issue in report.issues if issue.type == "redirect"],
        "On-page": [issue for issue in report.issues if issue.type not in {"error", "redirect"}],
    }
    lines = ["# Technical audit", "", "## Summary", "", f"- URLs crawled: {report.total_urls}",
             f"- Issues: {len(report.issues)}", ""]
    for heading, issues in groups.items():
        lines.extend([f"## {heading}", ""])
        if issues:
            lines.extend(["| URL | Type | Severity | Message |", "| --- | --- | --- | --- |"])
            lines.extend(f"| {i.url} | {i.type} | {i.severity} | {i.message.replace('|', chr(92) + '|')} |" for i in issues)
        else:
            lines.append("N/D")
        lines.append("")
    lines.extend(["## Stats", "", f"- Status codes: {report.stats.get('status_codes') or 'N/D'}",
                  f"- Average content length: {_display(report.stats.get('avg_content_length'))}"])
    return "\n".join(lines)


@audit_app.command("run")
def audit_run(url: str = typer.Option(...), limit: int = typer.Option(200, min=1),
              workers: int = typer.Option(10, min=1, max=10), output: str = typer.Option("table"),
              save: Path | None = typer.Option(None)) -> None:
    """Crawl a site and report technical SEO issues."""
    if output.lower() == "md":
        try:
            report = audit_service.analyze(audit_service.crawl_site(url, limit, workers=workers))
            text = _audit_markdown(report)
            if save:
                save.parent.mkdir(parents=True, exist_ok=True)
                save.write_text(text, encoding="utf-8")
                console.print(f"Saved audit report to {save}")
            else:
                typer.echo(text)
        except (ValueError, httpx.HTTPError) as exc:
            console.print(f"[red]Error:[/red] {exc}", highlight=False)
            raise typer.Exit(code=1) from exc
        return
    _run(lambda: _audit_report(url, limit, workers), output, save)


@audit_app.command("issues")
def audit_issues(url: str = typer.Option(...), issue_type: str = typer.Option(..., "--type"),
                 limit: int = typer.Option(200, min=1), workers: int = typer.Option(10, min=1, max=10),
                 output: str = typer.Option("table"), save: Path | None = typer.Option(None)) -> None:
    """Crawl a site and show selected comma-separated issue types."""
    selected = {value.strip() for value in issue_type.split(",") if value.strip()}
    _run(lambda: _audit_report(url, limit, workers, selected), output, save)


@audit_app.command("crux")
def audit_crux(urls: str = typer.Option(...), strategy: str = typer.Option("mobile"),
               output: str = typer.Option("table"), save: Path | None = typer.Option(None)) -> None:
    """Fetch PageSpeed and Chrome UX metrics for comma-separated URLs."""
    _run(lambda: crux_service.crux_report([url.strip() for url in urls.split(",") if url.strip()], strategy), output, save)


@gsc_app.command("properties")
def gsc_properties(output: str = typer.Option("table"), save: Path | None = typer.Option(None)) -> None:
    """List accessible Search Console properties."""
    _run(lambda: [{"property": value} for value in gsc_service.list_properties(gsc_service.get_access_token())], output, save)


@gsc_app.command("queries")
def gsc_queries(property_name: str = typer.Option(..., "--property"), days: int = typer.Option(28, min=1),
                limit: int = typer.Option(20, min=1), output: str = typer.Option("table"),
                save: Path | None = typer.Option(None)) -> None:
    """Show top Search Console queries."""
    _run(lambda: gsc_service.top_queries(property_name, days, limit), output, save)


@gsc_app.command("pages")
def gsc_pages(property_name: str = typer.Option(..., "--property"), days: int = typer.Option(28, min=1),
              limit: int = typer.Option(20, min=1), output: str = typer.Option("table"),
              save: Path | None = typer.Option(None)) -> None:
    """Show top Search Console pages."""
    _run(lambda: gsc_service.top_pages(property_name, days, limit), output, save)


def _ga4_property_id() -> str:
    import os
    if not all(os.getenv(name) for name in
               ("GSC_CLIENT_ID", "GSC_CLIENT_SECRET", "GSC_REFRESH_TOKEN")):
        raise ValueError("GSC credentials missing")
    property_id = os.getenv("GA4_PROPERTY_ID")
    if not property_id:
        raise ValueError("GA4_PROPERTY_ID missing")
    return property_id


@ga4_app.command("daily")
def ga4_daily(days: int = typer.Option(28, min=1), output: str = typer.Option("table"),
              save: Path | None = typer.Option(None)) -> None:
    """Show daily GA4 traffic."""
    _run(lambda: ga4_service.daily_traffic(_ga4_property_id(), days), output, save)


@ga4_app.command("sources")
def ga4_sources(days: int = typer.Option(28, min=1), limit: int = typer.Option(10, min=1),
                output: str = typer.Option("table"), save: Path | None = typer.Option(None)) -> None:
    """Show GA4 traffic by channel group."""
    _run(lambda: ga4_service.traffic_by_source(_ga4_property_id(), days, limit), output, save)


@ga4_app.command("pages")
def ga4_pages(days: int = typer.Option(28, min=1), limit: int = typer.Option(10, min=1),
              output: str = typer.Option("table"), save: Path | None = typer.Option(None)) -> None:
    """Show top GA4 page paths."""
    _run(lambda: ga4_service.top_pages(_ga4_property_id(), days, limit), output, save)


@local_app.command("listings")
def local_listings(query: str = typer.Option(...), city: str = typer.Option(...),
                   country: str = typer.Option("FR"), limit: int = typer.Option(20, min=1),
                   output: str = typer.Option("table"), save: Path | None = typer.Option(None)) -> None:
    """Search Google business listings in a city."""
    _run(lambda: local_service.listings(query, city, country, limit), output, save)


@local_app.command("rank")
def local_rank(keyword: str = typer.Option(...), city: str = typer.Option(...),
               country: str = typer.Option("FR"), limit: int = typer.Option(10, min=1),
               output: str = typer.Option("table"), save: Path | None = typer.Option(None)) -> None:
    """Show businesses in a locally targeted SERP pack."""
    _run(lambda: local_service.local_rank(keyword, city, country, limit), output, save)


def _log_rows(path: Path, bot: str | None) -> list[dict[str, Any]]:
    report = logs_service.analyze_logs(logs_service.parse_log(path, bot))
    rows: list[dict[str, Any]] = [{"section": "summary", "key": "entries", "value": report.entries_count}]
    rows.extend({"section": "status", "key": f"{status // 100}xx", "value": count}
                for status, count in report.status_stats.items())
    rows.extend({"section": "top URL", "key": url, "value": count} for url, count in report.top_urls)
    rows.extend({"section": "top IP", "key": ip, "value": count} for ip, count in report.top_ips)
    rows.extend({"section": "bot hits", "key": date, "value": count} for date, count in report.bot_hits)
    rows.extend({"section": "problem", "key": f"{status} {url}", "value": count}
                for status, url, count in report.problem_urls)
    return rows


@logs_app.command("analyze")
def logs_analyze(file: Path = typer.Option(..., exists=True, dir_okay=False), bot: str | None = typer.Option(None),
                 output: str = typer.Option("table"), save: Path | None = typer.Option(None)) -> None:
    """Analyze a common or combined web access log."""
    _run(lambda: _log_rows(file, bot), output, save)


@logs_app.command("robots")
def logs_robots(file: Path = typer.Option(..., exists=True, dir_okay=False), output: str = typer.Option("table"),
                save: Path | None = typer.Option(None)) -> None:
    """Analyze Googlebot entries in a web access log."""
    _run(lambda: _log_rows(file, "googlebot"), output, save)


@monitor_app.command("init")
def monitor_init(url: str = typer.Option(...), limit: int = typer.Option(100, min=1),
                 db: Path = typer.Option(Path("data/monitor.db"), "--db")) -> None:
    """Initialize or replace a crawl monitoring baseline."""
    try:
        count = monitor_service.init_baseline(url, limit, db)
        console.print(f"Baseline initialized with {count} page(s)")
    except (ValueError, httpx.HTTPError) as exc:
        console.print(f"[red]Error:[/red] {exc}", highlight=False)
        raise typer.Exit(code=1) from exc


@monitor_app.command("check")
def monitor_check(url: str = typer.Option(...), limit: int = typer.Option(100, min=1),
                  db: Path = typer.Option(Path("data/monitor.db"), "--db"),
                  alert_url: str | None = typer.Option(None), output: str = typer.Option("table"),
                  save: Path | None = typer.Option(None)) -> None:
    """Compare a new crawl with the baseline and optionally notify a webhook."""
    try:
        result = monitor_service.check(url, limit, db)
        if result.changes and alert_url:
            try:
                httpx.post(alert_url, json={"text": f"SEO monitor detected {len(result.changes)} change(s) for {url}"}, timeout=10)
            except httpx.HTTPError:
                console.print("[yellow]Warning: alert webhook failed[/yellow]")
        if not result.changes and output.lower() == "table" and not save:
            console.print("No changes")
        else:
            _emit(result.changes, output.lower(), save)
    except (ValueError, httpx.HTTPError) as exc:
        console.print(f"[red]Error:[/red] {exc}", highlight=False)
        raise typer.Exit(code=1) from exc


@report_app.command("build")
def report_build(input_path: Path = typer.Option(..., "--input", exists=True, dir_okay=False),
                 title: str = typer.Option(...), output_path: Path = typer.Option(..., "--output"),
                 brand_color: str = typer.Option("#0ea5e9")) -> None:
    """Build a standalone white-label HTML report from Markdown."""
    destination = report_service.build_report(input_path, title, output_path, brand_color)
    console.print(f"Saved report to {destination}")


@content_app.command("terms")
def content_terms(keyword: str = typer.Option(...), country: str = typer.Option("FR"),
                  limit: int = typer.Option(10, min=1), ngram_size: int = typer.Option(2, min=1),
                  output: str = typer.Option("table"), save: Path | None = typer.Option(None)) -> None:
    """Extract recurring n-grams from top organic results."""
    _run(lambda: content_service.serp_terms(keyword, country, limit, ngram_size), output, save)


@content_app.command("score")
def content_score(url: str = typer.Option(...), keyword: str = typer.Option(...),
                  country: str = typer.Option("FR"), output: str = typer.Option("table"),
                  save: Path | None = typer.Option(None)) -> None:
    """Score verified on-page content signals for a URL."""
    _run(lambda: [content_service.content_score(url, keyword, country)], output, save)


if __name__ == "__main__":
    app()
