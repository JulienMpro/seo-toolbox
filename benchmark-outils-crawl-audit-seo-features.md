# Inventaire des features — Outils de crawl technique & audit SEO payants

> **Objet** : benchmark concurrentiel pour la création d'une toolbox consultant SEO (reproduction des features via API DataForSEO + outils gratuits).
> **Méthode** : visite des sites officiels / pages features (août 2026). Zéro donnée inventée — toute feature non confirmée par une source est notée **N/D**.
> **Note de contexte marché** : Botify a pivoté vers « AI Readiness » ; ContentKing a été racheté par Conductor (devient « Conductor Monitoring ») ; Ryte racheté par Semrush (2024) ; DeepCrawl est devenu Lumar ; WooRank appartient à Bridgeline.

---

## Screaming Frog SEO Spider
*Crawler desktop (Windows/macOS/Linux). Gratuit ≤ 500 URLs, licence €245/an (illimité). 300+ issues SEO.*

### 1) Crawl
- Crawl 500 URLs en version gratuite ; licence €245/an lève la limite (illimité, dépendant mémoire/stockage)
- Algorithme de crawl breadth-first « comme Googlebot » (découverte des hyperliens dans le HTML)
- Moteur de stockage hybride (décharge sur disque) pour crawler de très grands sites
- JavaScript rendering via Chromium WRS intégré (Angular, React, Vue.js) ; mode raw HTML par défaut
- Store & view HTML + rendered HTML (analyse du DOM)
- Rendered screenshots (captures des pages rendues)
- User-Agent personnalisable (Googlebot, Bingbot, AI crawlers, UA custom)
- Custom HTTP Headers (Accept-Language, cookie, etc.)
- Custom robots.txt (télécharger, éditer, tester)
- Custom JavaScript (exécuter des snippets pendant le crawl : extraction, mouseover, scroll)
- Custom Extraction (XPath, CSS Path, regex)
- Segmentation
- Save & open crawls + configuration de crawl complète
- Scheduling : crawls planifiés + auto-export (dont Google Sheets) + automatisation CLI
- Forms-based authentication
- Crawl XML sitemap de façon indépendante ou dans un crawl
- AMP crawling & validation (AMP Validator officiel intégré)
- Visualisations : diagrammes force-directed (crawl + directory) et tree graphs

### 2) Détection d'erreurs
- 300+ issues, warnings et opportunités SEO
- Erreurs : liens cassés (404), erreurs serveur (no response, 4XX, 5XX)
- Redirects : permanents, temporaires, JS redirects, meta/HTTP refresh, chaînes et boucles
- Chaque issue a un « type » + une « priorité » estimée par impact, avec explication in-app
- Export en masse des erreurs + URLs sources (pour transmettre aux devs)
- URL issues : caractères non-ASCII, underscores, majuscules, paramètres, URLs longues, chemins répétitifs

### 3) On-page
- Page titles : missing, duplicate, long, short, multiple
- Meta descriptions : missing, duplicate, long, short, multiple
- Headings : h1/h2 missing, duplicate, long, short, multiple, non-séquentiels
- Contenu : word count, lisibilité, contenu à faible pertinence (écart au focus moyen du site)
- Duplicate content : exact (md5), near duplicate, sémantiquement similaire (vector embeddings)
- Canonicals : éléments canonical link + en-têtes HTTP canonical
- hreflang : return tags manquants, codes langue incohérents/incorrects, hreflang non-200
- Pagination : rel next/prev + problèmes de configuration
- Anchor text : agrégé et granulaire (détection ancres non descriptives)
- Internal linking : link counts, crawl depth, Internal Link Score
- Images : trop lourdes, alt manquant, images d'arrière-plan, attributs size manquants
- Structured data : extraction + validation (Schema.org + rich results Google)
- Spelling & grammar (25+ langues)
- Extraction custom (social tags, headings, prix, SKU…)

### 4) Core Web Vitals / performance
- Intégration PageSpeed Insights API (métriques Lighthouse, opportunités vitesse, diagnostics, données CrUX)
- Mobile usability via Lighthouse
- Accessibilité : moteur AXE (règles WCAG)

