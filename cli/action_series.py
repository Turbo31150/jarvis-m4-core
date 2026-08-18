#!/usr/bin/env python3
"""action_series.py — Séries d'actions réutilisables (cascade 0-token).

Concept : une TÂCHE = série d'actions (command_ids de la bibliothèque cmdlib),
enregistrée et indexée par mots-clés. Pour rejouer : on ASSEMBLE par mots-clés,
zéro LLM, zéro RAM. C'est le pont bibliothèque×cascade.

Table : action_series(id, name, keywords, steps JSON, source) dans jarvis_master.db.
Résolution des steps → commandes réelles via Postgres cmdlib (container jv-infra-biblio-db).

Usage :
  action_series.py --seed                 # enregistre les séries de base
  action_series.py --list
  action_series.py --assemble "déployer docker"   # assemble par mots-clés
  action_series.py --record "nom" "kw1,kw2" "cmd.id.1,cmd.id.2"
"""

from __future__ import annotations
import argparse
import json
import sqlite3
import subprocess

MASTER = "/home/pamerys/jarvis/jarvis_master.db"
PG = [
    "docker",
    "exec",
    "-i",
    "jv-infra-biblio-db",
    "psql",
    "-U",
    "cmduser",
    "-d",
    "cmdlib",
    "-tA",
]

SEED = [
    (
        "déployer stack docker",
        ["déployer docker", "deploy stack", "lancer container", "monter stack"],
        ["docker.build", "docker.compose.up", "docker.compose.logs"],
    ),
    (
        "sauvegarder un disque",
        ["backup disque", "cloner disque", "sauvegarde disk", "copie disque"],
        ["disk.list.lsblk", "disk.smart.check", "disk.clone.dd"],
    ),
    (
        "publier du code git",
        ["push code", "commit push", "publier git", "envoyer sur github"],
        ["git.status", "git.add.all", "git.commit", "git.push"],
    ),
    (
        "diagnostiquer un service",
        ["debug service", "service planté", "réparer service", "service failed"],
        ["svc.status", "svc.log.journal", "svc.restart"],
    ),
    (
        "diagnostiquer le GPU",
        ["gpu chaud", "état gpu", "vram pleine", "gpu lent"],
        ["gpu.status", "gpu.memory.check", "gpu.proc.list"],
    ),
    (
        "nettoyer docker",
        ["nettoyer docker", "prune docker", "libérer espace docker"],
        ["docker.ps.all", "docker.prune.containers", "docker.prune.images"],
    ),
    (
        "mettre à jour le système",
        ["update système", "upgrade système", "mettre à jour paquets"],
        ["pkg.update.apt", "pkg.upgrade.apt", "pkg.autoremove.apt"],
    ),
    (
        "diagnostiquer le réseau",
        ["réseau coupé", "debug réseau", "pas d internet", "ping échoue"],
        ["net.iface.list", "net.ping", "net.route.list", "net.dns.dig"],
    ),
]


def db():
    # WAL : un seul écrivain à la fois sur une base très sollicitée,
    # il faut attendre au lieu d'échouer sur "database is locked".
    c = sqlite3.connect(MASTER, timeout=120)
    c.execute("PRAGMA busy_timeout=120000")
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("""CREATE TABLE IF NOT EXISTS action_series(
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, keywords TEXT,
        steps TEXT, source TEXT, created_at TEXT DEFAULT (datetime('now')),
        usage_count INTEGER DEFAULT 0)""")
    return c


def resolve(cmd_ids):
    """command_id -> commande réelle (via cmdlib)."""
    if not cmd_ids:
        return {}
    quoted = ",".join("'" + i.replace("'", "''") + "'" for i in cmd_ids)
    out = subprocess.run(
        PG
        + [
            "-c",
            f"SELECT id||'|'||action||'|'||command FROM commands WHERE id IN ({quoted});",
        ],
        capture_output=True,
        text=True,
        timeout=20,
    ).stdout
    res = {}
    for line in out.splitlines():
        p = line.split("|", 2)
        if len(p) == 3:
            res[p[0]] = (p[1], p[2])
    return res


def cmd_seed(_):
    c = db()
    n = 0
    for name, kw, steps in SEED:
        cur = c.execute(
            "INSERT OR IGNORE INTO action_series(name,keywords,steps,source) VALUES(?,?,?,?)",
            (name, json.dumps(kw, ensure_ascii=False), json.dumps(steps), "seed"),
        )
        n += cur.rowcount
    c.commit()
    c.close()
    print(f"seed: +{n} séries enregistrées")


def cmd_record(a):
    c = db()
    steps = [s.strip() for s in a.steps.split(",") if s.strip()]
    kw = [k.strip() for k in a.keywords.split(",") if k.strip()]
    c.execute(
        "INSERT OR REPLACE INTO action_series(name,keywords,steps,source) VALUES(?,?,?,?)",
        (a.name, json.dumps(kw, ensure_ascii=False), json.dumps(steps), "manual"),
    )
    c.commit()
    c.close()
    print(f"série « {a.name} » enregistrée ({len(steps)} actions)")


def cmd_list(_):
    c = db()
    for name, kw, steps in c.execute(
        "SELECT name,keywords,steps FROM action_series ORDER BY name"
    ):
        print(
            f"  {name}  [{', '.join(json.loads(kw)[:3])}]  → {len(json.loads(steps))} actions"
        )
    c.close()


def cmd_assemble(a):
    q = a.query.lower()
    c = db()
    best = None
    for row in c.execute("SELECT name,keywords,steps FROM action_series"):
        name, kw, steps = row
        kws = json.loads(kw)
        score = sum(
            2
            if k.lower() in q
            else (1 if all(w in q for w in k.lower().split()) else 0)
            for k in kws
        )
        if score and (best is None or score > best[0]):
            best = (score, name, json.loads(steps))
    if not best:
        print(f"aucune série ne matche « {a.query} »")
        c.close()
        return
    _, name, steps = best
    c.execute(
        "UPDATE action_series SET usage_count=usage_count+1 WHERE name=?", (name,)
    )
    c.commit()
    c.close()
    resolved = resolve(steps)
    print(f"🔧 Tâche assemblée : « {name} »  ({len(steps)} actions, 0 token)\n")
    for i, sid in enumerate(steps, 1):
        action, command = resolved.get(sid, ("(inconnu)", "?"))
        print(f"  {i}. [{sid}] {action}\n     $ {command}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--assemble", dest="query")
    ap.add_argument("name", nargs="?")
    ap.add_argument("keywords", nargs="?")
    ap.add_argument("steps", nargs="?")
    a = ap.parse_args()
    if a.seed:
        cmd_seed(a)
    elif a.list:
        cmd_list(a)
    elif a.query:
        cmd_assemble(a)
    elif a.name and a.keywords and a.steps:
        cmd_record(a)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
