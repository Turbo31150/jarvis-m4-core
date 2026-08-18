#!/usr/bin/env python3
"""
content-score.py — Scoring algorithmique contenu social JARVIS
Usage: python3 content-score.py score --caption "..." --images /tmp/slides/ [--json]
       python3 content-score.py rank --db autopilot.db [--top 10]
"""

import sys
import re
import json
import argparse
import math
from pathlib import Path

# ── Référentiels viraux (calibrés sur top créateurs tech LinkedIn/IG 2025) ──
POWER_HOOKS = [
    r"\d+\s*(raisons?|tips?|erreurs?|secrets?|façons?|étapes?|règles?|leçons?)",
    r"(ce que|ce qu[e']|voici|comment|pourquoi|j'ai|nous avons|on a)",
    r"(thread|carrousel|carousel|🧵|👇)",
    r"(résultat|résultats|before.?after|avant.?après)",
    r"(€|\$|k€|M€|\d+%|\d+x)",
    r"(hack|astuce|secret|insider|exclusif)",
]
ENGAGEMENT_HASHTAGS = {
    "tech": [
        "ia",
        "ai",
        "machinelearning",
        "deeplearning",
        "llm",
        "gpt",
        "claude",
        "openai",
        "tech",
        "python",
        "devops",
        "cloud",
        "startup",
        "innovation",
        "futur",
        "intelligence",
    ],
    "growth": [
        "linkedin",
        "content",
        "marketing",
        "growth",
        "entrepreneur",
        "buildinpublic",
        "indiehacker",
        "sideproject",
        "creator",
        "personal_branding",
    ],
    "jarvis": [
        "jarvis",
        "jarvisos",
        "aicluster",
        "homelab",
        "selfhosted",
        "opensource",
    ],
}
TOP_HASHTAG_POOL = [h for hs in ENGAGEMENT_HASHTAGS.values() for h in hs]

IDEAL_CAPTION_RANGE = (150, 400)  # chars — engagement peak LinkedIn/IG
IDEAL_HASHTAG_COUNT = (5, 15)
SLIDE_COUNT_SWEET_SPOT = (5, 10)  # LinkedIn carousel ideal


def score_hook(caption: str) -> dict:
    """Score la force du hook (première ligne = 90% du reach)."""
    first_line = caption.strip().split("\n")[0]
    hits = sum(1 for p in POWER_HOOKS if re.search(p, first_line, re.I))
    score = min(25, hits * 8 + (5 if any(c.isdigit() for c in first_line[:30]) else 0))
    return {
        "score": score,
        "max": 25,
        "first_line": first_line[:80],
        "hook_matches": hits,
    }


def score_caption_structure(caption: str) -> dict:
    """Longueur, structure, appel à l'action."""
    length = len(caption)
    lines = [l.strip() for l in caption.split("\n") if l.strip()]
    has_cta = bool(
        re.search(
            r"(commente|partage|like|sauvegarde|follow|abonne|dis.moi|tag|réponds|réagis|vote)",
            caption,
            re.I,
        )
    )
    has_emoji = bool(re.search(r"[\U0001F300-\U0001FAFF]", caption))
    in_range = IDEAL_CAPTION_RANGE[0] <= length <= IDEAL_CAPTION_RANGE[1]
    score = 0
    score += 15 if in_range else (8 if length >= 80 else 2)
    score += 10 if has_cta else 0
    score += 5 if has_emoji else 0
    score += 5 if len(lines) >= 3 else 0  # paragraphes courts
    return {
        "score": min(35, score),
        "max": 35,
        "length": length,
        "has_cta": has_cta,
        "has_emoji": has_emoji,
        "paragraphs": len(lines),
    }


