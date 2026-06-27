#!/usr/bin/env python3
"""
JARVIS Recherche - Agent de recherche pédagogique pour enseignants
API: http://192.168.1.26:1234/v1/chat/completions (M2 / qwen3.5-9b)
Sauvegarde: ~/Documents/Recherche/YYYY-MM-DD_sujet.md
"""

import sys
import argparse
import requests
from datetime import datetime
from pathlib import Path
import urllib.parse

# Configuration
M2_API = "http://192.168.1.26:1234/v1/chat/completions"
MODEL = "qwen/qwen3.5-9b"
SAVE_DIR = Path.home() / "Documents" / "Recherche"
SAVE_DIR.mkdir(parents=True, exist_ok=True)

# Prompts enseignant
SYSTEM_TEACHER = """Tu es un assistant pédagogique expert. Réponds en tant que professeur
avec expérience en enseignement. Adapte ton niveau de langage au niveau scolaire demandé.
Sois précis, structuré et pédagogue."""


def query_m2(prompt: str, system: str = SYSTEM_TEACHER) -> str:
    """Interroge M2 via API LM Studio"""
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 2000,
    }

    try:
        resp = requests.post(M2_API, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except requests.RequestException as e:
        return f"[ERREUR API M2] {e}"


def recherche_simple(sujet: str, niveau: str = "lycee") -> str:
    """Recherche simple avec adaptation de niveau"""
    niveaux = {
        "primaire": "pour élèves de 6-11 ans, vocabulaire simple",
        "college": "pour élèves de 11-15 ans, concepts intermédiaires",
        "lycee": "pour élèves de 15-18 ans, concepts avancés",
        "universite": "pour niveau universitaire, approche scientifique rigoureuse",
    }

    prompt = f"""Explique '{sujet}' ({niveaux.get(niveau, niveaux["lycee"])}).

Format:
1. **Définition** (2-3 phrases clés)
2. **Concept principal** (développé)
3. **Exemples concrets** (2-3 exemples)
4. **Liens avec autres sujets** (ce qu'il faut savoir avant)
5. **Astuce mnémotechnique** (pour retenir)"""

    return query_m2(prompt)


def recherche_biblio(sujet: str) -> str:
    """Générer bibliographie APA"""
    prompt = f"""Pour le sujet '{sujet}', fournis une bibliographie au format APA
avec 5-8 sources variées (livres, articles, sites éducatifs fiables).
Format strict APA 7e édition."""

    return query_m2(prompt)


def generer_exercices(sujet: str, nb: int = 5, niveau: str = "lycee") -> str:
    """Générer exercices + correction"""
    niveaux = {
        "primaire": "très simples, QCM et vrai/faux",
        "college": "modérés, mix QCM et réponses courtes",
        "lycee": "avancés, analyse et raisonnement",
        "universite": "complexes, problèmes et démonstrations",
    }

    prompt = f"""Crée {nb} exercices sur '{sujet}' ({niveaux.get(niveau, niveaux["lycee"])}).

Pour chaque exercice:
- **Énoncé** (clair et précis)
- **Réponse** (avec explication pédagogique)
- **Compétence** (ce qu'il teste)

Numérote les exercices."""

    return query_m2(prompt)


def sauvegarder(contenu: str, sujet: str, type_doc: str = "recherche") -> str:
    """Sauvegarde avec métadonnées"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    slug = urllib.parse.quote(sujet, safe="")[:50]
    filename = f"{timestamp}_{slug}_{type_doc}.md"
    filepath = SAVE_DIR / filename

    header = f"""# Recherche: {sujet}
**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Type:** {type_doc}
**Sujet:** {sujet}

---

"""

    filepath.write_text(header + contenu, encoding="utf-8")
    return str(filepath)


def main():
    parser = argparse.ArgumentParser(
        description="JARVIS Recherche - Assistant pédagogique",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Exemples:
  recherche.py "photosynthèse lycée"
  recherche.py --niveau college "théorème de Pythagore"
  recherche.py --biblio "révolution française"
  recherche.py --exercices "sujet" --nb 8""",
    )

    parser.add_argument("sujet", nargs="?", help="Sujet de recherche")
    parser.add_argument(
        "--niveau",
        default="lycee",
        choices=["primaire", "college", "lycee", "universite"],
        help="Niveau scolaire (défaut: lycee)",
    )
    parser.add_argument("--biblio", action="store_true", help="Mode bibliographie APA")
    parser.add_argument("--exercices", action="store_true", help="Générer exercices")
    parser.add_argument(
        "--nb", type=int, default=5, help="Nombre d'exercices (défaut: 5)"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        default=True,
        help="Sauvegarder résultat (défaut: oui)",
    )
    parser.add_argument(
        "--no-save", action="store_false", dest="save", help="Ne pas sauvegarder"
    )

    args = parser.parse_args()

    if not args.sujet:
        parser.print_help()
        sys.exit(1)

    print(f"🔍 JARVIS Recherche: {args.sujet}")
    print("⏳ Interrogation M2 (qwen3.5-9b)...")

    # Routing
    if args.biblio:
        print("📚 Mode: Bibliographie APA")
        resultat = recherche_biblio(args.sujet)
        type_doc = "biblio"
    elif args.exercices:
        print(f"✏️  Mode: {args.nb} exercices ({args.niveau})")
        resultat = generer_exercices(args.sujet, args.nb, args.niveau)
        type_doc = "exercices"
    else:
        print(f"📖 Mode: Recherche simple ({args.niveau})")
        resultat = recherche_simple(args.sujet, args.niveau)
        type_doc = "recherche"

    print("\n" + "=" * 60)
    print(resultat)
    print("=" * 60 + "\n")

    if args.save:
        filepath = sauvegarder(resultat, args.sujet, type_doc)
        print(f"✅ Sauvegardé: {filepath}")


if __name__ == "__main__":
    main()
