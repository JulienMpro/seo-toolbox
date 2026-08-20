# SEO Toolbox

Ce fichier guide les agents IA (Claude Code, Codex, Cursor, etc.) qui travaillent sur ce repo. Lis-le en entier avant de modifier quoi que ce soit.

## Vue d'ensemble

- Quoi : boîte à outils CLI Python pour consultants SEO, reproduisant les features des suites payantes via l'API DataForSEO + modules maison.
- Pourquoi : réduire le coût d'outillage SEO (pay-per-request vs abonnements 130 $+/mois), agnostique et configurable par chacun (son domaine, ses clés API).
- Architecture : package `seotoolbox/` (wrapper DataForSEO + modules métier) + CLI Typer ; API FastAPI et UI web en phase 2.

## Stack

- Python 3.11+, httpx, Typer, Rich, SQLite (stdlib).
- Contraintes : zéro dépendance payante, zéro service tiers imposé, toutes les clés API en variables d'environnement.

## Structure du repo

```
seotoolbox/        # package cœur (client.py, keywords.py, models.py, ...)
cli.py             # → en réalité l'app CLI vit dans seotoolbox/cli.py (entry point `seo`)
api/               # FastAPI — phase 2
web/               # UI web — phase 2
data/              # SQLite : cache, projets, historique (gitignoré)
TOOLBOX-CONSULTANT-SEO.md   # benchmark + matrice features → reproduction
catalogue-dataforseo-endpoints.md  # catalogue des endpoints utilisés
```

## Installation & lancement

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export DATAFORSEO_USERNAME=... DATAFORSEO_PASSWORD=...
seo --help
```

## Variables d'environnement

| Variable | Défaut | Rôle |
|---|---|---|
| `DATAFORSEO_USERNAME` | — | Login API DataForSEO (requis) |
| `DATAFORSEO_PASSWORD` | — | Mot de passe API DataForSEO (requis) |

Jamais de secret en dur dans le code ; un `.env` local est gitignoré.

## Schéma de données

- SQLite dans `data/` : table `cache` (hash requête → réponse JSON + timestamp) — chaque appel DataForSEO coûte de l'argent, le cache est obligatoire.

## API DataForSEO — pièges

1. Authentification HTTP Basic (`DATAFORSEO_USERNAME` / `DATAFORSEO_PASSWORD`) ; base URL `https://api.dataforseo.com/v3/`.
2. Tous les appels passent par `seotoolbox/client.py` (retry, timeout, quota, cache) — jamais d'appel direct ailleurs.
3. Les réponses sont `{"tasks": [{"status_code": 20000, "result": [...]}]}` — normaliser l'extraction dans le client.
4. `task.status_code != 20000` = erreur métier (message dans `status_message`) — toujours le vérifier.
5. Ne jamais logger les credentials ni les réponses brutes en clair.

## Conventions & pièges

1. Zéro donnée inventée : si un endpoint échoue ou renvoie vide, afficher `N/D` — jamais de fallback bidon.
2. Cache SQLite obligatoire pour tout appel DataForSEO (coût par requête).
3. CLI : sorties lisibles (Rich), exit codes non nuls sur erreur, option `--output table|csv|md|json`.
4. Tests : `pytest` ; tout module livré avec au moins un test (mocking du client, pas d'appels réseau en CI).
5. Repo : ne jamais committer `data/`, `.env`, `*.db`, clés API.

## Roadmap (contributions bienvenues)

- [x] Module 1 : Keyword Research (volumes, KD, intent, clustering, gap)
- [x] Module 2 : Rank Tracking + tracking IA/GEO
- [x] Module 3 : Backlinks
- [x] Module 4 : Audit technique (spider + CrUX + GSC)
- [x] Module 5 : Analyse SERP
- [ ] API FastAPI + MCP server

## Vérification rapide après modification

```bash
pytest -q
seo keywords research "test" --limit 3   # smoke test CLI (cache)
git status                               # rien de perso tracké
```
