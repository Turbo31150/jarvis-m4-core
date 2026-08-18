#!/usr/bin/env python3
"""jarvis-executor.py — CONSOMMATEUR autonome de la file de production JARVIS.

Le producer (jarvis-producer.py) REMPLIT la file `needs_impl` ; il ne FAIT rien.
Cet exécuteur la VIDE en exécutant RÉELLEMENT chaque tâche, en cascade :

  1. match DOMINO sûr   -> `dominos <nom> --run`  (exécution RÉELLE, 🔴 destructifs exclus)
  2. sinon ROUTER       -> jarvis-router.dispatch (handlers safe github/ollama/mcp/browseros/…)
  3. sinon PROJET-code  -> décomposition via LLM local (LM Studio :1234) en sous-tâches planning

Tout ce qui est destructif (envoi/publish/deploy/delete/push) -> file `approval`, JAMAIS auto.
Idempotent, vérifié (verify), journalisé. Conçu pour un timer systemd (tick borné).

  jarvis-executor.py --tick N     exécute jusqu'à N tâches de la file puis rend la main
  jarvis-executor.py --status     état des files + dernier journal
  jarvis-executor.py --dry        montre ce qui SERAIT exécuté sans rien faire
"""

import json
import os
import re
import sqlite3
import subprocess
import time

HOME = os.path.expanduser("~")
QDB = os.path.join(HOME, "jarvis", "data", "producer_queues.db")
PLAN = os.path.join(HOME, "jarvis", "bin", "jarvis-plan.py")
DOMINOS = os.path.join(HOME, "jarvis", "bin", "dominos")
ROUTER = os.path.join(HOME, "jarvis", "bin", "jarvis-router.py")
LOG = os.path.join(HOME, ".local", "share", "jarvis-executor.log")
LMS = "http://127.0.0.1:1234/v1/chat/completions"

# Mots-clés destructifs/SORTANTS -> jamais d'exécution auto (file approval).
# NB: 'mail'/'email' seuls ne sont PAS destructifs (analyse/tri = lecture) ; seul
# l'ENVOI l'est -> 'send'/'envoi'/'reply-send'/'followup' captent les sorties réelles.
DESTRUCTIF = re.compile(
    r"\b(delete|suppr|rm\b|drop|\bpush\b|publish|publi|envoi|envoie|send|deploy|"
    r"déploie|\bpost\b|post-auto|reply-auto|reply-send|followup|\bdm\b|tweet|"
    r"payer|achat|buy|transfer|virement|reset|\bforce\b|\bkill\b|restart|reboot)\b",
    re.I,
)


def log(m):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    line = "%s %s" % (time.strftime("%F %T"), m)
    try:
        open(LOG, "a", encoding="utf-8").write(line + "\n")
    except Exception:
        pass
    return line


def _run(argv, timeout=90):
    try:
        r = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            stdin=subprocess.DEVNULL,
        )
        return (r.returncode == 0), ((r.stdout or "") + (r.stderr or "")).strip()
    except Exception as e:
        return False, str(e)


