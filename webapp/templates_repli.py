#!/usr/bin/env python3
"""Moteur de repli HORS-IA (0 réseau, 0 token, jamais de 503).

Quand toute la cascade ai_local est indisponible (cluster down + cloud throttlé +
local surchauffé), au lieu de lever AIUnavailable, on renvoie un CONTENU UTILE à
compléter, adapté au type de demande détecté dans le prompt. L'ancienne app Windows
avait ce filet (templates locaux) ; Pousseline le retrouve ici.

Usage : ai_local.generate() appelle repli(user, system) en dernier recours.
Retour : str markdown, toujours préfixée d'un bandeau « mode hors-ligne ».
"""

BANDEAU = "> ⚠️ **Mode hors-ligne** (IA indisponible — cloud/serveurs saturés). Voici une trame à compléter/adapter. Relance quand un backend est revenu pour la version rédigée.\n\n"

# Phrases-types d'appréciation par niveau global (accord genre via {e}).
_APPRECIATIONS = {
    "excellent": "{prenom} est un{e} élève brillant{e}, motivé{e} et autonome. {Il} s'investit avec constance et tire le groupe vers le haut.",
    "bon": "{prenom} est un{e} élève appliqué{e} et impliqué{e}. {Il} progresse régulièrement ; à encourager à prendre la parole davantage.",
    "moyen": "{prenom} fournit des efforts. Les acquis sont fragiles sur {domaine} ; un travail régulier à la maison consoliderait les bases.",
    "difficulte": "{prenom} rencontre des difficultés sur {domaine}. {Il} a besoin d'étayage et de temps ; les progrès sont réels quand {il} est accompagné{e}.",
}


def _genre(system, user):
    t = (system + " " + user).lower()
    if any(k in t for k in ("élève : f", "genre f", "fille", "elle ")):
        return {"e": "e", "Il": "Elle", "il": "elle"}
    return {"e": "", "Il": "Il", "il": "il"}


def _kind(user, system):
    t = (user + " " + system).lower()
    if any(
        k in t for k in ("bulletin", "appréciation", "appreciation", "lsu", "synthèse")
    ):
        return "bulletin"
    if any(k in t for k in ("mail", "courrier", "parents", "cahier de liaison")):
        return "mail"
    if any(
        k in t
        for k in ("séance", "seance", "séquence", "cahier-journal", "cahier journal")
    ):
        return "seance"
    if any(
        k in t
        for k in ("exercice", "fiche", "problème", "probleme", "rituel", "dictée")
    ):
        return "fiche"
    return "generic"


def repli(user, system=""):
    k = _kind(user, system)
    g = _genre(system, user)
    if k == "bulletin":
        blocs = "\n\n".join(
            f"**{niv.capitalize()}** — "
            + txt.format(prenom="[Prénom]", domaine="[domaine]", **g)
            for niv, txt in _APPRECIATIONS.items()
        )
        return (
            BANDEAU
            + "## Appréciation (choisir le niveau qui correspond)\n\n"
            + blocs
            + "\n\n*Adapter le prénom, le domaine et affiner selon l'élève.*"
        )
    if k == "mail":
        return (
            BANDEAU + "## Modèle de courrier aux parents\n\n"
            "Bonjour,\n\nJe me permets de vous contacter au sujet de **[objet]**. "
            "**[Corps : décrire la situation en 2-3 phrases, ton bienveillant.]**\n"
            "Je reste disponible pour en échanger.\n\nBien cordialement,\n[Enseignante]\n\n"
            "*Astuce : la banque de 42 modèles (table `modeles` / static/modeles) contient déjà des courriers prêts.*"
        )
    if k == "seance":
        return (
            BANDEAU + "## Trame de séance\n\n"
            "**Objectif :** [compétence visée — B.O.]\n**Matériel :** [...]\n**Durée :** [...] min\n\n"
            "1. **Découverte / mise en situation** ([..] min)\n2. **Recherche / manipulation** ([..] min)\n"
            "3. **Mise en commun / institutionnalisation** ([..] min)\n4. **Entraînement** ([..] min)\n\n"
            "**Différenciation :** soutien / standard / approfondissement\n**Trace écrite :** [...]\n**Évaluation :** [...]"
        )
    if k == "fiche":
        return (
            BANDEAU + "## Fiche d'exercices — [notion]\n\n"
            "### 🟢 SOUTIEN\n**Consigne :** [...]\n1. [...]\n2. [...]\n\n"
            "### 🟡 STANDARD\n**Consigne :** [...]\n1. [...]\n2. [...]\n\n"
            "### 🔵 APPROFONDISSEMENT\n**Consigne :** [...]\n1. [...]\n\n"
            "### ✅ Corrigé\n[...]\n\n*Astuce : l'onglet Plan B contient 600+ fiches déjà générées à piocher.*"
        )
    return (
        BANDEAU
        + "**Trame à compléter :**\n\n- Objectif : [...]\n- Points clés : [...]\n- À développer : [...]"
    )


if __name__ == "__main__":
    for demo in (
        "Rédige une appréciation de bulletin pour un élève",
        "Écris un mail aux parents",
        "Crée une fiche d'exercices d'addition",
        "Prépare une séance sur les fractions",
    ):
        print("=" * 60, "\nPROMPT:", demo, "\n")
        print(repli(demo)[:400])
