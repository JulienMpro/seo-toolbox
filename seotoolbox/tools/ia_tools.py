"""Deterministic French prompt templates for common SEO work."""

from __future__ import annotations

from . import ArgSpec, ToolSpec, register

TEMPLATES = {
    "audit": [("technique", "Réalise un audit SEO technique de {sujet} et priorise les corrections par impact et effort."), ("contenu", "Analyse la qualité, l'intention et les lacunes de contenu de {sujet}."), ("plan", "Construis un plan d'action SEO à 30, 60 et 90 jours pour {sujet}.")],
    "brief": [("structure", "Crée un brief éditorial SEO complet sur {sujet} avec intention, Hn et questions."), ("SERP", "Propose les angles indispensables pour dépasser les résultats actuels sur {sujet}."), ("qualité", "Établis une checklist E-E-A-T et de relecture pour un contenu sur {sujet}.")],
    "geo": [("citations", "Analyse comment rendre {sujet} citable par les moteurs génératifs, sans inventer de faits."), ("entités", "Liste les entités, preuves et sources primaires à associer à {sujet}."), ("format", "Transforme {sujet} en réponses concises, factuelles et structurées adaptées aux assistants IA.")],
    "meta": [("title", "Propose cinq titles SEO uniques pour {sujet}, précis et inférieurs à 60 caractères."), ("description", "Rédige cinq meta descriptions pour {sujet}, sans promesse invérifiable et sous 155 caractères."), ("test", "Conçois trois variantes de title et description à tester pour {sujet}.")],
    "strategy": [("objectifs", "Définis une stratégie SEO mesurable pour {sujet}, avec hypothèses, KPI et priorités."), ("roadmap", "Crée une roadmap SEO trimestrielle pour {sujet} avec dépendances et responsables."), ("risques", "Identifie les opportunités et risques SEO de {sujet} et propose des mitigations.")],
    "email": [("prospection", "Rédige un email de prospection personnalisé au sujet de {sujet}, sobre et sans affirmation inventée."), ("relance", "Rédige une relance courte et respectueuse concernant {sujet}."), ("synthèse", "Rédige un email de synthèse client clair sur {sujet}, avec décisions et prochaines étapes.")],
}


def prompt_generator(type: str, subject: str) -> list[dict]:
    """Generate three ready-to-use French prompts from an embedded template family."""
    kind = type.casefold()
    if kind not in TEMPLATES:
        raise ValueError("type must be audit, brief, geo, meta, strategy, or email")
    if not subject.strip():
        raise ValueError("subject must not be empty")
    return [{"n": index, "usage": usage, "prompt": prompt.format(sujet=subject.strip())}
            for index, (usage, prompt) in enumerate(TEMPLATES[kind], 1)]


register(ToolSpec("prompt_generator", prompt_generator, "Generate reusable French SEO prompts.", "generators", [ArgSpec("type", True, help="audit, brief, geo, meta, strategy, or email."), ArgSpec("subject", True, help="Prompt subject.")], "table"))
