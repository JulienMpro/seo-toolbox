# Toolbox Consultant SEO — Benchmark & Plan

> **Provenance** : Agents : seo-orchestrator · benchmark-outils-concurrentiel · Références : catalogue-dataforseo-endpoints.md, benchmark-outils-crawl-audit-seo-features.md, benchmark-toolbox-seo-features-2026.md
> **Date** : 20/08/2026 · **Statut** : benchmark complet, architecture recommandée, backlog priorisé
> **Principe** : ZÉRO donnée inventée — features confirmées en live sur sites officiels (août 2026), prix non vérifiés = N/D.

---

## Résumé exécutif

Une toolbox de consultant SEO **100% Python** peut reproduire l'essentiel des features des suites payantes (Ahrefs $129+/mo, Semrush $139+/mo, Moz Pro, SE Ranking, Serpstat, Mangools) et des outils spécialisés (AccuRanker, Majestic, Surfer, BrightLocal, Screaming Frog…) en s'appuyant sur **deux briques** :

1. **API DataForSEO** (pay-per-request, ~65 endpoints documentés, catalogue joint) → keyword research, rank tracking, backlinks, SERP, whois/techno, content analysis, local listings, Amazon, et **GEO/IA** (l'avantage : la plupart des suites facturent le tracking IA en option premium).
2. **Modules maison sans API** (Python) → crawl complet de site (équivalent Screaming Frog), GSC, CrUX/PageSpeed, logs serveur, monitoring continu, reporting white-label.

**Conclusion** : ~80% des features payantes sont reproductibles via DataForSEO + Python. Les 20% restants (crawl massif, données GSC, logs, monitoring temps réel) se font maison avec des briques déjà existantes dans les scripts ai_skills (seo-spider.py, log-analyzer.py, drift-baseline.py, report-generator.py). Interface recommandée : **cœur CLI (Typer) + API FastAPI + UI web simple** (pattern mini-webapp-vps validé).

---

## 1. Périmètre benchmarké (40+ outils, août 2026)

| Famille | Outils benchmarkés | Livrable source |
|---|---|---|
| Suites tout-en-un | Ahrefs, Semrush, Moz Pro, SE Ranking, Serpstat, Mangools | collecte brute pages officielles (339 Ko) |
| Crawl & audit technique | Screaming Frog, Sitebulb, OnCrawl, Lumar, Botify, JetOctopus, ContentKing/Conductor, Ryte, WooRank | `benchmark-outils-crawl-audit-seo-features.md` (~170 features) |
| Spécialisés | AccuRanker, Wincher, Nightwatch, STAT, ProRankTracker, Majestic, Monitor Backlinks, SEOptimer, LRT, Surfer, Clearscope, Frase, MarketMuse, NeuronWriter, Sistrix, Conductor, BrightLocal, Whitespark, Yext, Splunk + 18 gratuits sans API | `benchmark-toolbox-seo-features-2026.md` |

**Signaux marché relevés** : convergence universelle vers le tracking **IA/GEO** (AccuRanker AccuLLM, SE Ranking AI Search, Ahrefs AI Overviews Tracker, Surfer AEO…) ; consolidations (Ryte→Semrush, DeepCrawl→Lumar, ContentKing→Conductor, RankRanger→Similarweb, Monitor Backlinks→SEOptimer) ; Botify pivote vers l'« AI Readiness ».

---

## 2. Matrice : features payantes → reproduction (LE CŒUR)

Légende : 🟢 = DataForSEO couvre · 🔵 = maison sans API (Python/gratuit) · 🟡 = hybride

### 2.1 Keyword Research (Ahrefs KE, Semrush KW Magic, Moz KW Explorer, KWFinder, Serpstat)

| Feature payante | Endpoint DataForSEO / méthode |
|---|---|
| Idées & suggestions de mots-clés (long-tail) | 🟢 `labs/google/keyword_ideas`, `keyword_suggestions`, `related_keywords` |
| Volumes, CPC, concurrence, SERP features par KW | 🟢 `labs/google/keyword_overview` + `keywords_data/google_ads/search_volume` |
| Keyword Difficulty (KD) | 🟢 `labs/google/bulk_keyword_difficulty` |
| Traffic potential (trafic si #1) | 🟢 `labs/google/bulk_traffic_estimation` |
| Volume par pays / multi-marchés | 🟢 `keywords_data/google_ads/locations` + param country |
| Historique volumes/KD (tendance) | 🟢 `labs/google/historical_keyword_data` |
| Intent de recherche | 🟢 `labs/google/search_intent` |
| KW d'un concurrent + positions | 🟢 `labs/google/keywords_for_site`, `ranked_keywords` |
| Keyword gap (intersection) | 🟢 `labs/google/domain_intersection` |
| Parent topic / clustering | 🟡 `keyword_ideas` + clustering maison (cosine/embeddings) |
| Questions (PAA) | 🟢 SERP live → extraction PAA |
| Mobile vs desktop | 🟢 `keyword_overview` (param device) |
| YouTube KW | 🟢 `serp/youtube/organic` |
| Amazon KW | 🟢 `labs/amazon/*` |
| Top searches marché | 🟢 `labs/google/top_searches` |
| Google Trends | 🟢 `keywords_data/google_trends/explore` + `dfs_trends/*` |

### 2.2 Rank Tracking (Ahrefs RT, Semrush Position Tracking, AccuRanker, Wincher, SE Ranking)

| Feature payante | Endpoint DataForSEO / méthode |
|---|---|
| Positions desktop/mobile | 🟢 `labs/google/domain_rank_overview` (device) |
| Tracking local (ville/ZIP, 65k+ loc) | 🟢 `serp/google/organic` avec location (ou `domain_rank_overview` par location) |
| Multi-moteurs (Bing, DDG, YouTube) | 🟢 SERP API multi-moteurs |
| Historique des positions | 🟢 `labs/google/historical_rank_overview`, `historical_serps` |
| SERP features tracking (snippets, PAA…) | 🟢 SERP live → parsing features |
| Détection cannibalisation (2 URLs/KW) | 🟢 `ranked_keywords` → groupement par URL |
| Concurrents SERP | 🟢 `labs/google/serp_competitors` |
| Alertes de perte de position | 🔵 cron maison + diff quotidien |
| Share of Voice / visibilité | 🔵 calcul maison (pondération positions/CTR) |
| **Tracking IA/GEO (GPT, Perplexity, AI Overviews)** | 🟢 **`ai_optimization/llm_mentions/*` + `chatgpt_scraper` + `llm_response` — avantage vs suites (option premium chez elles)** |
| Trafic value / estimated clicks | 🟡 `bulk_traffic_estimation` + modèles CTR |

### 2.3 Backlinks (Ahrefs Site Explorer, Semrush, Majestic, LinkMiner, LRT)

| Feature payante | Endpoint DataForSEO / méthode |
|---|---|
| Vue d'ensemble profil | 🟢 `backlinks/summary` |
| Liste des backlinks (filtrable) | 🟢 `backlinks/backlinks` |
| Domaines référents | 🟢 `backlinks/referring_domains` |
| Ancres | 🟢 `backlinks/anchors` |
| Réseaux référents | 🟢 `backlinks/referring_networks` |
| Pages qui reçoivent des liens | 🟢 `backlinks/domain_pages` + `domain_pages_summary` |
| Nouveaux / perdus (flux) | 🟢 `backlinks/timeseries_new_lost_summary` + `bulk_new_lost_*` |
| Spam score | 🟢 `backlinks/bulk_spam_score` |
| Rank score type DR/TF | 🟢 `backlinks/bulk_ranks` |
| Backlink gap / intersection | 🟢 `backlinks/domain_intersection`, `page_intersection` |
| Concurrents backlink | 🟢 `backlinks/competitors` |
| Index frais vs historique | 🟢 paramètres date (fresh/historic) |
| Surveillance negative SEO | 🟡 `timeseries` + alertes cron maison |
| Génération disavow | 🔵 export maison (format Google) |
| Prospection (unlinked mentions, broken links) | 🟡 `backlinks` + filtres + recherche maison |

### 2.4 Audit technique / crawl (Screaming Frog, Sitebulb, JetOctopus, Lumar…)

| Feature payante | Endpoint DataForSEO / méthode |
|---|---|
| Audit instantané d'une URL (balises, canonicals, hreflang) | 🟢 `on_page/instant_pages` |
| Parsing contenu | 🟢 `on_page/content_parsing` |
| Lighthouse (perf, SEO, a11y, best practices) | 🟢 `on_page/lighthouse` |
| **Crawl complet multi-URLs (statuts, balises, titres, images, schema…)** | 🔵 **spider maison** (pattern `seo-spider.py` / `crawl-content.py` existants dans ai_skills) |
| CWV field (CrUX, users réels) | 🔵 API CrUX Google (gratuite) / PageSpeed Insights |
| Erreurs 4XX/5XX, redirects, chaînes | 🔵 spider maison |
| Contenu dupliqué (exact + quasi) | 🔵 hash md5 + cosine (pattern `cos-salton.py` existant) |
| Cannibalisation KW | 🔵 croisement GSC + crawl |
| Liens internes, orphelines, profondeur | 🔵 spider maison (pattern `maillage-interne.py`/`pagerank-interne.py`) |
| Hreflang / canonicals / robots / sitemap | 🔵 spider maison + `instant_pages` |
| Structured data validation | 🔵 parser maison (ou Rich Results Test API) |
| Mobile-friendliness | 🔵 Lighthouse (via DataForSEO ou PSI) |

### 2.5 Contenu (Surfer, Clearscope, Frase, MarketMuse)

| Feature payante | Endpoint DataForSEO / méthode |
|---|---|
| Analyse SERP pour optimiser (termes à inclure) | 🟢 SERP live + `content_analysis/search` (NLP) |
| Content score / grade | 🔵 checklist pondérée maison (ou LLM local) |
| Topic modeling / coverage | 🔵 NLP maison (embeddings, centroide — pattern `centroide-thematique.py`) |
| Briefs de contenu | 🔵 template maison + données SERP |
| Questions (PAA) | 🟢 SERP live |
| Plagiat / similarité | 🔵 recherche de snippets maison |
| Brand voice / humanizer | 🔵 LLM (prompts) |
| Maillage interne assisté IA | 🔵 graph + LLM (pattern `anchor-registry.py`) |
| Content decay / refresh | 🔵 GSC + dates (pattern `content-pruning`) |

### 2.6 SERP / visibilité / concurrents

| Feature payante | Endpoint DataForSEO / méthode |
|---|---|
| SERP live complète + features | 🟢 `serp/google/organic/live/advanced` |
| Historique SERP | 🟢 `labs/google/historical_serps` |
| Concurrents d'un domaine | 🟢 `labs/google/competitors_for_domain` |
| Pages pertinentes / subdomains | 🟢 `labs/google/relevant_pages`, `subdomains` |
| Stack technique d'un site | 🟢 `domain_analytics/technologies` |
| WHOIS | 🟢 `domain_analytics/whois/overview` |
| Visibility index | 🔵 calcul maison |
| Signaux sociaux | 🔵 (métriques publiques / N/D via DataForSEO) |

### 2.7 Local SEO (BrightLocal, Whitespark, Semrush Local)

| Feature payante | Endpoint DataForSEO / méthode |
|---|---|
| Rank tracking local (grids, heatmaps) | 🟢 SERP live par location + heatmap maison |
| Recherche d'établissements | 🟢 `business_data/google/business_listings/search` |
| Audit cohérence NAP / citations | 🔵 manuel + vérifications maison |
| Review management | 🔵 manuel (pas d'API DataForSEO dédiée) |
| Distribution annuaires | 🔵 manuel (ou Yext-like payant hors périmètre) |
| Insights GBP | 🔵 API Google Business Profile (gratuite, OAuth) |

### 2.8 Log analysis (Splunk, log analyzers)

| Feature payante | Endpoint DataForSEO / méthode |
|---|---|
| Analyse logs Googlebot (crawl budget, fréquence) | 🔵 **100% maison** (pattern `log-analyzer.py` existant dans ai_skills) |
| Pages crawlées vs indexées | 🔵 croisement logs + GSC + sitemap (pattern `indexability-join.py`) |
| Bots détectés / faux bots | 🔵 reverse DNS maison |

### 2.9 Monitoring continu (ContentKing, JetOctopus)

| Feature payante | Endpoint DataForSEO / méthode |
|---|---|
| Crawl récurrent + détection de changements | 🔵 cron + diff (patterns `drift-baseline.py` / `drift-compare.py` existants) |
| Alertes (Slack/Telegram/email) | 🔵 planification cron + notifications |
| Historique des changements (60 mois) | 🔵 base SQLite maison |
| QA pré-publication (templates, seuils) | 🔵 script maison (pattern `render-check.py`) |

### 2.10 Reporting / white-label / API

| Feature payante | Endpoint DataForSEO / méthode |
|---|---|
| Rapports clients (markdown → HTML/PDF) | 🔵 `report-generator.py` existant |
| White-label (logo, couleurs) | 🔵 template maison |
| Export Looker Studio / Sheets | 🔵 export CSV + connecteurs maison |
| API d'accès | 🔵 FastAPI maison |
| MCP server (interroger depuis IA) | 🔵 MCP maison (pattern JetOctopus — différenciateur) |

---

## 3. Gap analysis — ce que DataForSEO ne couvre pas

| Manque DataForSEO | Solution | Coût |
|---|---|---|
| Crawl complet d'un site (millions URLs, JS render) | Spider maison (httpx + Playwright si besoin de render) | 0 € |
| Données GSC (clics, impressions, couverture) | API GSC OAuth (gratuite) | 0 € |
| CWV field (CrUX) | API CrUX | 0 € |
| Logs serveur | Analyse maison | 0 € |
| Monitoring continu + alertes | Cron + diff + Telegram | 0 € |
| Content scoring avancé | NLP/LLM maison | 0 € |
| Backlinks en volume massif | Quota DataForSEO (crédits) — seul vrai poste de coût | pay-per-request |

**Modèle économique** : DataForSEO se facture **par requête** (pas d'abonnement fixe ; prix précis N/D — page pricing JS, à vérifier au moment de l'achat). Un consultant qui lance quelques audits/mois consomme quelques centaines de requêtes → coût très inférieur à un abonnement Ahrefs/Semrush (~$130-140/mo). Cache SQLite obligatoire pour ne pas re-payer les mêmes données.

---

## 4. Architecture recommandée (Python)

```
seo-toolbox/
├── seotoolbox/                  # package cœur
│   ├── client.py                # wrapper DataForSEO (auth, retry, quotas, cache SQLite)
│   ├── keywords.py              # KW research + clustering + intent
│   ├── ranktracker.py           # positions, historique, SERP features, GEO mentions
│   ├── backlinks.py             # profil, flux, ancres, gap, disavow export
│   ├── audit.py                 # spider maison (sitemap → crawl → rapports)
│   ├── crux.py                  # CWV field (API CrUX/PSI)
│   ├── gsc.py                   # API GSC (OAuth)
│   ├── serp.py                  # SERP live + features + historique
│   ├── geo.py                   # AI Optimization API (llm_mentions, chatgpt)
│   ├── local.py                 # business listings + rank local
│   ├── logs.py                  # analyse logs serveur
│   ├── monitor.py               # diff + alertes
│   └── report.py                # markdown → HTML/PDF white-label
├── api/                         # FastAPI (endpoints REST + MCP server)
├── web/                         # UI (Jinja2, pattern mini-webapp-vps) — phase 2
├── cli.py                       # interface CLI (Typer)
├── data/                        # SQLite (cache, projets, historique)
└── README.md
```

**Interface recommandée** (au vu de ton usage et de tes contraintes UI) :
1. **CLI (Typer)** — la base, prioritaire : `seo kw research "plombier paris"`, `seo audit https://site.fr`, `seo backlinks domaine.fr`, `seo geo site.fr`. Rapide, scriptable, testable.
2. **API FastAPI + UI web** — phase 2 : dashboards par projet client, rapports exportables, MCP server pour interroger depuis un LLM.
3. Pas de desktop app (Streamlit/Gradio écartés : UI lourde, moins pro pour du white-label).

**Dépendances** : httpx, typer, rich, pandas, sqlite3 (stdlib), beautifulsoup4, rapidfuzz (clustering), playwright (render JS optionnel), reportlab/weasyprint (PDF). Toutes gratuites/open-source — vérification santé des libs à faire avant validation.

---

## 5. Backlog produit (ordre de priorité)

| # | Module | Couverture DataForSEO | Effort | Valeur |
|---|---|---|---|---|
| 1 | Keyword Research suite | 🟢 quasi totale | M | ★★★★★ |
| 2 | Rank Tracker (+ GEO/IA) | 🟢 totale + avantage GEO | M | ★★★★★ |
| 3 | Backlinks suite | 🟢 totale | M | ★★★★★ |
| 4 | Audit technique (spider + CrUX + GSC) | 🟡 hybride | L | ★★★★☆ |
| 5 | SERP analysis | 🟢 totale | S | ★★★★☆ |
| 6 | Reporting client white-label | 🔵 maison | M | ★★★★☆ |
| 7 | Monitoring + alertes | 🔵 maison | M | ★★★☆☆ |
| 8 | Local SEO | 🟡 hybride | M | ★★★☆☆ |
| 9 | Log analysis | 🔵 maison | S | ★★★☆☆ |
| 10 | Contenu (score, briefs) | 🟡 hybride | L | ★★☆☆☆ |

**Filtre « scratch your own itch » appliqué** : ✅ toi-même (consultant SEO) tu utiliserais chaque module de cette toolbox dans tes missions quotidiennes — le filtre est validé pour l'ensemble.

---

## 6. Sources

- Collecte brute suites SEO (août 2026) : pages officielles (ahrefs, semrush, seranking, serpstat, moz, mangools)
- Crawl/audit : `benchmark-outils-crawl-audit-seo-features.md` (joint au repo, 38 URLs officielles)
- Spécialisés + gratuits : `benchmark-toolbox-seo-features-2026.md` (joint au repo, ~45 URLs officielles)
- Endpoints : `catalogue-dataforseo-endpoints.md` (joint au repo, ~65 endpoints)
- Prix DataForSEO : N/D (page pricing JS-rendered, non vérifiable en curl — à valider sur dataforseo.com)
