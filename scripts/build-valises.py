#!/usr/bin/env python3
"""build-valises.py — Cascade P2 : génère la « valise » des unités sans valise.

Pour chaque ligne unit_registry has_valise=0 : détecte le type de repo, déduit la
commande de lancement, et crée (SI MANQUANT, jamais d'écrasement) :
  .claude/skills/run-<slug>/SKILL.md · PORTS.md · .backup.json · AUTOMATION.md
+ README.md minimal si absent. Met has_valise=1. stdlib, 0 token, additif.
"""

import os
import re
import json
import sqlite3
from datetime import datetime, timezone

ROOT = "/home/pamerys/jarvis"
DB = f"{ROOT}/jarvis_master.db"
TS = datetime.now(timezone.utc).isoformat(timespec="seconds")


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def detect(path):
    """→ (type, run_cmd, prereq)"""
    has = lambda f: os.path.exists(os.path.join(path, f))
    if has("package.json"):
        try:
            pj = json.load(open(os.path.join(path, "package.json")))
        except Exception:
            pj = {}
        deps = {**pj.get("dependencies", {}), **pj.get("devDependencies", {})}
        scripts = pj.get("scripts", {})
        if "electron" in deps or any("electron" in str(v) for v in scripts.values()):
            return (
                "electron",
                "xvfb-run -a npm start  # GUI Electron — voir examples electron",
                "npm install",
            )
        if "vite" in deps or "next" in deps or "react" in deps:
            dev = (
                "dev"
                if "dev" in scripts
                else ("start" if "start" in scripts else "build")
            )
            return (
                "web-frontend",
                f"npm install && npm run {dev}  # puis chromium-cli sur le port Vite/Next",
                "npm install",
            )
        if "start" in scripts:
            return (
                "node-server",
                "npm install && npm start  # serveur — smoke via curl",
                "npm install",
            )
        return ("node", "npm install && npm test", "npm install")
    if has("pyproject.toml") or has("requirements.txt") or has("setup.py"):
        return (
            "python",
            "python3 -m venv .venv && . .venv/bin/activate && pip install -e . && python3 -m <module>",
            "python3-venv",
        )
    if has("Dockerfile") or has("docker-compose.yml") or has("compose.yml"):
        return ("docker", "docker compose up -d  # puis docker logs", "docker")
    if has("CMakeLists.txt") or has("Makefile"):
        return (
            "native",
            "make -j$(nproc)  # build C/C++ ; binaire dans build/ ou ./",
            "build-essential cmake",
        )
    if has("index.html"):
        return (
            "static",
            "python3 -m http.server 8090  # puis chromium-cli http://localhost:8090",
            "",
        )
    # repos data / config sans runtime
    return (
        "data",
        "(pas de runtime — repo data/config) ; backup via run-jarvis-sql-backup",
        "",
    )


def write_if_absent(p, content):
    if os.path.exists(p):
        return False
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(content)
    return True


def valise(code, brand, slug, path):
    name = "run-" + slugify(slug)
    skill_dir = os.path.join(path, ".claude/skills", name)
    typ, run_cmd, prereq = detect(path)
    created = []

    skill_md = f"""---
name: {name}
description: Lancer, build, tester, screenshot {brand} ({code}). Type {typ}. Triggers — "run {slug}", "lance {brand}", "start {slug}", "build {slug}", "test {slug}".
---

# {brand} — valise ({code})

Unité **{code}** ({brand}), division extraite de l'organigramme JARVIS. Type détecté : **{typ}**.

> ⚠️ Valise SCAFFOLD générée par `scripts/build-valises.py` (cascade P2, {TS}).
> La commande ci-dessous est déduite du manifeste — à **valider en lançant l'app** (P2b) puis raffiner.

## Prérequis
```bash
{("sudo apt-get install -y " + prereq) if prereq else "# aucun paquet système détecté"}
```

## Run (chemin agent)
```bash
cd {path}
{run_cmd}
```

## Backup
Voir `.backup.json` — cible incluse dans `run-jarvis-sql-backup`.

## Index
Enregistrée dans `unit_registry` (jarvis_master.db) + `docs/INDEX_UNITES.md`.
"""
    if write_if_absent(os.path.join(skill_dir, "SKILL.md"), skill_md):
        created.append("SKILL.md")

    ports_md = f"# PORTS — {brand} ({code})\n\n> Registre central : `{ROOT}/docs/PORTS_REGISTRY.md`\n\nType {typ}. Ports propres à cette unité à renseigner ici après lancement (P2b).\n"
    if write_if_absent(os.path.join(path, "PORTS.md"), ports_md):
        created.append("PORTS.md")

    backup = {
        "unit": code,
        "brand": brand,
        "type": typ,
        "targets": ["*.db", "*.sqlite", ".env (redacted)"] if typ != "data" else ["./"],
        "via": "run-jarvis-sql-backup",
        "generated": TS,
    }
    if write_if_absent(
        os.path.join(path, ".backup.json"),
        json.dumps(backup, indent=2, ensure_ascii=False),
    ):
        created.append(".backup.json")

    auto_md = f"# AUTOMATION — {brand} ({code})\n\n> Généré {TS}. Timers/crons/hooks propres à l'unité.\n\n- Réindex global : `jarvis-unit-index.timer` (quotidien).\n- Backup : `run-jarvis-sql-backup`.\n- (Ajouter ici les automatisations spécifiques.)\n"
    if write_if_absent(os.path.join(path, "AUTOMATION.md"), auto_md):
        created.append("AUTOMATION.md")

    readme = os.path.join(path, "README.md")
    if not os.path.exists(readme):
        if write_if_absent(
            readme,
            f"# {brand} ({code})\n\nUnité de la holding JARVIS. Type {typ}.\nLancement : voir `.claude/skills/{name}/SKILL.md`.\n",
        ):
            created.append("README.md(min)")

    return name, typ, created


def main():
    # WAL : un seul écrivain à la fois sur une base très sollicitée,
    # il faut attendre au lieu d'échouer sur "database is locked".
    con = sqlite3.connect(DB, timeout=120)
    con.execute("PRAGMA busy_timeout=120000")
    rows = con.execute(
        "SELECT code,brand,slug,repo_path FROM unit_registry WHERE has_valise=0 AND repo_path!=''"
    ).fetchall()
    done = 0
    for code, brand, slug, path in rows:
        if not os.path.isdir(path):
            print(f"  ⏭️  {code}: repo absent ({path})")
            continue
        name, typ, created = valise(code, brand, slug, path)
        con.execute("UPDATE unit_registry SET has_valise=1 WHERE code=?", (code,))
        done += 1
        print(
            f"  ✅ {code:32} [{typ:13}] {name}  (+{','.join(created) or 'déjà complet'})"
        )
    con.commit()
    con.close()
    print(f"\n✅ P2 : {done} valises générées/complétées.")


if __name__ == "__main__":
    main()
