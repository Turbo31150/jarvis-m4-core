#!/usr/bin/env python3
"""biblio_filler.py — Bibliothèque Vivante Infinie (0-token, anti-surchauffe).

Remplit en continu la bibliothèque unifiée M1 :
  - commandes techniques  -> Postgres `cmdlib` (container jv-infra-biblio-db) + command_list.md
  - fiches de connaissance -> SQLite jarvis_master.db (table biblio_knowledge) + .md sur disque

Piloté par une todoliste dynamique auto-alimentée (table biblio_topics) : quand les sujets
`pending` se raréfient, le LLM local en génère de nouveaux -> remplissage perpétuel.

Moteur 0-token : LM Studio M1 :1234 PRIORITAIRE (qwen3.5-9b) -> fallback jarvis_dispatcher.ask().
Garde thermique GPU (nvidia-smi) : jamais saturer -> pause au lieu de crash.
Cache SQL (ai_cache, SHA256) : ne jamais regénérer deux fois.

Usage :
  biblio_filler.py --init                 # migre + seed les domaines de base
  biblio_filler.py --once --batch 2       # un lot borné (test)
  biblio_filler.py --loop --batch 3 --pace 60 --temp-max 84   # daemon perpétuel
  biblio_filler.py --status               # avancement
"""

from __future__ import annotations
import argparse
import hashlib
import json
import os
import random
import re
import sqlite3
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # ~/jarvis
MASTER_DB = ROOT / "jarvis_master.db"
CATALOGUE = Path.home() / "Documents/Commande_Directe_Bibliotheque/command_list.md"
KNOW_DIR = ROOT / "data" / "biblio_knowledge"
LOG = ROOT / "data" / "biblio_filler.log"

# 2026-08-18 — le defaut etait "http://127.0.0.1:1234/...", herite de M1 ou LM Studio
# tournait en local. Sur M4 rien n'ecoute sur 1234 : chaque appel tombait en fallback
# dispatcher, et expand() rendait "pas de JSON exploitable" — la todoliste ne se
# regenerait donc jamais (pending=0 fige). LM Studio tourne sur M6, cable en direct
# (10.42.0.230:1234, RTT ~1.4 ms). Override toujours possible via $LMS_URL.
LMS_DEFAUT = "http://10.42.0.230:1234/v1/chat/completions"
LMS_URL = os.environ.get("LMS_URL", LMS_DEFAUT)
LMS_MODEL = os.environ.get(
    "LMS_MODEL", "qwen/qwen3.5-9b"
)  # qualité ; gemma-4-e4b = rapide
# Parallélisme multi-modèles sans collision : partitionne la file par kind.
# KIND_FILTER=command | knowledge | all (défaut). Deux workers sur kinds
# disjoints + LMS_MODEL distincts => 2 flux LM Studio réellement parallèles.
KIND_FILTER = os.environ.get("KIND_FILTER", "all")
# 2026-08-18 — trois decalages herites de M1, corriges ensemble :
#   1. `docker` en local frappe une pile PERIMEE sur M4 (ecritures silencieusement
#      perdues) et un hook la bloque -> on passe par bin/jarvis-docker, qui route
#      vers la tour ou la pile reelle tourne.
#   2. le conteneur `jv-infra-biblio-db` n'existe plus ; c'est `jarvis-pg-biblio`.
#   3. le role `cmduser` n'existe pas dans ce conteneur (POSTGRES_USER=jarvis).
# La base `cmdlib` et sa table `commands` ont ete creees le 2026-08-18 (elles
# n'avaient pas suivi la migration) : sans elles, chaque topic `command` sortait
# en FAIL et la moitie du remplissage etait perdue.
PG_DOCKER = os.environ.get("PG_DOCKER", str(Path.home() / "jarvis/bin/jarvis-docker"))
PG_CONTAINER = os.environ.get("PG_CONTAINER", "jarvis-pg-biblio")
PG_USER = os.environ.get("PG_USER", "jarvis")
PG_DB = os.environ.get("PG_DB", "cmdlib")
PG = [
    PG_DOCKER,
    "exec",
    "-i",
    PG_CONTAINER,
    "psql",
    "-U",
    PG_USER,
    "-d",
    PG_DB,
    "-v",
    "ON_ERROR_STOP=1",
    "-qtA",
]

