#!/usr/bin/env python3
"""distribuer_methodes.py — distribue les 7 protocoles méthodo à TOUTES les familles
d'agents JARVIS, généré 0-token via LM Studio M1 :1234 (moteur biblio_filler).

Idempotent (skip si existe), cache SQL, garde thermique GPU. Régénère à la fin :
methodes-registry.json + tool_map (jarvis_master.db) + prompt-library.json.
"""

import os
import sys
import json
import sqlite3
from datetime import datetime

sys.path.insert(0, "/home/turbo/jarvis/cli")
import biblio_filler as b  # réutilise gen() = cache -> LM Studio :1234 -> fallback

PBASE = "/home/turbo/prompts/prompts"
CANON = os.path.join(PBASE, "methodes-jarvis")
MASTER = "/home/pamerys/jarvis/jarvis_master.db"
METHODS = [
    "plan-mode",
    "deep-recherche",
    "todolist-dynamique",
    "protocole",
    "cahier-des-charges",
    "contexte-maximal",
    "cascade-bibliotheque",
]
KW = {
    "plan-mode": ["plan", "explore", "conception", "plan mode"],
    "deep-recherche": ["deep research", "recherche", "sources", "veille"],
    "todolist-dynamique": ["todoliste", "tasks", "queue", "auto-alimentation"],
    "protocole": ["protocole", "0-token", "cascade", "délégation"],
    "cahier-des-charges": ["cdc", "cahier des charges", "spec", "exigences"],
    "contexte-maximal": ["contexte", "context", "charger", "few-shot"],
    "cascade-bibliotheque": ["bibliothèque", "remplissage", "infini", "vivante"],
}
# Familles d'agents (legions) restantes à couvrir — "les 1000 agents"
FAMILIES = {
    "ai-engine": "gestion modèles, routing LLM, embeddings, fine-tuning, génération de code",
    "automation": "workflows, automatisation navigateur, scheduling, ops proactives, CI/CD",
    "boot-layer": "séquence de boot, checks de démarrage, init des services",
    "cli-tools": "CLI JARVIS, utilitaires, dispatcher d'actions, API gateway",
    "cluster-mgr": "santé nœuds, allocation GPU, load-balancing, failover, réseau",
    "comms": "bot Telegram, notifications, messagerie, alertes",
    "core-agents": "container operator, health guardian, consensus engine, agent factory",
    "deployment": "scripts de déploiement, boot OpenClaw, setup, installation",
    "dispatch": "routage priorité, load-balancing, coordination multi-agents",
    "linux-admin": "paquets, filesystem, permissions, cron, systemd, sécurité",
    "maintenance": "backups, nettoyage, zombie reaper, santé des bases",
    "monitoring": "détection d'anomalies, analyse de logs, benchmarks, métriques",
    "ops-sre": "cowork engine, déploiement, auto-healing, réponse incident",
    "security": "audit sécu, threat model, hardening, revue, ownership map",
    "social-growth": "LinkedIn, publication contenu, croissance audience, automation post",
    "voice-engine": "STT, TTS, wake word, pipeline audio, Piper/Whisper",
    "win-admin": "registre Windows, PowerShell, services, firewall, réseau, monitoring",
}


def log(m):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {m}", flush=True)


def _one(task):
    import time

    fam, desc, m, canon_m = task
    fp = os.path.join(PBASE, fam, "methodes", f"{m}.md")
    if os.path.exists(fp):
        return ("skip", fam, m)
    while b.gpu_temp_max() >= 84:
        log("⏸️ pause thermique")
        time.sleep(60)
    prompt = (
        f"Adapte ce protocole méthodologique JARVIS à la famille d'agents « {fam} » "
        f"({desc}). Garde la structure Markdown (titre #, sections, tableaux compacts), "
        f"~30 lignes, factuel, ancré dans le runtime réel de cette famille. "
        f"Termine par une ligne « Base: methodes-jarvis/{m}.md ».\n\n"
        f"--- PROTOCOLE CANONIQUE ---\n{canon_m}"
    )
    txt = b.gen(
        prompt,
        system="Tu es un architecte JARVIS. Réponds en Markdown français, concis, sans préambule.",
        timeout=150,
    )
    if txt and len(txt) > 120:
        open(fp, "w", encoding="utf-8").write(txt.strip() + "\n")
        return ("made", fam, m)
    return ("fail", fam, m)


