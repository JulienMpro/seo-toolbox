# Catalogue des mini-outils SEO — SEO Toolbox (JulienMpro/seo-toolbox)

> **Objet** : inventaire dense des 125+ mini-outils utilitaires de la toolbox consultant SEO.
> **Alignement** : complète `benchmark-toolbox-seo-features-2026.md` (features des outils payants) en les traduisant en mini-outils unitaires réplicables via **API DataForSEO** + **calcul local** + **API gratuites nommées**.
> **Règle** : zéro donnée inventée. Chaque outil est réel et faisable. Source incertaine = `[À VÉRIFIER]`.
> **Légende source** : `calcul local` (Python maison) · `DataForSEO <endpoint>` (nom réel de l'endpoint) · `API gratuite <nom>` · `fichier utilisateur` (upload client : CSV/GSC export/logs).

---

## 1) Calculatrices SEO

| Nom | But (entrée → sortie) | Source |
|---|---|---|
| ROI SEO | Budget SEO mensuel + panier moyen + marge → ROI net cumulé sur 12-24 mois | calcul local |
| Projection de trafic | Volumes de recherche + CTR par position visée → trafic organique mensuel estimé | calcul local + DataForSEO `kw_data_google_ads_search_volume` |
| Valeur d'une position | Vol + CPC + position actuelle/voulue → valeur monétaire € du gain de position | calcul local + DataForSEO `kw_data_google_ads_search_volume` |
| Modèles de CTR | Position → CTR estimé (courbes desktop/mobile/featured) | calcul local (courbes type AWR) |
| Budget SEO équivalent AdWords | Objectif trafic + CPC → budget SEO nécessaire vs coût Ads équivalent | calcul local |
| Taux de conversion | Visites + conversions → taux de conversion + intervalle de confiance | calcul local |
| Coût par clic implicite | Trafic organique + coût SEO → CPC équivalent vs achat Ads | calcul local |
| Coût d'acquisition (CAC) & LTV | Coûts SEO + nouveaux clients + valeur client → CAC, LTV, ratio LTV/CAC | calcul local |
| Temps de crawl estimé | Nb pages + crawl budget quotidien → jours pour un recrawl complet | calcul local + fichier utilisateur (logs/GSC) |
| Taille & découpage sitemap | Nb URLs → répartition en fichiers ≤ 50 000 URLs + index sitemap | calcul local |
| Score E-E-A-T | Checklist signaux (auteur, sources, mentions, preuves) → score pondéré /100 | calcul local (checklist) |
| Valeur d'un backlink | Métriques du lien (autorité, trafic) → valeur marchande estimée € | calcul local + DataForSEO `backlinks_summary` |
| Coût de production de contenu | Nb mots + tarif rédacteur → coût d'un article + coût/1 000 mots | calcul local |
| Longueur de contenu idéale | Mot-clé → moyenne de mots du top 10 SERP → longueur cible recommandée | DataForSEO `serp_organic_live_advanced` + `on_page_content_parsing` |

## 2) Convertisseurs & encodeurs

| Nom | But (entrée → sortie) | Source |
|---|---|---|
| URL encode/decode | URL brute → encodée/décodée (caractères spéciaux, espaces, UTF-8) | calcul local |
| Texte → slug | Titre/texte → slug URL propre (minuscules, accents, ponctuation) | calcul local |
| Liste → URLs | Liste de mots-clés → slugs/URLs propres | calcul local |
| Markdown → HTML | Texte markdown → HTML propre | calcul local (bibliothèque) |
| HTML → Markdown | HTML → markdown | calcul local (bibliothèque) |
| CSV ↔ JSON | Conversion bidirectionnelle CSV↔JSON | calcul local |
| Convertisseur de casse | Texte → UPPER/lower/Title/Sentence case | calcul local |
| Suppression d'accents | Texte → sans diacritiques (é→e) ou translittération | calcul local |
| Convertisseur de dates | Timestamp ↔ ISO 8601 ↔ date FR + format sitemap `lastmod` | calcul local |
| Convertisseur d'unités octets | Ko/Mo/Go → poids de pages/fichiers comparés | calcul local |
| Tokeniseur mots-clés | Texte → liste de termes uniques triés + stopwords retirés | calcul local |
| Dédoublonneur de liste | Liste de mots-clés/URLs → liste nettoyée, dédupliquée, triée | calcul local |
| HTML entities encode/decode | Texte ↔ entités HTML (`&amp;` `<` `>` `"`) | calcul local |
| Minifier JSON-LD | Bloc JSON-LD → minifié / beautifié | calcul local |

## 3) Générateurs

| Nom | But (entrée → sortie) | Source |
|---|---|---|
| Générateur de redirections 301 | Ancienne URL + nouvelle URL → règle `.htaccess`/nginx | calcul local |
| Générateur robots.txt | Directives (allow/disallow, sitemap, user-agent) → fichier robots.txt | calcul local |
| Générateur sitemap.xml | Liste URLs + lastmod/priority → sitemap.xml valide | calcul local |
| Générateur balises title/meta | Mots-clés + template → balises title/meta à la bonne longueur (pixels) | calcul local |
| Générateur hreflang | Langues + URLs → balises hreflang + x-default | calcul local |
| Générateur d'ancres | Mots-clés cibles → variantes d'ancres naturelles (exactes/partielles/marque/nue) | calcul local |
| Expansion de mots-clés (seed) | Mot seed → longue traîne, questions, variantes, suggestions | DataForSEO `dataforseo_labs_google_keyword_ideas` + `google_keyword_suggestions` |
| Générateur de briefs de contenu | Mots-clés + top SERP → brief structuré (Hn, questions, longueur, termes) | DataForSEO `serp_organic_live_advanced` + `on_page_content_parsing` |
| Générateur de questions FAQ | Mot-clé → questions PAA + variantes « qui/quoi/comment » | DataForSEO `serp_organic_live_advanced` (PAA) + `google_keyword_suggestions` |
| Générateur de variantes title/meta | Title/meta de base → N variantes A/B testables | calcul local |
| Générateur de maillage interne | Liste de pages + mots-clés → suggestions de liens internes | calcul local + fichier utilisateur |
| Générateur de fil d'Ariane | Arborescence → markup Breadcrumb + rendu visuel | calcul local |
| Générateur de snippets optimisés | Contenu → extraits formatés paragraphe/liste/tableau (featured snippet) | calcul local |
| Générateur de canonical | URL canonique + variantes → balises canonical | calcul local |
| Générateur Open Graph / Twitter Cards | Page (titre, image, type) → balises OG + Twitter Cards | calcul local |
| Générateur de cocon sémantique | Mots-clés → arborescence parent/enfant + plan de maillage | calcul local + DataForSEO `google_related_keywords` |

## 4) Analyseurs on-page

| Nom | But (entrée → sortie) | Source |
|---|---|---|
| Densité de mots-clés | Texte/URL + mot-clé → densité % + répartition par section | calcul local + DataForSEO `on_page_content_parsing` |
| Cannibalisation de mots-clés | Domaine + mots-clés → pages en concurrence sur la même requête | DataForSEO `dataforseo_labs_google_ranked_keywords` |
| Co-occurrence | Texte + mot principal → termes co-occurrents les plus fréquents | calcul local + `on_page_content_parsing` |
| N-grams | Texte → bigrams/trigrams fréquents | calcul local |
| Lisibilité FR/EN | Texte → scores Flesch/FOG/Ariane + recommandations | calcul local |
| Longueur de contenu | URL(s) → nb mots, paragraphes, images, Hn | DataForSEO `on_page_content_parsing` |
| Similarité de pages | 2+ URLs → % similarité (détection contenu dupliqué) | calcul local + `on_page_content_parsing` |
| H1/Hn checker (lot) | Liste d'URLs → audit H1-H6 (doublons, manques, ordre, longueurs) | calcul local (crawl) + `on_page_content_parsing` |
| Analyseur title/meta (lot) | Liste d'URLs → longueurs, doublons, troncature Google | calcul local + `on_page_content_parsing` |
| Analyse sémantique TF-IDF | Texte + corpus top SERP → termes manquants vs concurrents | calcul local + `on_page_content_parsing` |
| Détecteur de contenu fin (thin) | Texte/URL → score de contenu pauvre (peu de mots, peu de valeur) | calcul local (heuristique) |
| Extraction d'entités | Texte → entités nommées (personnes, marques, lieux) | calcul local (NLP spaCy) |
| Analyse des ancres internes | Site crawl → répartition des ancres de liens internes | calcul local (crawl) |
| Score de maillage interne | Site crawl → nb liens entrants/sortants + profondeur par page | calcul local (crawl) |

## 5) Outils SERP

| Nom | But (entrée → sortie) | Source |
|---|---|---|
| Comparateur de SERP | 2+ mots-clés → SERP côte à côte (positions, domaines, features) | DataForSEO `serp_organic_live_advanced` |
| Extracteur PAA | Mot-clé → questions « People Also Ask » + réponses | DataForSEO `serp_organic_live_advanced` |
| Détecteur de features SERP | Mot-clé → features présentes (featured, PAA, vidéo, images, map, shopping) | DataForSEO `serp_organic_live_advanced` |
| Différence de SERP devices | Mot-clé → comparaison desktop vs mobile | DataForSEO `serp_organic_live_advanced` (param device) |
| Différence de SERP pays/langue | Mot-clé + pays/langue → SERP par marché | DataForSEO `serp_organic_live_advanced` (location/language) + `serp_locations` |
| Historique SERP | Mot-clé → évolution du top 10 sur la période | DataForSEO `dataforseo_labs_google_historical_serps` |
| Position tracker en masse | Domaine + liste de mots-clés → positions + variations | DataForSEO `dataforseo_labs_google_ranked_keywords` + `serp_organic_live_advanced` |
| Analyse d'intention | Mot-clé → intention (informationnelle/transactionnelle/navigationnelle) | DataForSEO `dataforseo_labs_search_intent` |
| Gap de mots-clés | 2+ domaines → mots-clés uniques/partagés | DataForSEO `dataforseo_labs_google_domain_intersection` |
| Mots-clés d'un concurrent | Domaine concurrent → ses mots-clés rankés | DataForSEO `dataforseo_labs_google_ranked_keywords` |
| Suggestions liées | Mot-clé → suggestions Google/related | DataForSEO `dataforseo_labs_google_keyword_suggestions` + `google_related_keywords` |
| Top searches | Catégorie → recherches les plus populaires | DataForSEO `dataforseo_labs_google_top_searches` |
| Matrice features × mots-clés | Liste de mots-clés → matrice features présentes par requête | DataForSEO `serp_organic_live_advanced` |

## 6) Outils liens

| Nom | But (entrée → sortie) | Source |
|---|---|---|
| Répartition d'ancres | Domaine → distribution des ancres de backlinks | DataForSEO `backlinks_anchors` |
| Ratio dofollow/nofollow | Domaine → répartition dofollow vs nofollow | DataForSEO `backlinks_summary` |
| Générateur de désaveu | Liste de domaines toxiques → fichier disavow.txt formaté | calcul local (fichier utilisateur) |
| Détection de liens toxiques | Domaine → backlinks à spam score élevé | DataForSEO `backlinks_bulk_spam_score` |
| Link gap (écart de liens) | Mon domaine + concurrent → domaines référents manquants | DataForSEO `backlinks_domain_intersection` + `backlinks_competitors` |
| Analyse des domaines référents | Domaine → liste + métriques des domaines référents | DataForSEO `backlinks_referring_domains` |
| Nouveaux/liens perdus | Domaine → liens gagnés/perdus sur la période | DataForSEO `backlinks_timeseries_new_lost_summary` |
| Évolution du profil de liens | Domaine → courbe backlinks/référents dans le temps | DataForSEO `backlinks_timeseries_summary` |
| Comparateur de profils de liens | 2+ domaines → backlinks/référents/score comparés | DataForSEO `backlinks_summary` + `backlinks_bulk_referring_domains` |
| Pages les plus linkées | Domaine → pages recevant le plus de backlinks | DataForSEO `backlinks_bulk_pages_summary` |
| Détection de réseaux PBN | Domaine → IP/réseaux partagés entre référents | DataForSEO `backlinks_referring_networks` |
| Score d'autorité | Domaine → score d'autorité (rank) | DataForSEO `backlinks_bulk_ranks` |

## 7) Vérificateurs

| Nom | But (entrée → sortie) | Source |
|---|---|---|
| Status HTTP en masse | Liste d'URLs → code status, redirects, temps de réponse | calcul local (requests) |
| Chaîne de redirections | URL → chaîne complète (hops, codes, boucles) + URL finale | calcul local |
| robots.txt checker | URL + user-agent → test d'autorisation de crawl | calcul local |
| Validateur sitemap | URL de sitemap → validité XML + liste d'URLs | calcul local |
| Canonical checker | URL(s) → balise canonical, cohérence, conflits | calcul local + `on_page_content_parsing` |
| hreflang checker | URL(s) → balises hreflang, réciprocité, erreurs | calcul local |
| Validateur schema.org | URL/markup → validation JSON-LD + erreurs | calcul local (jsonschema) + API gratuite Google Rich Results Test [À VÉRIFIER] |
| Mobile viewport | URL → meta viewport + détection responsive | calcul local + DataForSEO `on_page_instant_pages` |
| Validateur meta title/description | URL(s) → longueurs, doublons, manques | calcul local |
| Validateur Open Graph | URL → présence/qualité des balises OG | calcul local |
| Lighthouse / Core Web Vitals | URL → scores perf/a11y/SEO + CWV | DataForSEO `on_page_lighthouse` |
| hreflang réciproque | URLs multilingues → vérification des liens retour hreflang | calcul local |
| Mixed content / SSL | Domaine → ressources mixtes HTTP/HTTPS | calcul local |
| Validateur de syntaxe d'URL | Liste → URLs valides + normalisation | calcul local |
| Checker d'indexation | Liste d'URLs → statut indexé/non indexé | fichier utilisateur (export GSC) |

## 8) Outils données structurées (JSON-LD)

| Nom | But (entrée → sortie) | Source |
|---|---|---|
| Générateur JSON-LD Article | Titre + auteur + date → markup Article | calcul local |
| Générateur JSON-LD FAQ | Liste Q/R → markup FAQPage | calcul local |
| Générateur JSON-LD LocalBusiness | Nom + adresse + tél → markup LocalBusiness | calcul local |
| Générateur JSON-LD Product | Produit (nom, prix, avis) → markup Product + Offer + AggregateRating | calcul local |
| Générateur JSON-LD Breadcrumb | Arborescence → markup BreadcrumbList | calcul local |
| Générateur JSON-LD Review | Évaluation + note → markup Review | calcul local |
| Générateur JSON-LD Event | Événement (date, lieu) → markup Event | calcul local |
| Générateur JSON-LD Organization | Société + logo → markup Organization | calcul local |
| Générateur JSON-LD HowTo | Étapes → markup HowTo | calcul local |
| Générateur JSON-LD JobPosting | Offre d'emploi → markup JobPosting | calcul local |
| Validateur de données structurées | URL/markup → validation + erreurs + éligibilité rich results | calcul local + API gratuite Google Rich Results Test [À VÉRIFIER] |
| Extracteur de données structurées | URL → tous les JSON-LD/microdata détectés | calcul local + `on_page_content_parsing` |

## 9) Planification & stratégie

| Nom | But (entrée → sortie) | Source |
|---|---|---|
| Calendrier éditorial | Mots-clés + priorités → plan de publication daté | calcul local (fichier utilisateur) |
| Projection SEO 12 mois | KPIs actuels + budget → trajectoire trafic/positions sur 12 mois | calcul local |
| Priorisation de mots-clés | Liste + vol + difficulté + valeur → score de priorité | calcul local + DataForSEO `dataforseo_labs_bulk_keyword_difficulty` |
| Scoring de difficulté | Mot-clé → KD (Keyword Difficulty) | DataForSEO `dataforseo_labs_bulk_keyword_difficulty` |
| Clusters de sujets | Mots-clés → regroupement thématique + pilier/sous-pages | calcul local + DataForSEO `google_related_keywords` |
| Cocon sémantique | Mots-clés → arborescence parent/enfant + maillage | calcul local + DataForSEO `google_related_keywords` |
| Estimation de trafic potentiel | Domaine + mots-clés cibles → trafic potentiel total | DataForSEO `dataforseo_labs_bulk_traffic_estimation` |
| Répartition par intention | Mots-clés → % par intention pour prioriser | DataForSEO `dataforseo_labs_search_intent` |
| Matrice effort/impact | Actions + effort + impact → matrice 2×2 quick wins | calcul local (fichier utilisateur) |
| Audit de contenu existant | Sitemap/export GSC → scoring (garder/améliorer/fusionner/supprimer) | fichier utilisateur + `on_page_content_parsing` |
| Benchmark concurrentiel | Concurrents → KPIs comparés (mots-clés, trafic, liens) | DataForSEO `dataforseo_labs_google_ranked_keywords` + `backlinks_summary` |

## 10) Divers utiles

| Nom | But (entrée → sortie) | Source |
|---|---|---|
| IP / User-Agent checker | URL → IP, headers, serveur, redirections | calcul local |
| Extraction d'emails | Texte/URL → emails trouvés | calcul local |
| Extraction d'URLs | Texte/HTML → URLs extraites | calcul local |
| Comparateur de domaines | 2 domaines → KPIs côte à côte (autorité, liens, mots-clés) | DataForSEO (multi-endpoints) |
| WHOIS lite | Domaine → registrar, dates, statut | DataForSEO `domain_analytics_whois_overview` |
| Détection de technologies | URL → CMS/stack détectée | DataForSEO `domain_analytics_technologies_domain_technologies` |
| Extracteur de meta brutes | URL → title/meta/OG/Hn bruts | calcul local + `on_page_content_parsing` |
| Comparateur de textes (diff) | 2 textes → diff côte à côte | calcul local |
| Compteur de caractères/mots | Texte → nb caractères/mots (calibration meta) | calcul local |
| Lorem ipsum SEO | Paramètres → texte de remplissage | calcul local |
| Convertisseur de fuseaux horaires | Heure + fuseaux → conversion (planification publication) | calcul local |
| Analyseur de log de crawl | Fichier logs → comportement Googlebot, crawl budget, codes | calcul local + fichier utilisateur (logs) |

---

## Les 20 outils les plus demandés par un consultant (priorité)

1. **Position tracker en masse** — cœur du métier : suivi quotidien des positions, variations, par device/localisation.
2. **Comparateur de SERP** — diagnostic concurrentiel immédiat, côte à côte sur plusieurs requêtes.
3. **Générateur de briefs de contenu** — produit l'input rédactionnel facturable au client.
4. **Analyseur title/meta (lot)** — audit rapide des balises à l'échelle d'un site.
5. **Cannibalisation de mots-clés** — problème n°1 détecté sur les audits, à forte valeur perçue.
6. **Gap de mots-clés** — opportunités d'un client face à ses concurrents.
7. **Audit de contenu existant** — rationalisation du parc de pages (garder/fusionner/supprimer).
8. **Status HTTP en masse** — premier réflexe de tout audit technique.
9. **Chaîne de redirections** — indispensable migrations/refontes.
10. **Lighthouse / Core Web Vitals** — priorisation des corrections de vitesse.
11. **Générateur de redirections 301** — livrable direct pour la mise en œuvre.
12. **Générateur sitemap.xml** — prérequis de toute soumission GSC.
13. **H1/Hn checker (lot)** — vérification structurelle rapide.
14. **Générateur JSON-LD FAQ** — rich results à faible effort, fort impact.
15. **Répartition d'ancres** — diagnostic du profil de liens en un coup d'œil.
16. **Détection de liens toxiques** — argument commercial pour un netlinking propre.
17. **Générateur de désaveu** — livrable disavow.txt prêt à soumettre.
18. **Priorisation de mots-clés** — transforme une liste brute en plan d'action.
19. **Projection de trafic / ROI SEO** — outil de vente (démontrer l'impact business).
20. **Comparateur de domaines** — benchmark one-shot pour prospects et reporting.

---

## Référentiel DataForSEO utilisé (endpoints réels)

**SERP / Labs** : `serp_organic_live_advanced`, `serp_locations`, `dataforseo_labs_google_keyword_ideas`, `google_keyword_suggestions`, `google_related_keywords`, `google_ranked_keywords`, `google_keywords_for_site`, `google_domain_intersection`, `google_page_intersection`, `google_historical_serps`, `google_historical_keyword_data`, `google_historical_rank_overview`, `google_top_searches`, `google_subdomains`, `google_relevant_pages`, `google_serp_competitors`, `search_intent`, `bulk_keyword_difficulty`, `bulk_traffic_estimation`.

**Backlinks** : `backlinks_anchors`, `backlinks_backlinks`, `backlinks_summary`, `backlinks_competitors`, `backlinks_domain_intersection`, `backlinks_page_intersection`, `backlinks_referring_domains`, `backlinks_referring_networks`, `backlinks_bulk_spam_score`, `backlinks_bulk_ranks`, `backlinks_bulk_referring_domains`, `backlinks_bulk_pages_summary`, `backlinks_timeseries_summary`, `backlinks_timeseries_new_lost_summary`, `backlinks_bulk_new_lost_backlinks`.

**On-page / domaine** : `on_page_content_parsing`, `on_page_instant_pages`, `on_page_lighthouse`, `domain_analytics_whois_overview`, `domain_analytics_technologies_domain_technologies`, `content_analysis_search`, `content_analysis_summary`, `kw_data_google_ads_search_volume`.

> Les endpoints `serp_*` disposent des paramètres `device` (desktop/mobile) et `location_code`/`language_code` → ils couvrent les outils « différence devices / pays / langue » sans endpoint supplémentaire.