EXPAND_THRESHOLD = 4  # si moins de N topics pending -> auto-alimentation
DANGER_MAP = {0: "🟢", 1: "🟠", 2: "🔴"}

SEED_DOMAINS = [
    ("command", "Réseau avancé"),
    ("command", "Docker & conteneurs"),
    ("command", "systemd & services"),
    ("command", "Sécurité & durcissement"),
    ("command", "GPU & NVIDIA"),
    ("command", "Performances & monitoring"),
    ("command", "Git & versioning"),
    ("command", "SSH & tunnels"),
    ("command", "n8n & workflows automation"),
    ("command", "PostgreSQL & SQL avancé"),
    ("command", "Kubernetes & orchestration"),
    ("command", "Ansible & Infrastructure as Code"),
    ("command", "Trading API & backtesting"),
    ("command", "Pentest & sécurité offensive"),
    ("command", "Firewall, VPN & réseau"),
    ("knowledge", "Architecture LLM locale"),
    ("knowledge", "Observabilité cluster"),
    ("knowledge", "Sauvegarde & résilience"),
    ("knowledge", "Automatisation 0-token"),
    ("knowledge", "RGPD & conformité des données"),
    ("knowledge", "LLMOps & MLOps"),
    ("knowledge", "RAG & bases vectorielles"),
    ("knowledge", "Micro-entreprise, fiscalité & business"),
    ("knowledge", "Prospection & vente B2B"),
    ("knowledge", "Fine-tuning & quantization LLM"),
    ("knowledge", "Agents autonomes & orchestration multi-agent"),
]


# ---------------------------------------------------------------- utilitaires
def log(msg: str) -> None:
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def db():
    import sqlite3

    conn = sqlite3.connect(MASTER_DB, timeout=120)
    conn.execute("PRAGMA journal_mode=WAL")
    # `timeout=` ne couvre pas tous les chemins du driver : le PRAGMA, lui, vaut
    # pour toute la connexion. Sans lui, un producteur concurrent (aspirateur
    # skillsmp, expansion biblio) fait tomber ce daemon en boucle sur
    # « database is locked » — il redémarre, retombe, et la file n'avance plus.
    conn.execute("PRAGMA busy_timeout=120000")
    return conn


def gpu_temp_max() -> int:
    try:
        out = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout
        temps = [int(x) for x in out.split() if x.strip().isdigit()]
        return max(temps) if temps else 0
    except Exception:
        return 0


# ---------------------------------------------------------------- moteur LLM
def _lms(prompt: str, system: str | None, timeout: float, max_tokens: int = 600) -> str | None:
    """Appel LM Studio :1234 avec fix anti-reasoning-runaway.

    qwen3.5-9b ouvre <think> par défaut (chat template GGUF) et LM Studio ne
    l'injecte pas fermé → le content revient VIDE sous ~2000 tokens (casse
    expand + génération JSON). Fix validé (cf. bin/qwen-nothink.sh) : passer par
    /v1/completions avec un <think></think> pré-fermé après l'en-tête assistant.
    """
    comp_url = LMS_URL.replace("/chat/completions", "/completions")
    sys_part = f"<|im_start|>system\n{system}<|im_end|>\n" if system else ""
    p = (
        f"{sys_part}<|im_start|>user\n{prompt}<|im_end|>\n"
        f"<|im_start|>assistant\n<think>\n\n</think>\n\n"
    )
    body = json.dumps(
        {
            "model": LMS_MODEL,
            "prompt": p,
            "temperature": 0.3,
            "max_tokens": max_tokens,
            "stop": ["<|im_end|>"],
            "stream": False,
        }
    ).encode()
    req = urllib.request.Request(
        comp_url, data=body, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read())
        if "choices" in d and d["choices"]:
            return d["choices"][0].get("text", "")
        err_msg = d.get("error", {}).get("message", "Unknown error")
        log(f"  LMS returned error: {err_msg}")
        return None
    except urllib.error.HTTPError as e:
        # « HTTP Error 400: Bad Request » seul ne dit rien : le motif est dans le
        # corps de la réponse (modèle inconnu, contexte dépassé, champ refusé).
        # Sans lui on croit à une panne réseau et on part diagnostiquer LM Studio.
        try:
            detail = e.read().decode("utf-8", "replace")[:300]
        except Exception:
            detail = ""
        log(f"  LMS refuse ({e.code}) : {detail} -> fallback dispatcher")
        return None
    except Exception as e:
        log(f"  LMS indisponible ({e}) -> fallback dispatcher")
        return None


