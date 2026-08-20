# SEO Toolbox

Boîte à outils **open-source** pour consultants SEO : reproduit l'essentiel des fonctionnalités des suites payantes (Ahrefs, Semrush, Moz, Screaming Frog…) à partir de l'**API DataForSEO** (pay-per-request) + de modules maison sans API (Python).

> **Pourquoi** : les suites SEO coûtent 130 $+/mois pour quelques fonctionnalités utilisées. DataForSEO facture à la requête : un consultant qui lance quelques audits par mois paie une fraction du prix — et récupère en bonus le tracking de visibilité IA/GEO (ChatGPT, Perplexity, AI Overviews).

## Modules couverts (benchmark août 2026)

| Module | Source de données | Statut |
|---|---|---|
| Keyword Research (volumes, KD, intent, clustering, gap) | DataForSEO Labs | ✅ disponible |
| Rank Tracking (positions, historique, concurrents) | DataForSEO Labs | ✅ disponible |
| Tracking IA/GEO (mentions et pages citées) | DataForSEO AI Optimization | ✅ disponible |
| Backlinks (profil, flux, ancres, gap, disavow) | DataForSEO Backlinks | ✅ disponible |
| Audit technique (crawl complet, CWV, GSC, CrUX) | Spider maison + API gratuites | ✅ disponible |
| Analyse SERP | DataForSEO SERP | ✅ disponible |
| SEO local (listings, local pack) | DataForSEO Business Data + SERP | ✅ disponible |
| Logs serveur | 100 % maison | ✅ disponible |
| Monitoring + alertes webhook | Spider maison + SQLite | ✅ disponible |
| Reporting white-label (markdown → HTML/PDF optionnel) | 100 % maison | ✅ disponible |
| Analyse et optimisation de contenu | DataForSEO SERP + NLP maison | ✅ disponible |

Le benchmark complet (matrice ~80 features payantes → reproduction) est dans [`TOOLBOX-CONSULTANT-SEO.md`](TOOLBOX-CONSULTANT-SEO.md).

## Architecture

```
seo-toolbox/
├── seotoolbox/        # package cœur
│   ├── client.py      # wrapper DataForSEO (auth, retry, quotas, cache SQLite)
│   ├── keywords.py    # KW research + clustering + intent
│   ├── ranktracker.py # positions, historique, SERP features, GEO mentions
│   ├── backlinks.py   # profil, flux, ancres, gap, disavow export
│   ├── audit.py       # spider maison (sitemap → crawl → rapports)
│   ├── crux.py        # CWV field (API CrUX/PageSpeed)
│   ├── gsc.py         # API Google Search Console (OAuth)
│   ├── ga4.py         # API Google Analytics 4 Data (OAuth)
│   ├── serp.py        # SERP live + features + historique
│   ├── geo.py         # AI Optimization API (llm_mentions, chatgpt)
│   ├── local.py       # business listings + rank local
│   ├── logs.py        # analyse logs serveur
│   ├── monitor.py     # diff + alertes
│   ├── report.py      # markdown → HTML/PDF white-label
│   └── content.py     # termes SERP + score de contenu réel
├── api/               # FastAPI (REST + MCP server) — phase 2
├── web/               # UI web — phase 2
├── cli.py             # interface CLI (Typer)
└── data/              # SQLite (cache, projets, historique)
```

## Stack

