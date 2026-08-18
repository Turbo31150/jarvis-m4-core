#!/usr/bin/env python3
"""jarvis-prod-exec.py — Exécuteur de PRODUCTION RÉELLE des tâches du planning.

Contrairement à l'ancien routage (titre → blabla LLM), cet outil PRODUIT un vrai
livrable par type de tâche, avec garde-fous, en suivant le cahier des charges :

  action=doc     : rédige un VRAI document Markdown structuré (qwen local 0-token,
                   /v1/completions think-fermé → pas de content vide) et le SAUVE.
  action=commit  : pour une tâche git, COMMIT réellement les fichiers code
                   (JAMAIS secrets/.env/.db ; DRY par défaut, --go pour agir).
  action=verify  : lance les tests d'un projet et capture le vrai résultat.

Sortie : chemin de l'artefact réel produit + statut. 0-token (LLM local).
Usage : jarvis-prod-exec.py <doc|commit|verify> --task "<titre>" [--ctx "<ctx>"] [--go]
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

HOME = os.path.expanduser("~")
QWEN = f"{HOME}/jarvis/bin/qwen-nothink.sh"
OUTDIR = f"{HOME}/jarvis/data/prod_output"
CDC = f"{HOME}/jarvis-linux/contexte-maximal"  # cahiers des charges produits par la cascade

# fichiers JAMAIS committés (garde-fou production)
_SECRET = re.compile(
    r"\.env|secret|\.key$|token|\.db$|credential|password|\.pem$", re.I
)
_NAME_OK = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def _arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


# hub LLM unifié (chat_proxy :18800) = failover multi-backend → FIABLE (qwen direct flaky)
HUB = "http://127.0.0.1:18800/v1/chat/completions"


def _generate(system: str, prompt: str) -> str:
    """Génère du texte via le hub (failover), fallback qwen-nothink. Retry 3×."""
    import json
    import urllib.request

    payload = json.dumps(
        {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 1400,
            "temperature": 0.3,
        }
    ).encode()
    for _ in range(3):
        try:
            req = urllib.request.Request(
                HUB, data=payload, headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=90) as r:
                d = json.loads(r.read().decode())
            body = (
                (d.get("choices", [{}])[0].get("message", {}).get("content"))
                or d.get("response")
                or ""
            ).strip()
            if len(body) >= 80:
                return body
        except Exception:
            pass
    # fallback : qwen-nothink direct
    try:
        r = subprocess.run(
            ["bash", QWEN, prompt, system, "1200"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        return (r.stdout or "").strip()
    except Exception:
        return ""


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60] or "doc"


def _cahier_context() -> str:
    """Injecte un extrait du cahier des charges le plus récent (guide la rédaction)."""
    try:
        dirs = sorted(
            (d for d in os.scandir(CDC) if d.is_dir()),
            key=lambda d: d.stat().st_mtime,
            reverse=True,
        )
        for d in dirs[:1]:
            p = os.path.join(d.path, "CAHIER_DES_CHARGES.md")
            if os.path.exists(p):
                return open(p, encoding="utf-8").read()[:1500]
    except Exception:
        pass
    return ""


# ─────────────────────── action: doc (production réelle d'un document) ───────────────────────
def action_doc() -> int:
    task = _arg("--task", "")
    if not task:
        print("usage: --task requis")
        return 2
    os.makedirs(OUTDIR, exist_ok=True)
    cdc = _cahier_context()
    system = (
        "Tu es un rédacteur professionnel pour AlkymIA-OS / PassCerfa (Franck Delmas, "
        "micro-entreprise libérale, Toulouse). Produis un document Markdown STRUCTURÉ, "
        "complet, factuel et actionnable. Titres, listes, tableaux si utile. "
        "Aucune donnée inventée : écris 'à compléter' si une info manque. Pas de blabla."
    )
    prompt = f"Rédige le document demandé : « {task} »."
    if cdc:
        prompt += f"\n\nContexte (cahier des charges) :\n{cdc}"
    body = _generate(system, prompt)
    if len(body) < 80:
        print("[prod-exec] génération vide (tous backends froids) — relancer plus tard")
        return 1
    out = os.path.join(OUTDIR, f"{_slug(task)}.md")
    header = f"# {task}\n\n_Produit en réelle production par jarvis-prod-exec · à valider._\n\n"
    open(out, "w", encoding="utf-8").write(header + body + "\n")
    print(f"[prod-exec] ✅ document produit ({len(body)}c) → {out}")
    return 0


# ─────────────────────── action: commit (production git réelle, gardée) ───────────────────────
def action_commit() -> int:
    task = _arg("--task", "")
    go = "--go" in sys.argv
    m = re.search(r"dans\s+([A-Za-z0-9._-]+)", task)
    if not m or not _NAME_OK.match(m.group(1)):
        print("[prod-exec] repo non identifiable dans le titre")
        return 2
    repo = m.group(1)
    paths = subprocess.run(
        ["find", HOME, "-maxdepth", "4", "-name", repo, "-type", "d"],
        capture_output=True,
        text=True,
        timeout=15,
    ).stdout.splitlines()
    if not paths:
        print(f"[prod-exec] repo '{repo}' introuvable")
        return 1
    repo_dir = paths[0]
    st = subprocess.run(
        ["git", "-C", repo_dir, "status", "--porcelain"],
        capture_output=True,
        text=True,
        timeout=15,
    ).stdout
    files = [ln[3:].strip().strip('"') for ln in st.splitlines() if ln.strip()]
    safe = [f for f in files if not _SECRET.search(f)]
    blocked = [f for f in files if _SECRET.search(f)]
    print(
        f"[prod-exec] {repo}: {len(safe)} fichiers commitables, {len(blocked)} bloqués (secrets)"
    )
    if blocked:
        print("  ⛔ bloqués:", ", ".join(blocked[:5]))
    if not go:
        print("  DRY — relancer avec --go pour committer les fichiers sûrs")
        return 0
    if not safe:
        print("  rien de sûr à committer")
        return 0
    for f in safe:
        subprocess.run(["git", "-C", repo_dir, "add", "--", f], timeout=10)
    subprocess.run(
        [
            "git",
            "-C",
            repo_dir,
            "commit",
            "-q",
            "-m",
            f"chore: commit auto (prod-exec) — {len(safe)} fichiers",
        ],
        timeout=20,
    )
    print(f"[prod-exec] ✅ {len(safe)} fichiers committés dans {repo}")
    return 0


def action_verify() -> int:
    task = _arg("--task", "")
    m = re.search(r"dans\s+([A-Za-z0-9._-]+)", task)
    if not m:
        print("[prod-exec] projet non identifiable")
        return 2
    repo = m.group(1)
    paths = subprocess.run(
        ["find", HOME, "-maxdepth", "4", "-name", repo, "-type", "d"],
        capture_output=True,
        text=True,
        timeout=15,
    ).stdout.splitlines()
    if not paths:
        return 1
    for cmd in (["pytest", "-q"], ["npm", "test"]):
        try:
            r = subprocess.run(
                cmd, cwd=paths[0], capture_output=True, text=True, timeout=120
            )
            print(f"[prod-exec] {' '.join(cmd)} →\n{(r.stdout + r.stderr)[:1500]}")
            return 0
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"[prod-exec] {cmd[0]} échec: {e}")
    print("[prod-exec] aucun runner de test trouvé")
    return 1


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "doc"
    return {
        "doc": action_doc,
        "commit": action_commit,
        "verify": action_verify,
    }.get(action, lambda: (print(f"action inconnue: {action}"), 2)[1])()


if __name__ == "__main__":
    raise SystemExit(main())