def score_hashtags(caption: str) -> dict:
    """Quantité + pertinence hashtags."""
    tags = re.findall(r"#(\w+)", caption.lower())
    count = len(tags)
    relevant = [t for t in tags if t in TOP_HASHTAG_POOL]
    in_range = IDEAL_HASHTAG_COUNT[0] <= count <= IDEAL_HASHTAG_COUNT[1]
    score = 0
    score += 10 if in_range else (5 if count >= 3 else 0)
    score += min(15, len(relevant) * 3)
    return {
        "score": min(25, score),
        "max": 25,
        "count": count,
        "relevant": relevant[:8],
        "relevant_count": len(relevant),
    }


def score_visual(images_path: str | None) -> dict:
    """Nombre de slides + taille fichiers (proxy qualité visuelle)."""
    if not images_path:
        return {"score": 0, "max": 15, "slide_count": 0, "note": "no images"}
    path = Path(images_path)
    slides = sorted(path.glob("*.png")) + sorted(path.glob("*.jpg"))
    count = len(slides)
    in_range = SLIDE_COUNT_SWEET_SPOT[0] <= count <= SLIDE_COUNT_SWEET_SPOT[1]
    avg_size = sum(s.stat().st_size for s in slides) / max(count, 1) / 1024  # KB
    score = 0
    score += 10 if in_range else (5 if count >= 3 else 2)
    score += 5 if avg_size >= 50 else (3 if avg_size >= 20 else 1)  # qualité image
    return {
        "score": min(15, score),
        "max": 15,
        "slide_count": count,
        "avg_size_kb": round(avg_size, 1),
    }


def score_seo_keywords(caption: str) -> dict:
    """Mots-clés SEO haute valeur dans la caption."""
    seo_terms = [
        "IA",
        "AI",
        "LLM",
        "GPU",
        "cluster",
        "automation",
        "JARVIS",
        "Python",
        "DevOps",
        "cloud",
        "open.source",
        "performance",
        "scalable",
        "deploy",
        "inference",
        "RAG",
        "agent",
        "workflow",
        "pipeline",
        "monitoring",
    ]
    found = [t for t in seo_terms if re.search(t, caption, re.I)]
    score = min(10, len(found) * 2)
    return {"score": score, "max": 10, "keywords_found": found[:6]}


def score_content(caption: str, images_path: str | None = None) -> dict:
    hook = score_hook(caption)
    struct = score_caption_structure(caption)
    tags = score_hashtags(caption)
    visual = score_visual(images_path)
    seo = score_seo_keywords(caption)

    total = (
        hook["score"] + struct["score"] + tags["score"] + visual["score"] + seo["score"]
    )
    max_total = hook["max"] + struct["max"] + tags["max"] + visual["max"] + seo["max"]
    pct = round(total / max_total * 100)

    grade = (
        "S"
        if pct >= 85
        else "A"
        if pct >= 70
        else "B"
        if pct >= 55
        else "C"
        if pct >= 40
        else "D"
    )
    virality_est = round(math.exp(pct / 100 * 3.5) * 10)  # vues estimées (relatif)

    improvements = []
    if hook["hook_matches"] == 0:
        improvements.append("Hook faible : ajouter chiffre + verbe d'action en ligne 1")
    if not struct["has_cta"]:
        improvements.append(
            "Pas de CTA : terminer par une question ou 'Sauvegarde pour plus tard'"
        )
    if not struct["has_emoji"]:
        improvements.append("Ajouter 2-3 emojis pour +23% engagement")
    if tags["count"] < 5:
        improvements.append(f"Trop peu de hashtags ({tags['count']}) : viser 8-12")
    if tags["relevant_count"] < 3:
        improvements.append(
            "Hashtags peu pertinents : utiliser #AI #LLM #DevOps #JARVIS"
        )
    if visual["slide_count"] < 5:
        improvements.append(
            f"Seulement {visual['slide_count']} slides : viser 7-10 pour max portée"
        )
    if struct["length"] < 150:
        improvements.append(
            f"Caption trop courte ({struct['length']} chars) : enrichir à 200-350"
        )

    return {
        "grade": grade,
        "total_score": total,
        "max_score": max_total,
        "percent": pct,
        "virality_index": virality_est,
        "breakdown": {
            "hook": hook,
            "structure": struct,
            "hashtags": tags,
            "visual": visual,
            "seo": seo,
        },
        "improvements": improvements,
        "verdict": f"Grade {grade} ({pct}%) — {'Excellent, prêt à publier' if pct >= 70 else 'Améliorer avant publication'}",
    }


