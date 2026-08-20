# SEO Toolbox

Ce fichier guide les agents IA (Claude Code, Codex, Cursor, etc.) qui travaillent sur ce repo. Lis-le en entier avant de modifier quoi que ce soit.

## Vue d'ensemble

- Quoi : boîte à outils open-source pour consultants SEO — **165 mini-outils** + 13 modules métier, propulsée par l'API DataForSEO + modules maison.
- Stack : Python 3.11+, CLI Typer (`seo`), httpx, Rich ; UI web optionnelle FastAPI + Jinja2 (`api/`). Tests pytest.
- Repo public : `JulienMpro/seo-toolbox`. Les credentials ne sont JAMAIS dans le repo (env vars uniquement).

## Règles d'or (non négociables)

1. **Zéro donnée inventée** : API HS / champ absent → `N/D` dans les sorties. Jamais de fallback fictif, jamais de données fabriquées.
2. **Zéro secret en dur** : credentials via variables d'environnement (`DATAFORSEO_USERNAME`, `DATAFORSEO_PASSWORD`, `GSC_CLIENT_ID`, `GSC_CLIENT_SECRET`, `GSC_REFRESH_TOKEN`, `GA4_PROPERTY_ID`, `PSI_API_KEY`). Ne jamais logger ni committer de secret. `data/`, `*.db`, `.env` sont gitignorés.
3. **Ne committe jamais toi-même** : laisse l'orchestrateur valider (tests + review) et committer.
4. **Tests obligatoires** pour tout nouveau code (pytest, mockés — zéro appel réseau dans les tests).
5. **Cache SQLite** obligatoire pour les appels DataForSEO (le client le gère — ne pas contourner).

## Architecture

### Modules métier (`seotoolbox/*.py`)
- `client.py` — `DataForSEOClient` : auth Basic, retry, timeout, **cache SQLite** (`data/cache.db`). `get_result(path, payload)` valide `status_code == 20000` et aplatit `tasks[].result[]`. Erreurs : `ApiError` (réseau), `DataForSEOError` (métier).
- `keywords.py` (research/overview/difficulty/suggestions/related/intent/gap/keywords_for_site/cluster) · `ranktracker.py` · `geo.py` (mentions IA) · `backlinks.py` · `serp.py` · `audit.py` (spider maison) · `crux.py` (PSI/CWV) · `gsc.py` + `ga4.py` (OAuth Google) · `local.py` · `logs.py` · `monitor.py` (baseline + diff) · `report.py` (markdown→HTML) · `content.py` · `google_auth.py` (helper OAuth partagé).
- `cli.py` — l'app Typer : groupes `keywords/ranks/geo/backlinks/serp/audit/gsc/ga4/local/logs/monitor/report/content` + commandes `tool` et `tools`.

### Mini-outils (`seotoolbox/tools/`) — LE registre
- `__init__.py` : `REGISTRY` (dict name → `ToolSpec`), `register()`, `list_tools()`. Les modules de catégorie s'importent en bas de `__init__.py` (déclenche l'enregistrement).
- `ToolSpec(name, fn, description, category, args: list[ArgSpec], returns="str"|"table")` ; `ArgSpec(name, required, default, help, is_flag)`.
- Modules : `calculators.py`, `converters.py`, `generators.py`, `schema.py`, `analyzers.py`, `checkers.py`, `serp_tools.py`, `link_tools.py`, `strategy.py`, `misc.py`, `domain_intel.py`, `youtube_tools.py`, `data_intel.py`, `refonte.py`, `netlinking_extra.py`, `business_calc.py`, `onpage_extra.py`, `ia_tools.py`.
- **Ajouter un outil** = 1 fonction + 1 `register(ToolSpec(...))` + 1 test. Le CLI (`seo tool <nom>`), l'aide et `seo tools list` sont automatiques. `returns="table"` → liste de dicts (les valeurs `None` s'affichent `N/D`).
- Nom de fonction = snake_case du nom d'outil. Catégories existantes : calculators, converters, generators, analyzers, checkers, serp, links, schema, strategy, misc, geo.

## Pièges connus (vérifiés en live — ne pas répéter)

1. **`search_intent` exige une localisation** : payload `{"keywords": [...], "language_name": "English"}` — `language_code` seul → `Invalid Field: 'language_name'`. La fonction `keywords.intent()` gère déjà ça (paramètre `language_name`, défaut English).
2. **`backlinks/summary`** : les clés réelles sont `backlinks`, `referring_domains`, `backlinks_spam_score` (PAS `live_backlinks`/`live_referring_domains`/`spam_score`).
3. **Endpoints MCP-only (404 en REST direct)** : `ai_optimization/llm_response/live`, `ai_optimization/chatgpt/scraper/live`, `ai_optimization/llm_models`, `ai_optimization/keyword_data/search_volume/live` → 404 en REST même avec creds valides. Capacités disponibles via le serveur MCP DataForSEO uniquement. Les outils concernés (`llm_response_extract`, `llm_volume`) affichent une erreur explicative propre.
4. **`content_analysis/search`** : la réponse est `{"items": [...]}` ; items avec `url`, `domain`, `url_rank`, `domain_rank`, `score`, `spam_score`, `content_info` (title dedans). Pas de champ `title` au niveau item.
5. **Le client met en cache 24h** : après un changement de payload/path, purger `data/cache.db` pour les tests réels.

## Convention de sortie
- `returns="str"` → texte brut (blocs, XML, JSON beautifié).
- `returns="table"` → liste de dicts ; en-têtes = clés du premier dict (ordre stable) ; `None` → `N/D`.
- Messages d'erreur : `Error: <message>` + exit code 1 (jamais de traceback dans le CLI).

## Validation avant livraison
1. `python -m pytest -q` → vert (les tests mockés ne doivent pas toucher le réseau).
2. `seo tools list` → nouveau outil présent.
3. Smoke test réel (si DataForSEO nécessaire) avec les creds de l'env — vérifier les sorties, les N/D honnêtes.
4. Scan : aucun secret/chemin perso (`git grep -E "/root/|julienmouttet"` doit être vide), `data/` non tracké.
