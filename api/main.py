"""FastAPI HTML demo backed by the real SEO Toolbox modules."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from seotoolbox import audit, backlinks, geo, keywords, serp

VERSION = "0.5.0"
COUNTRIES = ("FR", "GB", "US", "DE", "ES", "IT", "BE", "CH", "CA")
LIMITS = (5, 10, 25, 50)
ENGINES = ("chatgpt", "perplexity", "gemini")

app = FastAPI(title="SEO Toolbox", version=VERSION)
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def _nd(value: Any) -> Any:
    return value if value is not None and value != "" else "N/D"


templates.env.filters["nd"] = _nd


def _context(request: Request, **values: Any) -> dict[str, Any]:
    return {
        "request": request,
        "version": VERSION,
        "credentials_missing": not (
            os.getenv("DATAFORSEO_USERNAME") and os.getenv("DATAFORSEO_PASSWORD")
        ),
        "countries": COUNTRIES,
        "limits": LIMITS,
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
