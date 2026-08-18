#!/usr/bin/env python3
# Générateur Dynamique Automatique en Temps Réel — Analyse du Système & Injection de Tâches
import json
import re
import sqlite3
import sys
import time

db_path = "/home/pamerys/jarvis/jarvis_master.db"

# Le titre porte un horodatage ([DYNAMIC-HH:MM:SS] …) : deux cycles produisent donc
# deux titres différents pour le MÊME travail. Toute déduplication doit se faire sur
# la partie stable du titre, sinon le producteur réinjecte 8 doublons par minute
# (≈11 500/jour) qu'aucun exécutant ne consomme.
STAMP_RE = re.compile(r"^\[DYNAMIC-\d{2}:\d{2}:\d{2}\]\s*")


def stable_key(title):
    """Titre débarrassé de son horodatage — identité réelle de la tâche."""
    return STAMP_RE.sub("", title).strip()


def inspect_and_generate():
    # Sans attente explicite, ce producteur cron meurt sur « database is locked »
    # dès qu'un daemon écrit (filler, aspirateur skillsmp) — et un cron qui meurt
    # ne laisse aucune trace visible, la file cesse simplement de se remplir.
    conn = sqlite3.connect(db_path, timeout=120)
    conn.execute("PRAGMA busy_timeout=120000")
    cur = conn.cursor()

    # Ne pas surcharger si plus de 200 tâches pending
    cur.execute("SELECT COUNT(*) FROM tasks WHERE status='pending';")
    pending_count = cur.fetchone()[0]

    if pending_count > 200:
        conn.close()
        return

    # File déjà ouverte : on ne réinjecte pas un travail qui attend ou tourne déjà.
    cur.execute("SELECT title FROM tasks WHERE status IN ('pending', 'running');")
    en_cours = {stable_key(row[0] or "") for row in cur.fetchall()}

    # Tâches dynamiques basées sur l'heure et les besoins instantanés du système
    timestamp = time.strftime("%H:%M:%S")
    # (titre, légion, machine, domaine)
    # Le domaine alimente la vue « file par domaine » du widget :8899. Il doit
    # être écrit en JSON dans `context` : le widget fait json.loads() dessus et
    # retombait sur "?" pour 100 % des tâches tant que ce champ était du texte.
    dynamic_tasks = [
        (
            f"[DYNAMIC-{timestamp}] Audit santé instantané GPU M1 & M6",
            "L8_optimiseurs",
            "M1",
            "infra",
        ),
        (
            f"[DYNAMIC-{timestamp}] Refresh indexation RAG des nouveaux fichiers",
            "L9_erudits",
            "M1",
            "connaissance",
        ),
        (
            f"[DYNAMIC-{timestamp}] Nettoyage RAM & Compactage Cache ZRAM",
            "L8_optimiseurs",
            "M1",
            "infra",
        ),
        (
            f"[DYNAMIC-{timestamp}] Scan sécurité réseau et vérification proxy :18800",
            "L3_sentinelles",
            "M4",
            "securite",
        ),
        (
            f"[DYNAMIC-{timestamp}] Contrôle des services systemd autostart",
            "L5_automates",
            "M1",
            "infra",
        ),
        (
            f"[DYNAMIC-{timestamp}] Sync GitOps automatique repositories Workspaces",
            "L5_automates",
            "M1",
            "code",
        ),
        (
            f"[DYNAMIC-{timestamp}] Scraping et veille d opportunités freelance",
            "L6_traders",
            "M1",
            "business",
        ),
        (
            f"[DYNAMIC-{timestamp}] Vérification statut nœud direct câble M6 (10.42.0.230)",
            "L4_analystes",
            "M6",
            "cluster",
        ),
    ]

    added = 0
    ignorees = 0
    echecs = []
    for title, legion, machine, domain in dynamic_tasks:
        if stable_key(title) in en_cours:
            ignorees += 1
            continue
        context = json.dumps(
            {
                "domain": domain,
                "legion": legion,
                "machine": machine,
                "origine": "auto_dynamic_task_producer",
                "note": "Généré automatiquement selon les besoins temps réel du système",
            },
            ensure_ascii=False,
        )
        try:
            cur.execute(
                """
            INSERT INTO tasks (title, context, status, progress, agent, machine)
            VALUES (?, ?, 'pending', 0, ?, ?)
            """,
                (title, context, legion, machine),
            )
            added += 1
        except Exception as exc:
            # On ne masque plus les échecs en silence : un INSERT qui tombe doit
            # se voir, sinon le producteur rapporte un succès qu'il n'a pas eu.
            echecs.append(f"{domain}: {type(exc).__name__}: {exc}")

    conn.commit()
    conn.close()
    print(
        f"[{timestamp}] Auto-Producer : {added}/{len(dynamic_tasks)} tâches dynamiques injectées"
        f" ({ignorees} déjà en file, ignorées)"
    )
    if echecs:
        # exit non nul : un cycle partiel ne doit pas passer pour un succès
        for e in echecs:
            print(f"  ÉCHEC {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    inspect_and_generate()
