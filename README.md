# SEO Toolbox

Boîte à outils **open-source** pour consultants SEO : reproduit l'essentiel des fonctionnalités des suites payantes (Ahrefs, Semrush, Moz, Screaming Frog…) à partir de l'**API DataForSEO** (pay-per-request) + de modules maison sans API (Python).

> **Pourquoi** : les suites SEO coûtent 130 $+/mois pour quelques fonctionnalités utilisées. DataForSEO facture à la requête : un consultant qui lance quelques audits par mois paie une fraction du prix — et récupère en bonus le tracking de visibilité IA/GEO (ChatGPT, Perplexity, AI Overviews).

## Modules couverts (benchmark août 2026)

| Module | Source de données | Statut |
|---|---|---|
| Keyword Research (volumes, KD, intent, clustering, gap) | DataForSEO Labs | 🚧 en développement |
| Rank Tracking (positions, historique, SERP features, local) | DataForSEO Labs + SERP | 📋 planifié |
| Tracking IA/GEO (mentions ChatGPT/Perplexity) | DataForSEO AI Optimization | 📋 planifié |
| Backlinks (profil, flux, ancres, gap, disavow) | DataForSEO Backlinks | 📋 planifié |
| Audit technique (crawl complet, CWV, GSC, CrUX) | Spider maison + API gratuites | 📋 planifié |
| Analyse SERP | DataForSEO SERP | 📋 planifié |
| Logs serveur | 100 % maison | 📋 planifié |
| Monitoring + alertes | Cron + diff | 📋 planifié |
| Reporting white-label (markdown → HTML/PDF) | 100 % maison | 📋 planifié |

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
│   ├── serp.py        # SERP live + features + historique
│   ├── geo.py         # AI Optimization API (llm_mentions, chatgpt)
│   ├── local.py       # business listings + rank local
│   ├── logs.py        # analyse logs serveur
│   ├── monitor.py     # diff + alertes
│   └── report.py      # markdown → HTML/PDF white-label
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

## Configuration

| Variable | Rôle |
|---|---|
| `DATAFORSEO_LOGIN` | Login API DataForSEO |
| `DATAFORSEO_PASSWORD` | Mot de passe API DataForSEO |
| `GSC_CLIENT_ID` / `GSC_CLIENT_SECRET` | OAuth Google Search Console (module GSC) |

## Usage (CLI)

```bash
seo keywords research "plombier paris" --country FR --limit 50
seo keywords gap --domain exemple.fr --competitors conc1.fr,conc2.fr
seo audit https://exemple.fr --output rapport.md
seo backlinks exemple.fr --summary
seo geo exemple.fr --engine chatgpt
```

## Licence

MIT — libre d'utilisation, de modification et de redistribution. Les données DataForSEO restent soumises aux conditions de DataForSEO ; aucune donnée propriétaire n'est embarquée dans ce repo.
