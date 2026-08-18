#!/usr/bin/env python3
"""alimenter-deepresearch.py — alimente le shell deep-research depuis le RÉEL.

`deepresearch_audit.py` lit un unique fichier statique, `ANTIGRAVITY_TASKS.md`.
Ce fichier n'existe plus : le plan sortait donc « 0 étape » alors que la base
porte des centaines de tâches vivantes. Une source statique se tarit toujours ;
c'est le même défaut que l'ancienne file d'auto-génération.

On régénère ce fichier depuis les gisements réels, à chaque appel :

  tasks       file de travail (pending / to_validate)
  plan        créations à produire, avec leur commande prête
  unit_registry  unités lançables — leur run_cmd est une étape exécutable

0 token, 0 réseau, 0 LLM : tout est déjà en base.

  alimenter-deepresearch.py            régénère le fichier
  alimenter-deepresearch.py --dry      montre sans écrire
  alimenter-deepresearch.py --max 400  borne le volume
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sqlite3

DB = "/home/pamerys/jarvis/jarvis_master.db"
CIBLE = pathlib.Path("/home/pamerys/jarvis/ANTIGRAVITY_TASKS.md")


def ouvrir() -> sqlite3.Connection:
    # La base est écrite en continu : attendre plutôt qu'échouer.
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=120)
    conn.execute("PRAGMA busy_timeout=120000")
    conn.row_factory = sqlite3.Row
    return conn


def _sql(conn, req, args=()):
    try:
        return conn.execute(req, args).fetchall()
    except sqlite3.Error:
        return []


def collecter(conn, maxi: int) -> list[tuple[str, str, str, str]]:
    """→ [(section, id, titre, commande)] — la commande peut être vide."""
    out: list[tuple[str, str, str, str]] = []

    # 1. File de travail. `context` porte parfois « ▶ cmd » posé par le capteur
    #    de contexte : c'est une commande prête, on la récupère.
    for r in _sql(
        conn,
        "SELECT id, title, COALESCE(context,'') ctx FROM tasks"
        " WHERE status IN ('pending','to_validate') ORDER BY id DESC LIMIT ?",
        (maxi,),
    ):
        cmd = ""
        for ligne in (r["ctx"] or "").splitlines():
            if "▶" in ligne:
                cmd = ligne.split("▶", 1)[1].strip()
                break
        out.append(("File de travail", f"T{r['id']}", r["title"], cmd))

    # 2. Créations : le pack de contexte contient déjà la commande à jouer.
    for r in _sql(
        conn,
        "SELECT id, titre, COALESCE(preloaded,'') p FROM plan WHERE source='creation'",
    ):
        cmd = ""
        try:
            cmd = (json.loads(r["p"]) or {}).get("ready_cmd", "") or ""
        except Exception:
            pass
        out.append(("Créations", f"C{r['id']}", r["titre"], cmd))

    # 3. Unités lançables : un run_cmd renseigné EST une étape vérifiable.
    for r in _sql(
        conn,
        "SELECT code, brand, run_cmd FROM unit_registry"
        " WHERE COALESCE(run_cmd,'') <> '' ORDER BY code",
    ):
        out.append(
            (
                "Unités lançables",
                r["code"],
                f"Lancer {r['brand'] or r['code']}",
                r["run_cmd"],
            )
        )
    return out


def rendre(lignes) -> str:
    """Format attendu par deepresearch_audit.py : `### T<id> — titre`, puis la
    commande dans un bloc shell. Le parseur ne lit rien d'autre."""
    parts = [
        "# ANTIGRAVITY TASKS",
        "",
        "> Régénéré depuis la base par "
        "`scripts/alimenter-deepresearch.py`. Ne pas éditer à la main : "
        "toute modification est écrasée au prochain appel.",
        "",
    ]
    section_courante = None
    for section, ident, titre, cmd in lignes:
        if section != section_courante:
            parts += [f"## {section}", ""]
            section_courante = section
        titre_propre = " ".join((titre or "").split())[:150]
        parts.append(f"### {ident} — {titre_propre}")
        if cmd:
            parts += ["", "```bash", " ".join(cmd.split())[:400], "```", ""]
        else:
            parts.append("")
    return "\n".join(parts) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=400)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    conn = ouvrir()
    lignes = collecter(conn, a.max)
    conn.close()
    if not lignes:
        print("aucune source alimentée — la base est vide sur les 3 gisements")
        return 1

    contenu = rendre(lignes)
    par_section: dict[str, int] = {}
    avec_cmd = 0
    for s, _, _, c in lignes:
        par_section[s] = par_section.get(s, 0) + 1
        if c:
            avec_cmd += 1

    if a.dry:
        print(contenu[:1200])
    else:
        CIBLE.write_text(contenu, encoding="utf-8")
    print(
        f"[alimenter] {len(lignes)} étapes "
        f"({' · '.join(f'{k} {v}' for k, v in par_section.items())}) · "
        f"{avec_cmd} avec commande prête → "
        f"{'(dry)' if a.dry else CIBLE}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
