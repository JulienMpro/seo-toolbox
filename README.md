# SEO Toolbox

An **open-source** toolbox for SEO consultants: **165 mini-tools** covering every professional use case — keyword research, rank tracking, backlinks, technical audits, SERPs, structured data, business calculations, AI/GEO tracking — powered by the **DataForSEO API** (+ in-house modules that require no API).

> 🧰 The tool for **every** use case: one mini-tool = **one specific purpose**. Full catalog: `seo tools list`.

## ✨ Features

### 165 mini-tools across 11 categories

| Category | Count | Examples |
|---|---|---|
| **SERP** | 29 | SERP comparison, PAA, features, devices, countries, history, YouTube, Amazon, Trends, top searches, gap… |
| **Generators** | 18 | 301 redirects, robots.txt, sitemap.xml, hreflang, anchor text, content briefs, FAQ questions, AI prompts… |
| **Analyzers** | 17 | cannibalization, density, n-grams, readability, similarity, TF-IDF, entities, internal linking… |
| **Calculators** | 17 | SEO ROI, forecasting, position value, CTR, CAC/LTV, time-to-rank, opportunity cost… |
| **Checkers** | 17 | bulk HTTP status, redirect chains, robots, sitemap, canonicals, hreflang, mixed content… |
| **Converters** | 15 | URL encode/decode, text→slug, list→URLs, CSV↔JSON, letter case, accents, dates, tokenizer… |
| **Links** | 14 | anchor text distribution, dofollow, toxic links, disavow, gap, PBN, email outreach, broken link building… |
| **Schema JSON-LD** | 12 | 10 generators (Article, FAQ, LocalBusiness, Product, Breadcrumb, Review, Event, Organization, HowTo, JobPosting) + validator + extractor |
| **Misc** | 12 | HTTP check, WHOIS lite, technology detection, email/URL extraction, diff, lorem… |
| **Strategy** | 11 | editorial calendar, KW prioritization, clusters, semantic cocoon, competitor benchmarking… |
| **GEO / AI** | 3 | brand visibility in AI answers, LLM mentions (chatgpt/perplexity/claude/gemini)… |

### 12 module commands (in addition to the mini-tools)

`seo keywords` · `seo ranks` · `seo geo` · `seo backlinks` · `seo serp` · `seo audit` · `seo gsc` · `seo ga4` · `seo local` · `seo logs` · `seo monitor` · `seo report` · `seo content`

### Documented connectors

- **Google Search Console** and **Google Analytics 4**: complete guide in [`docs/connecteurs.md`](docs/connecteurs.md) — via **Google Cloud Console** (OAuth) or **MCP** (for AI agents). Nothing is connected by default: credentials are configured through environment variables.
- **DataForSEO**: `DATAFORSEO_USERNAME` / `DATAFORSEO_PASSWORD` (env).

### Demo web UI

FastAPI + Jinja2 dashboard (keyword research, SERP, AI mentions, backlinks, audit) — see [`api/`](api/).

### Demo

Complete workflow illustrated with a fictional project (zero real data): [`demo/README.md`](demo/README.md).

## 🚀 Installation

```bash
# Option 1 — from GitHub (recommended)
pip install seo-toolbox @ git+https://github.com/JulienMpro/seo-toolbox.git

# Option 2 — release wheel
pip install https://github.com/JulienMpro/seo-toolbox/releases/download/v0.6.0/seo_toolbox-0.6.0-py3-none-any.whl

# Option 3 — development (clone)
git clone https://github.com/JulienMpro/seo-toolbox.git
cd seo-toolbox
pip install -e ".[dev]"          # + ".[web]" for the UI

# Web UI (option 1 or 2): pip install "seo-toolbox[web] @ git+https://github.com/JulienMpro/seo-toolbox.git"

export DATAFORSEO_USERNAME=...   # DataForSEO credentials (optional: without them, everything displays N/D)
export DATAFORSEO_PASSWORD=...
```

## 🧰 Usage

```bash
# List the 165 tools
seo tools list
seo tools list --category serp

# Use a tool (help: seo tool <nom> --help)
seo tool serp_compare --keywords "plombier paris\nplombier lyon" --country FR
seo tool roi_seo --budget 2000 --basket 300 --margin 40 --conversion 2 --months 12
seo tool jsonld_faq --qa "Quel prix ?|50 euros"
seo tool redirect_generator --old "https://x.fr/old" --new "https://x.fr/new"
seo tool cannibalization --domain mon-site.fr --keywords "plombier paris" --country FR

# Business modules
seo keywords research "plombier paris" --country FR --limit 50
seo backlinks summary --domain mon-site.fr
seo geo mentions --keyword "geo seo" --engine chatgpt
seo audit run --url https://mon-site.fr --limit 500

# UI web
uvicorn api.main:app
```

## 🗂️ Project structure

```
seotoolbox/               # Python package
├── client.py             # DataForSEO client (auth, retry, SQLite cache)
├── keywords.py           # Keyword research module
├── ranktracker.py        # Rankings + history module
├── geo.py                # AI mentions module (GEO)
├── backlinks.py          # Backlinks module
├── serp.py               # SERP module
├── audit.py              # In-house spider + technical audit
├── crux.py               # Core Web Vitals (PageSpeed API)
├── gsc.py / ga4.py       # Google connectors (OAuth)
├── local.py / logs.py / monitor.py / report.py / content.py
├── cli.py                # Typer CLI (`seo`)
└── tools/                # ⭐ The 165 mini-tools (registry)
    ├── __init__.py       # REGISTRY + dispatcher
    ├── calculators.py, converters.py, generators.py, schema.py,
    ├── analyzers.py, checkers.py, serp_tools.py, link_tools.py,
    ├── strategy.py, misc.py, domain_intel.py, youtube_tools.py,
    ├── data_intel.py, refonte.py, netlinking_extra.py,
    ├── business_calc.py, onpage_extra.py, ia_tools.py
api/                      # FastAPI web UI + Jinja2 templates
demo/                     # Fictional demo project + screenshots
docs/connecteurs.md       # GSC/GA4 guide (API & MCP)
TOOLS-ROADMAP.md          # Catalog of the 165 tools
```

## 🧪 Tests

```bash
python -m pytest        # 140 tests (unit tests, mocked — zero network access)
```

## 🔒 Security & conventions

- **Zero fabricated data**: API unavailable / missing field → `N/D`, never a fictional fallback.
- **Zero hard-coded secrets**: credentials only in environment variables; `data/`, `*.db`, `.env` are gitignored.
- **SQLite cache** for all DataForSEO calls (lower cost for repeated runs).
- One mini-tool = one specific purpose; every tool has a description and tests.

## 🤝 Contributing

New tool? Add a function to its category module + `register(ToolSpec(...))` + a test — the CLI and help are generated automatically. See [`CLAUDE.md`](CLAUDE.md).

## 📄 License

MIT