- Python 3.11+, [httpx](https://www.python-httpx.org/), [Typer](https://typer.tiangolo.com/) (CLI), [Rich](https://rich.readthedocs.io/) (sortie console)
- SQLite (stdlib) pour le cache et l'historique
- Zéro dépendance payante, zéro service tiers imposé

## Installation

```bash
git clone git@github.com:JulienMpro/seo-toolbox.git
cd seo-toolbox
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

For the optional local web demonstration, install the web extra instead:

```bash
pip install -e ".[dev,web]"
uvicorn api.main:app --port 8010
```

Then open `http://127.0.0.1:8010`. The UI calls the same cached DataForSEO
modules as the CLI and reads the same environment variables. It is intended for
local use or deployment behind authentication; do not expose it publicly without
adding authentication and appropriate production hardening.

## Configuration

| Variable | Rôle |
|---|---|
| `DATAFORSEO_USERNAME` | Login API DataForSEO |
| `DATAFORSEO_PASSWORD` | Mot de passe API DataForSEO |
| `GSC_CLIENT_ID` / `GSC_CLIENT_SECRET` / `GSC_REFRESH_TOKEN` | OAuth Google Search Console |
| `GA4_PROPERTY_ID` | Numeric Google Analytics 4 property ID |
| `PSI_API_KEY` | Clé PageSpeed Insights optionnelle (limites plus élevées) |

## Usage (CLI)

```bash
seo keywords research "plombier paris" --country FR --limit 50
seo keywords gap --domain exemple.fr --competitors conc1.fr,conc2.fr
seo ranks domain "plombier paris" --domain exemple.fr --country FR --limit 20
seo ranks history "plombier paris" --domain exemple.fr --country FR --days 90
seo ranks competitors --domain exemple.fr --country FR --limit 20
seo geo mentions "geo seo" --engine chatgpt --limit 20
seo geo aggregated "geo seo,optimisation ia" --engines chatgpt,perplexity
seo geo top-pages "geo seo,optimisation ia" --limit 20
seo backlinks summary --domain exemple.fr
seo backlinks list --domain exemple.fr --limit 30
seo backlinks referring-domains --domain exemple.fr --limit 20
seo backlinks anchors --domain exemple.fr --limit 20
seo backlinks new-lost --domain exemple.fr --days 30
seo backlinks gap --domain exemple.fr --competitors conc1.fr,conc2.fr --limit 20
seo backlinks competitors --domain exemple.fr --limit 10
seo backlinks disavow --domain exemple.fr --output disavow.txt --max-spam 60
seo serp live "plombier paris" --country FR --limit 20 --device desktop
seo serp features "plombier paris" --country FR
seo audit run --url https://exemple.fr --limit 200 --workers 10
seo audit issues --url https://exemple.fr --type error,redirect,missing_title
seo audit crux --urls https://exemple.fr,https://exemple.fr/contact --strategy mobile
seo gsc properties
seo gsc queries --property sc-domain:exemple.fr --days 28 --limit 20
seo gsc pages --property sc-domain:exemple.fr --days 28 --limit 20
seo ga4 daily --days 28
seo ga4 sources --days 28 --limit 10
seo ga4 pages --days 28 --limit 10
seo local listings --query "plombier" --city paris --country FR --limit 20
seo local rank --keyword "plombier" --city paris --country FR --limit 10
seo logs analyze --file access.log --output md
seo logs robots --file access.log
seo monitor init --url https://exemple.fr --limit 100
seo monitor check --url https://exemple.fr --limit 100 --alert-url https://webhook.example/seo
seo report build --input rapport.md --title "Audit SEO — exemple.fr" --output rapport.html --brand-color "#0ea5e9"
seo content terms --keyword "plombier paris" --country FR --limit 10
seo content score --url https://exemple.fr/page --keyword "plombier paris" --country FR
```

All reporting commands accept `--output table|csv|md|json`; use `--save PATH`
with CSV, Markdown, or JSON output. Missing API values are displayed as `N/D`.
The monitoring alert URL receives a generic `{"text": "..."}` JSON payload; use a
Slack/Telegram-compatible incoming webhook or an adapter. Alert failures never block
the baseline update. PDF export is available from Python when WeasyPrint is installed
separately (`pip install weasyprint`).

## Connectors

Google Search Console and Google Analytics 4 can be connected through their direct
OAuth APIs or exposed to AI agents through MCP. See the complete setup and verification
guide in [Connector setup](docs/connecteurs.md).

## Licence

MIT — libre d'utilisation, de modification et de redistribution. Les données DataForSEO restent soumises aux conditions de DataForSEO ; aucune donnée propriétaire n'est embarquée dans ce repo.
