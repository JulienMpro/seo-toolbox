# Catalogue DataForSEO — endpoints disponibles (mapping brut)

> Base de travail pour la toolbox consultant SEO. Chaque endpoint = une capacité exploitable.
> Source : catalogue MCP DataForSEO connecté à Hermes (août 2026) — endpoints réels de l'API v3.
> Ce fichier sert d'annexe au benchmark : il permet de mapper chaque feature payante → endpoint.

## 1. Keyword Research (Labs + Keywords Data)

| Endpoint | Capacité |
|---|---|
| `dataforseo_labs/google/keyword_ideas/live` | Idées de mots-clés depuis un seed (broad) |
| `dataforseo_labs/google/keyword_suggestions/live` | Suggestions (autocomplete-like enrichi) |
| `dataforseo_labs/google/keyword_overview/live` | Volume, CPC, concurrence, tendance, SERP features par KW |
| `dataforseo_labs/google/related_keywords/live` | Mots-clés liés/sémantiquement |
| `dataforseo_labs/google/bulk_keyword_difficulty/live` | Difficulté (KD) en batch |
| `dataforseo_labs/google/bulk_traffic_estimation/live` | Estimation de trafic en batch |
| `dataforseo_labs/google/keywords_for_site/live` | KW d'un domaine (type SEMrush Organic Research) |
| `dataforseo_labs/google/ranked_keywords/live` | KW rankés par un domaine + positions |
| `dataforseo_labs/google/search_intent/live` | Intent de recherche (info/commercial/transactionnel/navigationnel) |
| `dataforseo_labs/google/top_searches/live` | Top recherches d'un marché |
| `dataforseo_labs/google/historical_keyword_data/live` | Historique volume/CPC/KD sur 12 mois |
| `dataforseo_labs/google/google_trends/explore` + `categories` | Tendances Google Trends (via kw_data) |
| `keywords_data/google_ads/search_volume/live` | Volumes Google Ads (batch) |
| `keywords_data/google_ads/locations` | Liste des locations Google Ads |
| `keywords_data/dfs_trends/explore` + `demography` + `subregion_interests` | Tendances DataForSEO par démographie/région |
| `keywords_data/google_trends/explore/live` + `categories` | Trends par catégorie |

## 2. Rank Tracking (Labs)

| Endpoint | Capacité |
|---|---|
| `dataforseo_labs/google/domain_rank_overview/live` | Positions d'un domaine sur ses KW (l'équivalent rank tracker) |
| `dataforseo_labs/google/historical_rank_overview/live` | Historique des positions |
| `dataforseo_labs/google/historical_serps/live` | SERPs historiques (retour dans le temps) |
| `dataforseo_labs/google/serp_competitors/live` | Concurrents SERP d'un domaine |
| `dataforseo_labs/google/subdomains/live` | Sous-domaines + leur performance |
| `serp/google/organic/live/advanced` | SERP live pour 1 KW (positions, features, résultats) |

## 3. Backlinks (Backlinks API)

| Endpoint | Capacité |
|---|---|
| `backlinks/summary/live` | Vue d'ensemble profil (nb backlinks, RD, DR, score...) |
| `backlinks/backlinks/live` | Liste brute des backlinks (filtrable) |
| `backlinks/referring_domains/live` | Domaines référents |
| `backlinks/anchors/live` | Répartition des ancres |
| `backlinks/referring_networks/live` | Réseaux référents (sociaux, blogs...) |
| `backlinks/domain_pages/live` | Pages d'un domaine qui reçoivent des liens |
| `backlinks/domain_pages_summary/live` | Résumé par page |
| `backlinks/competitors/live` | Domaines concurrents backlink (intersection) |
| `backlinks/domain_intersection/live` | Domaines communs entre 2+ cibles |
| `backlinks/page_intersection/live` | Pages communes entre 2+ URLs |
| `backlinks/bulk_backlinks/live` | Nb de backlinks en batch (1000 domains) |
| `backlinks/bulk_new_lost_backlinks/live` | Nouveaux/perdus en batch |
| `backlinks/bulk_new_lost_referring_domains/live` | RD nouveaux/perdus en batch |
| `backlinks/bulk_pages_summary/live` | Résumé pages en batch |
| `backlinks/bulk_ranks/live` | Rank scores en batch (type Ahrefs DR) |
| `backlinks/bulk_referring_domains/live` | RD en batch |
| `backlinks/bulk_spam_score/live` | Spam score en batch |
| `backlinks/timeseries_new_lost_summary/live` | Évolution nouveaux/perdus dans le temps (graphique) |
| `backlinks/available_filters` | Filtres disponibles |

