# SEO Toolbox

Boîte à outils **open-source** pour consultants SEO : **165 mini-outils** pour couvrir tous les usages du métier — recherche de mots-clés, tracking de positions, backlinks, audits techniques, SERP, données structurées, calculs business, tracking IA/GEO — propulsée par l'**API DataForSEO** (+ modules maison sans API).

> 🧰 L'outil pour **tous** les usages : un mini-outil = **un but précis**. Catalogue complet : `seo tools list`.

## ✨ Fonctionnalités

### 165 mini-outils en 11 catégories

| Catégorie | Nb | Exemples |
|---|---|---|
| **SERP** | 29 | comparateur de SERP, PAA, features, devices, pays, historique, YouTube, Amazon, Trends, top searches, gap… |
| **Générateurs** | 18 | redirections 301, robots.txt, sitemap.xml, hreflang, ancres, briefs de contenu, questions FAQ, prompts IA… |
| **Analyseurs** | 17 | cannibalisation, densité, n-grams, lisibilité, similarité, TF-IDF, entités, maillage interne… |
| **Calculatrices** | 17 | ROI SEO, projection, valeur d'une position, CTR, CAC/LTV, time-to-rank, coût d'opportunité… |
| **Vérificateurs** | 17 | status HTTP en masse, chaînes de redirection, robots, sitemap, canonicals, hreflang, mixed content… |
| **Convertisseurs** | 15 | URL encode/decode, texte→slug, liste→URLs, CSV↔JSON, casse, accents, dates, tokeniseur… |
| **Liens** | 14 | répartition d'ancres, dofollow, toxiques, désaveu, gap, PBN, prospection emails, broken link building… |
| **Schema JSON-LD** | 12 | 10 générateurs (Article, FAQ, LocalBusiness, Product, Breadcrumb, Review, Event, Organization, HowTo, JobPosting) + validateur + extracteur |
| **Divers** | 12 | check HTTP, WHOIS lite, détection de technologies, extraction emails/URLs, diff, lorem… |
| **Stratégie** | 11 | calendrier éditorial, priorisation de KW, clusters, cocon sémantique, benchmark concurrentiel… |
| **GEO / IA** | 3 | visibilité de marque dans les réponses IA, mentions LLM (chatgpt/perplexity/claude/gemini)… |

### 12 commandes de modules (au-delà des mini-outils)

`seo keywords` · `seo ranks` · `seo geo` · `seo backlinks` · `seo serp` · `seo audit` · `seo gsc` · `seo ga4` · `seo local` · `seo logs` · `seo monitor` · `seo report` · `seo content`

### Connecteurs documentés

- **Google Search Console** et **Google Analytics 4** : guide complet dans [`docs/connecteurs.md`](docs/connecteurs.md) — via **Google Cloud Console** (OAuth) ou **MCP** (pour les agents IA). Rien n'est connecté par défaut : les credentials se configurent en variables d'environnement.
- **DataForSEO** : `DATAFORSEO_USERNAME` / `DATAFORSEO_PASSWORD` (env).

### UI web de démonstration

Dashboard FastAPI + Jinja2 (keyword research, SERP, AI mentions, backlinks, audit) — voir [`api/`](api/).

### Démo

Workflow complet illustré sur un projet fictif (zéro donnée réelle) : [`demo/README.md`](demo/README.md).

## 🚀 Installation

```bash
git clone https://github.com/JulienMpro/seo-toolbox.git
cd seo-toolbox
pip install -e ".[dev]"          # + ".[web]" pour l'UI
export DATAFORSEO_USERNAME=...   # credentials DataForSEO
export DATAFORSEO_PASSWORD=...
```

## 🧰 Utilisation

```bash
# Lister les 165 outils
seo tools list
seo tools list --category serp

# Utiliser un outil (aide : seo tool <nom> --help)
seo tool serp_compare --keywords "plombier paris\nplombier lyon" --country FR
seo tool roi_seo --budget 2000 --basket 300 --margin 40 --conversion 2 --months 12
seo tool jsonld_faq --qa "Quel prix ?|50 euros"
seo tool redirect_generator --old "https://x.fr/old" --new "https://x.fr/new"
seo tool cannibalization --domain mon-site.fr --keywords "plombier paris" --country FR

# Modules métier
seo keywords research "plombier paris" --country FR --limit 50
seo backlinks summary --domain mon-site.fr
seo geo mentions --keyword "geo seo" --engine chatgpt
seo audit run --url https://mon-site.fr --limit 500

# UI web
uvicorn api.main:app
```

## 🗂️ Structure

```
seotoolbox/               # Package Python
├── client.py             # Client DataForSEO (auth, retry, cache SQLite)
├── keywords.py           # Module keyword research
├── ranktracker.py        # Module positions + historique
├── geo.py                # Module mentions IA (GEO)
├── backlinks.py          # Module backlinks
├── serp.py               # Module SERP
├── audit.py              # Spider + audit technique maison
├── crux.py               # Core Web Vitals (PageSpeed API)
├── gsc.py / ga4.py       # Connecteurs Google (OAuth)
├── local.py / logs.py / monitor.py / report.py / content.py
├── cli.py                # CLI Typer (`seo`)
└── tools/                # ⭐ Les 165 mini-outils (registre)
    ├── __init__.py       # REGISTRY + dispatcher
    ├── calculators.py, converters.py, generators.py, schema.py,
    ├── analyzers.py, checkers.py, serp_tools.py, link_tools.py,
    ├── strategy.py, misc.py, domain_intel.py, youtube_tools.py,
    ├── data_intel.py, refonte.py, netlinking_extra.py,
    ├── business_calc.py, onpage_extra.py, ia_tools.py
api/                      # UI web FastAPI + templates Jinja2
demo/                     # Démo projet fictif + captures
docs/connecteurs.md       # Guide GSC/GA4 (API & MCP)
TOOLS-ROADMAP.md          # Catalogue des 165 outils
```

## 🧪 Tests

```bash
python -m pytest        # 140 tests (unitaires, mockés — zéro réseau)
```

## 🔒 Sécurité & conventions

- **Zéro donnée inventée** : API HS / champ absent → `N/D`, jamais de fallback fictif.
- **Zéro secret en dur** : credentials uniquement en variables d'environnement ; `data/`, `*.db`, `.env` sont gitignorés.
- **Cache SQLite** sur tous les appels DataForSEO (coût ÷ par exécutions répétées).
- Un mini-outil = un but précis ; chaque outil a une description et des tests.

## 🤝 Contribuer

Nouvel outil ? Ajoute une fonction dans le module de sa catégorie + `register(ToolSpec(...))` + un test — le CLI et l'aide sont automatiques. Voir [`CLAUDE.md`](CLAUDE.md).

## 📄 Licence

MIT
