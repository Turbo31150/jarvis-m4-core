#!/usr/bin/env python3
"""Enregistre la surveillance box DOCSIS dans le planning JARVIS — idempotent.

Branche l'incident « voie de retour saturée » sur les rails qui existent déjà :

  cmddirecte-blocs.tsv   steps résolvables par domino-compile.py
  domino_chains          3 chaînes escaladées (diag → remédiation → escalade)
  plan (source=domino)   ce que le widget :8899 affiche comme dominos actionnables
  tasks                  tâches planifiées de la file vive
  domino_triggers        le déclenchement, tracé

Rejouable sans doublon : chaque écriture vérifie l'existant d'abord.
  --dry-run  montre sans écrire
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

DB = Path.home() / "jarvis" / "jarvis_master.db"
TSV = Path("/home/pamerys/labo/bibliotheque/lib/cmddirecte-blocs.tsv")
DRY = "--dry-run" in sys.argv

P = "python3 /home/pamerys/jarvis/scripts/ops"

# (bloc_id, mots_cles, action, danger) — format cmddirecte : 5 colonnes,
# c'est cols[3]=action et cols[4]=danger que le résolveur lit.
STEPS = [
    (
        "box.docsis.probe",
        "Sonde DOCSIS box — SNR, upstream, T3",
        f"{P}/box_docsis_probe.py",
        "🟢",
    ),
    (
        "box.docsis.snapshot",
        "Archive le relevé DOCSIS horodaté",
        "mkdir -p ~/jarvis/data/box_incidents && "
        f"{P}/box_docsis_probe.py > ~/jarvis/data/box_incidents/releve-$(date +%Y%m%d-%H%M).json",
        "🟢",
    ),
    (
        "box.docsis.journal",
        "Journalise l'état box dans ops/events.jsonl",
        f'{P}/box_docsis_probe.py | python3 -c "import json,sys,time,uuid;r=json.load(sys.stdin);'
        "print(json.dumps({'event_id':str(uuid.uuid4()),'schema_version':1,'ts':time.time(),"
        "'type':'box.docsis.'+r.get('severity','unknown'),'upstream_dbmv':r.get('upstream_max_dbmv'),"
        "'snr_db':r.get('downstream_snr_min_db'),'t3':r.get('log',{}).get('t3_timeout'),"
        "'uptime_min':r.get('uptime_min')}))\" >> ~/jarvis/ops/events.jsonl",
        "🟢",
    ),
    (
        "box.docsis.failover.check",
        "Vérifie que le secours 4G S9 est armé",
        "systemctl is-enabled s9-failover.timer && systemctl status s9-failover.timer --no-pager -l | head -12",
        "🟢",
    ),
    (
        "box.docsis.failover.kick",
        "Force une bascule du secours 4G S9",
        "systemctl start s9-failover.service && sleep 5 && ip route show default",
        "🟠",
    ),
    (
        "box.docsis.stability",
        "3 relevés espacés pour distinguer incident ponctuel et défaut permanent",
        f"{P}/box_docsis_trend.py --stability 3",
        "🟢",
    ),
    (
        "box.docsis.dossier",
        "Constitue le dossier d'escalade opérateur chiffré",
        f"{P}/box_operator_dossier.py",
        "🟢",
    ),
    # Remonte les 4 maillons (lien local → box → voie de retour → chemin) et
    # DÉSIGNE la cause racine, pour ne pas chercher au mauvais endroit.
    (
        "box.docsis.chain",
        "Diagnostic de la chaîne d'accès complète — désigne le maillon fautif",
        f"{P}/box_chain_diag.py",
        "🟢",
    ),
    # Corrobore la sonde par un angle indépendant : si le jitter naît au saut 2
    # alors que la box répond en <1 ms, le défaut est sur le segment d'accès.
    (
        "box.docsis.path",
        "Situe le jitter par saut (box vs premier équipement opérateur)",
        "mtr -r -c 20 -n --no-dns 8.8.8.8",
        "🟢",
    ),
    (
        "box.docsis.trend",
        "Échantillonne la voie de retour (série pour tester la dérive thermique)",
        f"{P}/box_docsis_trend.py",
        "🟢",
    ),
    (
        "box.docsis.trend.analyse",
        "Analyse la dérive thermique — refuse de conclure sous 8 échantillons",
        f"{P}/box_docsis_trend.py --analyse",
        "🟢",
    ),
    # A4 : l'effet de bord externe passe par `publish` (draft-first stage→approve
    # →commit lié au hash), jamais par l'adaptateur Telegram en direct.
    (
        "box.docsis.notify",
        "Met en brouillon l'alerte état voie de retour via publish (A4)",
        f"{P}/box_docsis_notify.py",
        "🟢",
    ),
    # A2 : la mémoire métier durable passe par `mem`. Le journal DOCSIS provient
    # de la box = entrée externe ⇒ --untrusted --source (A0 : donnée, pas ordre).
    (
        "box.docsis.mem",
        "Grave l'état de l'incident dans la mémoire durable (A2)",
        f"{P}/box_docsis_notify.py --mem",
        "🟢",
    ),
]

# Escalade conforme à RECOVERY-CATALOGUE : diag → remédiation → escalade humaine.
CHAINS = [
    (
        "box docsis diagnostic",
        "scenario-3-etapes",
        "🟢",
        [
            "box.docsis.chain",
            "box.docsis.snapshot",
            "box.docsis.journal",
            "box.docsis.mem",
        ],
        "box upstream degrade",
        "signal box_docsis → relevé chiffré + archive + journal + mémoire A2 (aucun effet de bord)",
    ),
    (
        "box upstream degrade",
        "scenario-4-etapes",
        "🟠",
        [
            "box.docsis.probe",
            "box.docsis.failover.check",
            "box.docsis.failover.kick",
            "box.docsis.notify",
        ],
        "box escalade operateur",
        "voie de retour saturée → garantir le secours 4G puis alerter ; ne répare pas la ligne",
    ),
    (
        "box escalade operateur",
        "scenario-3-etapes",
        "🟢",
        [
            "box.docsis.stability",
            "box.docsis.path",
            "box.docsis.trend.analyse",
            "box.docsis.dossier",
            "box.docsis.notify",
        ],
        "",
        "défaut permanent confirmé → dérive thermique tranchée + dossier chiffré pour l'opérateur",
    ),
]

# Ce que le widget :8899 liste comme dominos actionnables (plan.source='domino').
PLAN = [
    (
        "Diagnostiquer la voie de retour DOCSIS de la box (SNR, upstream, T3)",
        "🟢 box reseau docsis",
        "dominos box-docsis-diagnostic",
    ),
    (
        "Traiter une voie de retour saturée : secours 4G + alerte",
        "🟠 box reseau failover",
        "dominos box-upstream-degrade",
    ),
    (
        "Constituer le dossier d'escalade opérateur (chiffres à l'appui)",
        "🟢 box reseau operateur",
        "dominos box-escalade-operateur",
    ),
]

# Travail humain que le diagnostic implique. Volontairement PAS dans `tasks` :
# prod-loop.sh y pioche par motif de titre et marque done/score=0.95 sans vérifier
# la nature de l'action — une action physique s'y retrouve « faite » sans que
# personne n'ait touché un câble. `plan` est déclaratif, aucun runner ne l'exécute.
MANUEL = [
    (
        "🖐️ Supprimer les répartiteurs entre prise murale et box (chaque splitter coûte 3,5-7 dB d'émission)",
        "🖐️ action-physique box reseau p0",
        "python3 ~/jarvis/scripts/ops/box_docsis_probe.py  # vérifier l'upstream après",
    ),
    (
        "🖐️ Contrôler les connecteurs F et le coaxial (serrage, oxydation, pincement)",
        "🖐️ action-physique box reseau p0",
        "python3 ~/jarvis/scripts/ops/box_docsis_probe.py  # vérifier l'upstream après",
    ),
    (
        "🖐️ Relever l'upstream après recâblage — cible ≤ 45 dBmV",
        "🖐️ action-physique box reseau p1",
        "dominos box-escalade-operateur --run",
    ),
    (
        "🖐️ Si upstream reste ≥ 48 dBmV : escalade opérateur avec le dossier chiffré",
        "🖐️ action-humaine box reseau operateur p1",
        "python3 ~/jarvis/scripts/ops/box_operator_dossier.py",
    ),
    (
        "🖐️ Vérifier le retour des 2 lignes de téléphonie une fois l'upstream assaini",
        "🖐️ action-physique box reseau telephonie p2",
        "python3 ~/jarvis/scripts/ops/box_docsis_probe.py",
    ),
]

# Titres injectés par une version antérieure dans `tasks`, où des runners les ont
# marqués done/error sans exécution. Retirés pour ne pas laisser un faux « fait ».
LEGACY_TASK_TITLES = [
    "Supprimer les répartiteurs entre prise murale et box (chaque splitter coûte 3,5-7 dB d'émission)",
    "Contrôler les connecteurs F et le coaxial (serrage, oxydation, pincement)",
    "Relever l'upstream après recâblage — cible ≤ 45 dBmV",
    "Si upstream reste ≥ 48 dBmV : escalade opérateur avec le dossier chiffré",
    "Vérifier le retour des 2 lignes de téléphonie une fois l'upstream assaini",
]


def sync_tsv() -> int:
    """Ajoute les steps manquants au résolveur. Format 5 colonnes obligatoire."""
    if not TSV.exists():
        print(
            f"⚠ {TSV} absent — steps non résolvables, chaînes compilées en NON-RÉSOLU"
        )
        return 0
    lines = TSV.read_text(encoding="utf-8", errors="replace").splitlines()
    header, body = lines[0], lines[1:]
    want = {s[0]: s for s in STEPS}

    # Réécrire les lignes dont la commande a changé (sinon un domino recompilé
    # rejouerait l'ancienne version — ex. notify en direct au lieu de publish).
    out, seen, changed = [], set(), 0
    for ln in body:
        sid = ln.split("\t")[0].strip() if ln.strip() else ""
        if sid in want:
            seen.add(sid)
            s = want[sid]
            new_ln = f"{s[0]}\tcmd-directe\t{s[1]}\t{s[2]}\t{s[3]}"
            if new_ln != ln:
                changed += 1
            out.append(new_ln)
        else:
            out.append(ln)

    added = [s for sid, s in want.items() if sid not in seen]
    out += [f"{s[0]}\tcmd-directe\t{s[1]}\t{s[2]}\t{s[3]}" for s in added]
    if (added or changed) and not DRY:
        TSV.write_text("\n".join([header] + out) + "\n", encoding="utf-8")
    if changed:
        print(f"  ↻ {changed} step(s) mis à jour (commande modifiée)")
    return len(added)


def sync_db() -> dict[str, int]:
    n = {
        "chains": 0,
        "updates": 0,
        "plan": 0,
        "manuel": 0,
        "purges": 0,
        "triggers": 0,
    }
    # WAL : un seul écrivain à la fois sur une base très sollicitée,
    # il faut attendre au lieu d'échouer sur "database is locked".
    c = sqlite3.connect(DB, timeout=120)
    c.execute("PRAGMA busy_timeout=120000")
    try:
        for serie, verdict, danger, steps, nxt, logique in CHAINS:
            row = c.execute(
                "SELECT steps,logique FROM domino_chains WHERE serie=?", (serie,)
            ).fetchone()
            if row:
                # Chaîne connue : ne pas dupliquer, mais réaligner ses steps —
                # sinon un recompile rejoue l'ancienne composition.
                if row[0] != json.dumps(steps) or row[1] != logique:
                    n["updates"] += 1
                    if not DRY:
                        c.execute(
                            "UPDATE domino_chains SET steps=?,logique=?,danger=?,verdict=?,"
                            "next_serie=? WHERE serie=?",
                            (json.dumps(steps), logique, danger, verdict, nxt, serie),
                        )
                continue
            n["chains"] += 1
            if not DRY:
                c.execute(
                    "INSERT INTO domino_chains(serie,verdict,danger,steps,backend,next_serie,logique)"
                    " VALUES(?,?,?,?,?,?,?)",
                    (
                        serie,
                        verdict,
                        danger,
                        json.dumps(steps),
                        "local-shell",
                        nxt,
                        logique,
                    ),
                )

        for titre, tags, cmd in PLAN:
            if c.execute(
                "SELECT 1 FROM plan WHERE titre=? AND source='domino'", (titre,)
            ).fetchone():
                continue
            n["plan"] += 1
            if not DRY:
                c.execute(
                    "INSERT INTO plan(titre,source,tags,preloaded) VALUES(?,?,?,?)",
                    (titre, "domino", tags, json.dumps({"ready_cmd": cmd})),
                )

        for titre, tags, cmd in MANUEL:
            # Détection par fragment distinctif et non par titre exact : une action
            # cochée ✅ ou reformulée par Turbo ne doit pas être réinsérée en double.
            frag = "%" + titre.split("(")[0].strip("🖐️ ").strip()[:34] + "%"
            if c.execute(
                "SELECT 1 FROM plan WHERE source='domino' AND (titre=? OR titre LIKE ?)",
                (titre, frag),
            ).fetchone():
                continue
            n["manuel"] += 1
            if not DRY:
                c.execute(
                    "INSERT INTO plan(titre,source,tags,preloaded) VALUES(?,?,?,?)",
                    (titre, "domino", tags, json.dumps({"ready_cmd": cmd})),
                )

        # Purge des faux « done » laissés dans `tasks` par les runners automatiques.
        for title in LEGACY_TASK_TITLES:
            row = c.execute(
                "SELECT id,status FROM tasks WHERE title=?", (title,)
            ).fetchone()
            if not row:
                continue
            n["purges"] += 1
            if not DRY:
                c.execute("DELETE FROM tasks WHERE id=?", (row[0],))

        already = c.execute(
            "SELECT 1 FROM domino_triggers WHERE trigger_event='box_docsis_t3'"
        ).fetchone()
        if not already:
            n["triggers"] += 1
            if not DRY:
                c.execute(
                    "INSERT INTO domino_triggers(trigger_event,chain_name,threshold,status,payload_json)"
                    " VALUES(?,?,?,?,?)",
                    (
                        "box_docsis_t3",
                        "box docsis diagnostic",
                        1,
                        "armed",
                        json.dumps(
                            {
                                "seuil_upstream_dbmv": 48,
                                "seuil_snr_db": 33,
                                "escalade": [c[0] for c in CHAINS],
                                "equipe": "box-network-team",
                            },
                            ensure_ascii=False,
                        ),
                    ),
                )
        if not DRY:
            c.commit()
            # domino-compile.py lit la base en `mode=ro&immutable=1`, ce qui fait
            # IGNORER le WAL par SQLite : sans checkpoint, il recompile un état
            # antérieur et les steps ajoutés ici restent invisibles.
            # PASSIVE et non TRUNCATE : d'autres process écrivent dans cette base,
            # on ne leur arrache pas le WAL.
            try:
                c.execute("PRAGMA wal_checkpoint(PASSIVE)")
            except sqlite3.Error as e:
                print(f"  ⚠ checkpoint WAL refusé ({e}) — recompiler après")
    finally:
        c.close()
    return n


if __name__ == "__main__":
    t = sync_tsv()
    d = sync_db()
    tag = "[dry-run] " if DRY else ""
    print(f"{tag}steps résolveur ajoutés : {t}/{len(STEPS)}")
    print(
        f"{tag}chaînes domino : +{d['chains']} (↻{d['updates']} réalignée(s))"
        f"  | dominos widget : +{d['plan']}"
        f"  | actions manuelles : +{d['manuel']}  | trigger : +{d['triggers']}"
    )
    if d["purges"]:
        print(
            f"{tag}⚠ {d['purges']} tâche(s) purgée(s) de `tasks` : marquées done/error "
            "par un runner sans exécution réelle (action physique)"
        )
    print("(déjà présent = non redupliqué)" if not any(d.values()) and not t else "")
