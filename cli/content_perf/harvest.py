"""Sweep GitHub (gh CLI, jamais de clone) -> sources.json."""

import json
import subprocess
from pathlib import Path


def _run(args):
    return subprocess.run(args, capture_output=True, text=True, timeout=60).stdout


def search_repos(platform, limit=12):
    # Mots SÉPARÉS obligatoires : une phrase unique = recherche exacte = 0 résultat
    raw = _run(
        [
            "gh",
            "search",
            "repos",
            platform,
            "growth",
            "--sort",
            "stars",
            "--limit",
            str(limit),
            "--json",
            "fullName,stargazersCount,description",
        ]
    )
    return json.loads(raw or "[]")


def fetch_readme(full_name):
    raw = _run(
        [
            "gh",
            "api",
            f"repos/{full_name}/readme",
            "--jq",
            ".content",
            "--header",
            "Accept: application/vnd.github+json",
        ]
    )
    if not raw.strip():
        return ""
    import base64

    try:
        compact = "".join(
            raw.split()
        )  # le b64 de l'API GitHub contient des \n légitimes
        return base64.b64decode(compact, validate=True).decode(
            "utf-8", errors="replace"
        )
    except Exception:
        return raw  # déjà en clair (mock/tests)


def harvest(platform, outdir, limit=12):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    sources = []
    repos = search_repos(platform, limit)
    if not repos:
        raise RuntimeError(
            f"0 repo GitHub pour '{platform}' — recherche gh vide ou en échec ; "
            "AUCUNE fiche ne doit être distillée sans corpus (anti-hallucination)"
        )
    for repo in repos:
        readme = fetch_readme(repo["fullName"])
        sources.append(
            {
                "repo": repo["fullName"],
                "stars": repo.get("stargazersCount", 0),
                "description": repo.get("description") or "",
                "readme": readme[:20000],
            }
        )
    out = outdir / "sources.json"
    out.write_text(json.dumps(sources, ensure_ascii=False, indent=1))
    return out