def _lms_retry(prompt: str, system: str | None, timeout: float, essais: int = 3, max_tokens: int = 600) -> str | None:
    """LM Studio M6 echoue par intermittence sur /v1/completions.

    Constat 2026-08-18 : le meme prompt rend 1041 caracteres de JSON valide a un
    appel, puis « HTTP 400 Engine protocol completeRawText request failed: fetch
    failed » au suivant — sans rien changer. Un echec isole faisait tomber expand()
    en « pas de JSON exploitable », donc la todoliste ne se regenerait pas et le
    daemon tournait a vide (lot: +0 genere, en boucle).
    On ne bascule PAS sur /v1/chat/completions en secours : mesure faite, cet
    endpoint rend un content VIDE avec qwen3.5-9b (le <think> non ferme du chat
    template GGUF). Seul le /completions pre-ferme fonctionne. Donc : on reessaie.
    """
    for i in range(essais):
        txt = _lms(prompt, system, timeout, max_tokens)
        if txt and txt.strip():
            return txt
        if i < essais - 1:
            attente = 2 * (i + 1)
            log(f"  LMS: tentative {i + 1}/{essais} sans reponse -> nouvel essai dans {attente}s")
            time.sleep(attente)
    return None


def _fallback(prompt: str, system: str | None, timeout: float) -> str | None:
    try:
        sys.path.insert(0, str(ROOT / "cli"))
        from jarvis_dispatcher import ask

        r = ask(prompt, mode="reason", system=system, timeout=timeout)
        return r.get("text") if r.get("ok") else None
    except Exception as e:
        log(f"  fallback KO ({e})")
        return None