## 4. Audit technique / OnPage (OnPage API)

| Endpoint | Capacité |
|---|---|
| `on_page/instant_pages` | Audit instantané d'une URL (balises, canonicals, hreflang, ressources...) |
| `on_page/content_parsing` | Parsing du contenu d'une page |
| `on_page/lighthouse` | Audit Lighthouse (Perf, SEO, A11Y, Best Practices, PWA) |

## 5. SERP & Features (SERP API)

| Endpoint | Capacité |
|---|---|
| `serp/google/organic/live/advanced` | SERP complète : résultats + features (PAA, snippets, carrousels, maps...) |
| `serp/locations` | Locations pour cibler (pays/villes) |
| `serp/youtube/organic/live/advanced` | SERP YouTube |
| `serp/youtube/video/info/live/advanced` | Infos vidéo (vues, likes...) |
| `serp/youtube/video/comments/live/advanced` | Commentaires vidéo |
| `serp/youtube/video/subtitles/live/advanced` | Sous-titres (transcription) |

## 6. Content Analysis (Content API)

| Endpoint | Capacité |
|---|---|
| `content_analysis/search/live` | Recherche de contenu par phrase/KW avec metrics (pertinence, sentiment, topicalité) |
| `content_analysis/summary/live` | Résumé agrégé d'un corpus de pages |
| `content_analysis/phrase_trends/live` | Tendance d'une phrase dans le temps |

## 7. Domain Analytics (Whois + Technologies)

| Endpoint | Capacité |
|---|---|
| `domain_analytics/whois/overview/live` | WHOIS (registrar, dates, contacts, DNS) |
| `domain_analytics/technologies/domain_technologies/live` | Stack technique d'un site (CMS, serveur, analytics, CDN...) |
| `domain_analytics/technologies/available_filters` | Filtres technos |

## 8. Local SEO (Business Data)

| Endpoint | Capacité |
|---|---|
| `business_data/google/business_listings/search/live` | Recherche d'établissements Google Business Profile |

## 9. GEO / IA (AI Optimization API) — l'avantage concurrentiel

| Endpoint | Capacité |
|---|---|
| `ai_optimization/keyword_data/search_volume/live` + `loc_and_lang` | Volumes de requêtes LLM |
| `ai_optimization/llm_mentions/search/live` | Mentions d'un domaine/site dans les réponses IA |
| `ai_optimization/llm_mentions/aggregated_metrics/live` | Métriques agrégées de mentions |
| `ai_optimization/llm_mentions/cross_aggregated_metrics/live` | Comparaison cross-domaines |
| `ai_optimization/llm_mentions/top_domains/live` | Top domaines cités par les IA |
| `ai_optimization/llm_mentions/top_pages/live` | Top pages citées |
| `ai_optimization/llm_mentions/loc_and_lang` | Locations/langues des mentions |
| `ai_optimization/chatgpt/scraper/live` | Résultats ChatGPT (scraper) |
| `ai_optimization/llm_models` | Liste des modèles LLM suivis |
| `ai_optimization/llm_response/live` | Réponses structurées des LLM |

## 10. E-commerce / Amazon (Merchant API)

| Endpoint | Capacité |
|---|---|
| `merchant/amazon/products/live/advanced` | Recherche produits Amazon |
| `merchant/amazon/sellers/live/advanced` | Vendeurs Amazon |
| `merchant/amazon/asin/live/advanced` | Fiche produit par ASIN |
| `merchant/amazon/locations` | Locations |
| `dataforseo_labs/amazon/*` | Labs Amazon (volumes, compétiteurs produits, intersections) |

## Ce que DataForSEO ne couvre PAS (→ outils sans API / maison)

- Crawl complet d'un site (sitemap → toutes URLs → statuts HTTP) → spider maison (Python, style Screaming Frog)
- Core Web Vitals champ réel (CrUX) → API CrUX Google (gratuite) ou PageSpeed Insights
- Google Search Console (clics, impressions, CTR, couverture) → API GSC (OAuth, gratuit)
- Logs serveur → analyse maison (Python, style log-analyzer)
- Contenu dupliqué / similarité → cosine similarity maison
- Rendu JS complet → headless browser (Playwright) maison
- Backlinks en temps réel au-delà des quotas → quota DataForSEO