def print_report(result: dict, use_json: bool = False):
    if use_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    r = result
    g = r["grade"]
    colors = {
        "S": "\033[1;93m",
        "A": "\033[1;32m",
        "B": "\033[1;34m",
        "C": "\033[1;33m",
        "D": "\033[1;31m",
    }
    reset = "\033[0m"
    c = colors.get(g, "")

    print(f"\n{'━' * 52}")
    print(
        f"  CONTENT SCORE  {c}Grade {g}  {r['percent']}%{reset}  ({r['total_score']}/{r['max_score']})"
    )
    print(f"  Virality Index: ~{r['virality_index']}x baseline")
    print(f"{'━' * 52}")
    b = r["breakdown"]
    print(
        f"  Hook        {b['hook']['score']:>2}/{b['hook']['max']}  {b['hook']['first_line'][:45]}"
    )
    print(
        f"  Structure   {b['structure']['score']:>2}/{b['structure']['max']}  "
        f"len:{b['structure']['length']} cta:{b['structure']['has_cta']}"
    )
    print(
        f"  Hashtags    {b['hashtags']['score']:>2}/{b['hashtags']['max']}  "
        f"{b['hashtags']['count']} tags, {b['hashtags']['relevant_count']} pertinents"
    )
    print(
        f"  Visuel      {b['visual']['score']:>2}/{b['visual']['max']}  "
        f"{b['visual']['slide_count']} slides @ {b['visual']['avg_size_kb']}KB/img"
    )
    print(
        f"  SEO         {b['seo']['score']:>2}/{b['seo']['max']}  "
        f"{b['seo']['keywords_found'][:4]}"
    )
    print(f"{'─' * 52}")
    if r["improvements"]:
        print("  AMÉLIORATIONS:")
        for i, imp in enumerate(r["improvements"], 1):
            print(f"  {i}. {imp}")
    else:
        print("  ✅ Aucune amélioration critique")
    print(f"{'━' * 52}")
    print(f"  {r['verdict']}\n")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")

    sc = sub.add_parser("score")
    sc.add_argument("--caption", "-c", required=True)
    sc.add_argument("--images", "-i", default=None)
    sc.add_argument("--json", action="store_true")

    sg = sub.add_parser("suggest")
    sg.add_argument("--topic", "-t", required=True)
    sg.add_argument("--pilier", "-p", default="tech")

    args = p.parse_args()

    if args.cmd == "score":
        result = score_content(args.caption, args.images)
        print_report(result, use_json=args.json)
        sys.exit(0 if result["percent"] >= 55 else 1)

    elif args.cmd == "suggest":
        # Génère une caption optimisée via LLM local
        import subprocess

        prompt = (
            f"Tu es expert LinkedIn/Instagram growth hacking. "
            f"Génère une caption virale optimisée pour ce sujet : '{args.topic}' "
            f"(pilier: {args.pilier}). "
            f"Règles : ligne 1 = hook avec chiffre, 3 paragraphes courts, "
            f"8-10 hashtags pertinents #AI #LLM #DevOps, CTA final question ouverte. "
            f"200-350 chars max (hors hashtags). Réponds UNIQUEMENT avec la caption."
        )
        result = subprocess.run(
            ["bash", "-c", f"bash ~/jarvis/scripts/lm-ask.sh {json.dumps(prompt)}"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        caption = result.stdout.strip()
        if caption:
            print(f"\n{'─' * 52}\nCaption suggérée:\n{'─' * 52}\n{caption}\n{'─' * 52}")
            scored = score_content(caption)
            print_report(scored)
        else:
            print("ERR: LLM n'a pas répondu", file=sys.stderr)
            sys.exit(1)

    else:
        p.print_help()


if __name__ == "__main__":
    main()
