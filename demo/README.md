# Démo — Projet fictif « Ma Plomberie Paris »

> **Démonstration du workflow SEO Toolbox sur un projet 100 % FICTIF.**
> Aucune donnée de projet réel n'est utilisée : le domaine `maplomberie-paris.fr` n'existe pas, les chiffres de marché (volumes, CPC, SERP) sont les données réelles renvoyées par DataForSEO le 20/08/2026, et tout ce qui ne peut pas être mesuré (backlinks d'un domaine fictif, mentions IA) s'affiche honnêtement en `N/D`.

## Le projet fictif

- **Entreprise** : Ma Plomberie Paris (fictive) — artisan plombier, intervention 7j/7 sur Paris.
- **Domaine** : `maplomberie-paris.fr` (non enregistré, fictif).
- **Objectif illustré** : montrer le workflow complet d'analyse de marché qu'un consultant SEO exécute pour un nouveau client — sans aucune donnée de vrai projet.

## 1. Keyword Research — le marché « plombier paris »

Commande : `seo keywords research "plombier paris" --country FR --limit 8 --output csv`

| keyword | volume | KD | CPC | competition | intent |
|---|---|---|---|---|---|
| plombier paris 16 | 1 600 | 0 | 13,90 € | 0,89 | navigational |
| plombier paris 15 | 2 400 | 0 | 15,90 € | 0,93 | navigational |
| service plomberie paris | N/D | N/D | N/D | N/D | commercial |
| plombier paris 13 | 1 600 | 0 | 16,74 € | 0,74 | navigational |
| plombier paris 17 | 1 600 | 0 | 24,26 € | 0,80 | navigational |
| plombier paris 18 | 1 300 | 0 | 21,12 € | 0,79 | navigational |
| plombier paris 19 | 1 300 | 0 | 10,30 € | 0,89 | navigational |
| entreprise plomberie paris | 260 | 0 | 6,44 € | 0,90 | commercial |

**Lecture** : le marché est très local (intentions navigationnelles par arrondissement, CPC élevés 10-24 €) — un site fictif devrait viser les requêtes « plombier paris + arrondissement » avec des pages par zone.

## 2. SERP — les concurrents réels sur « plombier paris »

Commande : `seo serp live "plombier paris" --country FR --limit 6`

| Rank | Domaine | Titre | Élément clé |
|---|---|---|---|
| 6 | lesbonsartisans.fr | Meilleur artisan Plombier Paris (75000) | place de marché artisans |
| 10 | plombier-paris-express.com | Plombier Paris Express® — vu sur TF1 | urgence + Trustpilot 4,9★ |
| 11 | travaux.com | Plombiers Paris — tous arrondissements | comparateur devis |
| 12 | allovoisins.com | Plomberie - Installation sanitaire - Paris (75) | mise en relation |
| 13 | plombierparis15pascher.fr | Plombier Paris 15 pas cher 24/24h 68€ | EMD + prix d'appel |
| 14 | plombier-paris-artisans.fr | Art Plombier Paris : Agréé Assurances | urgence 24h/24 |

**Lecture** : SERP dominée par les places de marché (Les Bons Artisans, Travaux.com, AlloVoisins) — un indépendant fictif aurait intérêt à attaquer les requêtes d'arrondissement en premier.

## 3. Tracking du domaine fictif — comportement honnête

Commande : `seo backlinks summary --domain maplomberie-paris.fr`

→ **N/D partout** (backlinks, domaines référents, rank, spam score). Le domaine n'existe pas : l'outil n'invente rien. C'est le comportement voulu : un vrai consultant connecterait le domaine réel de son client ici.

Commande : `seo geo mentions "plombier paris" --engine chatgpt`

→ **N/D** : aucune mention structurée de domaine dans les réponses ChatGPT pour cette requête locale au moment du test. Là encore : pas d'invention, l'outil affiche ce qui est mesurable.

## 4. Workflow illustré

```
# 1. Analyser le marché (avant de créer le site)
seo keywords research "plombier paris" --country FR
seo serp live "plombier paris" --country FR
seo geo mentions "plombier paris"          # visibilité IA (N/D honnête ici)

# 2. Quand le site fictif existe (maquette, dev, staging)
seo audit run --url https://maplomberie-paris.fr
seo content score --url https://maplomberie-paris.fr --keyword "plombier paris 16"

# 3. Suivi hebdomadaire (une fois le site en ligne)
seo ranks domain "plombier paris 16" --domain maplomberie-paris.fr --country FR
seo monitor init --url https://maplomberie-paris.fr     # baseline
seo monitor check --url https://maplomberie-paris.fr    # à chaque passage

# 4. Rapport client
seo report build --input rapport-audit.md --title "Audit SEO — Ma Plomberie Paris" --output rapport.html
```

## Ce que cette démo prouve

1. **Zéro donnée inventée** : le marché est réel (volumes/CPC/SERP DataForSEO), le projet est fictif, et tout ce qui n'est pas mesurable s'affiche `N/D`.
2. **Workflow consultant complet** : recherche de marché → analyse concurrentielle → audit → tracking → monitoring → rapport white-label.
3. **Aucune donnée de projet réel** : aucun domaine client, aucune propriété, aucun identifiant de compte n'apparaît dans cette démo.