def gen(prompt: str, system: str | None = None, timeout: float = 120.0, max_tokens: int = 600) -> str | None:
    """Génère (cache -> LM Studio -> fallback). 0-token toujours."""
    key = hashlib.sha256(((system or "") + "||" + prompt).encode()).hexdigest()
    conn = db()
    row = conn.execute("SELECT text FROM ai_cache WHERE k=?", (key,)).fetchone()
    if row:
        conn.close()
        return row[0]
    txt = _lms_retry(prompt, system, timeout, max_tokens=max_tokens) or _fallback(prompt, system, timeout)
    if txt:
        conn.execute(
            "INSERT OR IGNORE INTO ai_cache(k,text,created_at) VALUES(?,?,?)",
            (key, txt, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    conn.close()
    return txt


def extract_json(txt: str):
    """Extrait le premier objet/array JSON d'une réponse LLM.

    2026-08-18 — ceinture de secours ajoutee : si le modele a ete coupe en cours
    de route (budget de sortie atteint), le tableau n'a pas son crochet fermant et
    json.loads rejette TOUT, y compris les 8 objets parfaitement valides qui
    precedent. On recupere alors les objets complets un par un plutot que de tout
    jeter. Corrige la cause principale du « +0 genere » en boucle.
    """
    m = re.search(r"\{.*\}|\[.*\]", txt, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    # repli : reponse tronquee -> on ramasse les objets JSON complets
    objets, prof, debut = [], 0, None
    for i, c in enumerate(txt):
        if c == "{":
            if prof == 0:
                debut = i
            prof += 1
        elif c == "}" and prof > 0:
            prof -= 1
            if prof == 0 and debut is not None:
                try:
                    objets.append(json.loads(txt[debut : i + 1]))
                except Exception:
                    pass
                debut = None
    return objets or None


# ---------------------------------------------------------------- migration + seed
def migrate() -> None:
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS biblio_topics (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      kind TEXT NOT NULL, domain TEXT NOT NULL, topic TEXT NOT NULL,
      status TEXT DEFAULT 'pending', priority INTEGER DEFAULT 5,
      source TEXT, created_at TEXT DEFAULT (datetime('now')),
      UNIQUE(kind, domain, topic)
    );
    CREATE TABLE IF NOT EXISTS ai_cache (
      k TEXT PRIMARY KEY, text TEXT, created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS biblio_knowledge (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      domain TEXT, topic TEXT UNIQUE, title TEXT, content_md TEXT,
      backend TEXT, path TEXT, created_at TEXT DEFAULT (datetime('now'))
    );
    """)
    conn.commit()
    conn.close()
    log("migration OK (biblio_topics, ai_cache, biblio_knowledge)")


def seed() -> None:
    conn = db()
    n = 0
    for kind, domain in SEED_DOMAINS:
        # 1 topic-amorce par domaine ; l'expansion générera le reste
        cur = conn.execute(
            "INSERT OR IGNORE INTO biblio_topics(kind,domain,topic,source,priority) "
            "VALUES(?,?,?, 'seed', 7)",
            (kind, domain, f"Introduction — {domain}"),
        )
        n += cur.rowcount
    conn.commit()
    conn.close()
    log(f"seed OK (+{n} topics)")


# ---------------------------------------------------------------- contexte à fond
def existing_categories() -> list[str]:
    cats = []
    if CATALOGUE.exists():
        cats = re.findall(
            r"^##\s+\S*\s*(.+)$", CATALOGUE.read_text(errors="ignore"), re.M
        )
    return [c.strip() for c in cats]


def existing_topics(conn) -> list[str]:
    return [r[0] for r in conn.execute("SELECT topic FROM biblio_topics").fetchall()]


def expand(conn) -> int:
    """Auto-alimentation infinie : le LLM propose de nouveaux sujets non couverts.

    Anti-saturation (fix cause racine) : on montre les DOMAINES RÉELS déjà couverts
    (issus de la base, pas un catalogue figé de 14 catégories) et on demande soit des
    domaines techniques NOUVEAUX, soit des sujets AVANCÉS ; un filtre de nouveauté
    côté client écarte les doublons AVANT insertion pour ne plus boucler à vide.
    """
    known = {t.strip().lower() for t in existing_topics(conn)}
    domains = [
        r[0]
        for r in conn.execute(
            "SELECT DISTINCT domain FROM biblio_topics ORDER BY domain"
        ).fetchall()
    ]
    # Anti cache-hit + anti-déterminisme : le prompt DOIT varier à chaque cycle,
    # sinon gen() (cache sha256 sur prompt) renvoie toujours la même réponse -> +0 éternel.
    random.seed()
    sample = random.sample(domains, min(60, len(domains))) if domains else []
    angle = random.choice(
        [
            "edge cases & incidents en production",
            "tuning / optimisation avancée",
            "sécurité offensive & durcissement",
            "observabilité, métriques & tracing",
            "automatisation & self-healing",
            "récupération de panne & résilience",
            "intégration cluster multi-nœuds",
            "performance des LLM locaux",
            "réseau bas niveau & diagnostic",
            "data / SQL / vecteurs & pipelines",
        ]
    )
    nonce = random.randint(1000, 999999)
    ctx = f"[cycle {nonce}] Domaines déjà couverts (échantillon) : " + ", ".join(sample)
    prompt = (
        "Tu enrichis une bibliothèque technique JARVIS "
        "(Linux/DevOps/LLM local/cluster/sécurité/réseau/data/observabilité).\n"
        f"{ctx}\n\n"
        f"Angle prioritaire de CE cycle : {angle}.\n"
        "Propose 10 sujets CONCRETS et utiles qui NE SONT PAS déjà couverts. Privilégie :\n"
        "(a) des DOMAINES TECHNIQUES NOUVEAUX absents de la liste ci-dessus, OU\n"
        "(b) des sujets AVANCÉS/pointus (edge cases, tuning, incidents, sécurité) dans des domaines existants.\n"
        "Varie les domaines, évite les redites. Réponds UNIQUEMENT en JSON: "
        '[{"kind":"command|knowledge","domain":"...","topic":"..."}, ...]'
    )
    # 2026-08-18 — CAUSE RACINE de « expand: pas de JSON exploitable ».
    # Le defaut max_tokens=600 suffisait tout juste : 10 sujets rendent ~1900
    # caracteres, soit ~550-650 tokens. Des qu'un titre etait un peu long, la
    # reponse etait COUPEE en plein milieu du JSON -> json.loads echouait ->
    # +0 topic -> pending restait a 0 -> le daemon tournait a vide en boucle.
    # Ce n'etait ni le reseau, ni le modele : une troncature de sortie.
    txt = gen(
        prompt,
        system="Tu réponds uniquement en JSON valide, sujets variés et non redondants.",
        timeout=180,
        max_tokens=2000,
    )
    data = extract_json(txt or "")
    if not isinstance(data, list):
        log("  expand: pas de JSON exploitable")
        return 0
    n = 0
    skipped = 0
    for it in data:
        try:
            topic = str(it["topic"])[:200]
            if (
                topic.strip().lower() in known
            ):  # filtre nouveauté (anti-collision silencieuse)
                skipped += 1
                continue
            k = (
                "command"
                if str(it.get("kind", "")).startswith("command")
                else "knowledge"
            )
            cur = conn.execute(
                "INSERT OR IGNORE INTO biblio_topics(kind,domain,topic,source) "
                "VALUES(?,?,?, 'llm-expand')",
                (k, str(it["domain"])[:80], topic),
            )
            if cur.rowcount:
                known.add(topic.strip().lower())
                n += cur.rowcount
        except Exception:
            continue
    conn.commit()
    log(f"  expand: +{n} nouveaux topics ({skipped} doublons écartés)")
    return n


# ---------------------------------------------------------------- générateurs
def _sql_str(s: str) -> str:
    return "'" + str(s).replace("'", "''") + "'"


def insert_command(obj: dict) -> bool:
    cid = re.sub(r"[^a-z0-9._]", "", str(obj.get("id", "")).lower())
    if not cid or not obj.get("command"):
        return False
    cat = str(obj.get("category", "Divers"))
    action = str(obj.get("action", ""))
    cmd = str(obj.get("command", ""))
    desc = str(obj.get("description", action))
    phs = obj.get("placeholders") or []
    if isinstance(phs, str):
        phs = [p.strip() for p in phs.split(",") if p.strip()]
    # normaliser : le LLM renvoie parfois des dicts/objets → forcer en str (fix crash join)
    if not isinstance(phs, list):
        phs = [phs]
    phs = [
        (
            p
            if isinstance(p, str)
            else (p.get("name") or p.get("placeholder") or str(p))
            if isinstance(p, dict)
            else str(p)
        )
        for p in phs
    ]
    danger = (
        int(obj.get("danger", 1))
        if str(obj.get("danger", 1)).lstrip("-").isdigit()
        else 1
    )
    danger = danger if danger in (0, 1, 2) else 1
    ph_sql = (
        ("ARRAY[" + ",".join(_sql_str(p) for p in phs) + "]::text[]")
        if phs
        else "'{}'::text[]"
    )
    sql = (
        f"INSERT INTO commands(id,category,action,command,description,placeholders,danger) "
        f"VALUES({_sql_str(cid)},{_sql_str(cat)},{_sql_str(action)},{_sql_str(cmd)},"
        f"{_sql_str(desc)},{ph_sql},{danger}) ON CONFLICT (id) DO NOTHING;"
    )
    r = subprocess.run(PG, input=sql, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        log(f"  PG insert KO: {r.stderr.strip()[:120]}")
        return False
    _append_catalogue(cid, cat, action, cmd, phs, danger)
    return True


def _append_catalogue(cid, cat, action, cmd, phs, danger) -> None:
    if not CATALOGUE.exists():
        return
    txt = CATALOGUE.read_text(errors="ignore")
    if f"| {cid} " in txt:  # idempotence md
        return
    header = "\n## 🌱 Bibliothèque vivante (auto-générée)\n"
    line = (
        f"| {cid} | {action} | `{cmd}` | "
        f"{','.join(phs) if phs else '-'} | {DANGER_MAP[danger]} |\n"
    )
    if "🌱 Bibliothèque vivante" not in txt:
        txt += (
            header
            + "\n| ID | Action | Commande | Trous | Danger |\n|----|--------|----------|-------|--------|\n"
        )
    txt += line
    CATALOGUE.write_text(txt)


def gen_command(domain: str, topic: str) -> bool:
    prompt = (
        f"Bibliothèque de commandes Linux/JARVIS. Domaine: {domain}. Sujet: {topic}.\n"
        "Génère UNE commande shell réelle, utile, avec des <trous> pour les paramètres.\n"
        "Réponds UNIQUEMENT en JSON:\n"
        '{"id":"<categorie>.<action>.<outil>","category":"' + domain + '",'
        '"action":"...","command":"... <param> ...","description":"...",'
        '"placeholders":["param"],"danger":0}\n'
        "danger: 0=lecture seule, 1=modifie l'état, 2=destructif. id en minuscules a.b.c."
    )
    txt = gen(
        prompt,
        system="Tu réponds uniquement en JSON valide, une seule commande.",
        timeout=120,
    )
    obj = extract_json(txt or "")
    return insert_command(obj) if isinstance(obj, dict) else False


def gen_knowledge(domain: str, topic: str) -> bool:
    prompt = (
        f"Rédige une fiche de connaissance technique concise (300-500 mots) en Markdown.\n"
        f"Domaine: {domain}. Sujet: {topic}.\n"
        "Structure: titre, contexte, points clés (liste), exemple concret, pièges. "
        "Français, factuel, orienté praticien JARVIS/Linux/LLM local."
    )
    txt = gen(prompt, system="Tu es un expert technique. Markdown clair.", timeout=120)
    if not txt or len(txt) < 120:
        return False
    slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")[:60]
    KNOW_DIR.mkdir(parents=True, exist_ok=True)
    path = KNOW_DIR / f"{slug}.md"
    path.write_text(f"# {topic}\n\n*Domaine : {domain}*\n\n{txt}\n")
    conn = db()
    conn.execute(
        "INSERT OR IGNORE INTO biblio_knowledge(domain,topic,title,content_md,backend,path) "
        "VALUES(?,?,?,?,?,?)",
        (domain, topic, topic, txt, LMS_MODEL, str(path)),
    )
    conn.commit()
    conn.close()
    return True


# ---------------------------------------------------------------- boucle
def counts(conn):
    p = conn.execute(
        "SELECT count(*) FROM biblio_topics WHERE status='pending'"
    ).fetchone()[0]
    d = conn.execute(
        "SELECT count(*) FROM biblio_topics WHERE status='done'"
    ).fetchone()[0]
    return p, d


def process_batch(batch: int) -> int:
    conn = db()
    pending, _ = counts(conn)
    if pending < EXPAND_THRESHOLD:
        expand(conn)
    if KIND_FILTER in ("command", "knowledge"):
        rows = conn.execute(
            "SELECT id,kind,domain,topic FROM biblio_topics "
            "WHERE status='pending' AND kind=? "
            "ORDER BY priority DESC, id ASC LIMIT ?",
            (KIND_FILTER, batch),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id,kind,domain,topic FROM biblio_topics WHERE status='pending' "
            "ORDER BY priority DESC, id ASC LIMIT ?",
            (batch,),
        ).fetchall()
    conn.close()
    done = 0
    for tid, kind, domain, topic in rows:
        ok = (
            gen_command(domain, topic)
            if kind == "command"
            else gen_knowledge(domain, topic)
        )
        c = db()
        c.execute(
            "UPDATE biblio_topics SET status=? WHERE id=?",
            ("done" if ok else "failed", tid),
        )
        c.commit()
        c.close()
        log(f"  [{kind}] {domain} / {topic[:50]} -> {'OK' if ok else 'FAIL'}")
        done += 1 if ok else 0
    return done


def run_loop(batch: int, pace: int, temp_max: int) -> None:
    log(f"=== boucle infinie (batch={batch}, pace={pace}s, temp_max={temp_max}°C) ===")
    while True:
        t = gpu_temp_max()
        if t >= temp_max:
            log(f"⏸️  pause thermique ({t}°C ≥ {temp_max}) — sleep 120s")
            time.sleep(120)
            continue
        # Un daemon perpétuel ne doit pas mourir d'un incident de lot. Une base
        # verrouillée ou un backend qui tousse doit coûter une pause, pas un
        # redémarrage : le service repartait de zéro toutes les 30 s sans jamais
        # produire (compteur de restart à 7).
        try:
            n = process_batch(batch)
            conn = db()
            p, d = counts(conn)
            conn.close()
            log(f"lot: +{n} générés | pending={p} done={d} | GPU {t}°C")
        except sqlite3.OperationalError as e:
            log(f"⏸️  base indisponible ({e}) — on repasse au lot suivant")
            time.sleep(30)
            continue
        except Exception as e:  # noqa: BLE001 — la boucle survit à tout incident de lot
            log(f"⏸️  lot en échec ({type(e).__name__}: {e}) — on continue")
            time.sleep(15)
            continue
        time.sleep(pace)


def status() -> None:
    conn = db()
    p, d = counts(conn)
    kn = conn.execute("SELECT count(*) FROM biblio_knowledge").fetchone()[0]
    conn.close()
    try:
        cmds = subprocess.run(
            PG,
            input="SELECT count(*) FROM commands;",
            capture_output=True,
            text=True,
            timeout=15,
        ).stdout.strip()
    except Exception:
        cmds = "?"
    print(
        f"Topics: pending={p} done={d} | Commandes cmdlib={cmds} | Fiches connaissance={kn}"
    )


# ---------------------------------------------------------------- CLI
def main():
    ap = argparse.ArgumentParser(description="Bibliothèque Vivante Infinie")
    ap.add_argument("--init", action="store_true", help="migre + seed")
    ap.add_argument("--once", action="store_true", help="un lot puis stop")
    ap.add_argument("--loop", action="store_true", help="boucle perpétuelle")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--batch", type=int, default=3)
    ap.add_argument("--pace", type=int, default=60)
    ap.add_argument("--temp-max", type=int, default=84)
    a = ap.parse_args()

    if a.init:
        migrate()
        seed()
        status()
        return
    migrate()  # idempotent : garantit les tables
    if a.status:
        status()
        return
    if a.once:
        n = process_batch(a.batch)
        log(f"once: +{n} générés")
        status()
        return
    if a.loop:
        run_loop(a.batch, a.pace, a.temp_max)
        return
    ap.print_help()


if __name__ == "__main__":
    main()
