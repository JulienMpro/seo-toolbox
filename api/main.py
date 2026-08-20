"""FastAPI HTML demo backed by the real SEO Toolbox modules."""

from __future__ import annotations

import os
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Callable, get_type_hints

import httpx
from fastapi import Body, FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from seotoolbox import audit, backlinks, geo, keywords, serp
from seotoolbox.client import ApiError, DataForSEOError
from seotoolbox.tools import REGISTRY, ToolSpec, coerce_tool_args, list_tools

VERSION = "0.5.0"
COUNTRIES = ("FR", "GB", "US", "DE", "ES", "IT", "BE", "CH", "CA")
LIMITS = (5, 10, 25, 50, 100, 250, 500, 1000)
ENGINES = ("chatgpt", "perplexity", "gemini")

app = FastAPI(title="SEO Toolbox", version=VERSION)
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def _nd(value: Any) -> Any:
    return value if value is not None and value != "" else "N/D"


templates.env.filters["nd"] = _nd


def _serialize_tool(tool: ToolSpec) -> dict[str, Any]:
    """Return the public, JSON-safe registry metadata used by the tools UI."""
    hints = get_type_hints(tool.fn)
    return {
        "name": tool.name,
        "category": tool.category,
        "description": tool.description,
        "returns": tool.returns,
        "args": [
            {
                "name": arg.name,
                "required": arg.required,
                "default": arg.default,
                "help": arg.help,
                "is_flag": arg.is_flag,
                "type": getattr(hints.get(arg.name, str), "__name__", "str")
                if hints.get(arg.name, str) in {str, int, float, bool}
                else "str",
            }
            for arg in tool.args
        ],
    }


def _tool_catalog() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    tools = [_serialize_tool(tool) for tool in list_tools()]
    counts: dict[str, int] = {}
    for tool in tools:
        category = tool["category"]
        counts[category] = counts.get(category, 0) + 1
    categories = [{"name": name, "count": count} for name, count in sorted(counts.items())]
    return tools, categories


def _context(request: Request, **values: Any) -> dict[str, Any]:
    _, tool_categories = _tool_catalog()
    return {
        "request": request,
        "version": VERSION,
        "credentials_missing": not (
            os.getenv("DATAFORSEO_USERNAME") and os.getenv("DATAFORSEO_PASSWORD")
        ),
        "countries": COUNTRIES,
        "limits": LIMITS,
        "tool_categories": tool_categories,
        **values,
    }


def _run(operation: Callable[[], Any]) -> tuple[Any, str | None]:
    try:
        return operation(), None
    except Exception as exc:  # API and crawl failures are presented in the UI.
        return None, str(exc) or exc.__class__.__name__


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": VERSION}


@app.get("/api/tools")
async def tools_api() -> list[dict[str, Any]]:
    tools, _ = _tool_catalog()
    return tools


@app.post("/api/tools/{name}/run")
async def run_tool_api(name: str, raw: dict[str, Any] = Body(...)) -> JSONResponse:
    """Run one registry tool with validated, typed JSON arguments."""
    spec = REGISTRY.get(name)
    if spec is None:
        return JSONResponse({"error": "unknown tool"}, status_code=404)
    try:
        kwargs = coerce_tool_args(spec, raw)
    except (ValueError, TypeError) as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)

    try:
        result = spec.fn(**kwargs)
        if spec.returns == "table":
            if not isinstance(result, list):
                raise ValueError("table tools must return a list of rows")
            output = []
            for row in result:
                if is_dataclass(row):
                    output.append(asdict(row))
                elif isinstance(row, dict):
                    output.append(row)
                else:
                    output.append({"keyword": str(row)})
            return JSONResponse({"returns": "table", "output": output})
        return JSONResponse({"returns": "str", "output": str(result)})
    except (ApiError, DataForSEOError, ValueError, TypeError, httpx.HTTPError, OSError) as exc:
        return JSONResponse(
            {"error": str(exc) or exc.__class__.__name__}, status_code=500
        )


@app.get("/tools", response_class=HTMLResponse)
async def tools_page(request: Request) -> HTMLResponse:
    tools, categories = _tool_catalog()
    return templates.TemplateResponse(
        request, "tools.html", _context(request, tools=tools, categories=categories)
    )


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, domain: str = "") -> HTMLResponse:
    backlink_summary = report = error = None
    if domain.strip():
        target = domain.strip()
        backlink_summary, backlink_error = _run(lambda: backlinks.summary(target))
        start_url = target if target.startswith(("http://", "https://")) else f"https://{target}"
        report, audit_error = _run(lambda: audit.analyze(audit.crawl_site(start_url, max_pages=10)))
        errors = [message for message in (backlink_error, audit_error) if message]
        error = " | ".join(errors) or None
    return templates.TemplateResponse(
        request, "index.html", _context(request, domain=domain, summary=backlink_summary, report=report, error=error)
    )


@app.get("/keywords", response_class=HTMLResponse)
async def keyword_research(request: Request, seed: str = "", country: str = "FR", limit: int = 10) -> HTMLResponse:
    results = error = None
    if seed.strip():
        results, error = _run(lambda: keywords.ideas(seed.strip(), country, limit))
    return templates.TemplateResponse(request, "keywords.html", _context(
        request, seed=seed, country=country, limit=limit, results=results, error=error))


@app.get("/serp", response_class=HTMLResponse)
async def serp_live(request: Request, keyword: str = "", country: str = "FR", limit: int = 10) -> HTMLResponse:
    results = error = None
    if keyword.strip():
        results, error = _run(lambda: serp.live(keyword.strip(), country, limit))
    return templates.TemplateResponse(request, "serp.html", _context(
        request, keyword=keyword, country=country, limit=limit, results=results, error=error))


@app.get("/geo", response_class=HTMLResponse)
async def geo_mentions(request: Request, keyword: str = "", engine: str = "chatgpt") -> HTMLResponse:
    results = error = None
    if keyword.strip():
        results, error = _run(lambda: geo.mentions(keyword.strip(), [engine], limit=50))
    return templates.TemplateResponse(request, "geo.html", _context(
        request, keyword=keyword, engine=engine, engines=ENGINES, results=results, error=error))


@app.get("/backlinks", response_class=HTMLResponse)
async def backlink_profile(request: Request, domain: str = "") -> HTMLResponse:
    summary = referring = error = None
    if domain.strip():
        target = domain.strip()
        summary, summary_error = _run(lambda: backlinks.summary(target))
        referring, referring_error = _run(lambda: backlinks.referring_domains(target, limit=10))
        errors = [message for message in (summary_error, referring_error) if message]
        error = " | ".join(errors) or None
    return templates.TemplateResponse(request, "backlinks.html", _context(
        request, domain=domain, summary=summary, referring=referring, error=error))


@app.get("/audit", response_class=HTMLResponse)
async def technical_audit(request: Request, url: str = "", limit: int = 10) -> HTMLResponse:
    report = error = None
    if url.strip():
        report, error = _run(lambda: audit.analyze(audit.crawl_site(url.strip(), max_pages=limit)))
    return templates.TemplateResponse(request, "audit.html", _context(
        request, url=url, limit=limit, report=report, error=error))
