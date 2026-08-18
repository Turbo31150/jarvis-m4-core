"""Sources -> fiche biblio + prompt réutilisable. Inference injectée (0 token API)."""

import subprocess
from pathlib import Path

QWEN = Path.home() / "jarvis/bin/qwen-nothink.sh"
SYSTEM = (
    "Tu es analyste de pratiques de créateurs de contenu. Distille des ACTIONS "
    "concrètes et CHIFFRÉES (seuils, benchmarks). Jamais de généralité sans nombre."
)


def qwen_ask(prompt):
    r = subprocess.run(
        ["bash", str(QWEN), prompt, SYSTEM, "1200"],
        capture_output=True,
        text=True,
        timeout=300,
    )
    return r.stdout.strip()


CORPUS_BUDGET = 11500  # chars — au-delà (~20k) le qwen local rend une synthèse vide


def build_prompt(platform, sources):
    kept = sources[:12]
    per_source = max(800, CORPUS_BUDGET // max(1, len(kept)))
    corpus = "\n\n".join(
        f"### {s['repo']} ({s['stars']}★)\n{s['readme'][:per_source]}" for s in kept
    )[:CORPUS_BUDGET]
    return (
        f"Plateforme: {platform}. À partir de ces README GitHub, liste 8-12 actions "
        f"mesurables de pro (formatées '1. action (chiffre)'), puis 5 anti-patterns.\n\n{corpus}"
    )


def distill(platform, sources, outdir, ask=qwen_ask):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    synthesis = ask(build_prompt(platform, sources))
    if not synthesis.strip():
        raise RuntimeError(
            "LLM local a rendu une synthèse vide (reasoning-runaway ? "
            "vérifier qwen-nothink.sh) — fiche NON écrite"
        )
    src_lines = "\n".join(
        f"- [{s['repo']}](https://github.com/{s['repo']}) {s['stars']}★ — "
        f"{s['description']}"
        for s in sources
    )
    fiche = outdir / f"{platform}-pro-performances-github.md"
    fiche.write_text(
        f"# {platform.title()} — meilleures performances (capture GitHub)\n\n"
        f"{synthesis}\n\n## Sources\n{src_lines}\n"
    )
    prompt_file = outdir / f"{platform}-pro-actions.md"
    prompt_file.write_text(
        f"# Prompt — stratège {platform} pro\n\n```text\nAgis comme "
        f"stratège {platform} professionnel. Applique ces règles :\n"
        f"{synthesis}\n```\n"
    )
    return fiche, prompt_file
