# SEO Toolbox

This file guides AI agents (Claude Code, Codex, Cursor, etc.) working on this repo. Read it in full before modifying anything.

## Overview

- What: open-source toolbox for SEO consultants — **165 mini-tools** + 13 business modules, powered by the DataForSEO API + in-house modules.
- Stack: Python 3.11+, Typer CLI (`seo`), httpx, Rich; optional FastAPI + Jinja2 web UI (`api/`). pytest tests.
- API DataForSEO : official docs [docs.dataforseo.com](https://docs.dataforseo.com/), sign up via [dataforseo](https://dataforseo.com/?aff=180453).
- Public repo: `JulienMpro/seo-toolbox`. Credentials are NEVER stored in the repo (env vars only).

## Golden rules (non-negotiable)

1. **Zero fabricated data**: API unavailable / missing field → `N/D` in outputs. Never use a fictional fallback or fabricated data.
2. **Zero hard-coded secrets**: credentials through environment variables (`DATAFORSEO_USERNAME`, `DATAFORSEO_PASSWORD`, `GSC_CLIENT_ID`, `GSC_CLIENT_SECRET`, `GSC_REFRESH_TOKEN`, `GA4_PROPERTY_ID`, `PSI_API_KEY`). Never log or commit secrets. `data/`, `*.db`, `.env` are gitignored.
3. **Never commit changes yourself**: let the orchestrator validate (tests + review) and commit.
4. **Tests are mandatory** for all new code (pytest, mocked — zero network calls in tests).
5. **SQLite caching** is mandatory for DataForSEO calls (the client handles it — do not bypass it).

## Architecture

### Business modules (`seotoolbox/*.py`)
- `client.py` — `DataForSEOClient`: Basic auth, retry, timeout, **SQLite cache** (`data/cache.db`). `get_result(path, payload)` validates `status_code == 20000` and flattens `tasks[].result[]`. Errors: `ApiError` (network), `DataForSEOError` (business logic).
- `keywords.py` (research/overview/difficulty/suggestions/related/intent/gap/keywords_for_site/cluster) · `ranktracker.py` · `geo.py` (AI mentions) · `backlinks.py` · `serp.py` · `audit.py` (in-house spider) · `crux.py` (PSI/CWV) · `gsc.py` + `ga4.py` (Google OAuth) · `local.py` · `logs.py` · `monitor.py` (baseline + diff) · `report.py` (markdown→HTML) · `content.py` · `google_auth.py` (shared OAuth helper).
- `cli.py` — the Typer app: groups `keywords/ranks/geo/backlinks/serp/audit/gsc/ga4/local/logs/monitor/report/content` + `tool` and `tools` commands.

### Mini-tools (`seotoolbox/tools/`) — THE registry
- `__init__.py`: `REGISTRY` (dict name → `ToolSpec`), `register()`, `list_tools()`. Category modules are imported at the bottom of `__init__.py` (triggering registration).
- `ToolSpec(name, fn, description, category, args: list[ArgSpec], returns="str"|"table")`; `ArgSpec(name, required, default, help, is_flag)`.
- Modules: `calculators.py`, `converters.py`, `generators.py`, `schema.py`, `analyzers.py`, `checkers.py`, `serp_tools.py`, `link_tools.py`, `strategy.py`, `misc.py`, `domain_intel.py`, `youtube_tools.py`, `data_intel.py`, `refonte.py`, `netlinking_extra.py`, `business_calc.py`, `onpage_extra.py`, `ia_tools.py`.
- **Add a tool** = 1 function + 1 `register(ToolSpec(...))` + 1 test. The CLI (`seo tool <nom>`), help, and `seo tools list` are generated automatically. `returns="table"` → list of dicts (`None` values are displayed as `N/D`).
- Function name = snake_case tool name. Existing categories: calculators, converters, generators, analyzers, checkers, serp, links, schema, strategy, misc, geo.

### Mini-tool web UI

- `seotoolbox/tools/ui.py` maps every registry tool to one of ten UX archetypes and stores labels, widgets, choices, and result hints.
- `/tools/{name}` renders a dedicated page; `api/static/tool.js` builds its archetype-specific form and results.
- Every new registry tool must receive a `TOOL_UI` entry so the completeness test remains green.
- Related tools are selected from the same category, with matching archetypes first.

## Known pitfalls (verified live — do not repeat)

1. **`search_intent` requires a location**: payload `{"keywords": [...], "language_name": "English"}` — `language_code` alone → `Invalid Field: 'language_name'`. The `keywords.intent()` function already handles this (`language_name` parameter, defaults to English).
2. **`backlinks/summary`**: the actual keys are `backlinks`, `referring_domains`, `backlinks_spam_score` (NOT `live_backlinks`/`live_referring_domains`/`spam_score`).
3. **MCP-only endpoints (404 through direct REST)**: `ai_optimization/llm_response/live`, `ai_optimization/chatgpt/scraper/live`, `ai_optimization/llm_models`, `ai_optimization/keyword_data/search_volume/live` → 404 through REST even with valid credentials. Capabilities are available only through the DataForSEO MCP server. The affected tools (`llm_response_extract`, `llm_volume`) display a clear explanatory error.
4. **`content_analysis/search`**: the response is `{"items": [...]}`; items contain `url`, `domain`, `url_rank`, `domain_rank`, `score`, `spam_score`, `content_info` (title is inside it). There is no `title` field at the item level.
5. **The client caches for 24h**: after changing a payload/path, clear `data/cache.db` for real-world tests.

## Output conventions
- `returns="str"` → raw text (blocks, XML, formatted JSON).
- `returns="table"` → list of dicts; headers = keys of the first dict (stable order); `None` → `N/D`.
- Error messages: `Error: <message>` + exit code 1 (never show a traceback in the CLI).

## Validation before delivery
1. `python -m pytest -q` → green (mocked tests must not access the network).
2. `seo tools list` → new tool is present.
3. Real-world smoke test (if DataForSEO is required) with credentials from the env — verify outputs and honest N/D values.
4. Scan: no secret/personal path (`git grep -E "/root/|julienmouttet"` must return nothing), `data/` is untracked.
