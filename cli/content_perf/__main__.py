"""content_perf — capture des meilleures perfs d'une plateforme de contenu.
Usage: python3 -m cli.content_perf <plateforme> [--limit 12]
Prod: fiche -> ~/jarvis/data/biblio_knowledge/, prompt -> ~/prompts/prompts/claude-code/,
blocs -> ~/labo/bibliotheque/lib/BLOCS-INDEX.tsv. `base` surchargeable pour les tests."""

import argparse
import json
import shutil
from pathlib import Path
from . import blocs as bl
from . import distill as dt
from . import harvest as hv
from . import scoring as sc


def run(platform, base=None, ask=dt.qwen_ask, limit=12):
    home = Path.home()
    if base:  # arborescence de test auto-contenue
        base = Path(base)
        fiche_dir, prompt_dir = base / "biblio_knowledge", base / "prompts"
        index, work = base / "lib/BLOCS-INDEX.tsv", base / "content_perf" / platform
    else:  # chemins de prod réels
        fiche_dir = home / "jarvis/data/biblio_knowledge"
        prompt_dir = home / "prompts/prompts/claude-code"
        index = home / "labo/bibliotheque/lib/BLOCS-INDEX.tsv"
        work = home / "jarvis/data/content_perf" / platform
    src = hv.harvest(platform, work, limit=limit)
    sources = json.loads(src.read_text())
    fiche, prompt_file = dt.distill(platform, sources, work, ask=ask)
    fiche_dir.mkdir(parents=True, exist_ok=True)
    prompt_dir.mkdir(parents=True, exist_ok=True)
    index.parent.mkdir(parents=True, exist_ok=True)
    fiche_final = fiche_dir / fiche.name
    shutil.copy(fiche, fiche_final)
    prompt_final = prompt_dir / prompt_file.name
    shutil.copy(prompt_file, prompt_final)
    added = bl.merge_index(bl.make_blocs(platform, fiche_final, prompt_final), index)
    score = sc.score_fiche(fiche_final, sources_count=len(sources))
    log_db = (base / "logs.db") if base else sc.DEFAULT_DB
    sc.log_run(
        platform, sources=len(sources), score=score, fiche=fiche_final, db_path=log_db
    )
    print(
        f"[content-perf] {platform}: {len(sources)} sources, score={score}/100, "
        f"fiche={fiche_final}, prompt={prompt_final}, +{added} bloc(s)"
    )
    return {
        "fiche": fiche_final,
        "prompt": prompt_final,
        "added": added,
        "score": score,
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("platform")
    ap.add_argument("--limit", type=int, default=12)
    a = ap.parse_args()
    run(a.platform, limit=a.limit)