# ── files ────────────────────────────────────────────────────────────────────
def _q():
    c = sqlite3.connect(QDB, timeout=10)
    c.execute(
        "CREATE TABLE IF NOT EXISTS queue(uid TEXT PRIMARY KEY, kind TEXT, "
        "titre TEXT, cmd TEXT, ts TEXT DEFAULT (datetime('now')))"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS executed(uid TEXT PRIMARY KEY, titre TEXT, "
        "voie TEXT, statut TEXT, sortie TEXT, ts TEXT DEFAULT (datetime('now')))"
    )
    # compteur d'échecs par tâche (anti-reboucle du mode continu)
    c.execute("CREATE TABLE IF NOT EXISTS fails(uid TEXT PRIMARY KEY, n INT DEFAULT 0)")
    return c


MAX_FAILS = 2  # après 2 blocages -> file 'review' (ne rebouclera plus)


def _pop(c, n):
    return c.execute(
        "SELECT uid,titre,cmd FROM queue WHERE kind='needs_impl' ORDER BY ts ASC LIMIT ?",
        (n,),
    ).fetchall()


def _record(c, uid, titre, voie, statut, out):
    c.execute(
        "INSERT OR REPLACE INTO executed(uid,titre,voie,statut,sortie) VALUES(?,?,?,?,?)",
        (uid, titre, voie, statut, (out or "")[:2000]),
    )
    if statut == "done":
        c.execute("DELETE FROM queue WHERE uid=?", (uid,))
        c.execute("DELETE FROM fails WHERE uid=?", (uid,))
    elif statut == "approval":
        c.execute("UPDATE queue SET kind='approval' WHERE uid=?", (uid,))
    elif statut == "blocked":
        c.execute(
            "INSERT INTO fails(uid,n) VALUES(?,1) ON CONFLICT(uid) DO UPDATE SET n=n+1",
            (uid,),
        )
        n = c.execute("SELECT n FROM fails WHERE uid=?", (uid,)).fetchone()[0]
        if n >= MAX_FAILS:  # trop d'échecs -> sort de la boucle vers review
            c.execute("UPDATE queue SET kind='review' WHERE uid=?", (uid,))
    c.commit()


# ── catalogue dominos (nom -> sûr/danger) ────────────────────────────────────
_DOM_CACHE = None


def dominos_index():
    global _DOM_CACHE
    if _DOM_CACHE is not None:
        return _DOM_CACHE
    ok, out = _run(["bash", DOMINOS, "list"], 30)
    names = set()
    if ok:
        for ln in out.splitlines():
            # nom en début de ligne (indenté), avant les colonnes 'N steps' / description
            m = re.match(r"\s{2,}([a-z][a-z0-9-]{2,})(?:\s{2,}|\s+\d+\s+steps|$)", ln)
            if m:
                names.add(m.group(1))
    _DOM_CACHE = names
    return names


_STOP = {
    "pour",
    "une",
    "systeme",
    "système",
    "automatique",
    "auto",
    "implementer",
    "implémenter",
    "creer",
    "créer",
    "mettre",
    "place",
    "gestion",
    "des",
    "les",
    "avec",
    "sur",
    "build",
    "monitor",
    "gen",
    "auto",
}


def _toks(s):
    return {
        t for t in re.findall(r"[a-z][a-z0-9]{2,}", (s or "").lower()) if t not in _STOP
    }


def match_domino(titre, cmd):
    """Match FLOU : le domino dont le nom partage le plus de tokens avec la tâche.
    'prospect-extract-b2b' -> 'mail-prospect-b2b' ; 'linkedin-engagement' -> 'linkedin-post-auto'."""
    cat = dominos_index()
    slug = re.sub(r"[^a-z0-9-]+", "-", titre.lower()).strip("-")
    if slug in cat:  # match exact prioritaire
        return slug
    want = _toks(titre + " " + (cmd or ""))
    if not want:
        return None
    best, best_score = None, 0
    for nom in cat:
        nt = _toks(nom.replace("-", " "))
        # cible valable : au moins 2 tokens significatifs (évite les faux positifs
        # génériques type 'daily', 'audit' seuls)
        if len(nt) < 2:
            continue
        inter = want & nt
        if not inter:
            continue
        # 3 pts par token partagé, -1 par token du domino non couvert (spécificité)
        score = 3 * len(inter) - (len(nt) - len(inter))
        if score > best_score:
            best, best_score = nom, score
    return best if best_score >= 2 else None


# ── CANAUX câblés : détection thème -> dominos SÛRS dédiés (le "faire" par canal) ─
# Chaque canal liste ses dominos NON-destructifs (génération/audit/analyse local).
# Les actions sortantes (publish/send/post-auto/reply-auto/dm) tombent dans
# DESTRUCTIF -> file approval, jamais auto.
CANAUX = [
    (
        "github",
        r"\b(github|repo|dépôt|readme|badge|issue|\bpr\b|commit)\b",
        ["github-repos-audit", "github-audit"],
    ),
    (
        "linkedin",
        r"\b(linkedin|carrousel|carousel|hook|post|profil)\b",
        [
            "linkedin-carousel-gen",
            "linkedin-hook-generator",
            "linkedin-content-week",
            "linkedin-profile-audit",
        ],
    ),
    (
        "prospection",
        r"\b(prospect|prospection|lead|b2b|pipeline commercial|crm)\b",
        [
            "prospect-pipeline-view",
            "prospect-score-ml",
            "prospect-weekly-report",
            "prospect-domino",
        ],
    ),
    (
        "gmail",
        r"\b(mail|email|e-mail|gmail|emploi|candidature|relance)\b",
        [
            "mail-analyze-digest",
            "mail-triage-auto",
            "crm-audit-mail",
            "mail-subject-optimizer",
        ],
    ),
    (
        "youtube",
        r"\b(youtube|vidéo|video|chaîne|short|script vidéo)\b",
        ["youtube-script-auto"],
    ),
    (
        "entreprise",
        r"\b(entreprise|analyse.*(société|marché|concurrent)|veille|due diligence)\b",
        [
            "pipelinejarvis-presentation-entreprise-evalu",
            "pipelinejarvis-presentation-entreprise-optim",
        ],
    ),
    ("seo", r"\b(seo|référencement|ranking|serp|mots-clés)\b", ["seo-check"]),
    (
        "agents",
        r"\b(agent|créer un agent|create agent|outil|tool|skill)\b",
        ["agents-build", "agent-tools"],
    ),
    (
        "content",
        r"\b(contenu|content|article|repurpose|carrousel)\b",
        ["content-repurpose"],
    ),
]


def channel_route(titre, cmd):
    """Détecte le canal de la tâche et renvoie le 1er domino SÛR disponible du canal."""
    cat = dominos_index()
    t = (titre + " " + (cmd or "")).lower()
    for canal, rx, doms in CANAUX:
        if re.search(rx, t):
            for d in doms:
                if d in cat and not DESTRUCTIF.search(d):
                    return canal, d
    return None, None


# ── voie 1 : DOMINO réel ─────────────────────────────────────────────────────
def exec_domino(nom):
    """Exécute un domino EN RÉEL (--run). Refuse si destructif."""
    if DESTRUCTIF.search(nom):
        return "approval", "domino '%s' potentiellement destructif -> approbation" % nom
    ok, out = _run(["bash", DOMINOS, nom, "--run"], 120)
    # verify : sortie non vide et pas d'erreur bloquante
    if ok and not re.search(r"\b(error|traceback|failed|introuvable)\b", out, re.I):
        return "done", "domino %s --run OK\n%s" % (nom, out[:800])
    return "blocked", "domino %s: %s" % (nom, out[:600])


# ── voie 2 : ROUTER (handlers safe) ──────────────────────────────────────────
def exec_router(titre):
    ok, out = _run(["python3", ROUTER, "--test", titre], 40)
    if ok and "statut=done" in out:
        return "done", out[:800]
    if "statut=blocked" in out:
        return "blocked", out[:600]
    if "tâche de code" in out or "omega-dev" in out:
        return "code", out[:400]
    return ("done" if ok else "blocked"), out[:600]


# ── voie 3 : LLM local — décompose un projet en sous-tâches actionnables ──────
def exec_llm_decompose(titre):
    """Un 'projet' (bot MEXC, agent SEO…) n'est pas exécutable en 1 clic :
    on le DÉCOMPOSE via LM Studio en 3-5 sous-tâches concrètes, ajoutées au planning.
    C'est du FAIRE réel : le planning avance, pas de code auto-appliqué à l'aveugle."""
    prompt = (
        "Décompose cette tâche JARVIS en 3 à 5 sous-tâches TRÈS concrètes et "
        "actionnables (chacune faisable en une commande ou un script court). "
        'Réponds UNIQUEMENT en JSON: {"sous_taches":["...","..."]}. '
        "Tâche: " + titre
    )
    body = json.dumps(
        {
            "model": "qwen/qwen3.5-9b",
            "messages": [{"role": "user", "content": prompt + " /no_think"}],
            "temperature": 0.2,
            "max_tokens": 500,
        }
    )
    ok, out = _run(
        [
            "curl",
            "-s",
            "--max-time",
            "60",
            LMS,
            "-H",
            "Content-Type: application/json",
            "-d",
            body,
        ],
        70,
    )
    subs = []
    if ok:
        try:
            content = json.loads(out)["choices"][0]["message"]["content"]
            content = re.sub(r"<think>.*?</think>", "", content, flags=re.S)
            m = re.search(r"\{.*\}", content, re.S)
            if m:
                subs = json.loads(m.group(0)).get("sous_taches", [])
        except Exception:
            pass
    if not subs:
        return "blocked", "LLM décompose: pas de sous-tâches exploitables"
    for s in subs[:5]:
        _run(["python3", PLAN, "--add", s[:120], "--priorite", "P2"], 20)
    return "done", "décomposé en %d sous-tâches (ajoutées au planning P2):\n- %s" % (
        len(subs),
        "\n- ".join(subs[:5]),
    )


# ── cascade d'exécution ──────────────────────────────────────────────────────
def execute_one(titre, cmd, dry=False):
    if DESTRUCTIF.search(titre):
        return "approval", "titre destructif/sortant -> approbation humaine"
    # priorité 1 : CANAL câblé (github/linkedin/prospection/gmail/youtube/entreprise/agents)
    canal, dom = channel_route(titre, cmd)
    if dom:
        if dry:
            return "would-canal", "[%s] domino %s --run" % (canal, dom)
        st, out = exec_domino(dom)
        return st, "[canal:%s] %s" % (canal, out)
    # priorité 2 : matching flou générique
    nom = match_domino(titre, cmd)
    if nom:
        if dry:
            return "would-domino", "domino %s --run" % nom
        return exec_domino(nom)
    # priorité 3 : router handlers safe
    if dry:
        return "would-router", "router dispatch"
    st, out = exec_router(titre)
    if st == "done":
        return st, out
    if st == "code":
        return exec_llm_decompose(titre)
    return st, out


def tick(n, dry=False):
    c = _q()
    rows = _pop(c, n)
    if not rows:
        print("file needs_impl vide — rien à exécuter")
        return
    print("═══ exécution de %d tâche(s) %s ═══" % (len(rows), "(DRY)" if dry else ""))
    done = appr = block = 0
    for uid, titre, cmd in rows:
        st, out = execute_one(titre, cmd, dry=dry)
        icon = {"done": "✅", "approval": "🔒", "blocked": "⛔"}.get(st, "▶")
        print("%s [%s] %s" % (icon, st, titre[:64]))
        if not dry:
            _record(c, uid, titre, ("domino/router/llm"), st, out)
            log("uid=%s statut=%s :: %s" % (uid, st, titre[:70]))
            done += st == "done"
            appr += st == "approval"
            block += st == "blocked"
    if not dry:
        print(
            "\nRésultat: %d faites · %d en approbation · %d bloquées"
            % (done, appr, block)
        )


def status():
    c = _q()
    for k in ("needs_impl", "approval"):
        n = c.execute("SELECT count(*) FROM queue WHERE kind=?", (k,)).fetchone()[0]
        print("file %-12s : %d" % (k, n))
    ex = c.execute("SELECT statut,count(*) FROM executed GROUP BY statut").fetchall()
    print("exécutées:", ", ".join("%s=%d" % (s, n) for s, n in ex) or "aucune")
    last = c.execute(
        "SELECT ts,statut,titre FROM executed ORDER BY ts DESC LIMIT 5"
    ).fetchall()
    for ts, st, ti in last:
        print("  %s [%s] %s" % (ts, st, ti[:60]))


def main():
    import argparse

    ap = argparse.ArgumentParser(prog="jarvis-executor")
    ap.add_argument("--tick", type=int, metavar="N", help="exécute jusqu'à N tâches")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--dry", action="store_true", help="montre sans exécuter")
    a = ap.parse_args()
    if a.status:
        status()
    elif a.tick is not None:
        tick(a.tick, dry=a.dry)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