def build():
    from concurrent.futures import ThreadPoolExecutor

    canon = {
        m: open(os.path.join(CANON, f"{m}.md"), encoding="utf-8").read()
        for m in METHODS
    }
    for fam in FAMILIES:
        os.makedirs(os.path.join(PBASE, fam, "methodes"), exist_ok=True)
    tasks = [
        (fam, desc, m, canon[m]) for fam, desc in FAMILIES.items() for m in METHODS
    ]
    made = skipped = fail = 0
    with ThreadPoolExecutor(max_workers=4) as ex:  # LM Studio parallel=4
        for status, fam, m in ex.map(_one, tasks):
            if status == "made":
                made += 1
                log(f"  ✓ {fam}/{m}")
            elif status == "skip":
                skipped += 1
            else:
                fail += 1
                log(f"  ✗ {fam}/{m}")
    log(f"génération: +{made} créés, {skipped} présents, {fail} échecs")
    return made


def reindex():
    # registry central
    platforms = [
        d
        for d in os.listdir(PBASE)
        if os.path.isdir(os.path.join(PBASE, d, "methodes"))
    ]
    reg = {
        "name": "JARVIS Méthodes Registry",
        "generated": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "canonical": "methodes-jarvis",
        "platforms": sorted(platforms),
        "methods": {},
    }
    for m in METHODS:
        variants = [
            {"platform": p, "path": os.path.join(PBASE, p, "methodes", f"{m}.md")}
            for p in sorted(platforms)
            if os.path.isfile(os.path.join(PBASE, p, "methodes", f"{m}.md"))
        ]
        reg["methods"][m] = {
            "keywords": KW[m],
            "variants": variants,
            "count": len(variants),
        }
    reg["total_variants"] = sum(v["count"] for v in reg["methods"].values())
    open(os.path.join(CANON, "methodes-registry.json"), "w").write(
        json.dumps(reg, ensure_ascii=False, indent=2)
    )
    log(
        f"registry: {len(METHODS)} méthodes × {len(platforms)} plateformes = {reg['total_variants']} variantes"
    )
    # tool_map
    # WAL : un seul écrivain à la fois sur une base très sollicitée,
    # il faut attendre au lieu d'échouer sur "database is locked".
    conn = sqlite3.connect(MASTER, timeout=120)
    conn.execute("PRAGMA busy_timeout=120000")
    c = conn.cursor()
    for m in METHODS:
        c.execute(
            """INSERT INTO tool_map(name,category,loader,keywords,triggers,priority)
                     VALUES(?,?,?,?,?,8) ON CONFLICT(name) DO UPDATE SET
                     triggers=excluded.triggers,keywords=excluded.keywords""",
            (
                f"methode:{m}",
                "methode",
                f"prompt:methodes-jarvis/{m}.md",
                json.dumps(KW[m], ensure_ascii=False),
                json.dumps(
                    [f"platform:{p}" for p in sorted(platforms)], ensure_ascii=False
                ),
            ),
        )
    conn.commit()
    conn.close()
    log("tool_map: 7 méthodes enregistrées (découvrables par tous les agents)")
    # prompt-library index (récursif)
    prompts = []
    by_cat = {}
    for dp, _, files in os.walk(PBASE):
        for fn in files:
            fp = os.path.join(dp, fn)
            rel = os.path.relpath(fp, PBASE)
            cat = rel.split(os.sep)[0]
            import hashlib

            body = open(fp, "rb").read()
            prompts.append(
                {
                    "category": cat,
                    "file": os.path.relpath(fp, os.path.join(PBASE, cat)),
                    "path": fp,
                    "bytes": len(body),
                    "sha1": hashlib.sha1(body).hexdigest()[:12],
                }
            )
            by_cat[cat] = by_cat.get(cat, 0) + 1
    J = "/home/turbo/jarvis-linux/config/prompt-library.json"
    old = json.load(open(J)) if os.path.exists(J) else {}
    v = old.get("version", "2.4").split(".")
    v[-1] = str(int(v[-1]) + 1)
    out = {
        "name": old.get("name", "JARVIS Prompt Library"),
        "version": ".".join(v),
        "generated": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "base": PBASE,
        "total": len(prompts),
        "by_category": dict(sorted(by_cat.items(), key=lambda x: -x[1])),
        "prompts": prompts,
    }
    json.dump(out, open(J, "w"), ensure_ascii=False, indent=2)
    log(
        f"prompt-library.json v{out['version']} | {out['total']} prompts | {len(by_cat)} catégories"
    )


if __name__ == "__main__":
    b.migrate()  # garantit ai_cache
    build()
    reindex()
    log("✅ distribution 0-token terminée")