### 5) Indexation
- Directives meta robots + X-Robots-Tag (noindex, nofollow, none, nosnippet…)
- robots.txt : URLs bloquées (disallowed), ressources bloquées en rendering, test robots.txt
- Canonicals (éléments + en-têtes HTTP)
- Génération XML sitemap (XML + image sitemap, config lastmod/priority/changefreq)
- Analyse XML sitemap (pages manquantes, non-indexables, orphelines)
- Intégration GSC : Search Analytics + URL Inspection API (statut d'index en masse)

### 6) Monitoring continu
- Crawl comparison : comparer les crawls, détecter les changements, URL mapping staging vs production
- Scheduling + auto-export (dont Google Sheets)
- Looker Studio crawl reports (monitoring santé + tendances)
- Automatisation complète en ligne de commande

### 7) Intégrations / API / export
- Google Analytics (données utilisateurs + conversions pendant le crawl)
- Google Search Console (Search Analytics + URL Inspection API)
- PageSpeed Insights API
- Link metrics : Majestic, Ahrefs, Moz APIs
- AI Integration : prompts custom OpenAI, Gemini, Ollama, Anthropic pendant le crawl
- Export des éléments onsite clés (URL, title, meta, headings) en spreadsheet
- Rapports Looker Studio / Data Studio
- CLI (automatisation)
- Support technique gratuit (licence payante)

---

## Sitebulb
*Crawler Desktop + Cloud. 300+ issues. Hints priorisés. Rendering Evergreen Chromium. 500k URLs (Desktop) / 10M (Cloud).*

### 1) Crawl
- Deux modes : Desktop et Cloud (même moteur de crawl)
- Crawl jusqu'à 500 000 URLs par audit (Desktop) ; jusqu'à 10M URLs (Cloud)
- « All you can eat » crawling : pas de crédits de crawl ni de limites de projets
- JavaScript crawling via Evergreen Chromium (rendu « comme Googlebot »), activable au clic, inclus sans surcoût
- Response vs Render Report (comparaison source vs rendu)
- Crawl maps (visualisations de crawl)
- Code Coverage Analysis
- Custom URL explorer (colonnes, filtres, tri personnalisés au niveau URL)
- Data visualizations (pie charts, bar graphs, timelines, crawl maps)

### 2) Détection d'erreurs
- Prioritized Hints : liste d'issues priorisées et catégorisées, chacune expliquée (quoi + pourquoi)
- 300+ issues SEO
- Audit Comparison : suivi des changements entre audits + « audit change history » en graphiques

### 3) On-page
- Hreflang Checker
- Structured Data Validator
- XML Sitemaps Report
- Internal Link Auditing
- Website Content Extraction
- Accessibility Audit Report
- (couverture classique des 300+ issues : titres, meta, headings… — détail non listé individuellement sur la page features)

### 4) Core Web Vitals / performance
- Accessibility Audit Report (N/D pour le détail CWV/Lighthouse — non détaillé sur la page features)

### 5) Indexation
- XML Sitemaps Report
- Hreflang Checker
- (canonicals/noindex couverts dans les 300+ issues — N/D détail)

### 6) Monitoring continu
- Audit Comparison (suivi des changements dans le temps)
- Audits planifiés et récurrents (Pro et Cloud)

### 7) Intégrations / API / export
- Intégrations : Data Studio, Google Sheets, GA, Search Console
- Rapports PDF white-label personnalisables
- Exports CSV
- Sitebulb MCP (annoncé « Coming Soon » — interrogation des données d'audit)

---

## OnCrawl
*Plateforme cloud : crawl + log analysis + data. 100% non-échantillonné. +300M URLs crawlées (JS), +500M lignes de logs/jour.*

### 1) Crawl
- Crawler cloud conçu pour les sites complexes
- JavaScript rendering complet (voir le site comme les moteurs/AI, incl. contenu rendu + Core Web Vitals)
- Scalabilité : millions d'URLs sans limites artificielles de vitesse, profondeur ou taille
- Configurations de crawl : scope, fréquence, options de notification par configuration
- Multi-projets et multi-sites dans une plateforme unique
- Différents types de crawl : audits, monitoring, indexability checks, analyse custom
- Custom extraction (collecter n'importe quel data point on-page spécifique au site)
- Segmentation puissante
- +300M URLs crawlées (JS) — données non échantillonnées

### 2) Détection d'erreurs
- Audit systématique crawlability, indexing signals, internal linking, content quality, performance
- Monitoring technique (détection précoce des régressions)
- Alertes automatiques pour changements critiques
- Rapports prédéfinis + export des données brutes

### 3) On-page
- Content quality à l'échelle
- Internal linking : distribution du link equity, pages orphelines, goulots structurels
- Content Lens (IA évalue qualité + SEO readiness du contenu à l'échelle, recommandations priorisées)
- Custom extraction de n'importe quel data point

### 4) Core Web Vitals / performance
- Crawl inclut Core Web Vitals (rendu JS) — performance collectée pendant le crawl

### 5) Indexation
- Indexability checks (type de crawl dédié)
- Indexing signals + indexation
- Crawl budget : budget gaspillé, chemins de crawl inefficaces, fréquence de crawl
- Détection des pages ignorées vs priorisées par les moteurs

### 6) Monitoring continu
- Comparaison des résultats de crawl dans le temps (régressions, améliorations)
- Monitoring de la santé technique dans le temps
- Alertes automatiques de régression
- Planification des crawls + automatisation de l'ingestion de logs

### 7) Intégrations / API / export
- REST API complet (export données, déclenchement crawls, gestion projets)
- Oncrawl Query Language (OQL) pour requêter précisément les datasets
- Connecteurs natifs : Google Search Console, GA4, Majestic, Piano
- Ingestion de logs : Cloudflare, AWS, GCP, Azure, fichiers logs directs (continu, sans échantillonnage)
- Google Data Studio
- Export BI, data warehouses, Dataïku
- Serveur MCP (interroger depuis ChatGPT, Claude, Cursor)
- Import de datasets custom (revenu, conversion)
- Lenses (chemins d'analyse guidés) : AI Search Lens, Content Lens
- Analyse log : Googlebot/Bingbot + AI bots (OpenAI, Perplexity, Claude, Gemini, Mistral)

---

## Lumar (ex DeepCrawl)
*Plateforme cloud : Analyze / Monitor / Protect / Impact. Crawler 450 URLs/s (350 rendered). 250+ rapports SEO, 350+ tests QA. SOC 2 Type 2.*

### 1) Crawl
- Crawler « le plus rapide du marché » : jusqu'à 450 URLs/s (non-rendu), 350 URLs/s (rendu)
- Architecture serverless (crawl aussi vite que l'infra le permet)
- Rendering JS basé sur le moteur de rendu/parsing de Google
- Alignement continu avec les comportements de crawl de Google Search
- Crawl Safeguard : seuils de taux d'échec → pause auto du crawl + notification
- Écran de progression de crawl (req/s, taux d'échec, comptage URLs par code statut)
- Crawls flexibles/custom (métriques custom, extractions custom)
- Segmentation avancée (sections, géographies, types de contenu)
- Crawls ad-hoc ciblés
- Stockage des screenshots + HTML des crawls SEO
- 350+ rapports intégrés

### 2) Détection d'erreurs
- Health scores + visualisations de données pour priorisation
- Regroupement logique des issues + scores de santé par site
- 250+ rapports SEO intégrés
- Data Explorer
- AI dev ticket generator (génération de tickets dev en quelques secondes)
- Task Manager (créer/assigner/priorité/deadline/suivi par crawl)
- Rapports de changements de pages à l'échelle

### 3) On-page
- Métriques : canonical tags, HTTP status, hreflang, redirect chains, metadata, link structure, broken resources
- 250+ rapports tech SEO
- Custom metrics (métriques sur mesure)
- GEO Analytics (dédié AI Search)

### 4) Core Web Vitals / performance
- Site speed : reporting Lighthouse à l'échelle + données field CrUX au niveau origine
- Health scores + dashboards + drill-down granulaire + économies temps/octets
- Sort/filter/segment des métriques Lighthouse agrégées

### 5) Indexation
- Indexabilité, structure du site, page experience
- Canonicals, redirects, hreflang
- GEO (apparition en AI Search)

### 6) Monitoring continu
- Monitor : alertes custom (in-app, email, Slack, Teams), multi-domaines, dashboards personnalisables, tendances, progression des health scores
- Protect : QA tests automatisés (350+ tests), seuils (warn ou blocage de déploiement), tests template/key pages (jusqu'à horaire), intégration CI/CD

### 7) Intégrations / API / export
- API GraphQL
- BI/data : BigQuery, Google Data Studio, Tableau, Looker, Power BI, Dataiku, Pandas, Jupyter, Azure, Tealium, Python
- Log files : Logz.io, Splunk
- Web data : GSC, GA (GA360 + GA4 + conversions), Adobe Analytics, Majestic
- CI/CD : GitHub, CircleCI, Azure DevOps, Bamboo, CodeShip, Concourse, BuildBot, Google Cloud Build
- Productivité : Zapier, Asana, Trello, Slack, Microsoft Teams

---

## Botify
*Plateforme entreprise (pivot « AI Readiness »). Bricks historiques : SiteCrawler, LogAnalyzer, ActionBoard, AlertPanel + Activation (PageWorkers, SpeedWorkers, SmartIndex, SmartContent, SmartLink).*

### 1) Crawl (SiteCrawler)
- Crawl + render « comme Googlebot et OpenAI » (même moteur de rendu que Googlebot)
- Millions de pages en un seul crawl, sans limite de crawl budget
- Paramètres de crawl personnalisables selon l'architecture du site
- 1 000+ indicateurs techniques (crawl depth, internal linking, load times, status codes, structured data)
- Crawl de toutes les versions de pages : AMP, mobile, desktop, canonical, versions pays, staging
- Visualisations riches

### 2) Détection d'erreurs
- Broken links, duplicate content, crawl barriers, missing tags, pages lentes
- Insights priorisés et actionnables (filtrage des issues à fort impact)
- ActionBoard : priorisation data-driven (crawl frequency, trafic, PageRank), rafraîchissement auto après chaque crawl, regroupement par thèmes
- AlertPanel : alertes temps réel avec détection de déviations statistiquement significatives

### 3) On-page
- 1 000+ indicateurs techniques (dont internal linking, structured data)
- Détection de contenu dupliqué
- SmartContent (génération de contenu IA — Activation)
- SmartLink (maillage interne — Activation)

### 4) Core Web Vitals / performance
- Load times (dans les 1 000+ indicateurs)
- SpeedWorkers : pages rendues servies aux bots en <300ms (optimisation crawl/performance)

### 5) Indexation
- SmartIndex : sitemaps optimisés automatiques (générés quotidiennement)
- SmartIndex : notifications IndexNow automatiques
- SmartIndex : Push vers Bing et Qwant (pages illimitées/jour selon plan)
- SpeedWorkers : optimisation du crawl budget, versions fully-rendered servies aux moteurs

### 6) Monitoring continu
- AlertPanel : monitoring 24/7 (logs, crawls, robots.txt)
- Alertes Slack, Microsoft Teams, email, in-app ; Alert Groups (destinataires par type d'alerte)
- Alertes custom (n'importe quelle dimension/métrique) ; moyenne mobile + déviation statistique

### 7) Intégrations / API / export
- LogAnalyzer : ingestion logs CDN, refresh quotidien, filtre par type de bot (GPTBot, ChatGPT-User, OAI-SearchBot, PerplexityBot, ClaudeBot, Meta-ExternalAgent…)
- RealKeywords (analytics de mots-clés réels)
- PageWorkers (tag JS, SEO split testing, optimisations planifiées/réversibles)
- SpeedWorkers (rendering dynamique via CDN)
- Partenariat Shopify
- Emails personnalisables en fin de crawl
- Botify Assist (agent IA)

---

## JetOctopus
*Plateforme cloud entreprise. 6 modules : Log Analyzer, JavaScript Crawler, GSC Integration, GA Insights, Alerts, AI Internal Linker + MCP. Illimité (projets/users/crawls). 1M+ pages/jour. 400+ graphiques prédéfinis.*

### 1) Crawl
- Crawler cloud : 1M+ pages/jour
- JavaScript Crawler (rendu complet, détection des pages « zero-content », ce que voient Googlebot/AI bots)
- Aucune limite de crawl, de crawls simultanés, ni de projets
- Segmentation avec regex (segmenter « littéralement tout »)
- Custom data extracts
- Visualisations : charts, graphs, diagrammes de Venn, 400+ graphiques prédéfinis
- Datatable filtrable (filtrage de n'importe quelle donnée)

### 2) Détection d'erreurs
- Module Tech SEO Audit
- AI SEO Recommender (suggère les fixes par impact business)
- Preset reports avec insights actionnables
- Rapports exportables : URL impactée + provenance du lien + destination de redirection
- Filtres avancés (deep-dive)

### 3) On-page
- Meta tags, statuts HTTP, liens internes
- Analyse des liens internes ET externes
- AI Internal Linker (opportunités de liens, +30% d'efficacité de crawl)
- Titres/meta/H1 dupliqués (via alertes)
- Métriques de problèmes de contenu

### 4) Core Web Vitals / performance
- Intégration PageSpeed Insights (score moyen de toutes les pages, catégorisation poor/average/good)
- Alertes Core Web Vitals : LCP, CLS, INP, FCP par device ; métriques field + lab ; images offscreen

### 5) Indexation
- GSC Integration : 16+ mois de données complètes, cannibalisation, zombie pages, ranking decay
- Optimisation du crawl budget
- Détection des pages non-indexables / non-indexées
- Suivi indexation (cas Preply : +300% d'indexation)

### 6) Monitoring continu
- Alerts : Log alerts (temps réel, sans crawl supplémentaire), Crawl alerts (au rythme des crawls), GSC alerts (lag 2 jours), CWV alerts
- Routage : email, Slack, MS Teams ; combinaisons d'alertes custom + seuils
- Dashboards live partageables avec les devs
- Suivi des changements d'éléments on-page (custom extractions vs valeurs attendues)

### 7) Intégrations / API / export
- Ingestion logs : streaming temps réel NGINX, Cloudflare Enterprise, AWS CloudFront, Fastly, exports quotidiens, upload manuel
- Reverse DNS lookup (détection faux bots, 40+ types de crawlers classifiés)
- GSC via OAuth (2 min, fusion multi-propriétés), 16+ mois de rétention, export illimité
- GA4 (connexion trafic → revenu)
- BigQuery (export bulk GSC)
- JetOctopus MCP (Claude/ChatGPT, lancer/planifier des crawls depuis le chat)
- Export Google Sheets (analyse liens internes)
- Support humain chat/Slack (réponse <1h)

---

## ContentKing → Conductor Monitoring
*Monitoring continu 24/7. ContentKing racheté par Conductor — le produit s'appelle désormais « Conductor Monitoring » (AEO + SEO unifiés).*

### 1) Crawl
- Monitoring continu 24/7 (crawl permanent, pas de crawl planifié)
- Infrastructure de crawl unique (« zero blind spots »)

### 2) Détection d'erreurs
- Détection des issues techniques AEO + SEO dans un workflow unifié
- Page Health : quelles pages coûtent le plus, ce qui les casse, classées par impact business
- Priorisation par impact business (toujours les fixes au ROI le plus élevé d'abord)

### 3) On-page
- Page Health (diagnostic de ce qui casse chaque page)
- N/D pour le détail des checks on-page individuels (page Conductor Monitoring orientée monitoring)

### 4) Core Web Vitals / performance
- N/D (non confirmé sur la page produit actuelle)

### 5) Indexation
- Détection des issues techniques AEO/SEO (dont indexation) dans le flux continu
- N/D pour le détail robots/sitemap/canonicals

### 6) Monitoring continu (cœur du produit)
- Monitoring continu 24/7
- Alerting temps réel, routé à la bonne personne au bon niveau de sensibilité
- Changelog : chaque changement de page capturé dans un audit trail interrogeable, jusqu'à 60 mois d'historique
- Chaque snapshot préservé
- AI Crawling (détection des bugs bien plus tôt que des crawls hebdomadaires)

### 7) Intégrations / API / export
- Routage des alertes (N/D canaux exacts sur la page actuelle)
- N/D pour les exports/API (non détaillés sur la page produit)

---

## Ryte
*Plateforme WUX (Website User Experience), rachetée par Semrush (2024). 7 piliers : SEO, Quality Assurance, Web Performance, Sustainability, Accessibility, Compliance, Content. WUX Score 0-100.*

### 1) Crawl
- Crawler « le plus performant du secteur »
- Advanced crawling settings (rendu JS, viewports mobiles)
- Audits personnalisables (exclusion de répertoires, réglages robots.txt)
- Planification des crawls
- Mobile crawls (indexation mobile-first Google)

### 2) Détection d'erreurs
- Comprehensive Issue Reports : listes d'issues priorisées + Data Explorer
- Plan d'action priorisé (issues classées par importance décroissante)
- Single Page Analysis (analyse approfondie instantanée d'une page, avant mise en ligne/campagne)
- Broken assets : pages, liens, images cassés

### 3) On-page
- Contenu cassé, redirects, titres de page
- Mobile UX issues (petit texte, boutons trop rapprochés)
- Pilier Content (templates, « keyword magic », édition)
- SEO A/B tests (tester les optimisations)

### 4) Core Web Vitals / performance
- Lighthouse Web Vitals pour chaque page
- Bulk checks Core Web Vitals (technologie Chrome Lighthouse), filtres + tri
- Images à optimiser (plus lourdes, formats legacy, pages en sur-usage)
- Rapports JS/CSS (taille de fichiers, usage)
- Rapports de compression de données
- Server monitoring (ping serveur toutes les 10 minutes)

### 5) Indexation
- SEO technique (exigences techniques pour Google)
- Google Top10 Tests + Underperforming Keywords
- Segmentation (regrouper pages/produits/articles importants)

### 6) Monitoring continu
- Slack notifications & alertes custom (seuils personnalisés)
- Server monitoring (ping 10 min)
- Keyword Monitoring dashboards
- Organic Underperformers (quick wins)

### 7) Intégrations / API / export
- Enrichissement avec données GSC + Google Analytics (Data Explorer, issue reports)
- Intégration Slack
- Rapports partageables
- (écosystème Semrush — contexte acquisition)

---

## WooRank
*Outil « instant review » + crawl + keyword tracking + rapports white-label + API (agences). Score SEO. Extensions Chrome/Firefox/Edge.*

### 1) Crawl
- Site Crawl : audit + crawl de milliers de pages
- Crawls automatiques programmés (fresh crawls quotidiens)
- Extensions navigateur (Chrome, Firefox, Edge)

### 2) Détection d'erreurs
- Détection des issues techniques SEO
- Regroupement + filtrage des résultats
- Priorisation du travail
- Contextual helpers (explication des issues pour non-experts)
- « Google Vision » : comprendre comment Google voit le site (crawl, index, rank)

### 3) On-page
- Instant Website Review : score SEO instantané basé sur les best practices
- Critères on-page avec conseils actionnables par critère
- Competitive Analysis (benchmark concurrents)
- (détail Site Crawl on-page : titres/meta couverts — N/D granularité)

### 4) Core Web Vitals / performance
- N/D (non détaillé sur les pages produit consultées)

### 5) Indexation
- Site Crawl : crawl, index, rank (via « Google Vision »)
- N/D pour le détail robots/sitemap/canonicals

### 6) Monitoring continu
- Crawls programmés (données quotidiennes fraîches)
- Keyword tracking : positions dans le temps vs concurrents
- Ranking positions over time

### 7) Intégrations / API / export
- API (automatiser les reviews de sites, solutions agences, appels API à l'échelle)
- Bulk Reports (données de milliers d'URLs)
- White-label reporting (PDF personnalisables illimités)
- Téléchargement des résultats de Site Crawl (export)
- Export CSV des données keywords
- Intégration GA4 dans les rapports
- Keyword tracking localisé (jusqu'au niveau ville)
- Détection des featured results Google
- Extensions navigateur

---

# Synthèse modules
*Liste dédupliquée de TOUTES les features payantes identifiées (toutes sources confondues), groupée par module. Chaque puce = 1 feature distincte.*

## 1) Crawl
- Crawl desktop (installation locale) vs crawl cloud (scalable, multi-projets)
- Crawl cloud illimité (pas de crédits/limites de projets — Sitebulb, JetOctopus)
- Limite gratuite (500 URLs) levée par licence payante (Screaming Frog)
- Crawl de millions d'URLs / millions de pages par jour
- Vitesse de crawl élevée (450 URLs/s non-rendu, 350 rendu — Lumar ; 1M+ pages/jour — JetOctopus)
- Architecture serverless (crawl aussi vite que l'infra le permet)
- JavaScript rendering via Chromium/Googlebot (raw vs rendered HTML)
- Stockage et comparaison HTML source vs HTML rendu (Response vs Render)
- Rendered screenshots
- User-Agent personnalisable (Googlebot, Bingbot, AI crawlers, custom)
- Custom HTTP headers
- Custom robots.txt (éditer/tester)
- Custom JavaScript pendant le crawl
- Custom extraction (XPath, CSS Path, regex)
- Segmentation avancée (regex, sections, géographies, types de contenu)
- Crawl de toutes les versions de pages (AMP, mobile, desktop, canonical, pays, staging)
- Forms-based authentication
- Crawl XML sitemap indépendant ou intégré
- AMP crawling & validation
- Mobile crawl / viewports mobiles
- Planification des crawls (scheduling)
- Types de crawl multiples (audit, monitoring, indexability, custom)
- Visualisations de crawl : diagrammes force-directed, tree graphs, crawl maps, diagrammes de Venn
- Données 100% non échantillonnées
- Sauvegarde/réouverture des crawls
- Crawl progress monitoring (req/s, taux d'échec, comptage par code statut)
- Crawl safeguard (pause auto sur seuil de taux d'échec)
- Crawl à partir d'extensions navigateur (Chrome/Firefox/Edge)

## 2) Détection d'erreurs
- Grand volume d'issues détectées (250 à 1000+ indicateurs/rapports selon l'outil)
- Liste d'issues priorisées et catégorisées avec explication (quoi + pourquoi)
- Score de santé du site (health score 0-100)
- Priorisation par impact business/trafic/revenu
- Priorisation algorithmique (crawl frequency + trafic + PageRank)
- Regroupement thématique des actions (fix par catégorie d'issue)
- Filtres/tri/segmentation des issues
- Détection des liens cassés (404) + erreurs serveur (4XX/5XX)
- Détection des redirects (permanents, temporaires, JS, meta refresh) + chaînes et boucles
- Détection des ressources bloquées (rendering)
- Export en masse des erreurs + URLs sources
- Rapports prédéfinis avec insights actionnables
- Data Explorer (exploration libre des données de crawl)
- Génération automatique de tickets dev (IA)
- Task manager (assignation, priorité, deadline, suivi)
- Single Page Analysis (analyse instantanée d'une page)
- Contextual helpers (vulgarisation des issues)

## 3) On-page
- Analyse des page titles (missing/duplicate/long/short/multiple)
- Analyse des meta descriptions (idem)
- Analyse des headings h1/h2 (missing/duplicate/long/short/multiple/non-séquentiels)
- Word count + lisibilité + pertinence du contenu
- Détection contenu dupliqué exact (md5/algorithmique)
- Détection contenu quasi-dupliqué + sémantiquement similaire (vector embeddings)
- Détection de cannibalisation de mots-clés
- Canonicals (éléments + en-têtes HTTP)
- hreflang (return tags, codes langue, statuts)
- Pagination (rel next/prev)
- Analyse de l'anchor text (agrégé + granulaire)
- Internal linking (link counts, crawl depth, link score, distribution du link equity)
- Détection de pages orphelines
- Analyse des liens externes
- Analyse des images (alt, taille, attributs size, formats legacy, images offscreen)
- Structured data : extraction + validation (Schema.org, rich results)
- Spelling & grammar (multilingue)
- Mobile UX (petit texte, boutons trop rapprochés)
- Extraction custom de n'importe quel élément on-page
- Évaluation IA du contenu (qualité + SEO readiness à l'échelle)
- Génération de contenu IA (SmartContent)
- Maillage interne assisté IA (AI Internal Linker / SmartLink)

## 4) Core Web Vitals / performance
- Reporting Lighthouse à l'échelle (métriques lab)
- Données field CrUX (origine, utilisateurs réels)
- Métriques CWV : LCP, CLS, INP, FCP
- Intégration PageSpeed Insights API
- Score moyen de performance de toutes les pages (catégorisation poor/average/good)
- Tri/filtre/segmentation des métriques de performance
- Économies potentielles temps/octets par fix
- Analyse des images à optimiser (lourdes, legacy)
- Analyse JS/CSS (taille de fichiers, usage)
- Rapports de compression de données
- Accessibilité automatisée (WCAG, moteur AXE)
- Mobile usability (Lighthouse)
- Server monitoring (ping périodique, détection timeouts)
- Serving optimisé des pages rendues aux bots (<300ms — SpeedWorkers)
- Core Web Vitals en alertes (par device, field + lab)

## 5) Indexation
- Directives meta robots + X-Robots-Tag (noindex, nofollow, nosnippet…)
- robots.txt : URLs bloquées, ressources bloquées, test/édition
- Canonicals : analyse éléments + en-têtes HTTP
- Génération XML sitemap (+ image sitemap, config lastmod/priority/changefreq)
- Sitemaps optimisés automatiques (génération quotidienne)
- Analyse XML sitemap (pages manquantes, non-indexables, orphelines)
- Notifications IndexNow automatiques
- Push vers les index (Bing, Qwant) — soumission directe
- Intégration GSC : statut d'index (URL Inspection API), Search Analytics en masse
- Rétention étendue des données GSC (16+ mois, au-delà des 16 mois Google)
- Couverture/coverage d'indexation
- Crawl budget : budget gaspillé, chemins inefficaces, fréquence de crawl
- Détection pages non-indexables / zombie pages / ranking decay
- Crawl de toutes les versions (AMP, mobile, desktop, pays)

## 6) Monitoring continu
- Monitoring continu 24/7 (crawl permanent)
- Monitoring basé sur les logs serveur en temps réel
- Comparaison de crawls dans le temps (détection de changements/régressions)
- Historique/audit trail des changements de pages (jusqu'à 60 mois)
- Alertes temps réel (email, Slack, Microsoft Teams, in-app)
- Alertes custom (seuils, métriques, dimensions, combinaisons)
- Alertes par déviation statistique (moyenne mobile)
- Alertes Core Web Vitals (field + lab, par device)
- Alertes logs (statuts, 5xx, bots, crawl budget)
- Alertes GSC (positions, CTR, cannibalisation, fan-out)
- Alert Groups / routage par destinataire
- Dashboards de monitoring multi-domaines/sections
- Planification de crawls récurrents
- Auto-export programmé (dont Google Sheets)
- Rapports automatisés (Looker Studio / Data Studio)
- QA automatisée pré-publication (tests template/key pages, horaire)
- Seuils de QA (warn ou blocage de déploiement)
- Split testing SEO (test d'optimisations avant déploiement)
- Suivi des changements d'éléments on-page vs valeurs attendues

## 7) Intégrations / API / export
- REST API complet (export, déclenchement crawls, gestion projets)
- API GraphQL
- Langage de requête dédié (OQL)
- Serveur MCP (interrogation depuis ChatGPT/Claude/Cursor)
- Connecteurs GSC (Search Analytics + URL Inspection + multi-propriétés)
- Connecteur GA4 / GA360 (trafic, conversions, revenu)
- Connecteurs backlinks : Majestic, Ahrefs, Moz
- Intégration PageSpeed Insights
- Intégration Adobe Analytics
- Ingestion de logs : Cloudflare, AWS, GCP, Azure, NGINX, Fastly, fichiers bruts
- Détection/reverse DNS des faux bots (40+ types de crawlers)
- Export BigQuery
- Export BI/data : Tableau, Looker, Power BI, Dataiku, Pandas, Jupyter, Python
- Export Google Data Studio / Looker Studio
- Export Google Sheets
- Export CSV / spreadsheet
- Rapports PDF white-label personnalisables
- Bulk reports (milliers d'URLs)
- Intégrations CI/CD (GitHub, CircleCI, Azure DevOps, Bamboo, CodeShip, Concourse, BuildBot, Google Cloud Build)
- Intégrations productivité (Zapier, Asana, Trello, Slack, MS Teams)
- Automatisation CLI / ligne de commande
- Emails personnalisables en fin de crawl
- Extension navigateur
- Support humain dédié (chat/Slack <1h)
- Intégrations AI pour génération (OpenAI, Gemini, Ollama, Anthropic)
- Partenariats e-commerce (Shopify)

---

## Sources (URLs consultées, août 2026)

**Screaming Frog**
- https://www.screamingfrog.co.uk/seo-spider/

**Sitebulb**
- https://sitebulb.com/features/

**OnCrawl**
- https://www.oncrawl.com/
- https://www.oncrawl.com/platform/crawler/
- https://www.oncrawl.com/platform/log-analyzer/
- https://www.oncrawl.com/platform/integrations/
- https://www.oncrawl.com/platform/control-your-technical-performance/

**Lumar**
- https://www.lumar.io/platform/
- https://www.lumar.io/platform/analyze/
- https://www.lumar.io/platform/website-crawler/
- https://www.lumar.io/platform/technical-seo-metrics/
- https://www.lumar.io/platform/monitor/
- https://www.lumar.io/platform/protect/
- https://www.lumar.io/platform/integrations/
- https://www.lumar.io/platform/site-speed-metrics/

**Botify**
- https://www.botify.com/platform
- https://www.botify.com/platform/visibility
- https://www.botify.com/platform/visibility/sitecrawler-feature
- https://www.botify.com/platform/visibility/loganalyzer-feature
- https://www.botify.com/platform/visibility/actionboard-feature
- https://www.botify.com/platform/visibility/alertpanel-feature
- https://www.botify.com/platform/activation/pageworkers
- https://www.botify.com/platform/activation/smartindex
- https://www.botify.com/platform/ai-readiness/speedworkers

**JetOctopus**
- https://www.jetoctopus.com/
- https://www.jetoctopus.com/log-analyzer/
- https://www.jetoctopus.com/gsc-integration/
- https://www.jetoctopus.com/alerts/

**ContentKing / Conductor Monitoring**
- https://www.contentkingapp.com/features/ (redirige vers Conductor Monitoring)

**Ryte**
- https://www.ryte.com/
- https://en.ryte.com/platform/seo/
- https://en.ryte.com/platform/wux-overview/
- https://en.ryte.com/platform/performance/
- https://en.ryte.com/platform/quality-assurance/

**WooRank**
- https://www.woorank.com/
- https://www.woorank.com/en/marketing-tools/site-crawl
- https://www.woorank.com/en/marketing-tools/website-reviews
- https://www.woorank.com/en/marketing-tools/keyword-tool
