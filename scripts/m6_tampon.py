#!/usr/bin/env python3
"""
M6 TAMPON — encaisse les demandes, les mâche sur M6, remplit la bibliothèque, grave en mémoire.

Ce que ça fait, dans l'ordre, pour CHAQUE demande reçue :
  1. TANK        la demande entre dans une file SQLite et n'est jamais perdue (statut pending).
  2. BIBLIO      routage sur les ~39 000 blocs de BLOCS-INDEX.tsv (score par recouvrement de tokens).
  3. OUTILS      auto-détection des shells agentiques réellement présents sur le disque + en base.
  4. MÂCHAGE     les sondes read-only s'exécutent SUR M6 (un seul ssh batché), pas sur M1.
  5. SYNTHÈSE    cascade 0-token : LM Studio M1 (qwen3.5-9b / gpt-oss-20b) puis Ollama M6. Zéro API payante.
  6. AUTO-REMPLI les blocs nouveaux repartent dans la bibliothèque (lib/m6-tampon-blocs.tsv + index).
  7. MÉM         l'atome de clôture est gravé via `jarvis mem write` (loi A2 : mémoire durable unique).

Pourquoi M6 : M1 porte l'écran, les 4 GPU et l'orchestration. Le travail de shell (probes, greps,
comptages) est du CPU pur — il part sur les 4 cœurs de M6 pour que M1 ne le subisse pas. M6 est le
pare-chocs, pas le cerveau : la décision finale reste sur M1.

Doctrine : stdlib uniquement, un verbe par sous-commande, --json partout, aucun effet de bord
non demandé. Seuls les blocs 🟢 (sûrs) sont exécutables automatiquement ; 🟠 et 🔴 sont rapportés,
jamais lancés.
"""

import argparse
import fcntl
import json
import os
import re
import shlex
import sqlite3
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.environ.get("JARVIS_ROOT", "/home/pamerys/jarvis")
DB = os.path.join(ROOT, "jarvis_master.db")
BLOCS_INDEX = os.path.expanduser("~/labo/bibliotheque/lib/BLOCS-INDEX.tsv")
BLOCS_OUT = os.path.expanduser("~/labo/bibliotheque/lib/m6-tampon-blocs.tsv")
CONFIG = os.path.join(ROOT, "config", "m6-tampon.json")

# ── Configuration par défaut ─────────────────────────────────────────────────
# Volontairement PAS dans ~/.openclaw/openclaw.json : ce fichier a un schéma strict et
# toute clé étrangère y fait abort la gateway OpenClaw (panne constatée le 2026-07-29).
DEFAULTS = {
    "m6_host": "10.42.0.230",
    "m6_ssh": "m6",
    "m6_ollama": "http://10.42.0.230:11434",
    "m6_parallel_slots": 4,
    "backends": [
        # Ordre = préférence. Le premier qui répond non vide gagne. Tous 0-token.
        {
            "name": "m1-lms-qwen9b",
            "kind": "openai",
            "url": "http://127.0.0.1:1234",
            "model": "qwen/qwen3.5-9b",
            "weight": "muscle",
        },
        {
            "name": "m1-lms-gptoss20b",
            "kind": "openai",
            "url": "http://127.0.0.1:1234",
            "model": "openai/gpt-oss-20b",
            "weight": "muscle",
        },
        {
            "name": "m1-hub",
            "kind": "openai",
            "url": "http://127.0.0.1:18800",
            "model": "qwen/qwen3.5-9b",
            "weight": "cascade",
        },
        {
            "name": "m6-ollama",
            "kind": "ollama",
            "url": "http://10.42.0.230:11434",
            "model": "qwen2.5:1.5b",
            "weight": "leger",
        },
        {
            "name": "ol1-local",
            "kind": "ollama",
            "url": "http://127.0.0.1:11434",
            "model": "gemma3:4b",
            "weight": "leger",
        },
    ],
    "danger_auto": ["🟢"],
    "biblio_top_k": 8,
    "tool_top_k": 6,
}


def load_config():
    cfg = dict(DEFAULTS)
    try:
        with open(CONFIG, encoding="utf-8") as fh:
            cfg.update(json.load(fh))
    except FileNotFoundError:
        pass
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[tampon] config illisible ({exc}) — défauts utilisés", file=sys.stderr)
    return cfg


# ── Schéma SQLite ────────────────────────────────────────────────────────────
DDL = """
CREATE TABLE IF NOT EXISTS m6_tampon_queue (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  ts_in       TEXT NOT NULL,
  ts_out      TEXT,
  demande     TEXT NOT NULL,
  priority    INTEGER NOT NULL DEFAULT 5,
  status      TEXT NOT NULL DEFAULT 'pending',
  chewed_on   TEXT,
  package     TEXT,
  mem_atom    TEXT,
  error       TEXT
);
CREATE INDEX IF NOT EXISTS idx_tampon_status ON m6_tampon_queue(status, priority DESC, id);
CREATE TABLE IF NOT EXISTS agentic_shell_tools (
  name        TEXT PRIMARY KEY,
  path        TEXT,
  origin      TEXT,
  danger      TEXT,
  keywords    TEXT,
  descr       TEXT,
  detected_at TEXT
);
"""


def db_conn():
    # WAL : un seul écrivain à la fois, et plusieurs producteurs permanents
    # écrivent en continu — sans attente longue, "database is locked".
    conn = sqlite3.connect(DB, timeout=120)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=120000")
    conn.executescript(DDL)
    return conn


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


# ── 2. Bibliothèque : routage sur l'index géant ───────────────────────────────
# Les 3 seuls niveaux de danger valides. Tout autre valeur = ligne corrompue de l'index.
DANGER_LEVELS = ("🟢", "🟠", "🔴")

STOP = {
    "le",
    "la",
    "les",
    "de",
    "des",
    "du",
    "un",
    "une",
    "et",
    "ou",
    "a",
    "au",
    "aux",
    "en",
    "pour",
    "dans",
    "sur",
    "avec",
    "que",
    "qui",
    "est",
    "sont",
    "tout",
    "tous",
    "toute",
    "toutes",
    "fait",
    "faire",
    "the",
    "and",
    "for",
    "with",
    "cette",
    "ce",
    "ces",
    "par",
}


def tokenize(text):
    return {
        w
        for w in re.split(r"[^\wàâäéèêëîïôöùûüç-]+", text.lower())
        if len(w) > 2 and w not in STOP
    }


REMOTE_INDEX = "/home/pamerys/.cache/jarvis-biblio/BLOCS-INDEX.tsv"

# Le scoring de ~39 000 blocs (7 Mo) est du CPU pur. Le faire sur M1 à chaque demande,
# c'est exactement ce que le tampon est censé éviter : awk tourne donc SUR M6.
# $3 doit être un des 3 niveaux valides, sinon la ligne est corrompue et rejetée.
# Emojis LITTÉRAUX, pas d'escapes \xNN : mawk 1.3.4 (celui de M6) refuse le programme
# multi-ligne avec ces escapes (« syntax error at or near »). Forme vérifiée sur M6.
# Séparateur passé par -F en flag, jamais par FS dans BEGIN.
AWK_SCORE = (
    'BEGIN{n=split(TOKENS,T," ")} '
    # $2!="m6-tampon" : le tampon ne se cite pas lui-même. Ses traces sont des mesures
    # horodatées (« GPU à 63 °C il y a 10 min »), pas des blocs réutilisables — sans ce
    # filtre l'auto-remplissage noie la bibliothèque réelle sous ses propres échos.
    'NR>1 && NF>=4 && $2!="m6-tampon" && ($3=="🟢" || $3=="🟠" || $3=="🔴"){ '
    'hay=tolower($1" "$2" "$4); nom=tolower($1); s=0; '
    "for(i=1;i<=n;i++){ if(index(hay,T[i]))s++; if(index(nom,T[i]))s++ } "
    'if(s>0) print s"\\t"$1"\\t"$2"\\t"$3"\\t"substr($4,1,300) }'
)


def biblio_route_m6(cfg, demande, top_k=8, danger_auto=("🟢",)):
    """Même routage, mais exécuté sur M6. Retourne None si M6 n'est pas exploitable."""
    toks = tokenize(demande)
    if not toks:
        return [], []
    tokens = " ".join(sorted(toks))
    # 1. l'index doit être présent sur M6 (copié une fois, rafraîchi si la taille diffère)
    try:
        local_size = os.path.getsize(BLOCS_INDEX)
        probe = subprocess.run(
            [
                "ssh",
                "-o",
                "ConnectTimeout=6",
                "-o",
                "BatchMode=yes",
                cfg["m6_ssh"],
                f"stat -c %s {shlex.quote(REMOTE_INDEX)} 2>/dev/null || echo 0",
            ],
            capture_output=True,
            text=True,
            timeout=25,
        )
        remote_size = int((probe.stdout or "0").strip() or 0)
        if remote_size != local_size:
            subprocess.run(
                [
                    "ssh",
                    "-o",
                    "ConnectTimeout=6",
                    "-o",
                    "BatchMode=yes",
                    cfg["m6_ssh"],
                    f"mkdir -p {shlex.quote(os.path.dirname(REMOTE_INDEX))}",
                ],
                capture_output=True,
                text=True,
                timeout=25,
                check=False,
            )
            subprocess.run(
                [
                    "scp",
                    "-o",
                    "ConnectTimeout=6",
                    "-o",
                    "BatchMode=yes",
                    "-q",
                    BLOCS_INDEX,
                    f"{cfg['m6_ssh']}:{REMOTE_INDEX}",
                ],
                capture_output=True,
                text=True,
                timeout=180,
                check=True,
            )
        # 2. le scoring, chez M6
        proc = subprocess.run(
            [
                "ssh",
                "-o",
                "ConnectTimeout=6",
                "-o",
                "BatchMode=yes",
                cfg["m6_ssh"],
                f"nice -n 5 awk -F'\\t' -v TOKENS={shlex.quote(tokens)} {shlex.quote(AWK_SCORE)} "
                f"{shlex.quote(REMOTE_INDEX)} | sort -t$'\t' -k1,1nr -k2,2 | head -{top_k * 3}",
            ],
            capture_output=True,
            text=True,
            timeout=120,
            check=True,
        )
    except (subprocess.SubprocessError, OSError, ValueError):
        return None

    auto, reported = [], []
    for line in proc.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 5:
            continue
        entry = {
            "score": int(parts[0]) if parts[0].isdigit() else 0,
            "nom": parts[1],
            "source": parts[2],
            "danger": parts[3],
            "bloc": parts[4],
        }
        (auto if entry["danger"] in danger_auto else reported).append(entry)
    return auto[:top_k], reported[:top_k]


def biblio_route(demande, top_k=8, danger_auto=("🟢",)):
    """Score chaque bloc de l'index par recouvrement de tokens. Retourne (auto, rapportes)."""
    toks = tokenize(demande)
    if not toks or not os.path.exists(BLOCS_INDEX):
        return [], []
    scored = []
    # newline="\n" : SANS ça, le mode texte de Python coupe aussi sur \r seul, alors
    # qu'awk (côté M6) ne coupe que sur \n. Cette divergence rendait le repli local
    # PLUS permissif que la voie durcie — fail-open exactement quand M6 tombe.
    with open(BLOCS_INDEX, encoding="utf-8", errors="replace", newline="\n") as fh:
        next(fh, None)  # entête
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 4:
                continue
            if any(("\r" in c or "\t" in c) for c in parts[:4]):
                continue  # caractère de contrôle résiduel = ligne forgée, on refuse
            nom, source, danger, bloc = parts[0], parts[1], parts[2], parts[3]
            if source == "m6-tampon":
                # même règle que côté M6 : pas d'auto-citation des mesures du tampon.
                continue
            if danger not in DANGER_LEVELS:
                # 83 lignes de l'index ont un champ danger pollué (annotations « [trous: …] »
                # écrites dans la mauvaise colonne). Un danger inconnu n'est pas dans
                # danger_auto, donc jamais auto-exécuté — mais on refuse la ligne
                # explicitement plutôt que de la faire remonter avec un danger fantaisiste.
                continue
            hay = f"{nom} {source} {bloc}".lower()
            score = sum(1 for t in toks if t in hay)
            if score:
                # un bloc dont le NOM matche vaut plus qu'un bloc qui ne matche que par son corps
                score += sum(1 for t in toks if t in nom.lower())
                scored.append((score, nom, source, danger, bloc))
    scored.sort(key=lambda r: (-r[0], r[1]))
    auto, reported = [], []
    for score, nom, source, danger, bloc in scored[: top_k * 3]:
        entry = {
            "score": score,
            "nom": nom,
            "source": source,
            "danger": danger,
            "bloc": bloc,
        }
        (auto if danger in danger_auto else reported).append(entry)
    return auto[:top_k], reported[:top_k]


# ── 3. Auto-détection des shells agentiques ──────────────────────────────────
SHELL_DIRS = [
    (os.path.join(ROOT, "bin"), "bin"),
    (os.path.join(ROOT, "scripts"), "scripts"),
    (os.path.join(ROOT, "series"), "series"),
    (os.path.expanduser("~/labo/bibliotheque/series"), "biblio-series"),
]
SHELL_BLOC_SOURCES = {
    "script",
    "commande-directe",
    "cmd-directe",
    "tool-map",
    "action-series",
    "ocow-script",
}
DANGER_WORDS = re.compile(
    r"\b(rm|dd|mkfs|shutdown|reboot|kill|pkill|truncate|drop\s+table|delete\s+from)\b",
    re.I,
)
MUTATE_WORDS = re.compile(
    r"\b(restart|stop|start|install|apt|systemctl|docker\s+(run|rm|stop)|git\s+push|write|update|insert)\b",
    re.I,
)


def _describe(path):
    """Première ligne de commentaire utile — sans exécuter le script (0 risque, 0 coût)."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for _ in range(15):
                line = fh.readline()
                if not line:
                    break
                s = line.strip()
                if s.startswith(("#!", "# ---", "# ===", '"""')) or not s:
                    continue
                if s.startswith(("#", '"', "'")):
                    return s.lstrip("#\"' ").strip()[:200]
    except OSError:
        pass
    return ""


def detect_shell_tools(conn, refresh=False):
    """Découvre les outils shell réellement présents. Pas de liste en dur : on regarde le disque."""
    cur = conn.cursor()
    if not refresh:
        rows = cur.execute(
            "SELECT name, path, origin, danger, keywords, descr FROM agentic_shell_tools"
        ).fetchall()
        if rows:
            return [
                {
                    "name": r[0],
                    "path": r[1],
                    "origin": r[2],
                    "danger": r[3],
                    "keywords": json.loads(r[4] or "[]"),
                    "descr": r[5],
                }
                for r in rows
            ]

    found = {}
    # (a) exécutables sur disque
    for base, origin in SHELL_DIRS:
        if not os.path.isdir(base):
            continue
        for entry in sorted(os.listdir(base)):
            path = os.path.join(base, entry)
            if not os.path.isfile(path) or not os.access(path, os.X_OK):
                continue
            if not entry.endswith((".sh", ".py")) and "." in entry:
                continue
            descr = _describe(path)
            blob = f"{entry} {descr}"
            danger = (
                "🔴"
                if DANGER_WORDS.search(blob)
                else ("🟠" if MUTATE_WORDS.search(blob) else "🟢")
            )
            found[entry] = {
                "name": entry,
                "path": path,
                "origin": origin,
                "danger": danger,
                "keywords": sorted(tokenize(blob))[:12],
                "descr": descr,
            }
    # (b) blocs de la bibliothèque qui SONT des commandes shell
    if os.path.exists(BLOCS_INDEX):
        with open(BLOCS_INDEX, encoding="utf-8", errors="replace", newline="\n") as fh:
            next(fh, None)
            for line in fh:
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 4 or parts[1] not in SHELL_BLOC_SOURCES:
                    continue
                if any(("\r" in c or "\t" in c) for c in parts[:4]):
                    continue  # un bloc forgé ne devient PAS un outil exécutable
                nom, source, danger, bloc = parts[0], parts[1], parts[2], parts[3]
                key = f"{source}:{nom}"
                if key in found or not bloc.strip() or danger not in DANGER_LEVELS:
                    continue
                found[key] = {
                    "name": key,
                    "path": bloc[:400],
                    "origin": f"biblio/{source}",
                    "danger": danger,
                    "keywords": sorted(tokenize(f"{nom} {bloc}"))[:12],
                    "descr": bloc[:160],
                }

    cur.execute("DELETE FROM agentic_shell_tools")
    cur.executemany(
        "INSERT INTO agentic_shell_tools(name,path,origin,danger,keywords,descr,detected_at) VALUES (?,?,?,?,?,?,?)",
        [
            (
                t["name"],
                t["path"],
                t["origin"],
                t["danger"],
                json.dumps(t["keywords"]),
                t["descr"],
                now(),
            )
            for t in found.values()
        ],
    )
    conn.commit()
    return list(found.values())


def match_tools(tools, demande, top_k=6, danger_auto=("🟢",)):
    toks = tokenize(demande)
    scored = []
    for t in tools:
        score = len(toks & set(t["keywords"]))
        if score:
            scored.append((score, t))
    scored.sort(key=lambda r: -r[0])
    return [t for s, t in scored if t["danger"] in danger_auto][:top_k]


# ── 4. Mâchage sur M6 (un seul ssh, batché) ──────────────────────────────────
# Sondes read-only. Chacune est bornée en temps et en sortie : le tampon ne doit jamais
# devenir lui-même une source de charge.
PROBES = {
    "gpu": (
        "nvidia-smi --query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used,memory.total --format=csv,noheader",
        ("gpu", "nvidia", "vram", "carte", "thermique"),
    ),
    "charge": (
        "uptime; free -m | head -3",
        ("cpu", "charge", "load", "ram", "memoire", "lent", "saturation"),
    ),
    "disque": (
        "df -h / /storage2 2>/dev/null | head -5",
        ("disque", "espace", "disk", "storage", "plein"),
    ),
    "reseau": (
        "ip -brief addr | head -8",
        ("reseau", "ip", "network", "interface", "cable"),
    ),
    "procs": (
        "ps -eo pcpu,rss,comm --sort=-pcpu | head -8",
        ("processus", "proc", "consomme", "zombie"),
    ),
    "ollama": (
        "ollama ps 2>/dev/null; ollama list 2>/dev/null | head -8",
        ("ollama", "modele", "model", "llm", "inference"),
    ),
    "services": (
        "systemctl --user --failed --no-legend --no-pager 2>/dev/null | head -6",
        ("service", "systemd", "failed", "panne", "daemon"),
    ),
}


def pick_probes(demande):
    toks = tokenize(demande)
    picked = [n for n, (_, kws) in PROBES.items() if toks & set(kws)]
    return picked or ["charge", "gpu"]


def chew_on_m6(cfg, demande, tools):
    """Exécute le mâchage SUR M6. C'est le cœur du tampon : le CPU dépensé n'est pas celui de M1."""
    names = pick_probes(demande)
    script_parts = []
    for n in names:
        cmd = PROBES[n][0]
        script_parts.append(
            f"echo '###{n}'; timeout 8 bash -c {shlex.quote(cmd)} 2>&1 | head -20"
        )
    # les outils 🟢 auto-détectés qui savent s'auto-décrire, sans effet de bord
    for t in tools[:3]:
        if t["origin"] in ("bin", "scripts") and t["path"].endswith(".sh"):
            # shlex.quote : un nom de fichier contenant une apostrophe casserait le
            # quoting du script envoyé à `ssh … bash -s`.
            script_parts.append(
                f"echo {shlex.quote('###tool:' + t['name'])}; "
                f"echo {shlex.quote('(présent sur M1 : ' + t['path'] + ')')}"
            )
    remote = "\n".join(script_parts)

    where = "m6"
    try:
        proc = subprocess.run(
            [
                "ssh",
                "-o",
                "ConnectTimeout=6",
                "-o",
                "BatchMode=yes",
                cfg["m6_ssh"],
                "bash -s",
            ],
            input=remote,
            capture_output=True,
            text=True,
            timeout=90,
        )
        out = proc.stdout
        if proc.returncode != 0 and not out.strip():
            raise RuntimeError(proc.stderr.strip()[:200] or f"ssh rc={proc.returncode}")
    except (subprocess.SubprocessError, OSError, RuntimeError) as exc:
        # Repli explicite et tracé : mieux vaut un mâchage local signalé qu'un silence.
        where = f"m1-fallback ({exc})"
        proc = subprocess.run(
            ["bash", "-c", remote], capture_output=True, text=True, timeout=90
        )
        out = proc.stdout

    chunks, current = {}, None
    for line in out.splitlines():
        if line.startswith("###"):
            current = line[3:].strip()
            chunks[current] = []
        elif current:
            chunks[current].append(line)
    return where, {
        k: "\n".join(v).strip() for k, v in chunks.items() if "".join(v).strip()
    }


# ── 5. Synthèse 0-token : cascade LM Studio + Ollama ─────────────────────────
# Borne DURE de concurrence LLM, à la source. Sans elle, 4 workers du drain =
# autant d'appels simultanés sur la gateway → CPU thrashing et yo-yo de load
# (panne constatée : load 80). Même principe que le sémaphore de qwen-nothink.sh.
LLM_SEM = threading.Semaphore(int(os.environ.get("TAMPON_MAX_LLM", "4")))

AGENT_BIN = os.path.join(ROOT, "bin", "jarvis-agent")


def ask_via_agent(prompt, timeout=180, max_tokens=420):
    """Délègue l'inférence à la brique `agent` — loi A1 : gateway LLM unique.

    Le tampon ne parle plus à LM Studio ni à Ollama en direct. Trois raisons, dans
    l'ordre d'importance :
      1. A1 : un seul point de passage par capacité, sinon l'écosystème n'est plus
         testable — et le garde de frontières ne peut plus rien prouver.
      2. Anti-duplication : la parade au reasoning-runaway de qwen3.5 (ChatML avec
         <think></think> pré-fermé) vit DÉJÀ dans la brique agent, avec la preuve
         gravée que le soft-switch /no_think officiel est inopérant sur ce build.
         L'avoir réécrite ici, c'était condamner la prochaine correction à être
         trouvée deux fois.
      3. Traçabilité : agent émet `agent.fallback_used` au journal et positionne
         JARVIS_DEGRADED_MODE. En direct, une bascule sur le plancher souverain
         était silencieuse.

    `agent` est un nœud feuille (A1-bis) : l'appeler ne crée aucun cycle.
    Retourne (backend_effectif, texte) ou (None, None).
    """
    with LLM_SEM:
        try:
            proc = subprocess.run(
                [AGENT_BIN, "ask", prompt, "--max", str(max_tokens), "--json"],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except (subprocess.SubprocessError, OSError) as exc:
            return None, f"__ERR__{exc}" if os.environ.get("TAMPON_DEBUG") else None
    if proc.returncode != 0:
        # exit 3 = E_LLM_EXHAUSTED : plus aucun modèle souverain ne répond.
        return None, None
    try:
        env = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None, None
    data = env.get("data") or {}
    txt = (data.get("response") or "").strip()
    backend = data.get("backend")
    if env.get("meta", {}).get("fallback_used"):
        backend = f"{backend} (fallback)"
    return (backend, txt) if txt else (backend, None)


def synthesize(cfg, demande, biblio_auto, biblio_rep, tools, chewed, where):
    """Interroge les backends EN PARALLÈLE et garde la première réponse utile (massivement 0-token)."""
    ctx = [f"DEMANDE: {demande}", f"MÂCHÉ SUR: {where}"]
    if biblio_auto:
        ctx.append("BLOCS BIBLIOTHÈQUE (sûrs, applicables):")
        ctx += [
            f"  - [{b['source']}] {b['nom']} → {b['bloc'][:140]}"
            for b in biblio_auto[:6]
        ]
    if biblio_rep:
        ctx.append(
            "BLOCS SENSIBLES (à ne pas lancer seul): "
            + ", ".join(f"{b['danger']}{b['nom']}" for b in biblio_rep[:5])
        )
    if tools:
        ctx.append(
            "SHELLS AGENTIQUES DISPONIBLES: " + ", ".join(t["name"] for t in tools[:6])
        )
    for k, v in chewed.items():
        ctx.append(f"MESURE[{k}]:\n{v[:600]}")

    prompt = (
        "Tu es le préprocesseur du nœud tampon M6 de JARVIS. On te donne une demande et des mesures "
        "déjà collectées. Rends un plan d'action court et FACTUEL en français.\n\n"
        + "\n".join(ctx)
        + "\n\nRéponds en 3 sections courtes:\n"
        "CONSTAT: ce que les mesures montrent (chiffres à l'appui, rien d'inventé).\n"
        "PLAN: 1 à 3 actions concrètes, la commande exacte quand elle est connue.\n"
        "RISQUE: ce qu'il ne faut PAS lancer automatiquement et pourquoi.\n"
        "Si une mesure manque, dis-le au lieu de supposer."
    )

    # Un seul appel, à la brique agent. C'est elle qui porte la cascade
    # (hub → LM Studio nothink → Ollama → tampon M6) et qui trace ses bascules.
    # Le tampon n'a plus à connaître la liste des backends : c'est le sens de A1.
    backend, txt = ask_via_agent(prompt, timeout=240, max_tokens=520)
    attempts = {"jarvis-agent": bool(txt)}
    if txt:
        return backend or "jarvis-agent", txt, attempts
    return None, None, attempts


# ── 6. Auto-remplissage de la bibliothèque ───────────────────────────────────
def _san(value):
    """Neutralise les séparateurs TSV dans une cellule.

    Indispensable : le champ `bloc` interpole des données NON FIABLES — stderr de ssh
    (multi-ligne), sorties de sondes exécutées sur M6, texte produit par un LLM. Un seul
    \t ou \r suffisait à scinder la ligne et à fabriquer un bloc entier de toutes pièces,
    avec un danger 🟢 et une source arbitraire — donc à contourner le filtre anti-boucle
    et à faire passer une commande hostile pour « sûre et applicable ».
    Faille prouvée par revue adverse le 2026-07-30.
    """
    return re.sub(r"[\t\r\n]+", " ", str(value))


def autofill_biblio(demande, served_by, synth, chewed, where="inconnu"):
    """Ce que le tampon vient d'apprendre repart dans la bibliothèque, dédupliqué.

    La provenance écrite est celle qui a RÉELLEMENT tourné (`where`), jamais « M6 » par
    défaut. Un flag de provenance posé par l'appelant au lieu d'être dérivé de l'exécution
    réelle est un mensonge silencieux : le bloc affirmerait « mesuré sur M6 » alors que le
    repli a tourné sur M1, et la bibliothèque se remplirait de fausses attributions.
    """
    slug = re.sub(r"[^a-z0-9]+", "-", demande.lower()).strip("-")[:60] or "demande"
    host = "M6" if where == "m6" else _san(where)
    lines = []
    for k, v in chewed.items():
        one = _san(" | ".join(v.split("\n")))[:300]
        lines.append(
            (
                _san("m6-" + slug + "-" + k),
                "m6-tampon",
                "🟢",
                f"# mesuré sur {host} {now()} :: {one}",
            )
        )
    if synth:
        lines.append(
            (
                f"m6-{slug}-plan",
                "m6-tampon",
                "🟢",
                f"# plan {_san(served_by)} {now()} :: "
                + _san(" | ".join(synth.split("\n")))[:400],
            )
        )

    existing = set()
    for path in (BLOCS_OUT, BLOCS_INDEX):
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    p = line.split("\t")
                    if len(p) >= 2:
                        existing.add((p[0], p[1]))
        except FileNotFoundError:
            continue
    fresh = [r for r in lines if (r[0], r[1]) not in existing]
    if not fresh:
        return 0
    os.makedirs(os.path.dirname(BLOCS_OUT), exist_ok=True)
    new_file = not os.path.exists(BLOCS_OUT)
    fresh = [tuple(_san(c) for c in r) for r in fresh]  # ceinture-bretelles
    with open(BLOCS_OUT, "a", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)  # N workers appendent le même fichier
        if new_file:
            fh.write("nom\tsource\tdanger\tbloc\n")
        for r in fresh:
            fh.write("\t".join(r) + "\n")
    if os.path.exists(BLOCS_INDEX):
        with open(BLOCS_INDEX, "a", encoding="utf-8") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX)
            for r in fresh:
                fh.write("\t".join(r) + "\n")
    return len(fresh)


# ── 7. Protocole mem (loi A2) ────────────────────────────────────────────────
def mem_write(demande, served_by, where, synth, n_blocs):
    """Mémoire durable = la brique mem, jamais un .md ni une table ad-hoc."""
    content = (
        f"[m6-tampon] demande={demande!r} mâché_sur={where} synthèse_par={served_by or 'aucun'} "
        f"blocs_ajoutés={n_blocs}. " + (synth or "").replace("\n", " ")[:900]
    )
    try:
        proc = subprocess.run(
            [
                os.path.join(ROOT, "bin", "jarvis-mem"),
                "write",
                "--scope",
                "m6_tampon",
                "--content",
                content,
                "--tags",
                "m6",
                "tampon",
                "biblio",
                "--json",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if proc.returncode == 0:
            try:
                return json.loads(proc.stdout).get("data", {}).get("id") or "written"
            except json.JSONDecodeError:
                return "written"
        return f"mem-rc={proc.returncode}"
    except (subprocess.SubprocessError, OSError) as exc:
        return f"mem-indispo: {exc}"


# ── Pipeline complet ─────────────────────────────────────────────────────────
def process(cfg, conn, demande, row_id=None):
    t0 = time.time()
    if conn is None:
        conn = db_conn()
    tools_all = detect_shell_tools(conn)
    # Le routage biblio part sur M6 en priorité — c'est le gros du CPU par demande.
    # Repli local seulement si M6 est injoignable, et on le trace dans le paquet.
    biblio_where = "m6"
    routed = biblio_route_m6(
        cfg, demande, cfg["biblio_top_k"], tuple(cfg["danger_auto"])
    )
    if routed is None:
        biblio_where = "m1-fallback"
        routed = biblio_route(demande, cfg["biblio_top_k"], tuple(cfg["danger_auto"]))
    biblio_auto, biblio_rep = routed
    tools = match_tools(
        tools_all, demande, cfg["tool_top_k"], tuple(cfg["danger_auto"])
    )
    where, chewed = chew_on_m6(cfg, demande, tools)
    served_by, synth, attempts = synthesize(
        cfg, demande, biblio_auto, biblio_rep, tools, chewed, where
    )
    n_blocs = autofill_biblio(demande, served_by, synth, chewed, where)
    atom = mem_write(demande, served_by, where, synth, n_blocs)

    pkg = {
        "demande": demande,
        "chewed_on": where,
        "biblio_routed_on": biblio_where,
        "served_by": served_by,
        "biblio_auto": biblio_auto,
        "biblio_sensibles": biblio_rep,
        "shells_detectes_total": len(tools_all),
        "shells_retenus": [t["name"] for t in tools],
        "mesures": chewed,
        "synthese": synth,
        "backends_tentes": {k: bool(v) for k, v in attempts.items()},
        "blocs_ajoutes": n_blocs,
        "mem_atom": atom,
        "elapsed_s": round(time.time() - t0, 1),
        "ts": now(),
    }
    if row_id is not None:
        conn.execute(
            "UPDATE m6_tampon_queue SET status=?, ts_out=?, chewed_on=?, package=?, mem_atom=?, error=? WHERE id=?",
            (
                "done" if synth else "partial",
                now(),
                where,
                json.dumps(pkg, ensure_ascii=False),
                str(atom),
                None if synth else "aucun backend 0-token n'a répondu",
                row_id,
            ),
        )
        conn.commit()
    return pkg


# ── Sous-commandes ───────────────────────────────────────────────────────────
def cmd_enqueue(cfg, args):
    conn = db_conn()
    ids = []
    for d in args.demande:
        cur = conn.execute(
            "INSERT INTO m6_tampon_queue(ts_in,demande,priority) VALUES (?,?,?)",
            (now(), d, args.priority),
        )
        ids.append(cur.lastrowid)
    conn.commit()
    print(
        json.dumps(
            {"ok": True, "tanked": ids, "pending": pending_count(conn)},
            ensure_ascii=False,
        )
    )


def pending_count(conn):
    return conn.execute(
        "SELECT COUNT(*) FROM m6_tampon_queue WHERE status='pending'"
    ).fetchone()[0]


def cmd_drain(cfg, args):
    conn = db_conn()
    rows = conn.execute(
        "SELECT id, demande FROM m6_tampon_queue WHERE status='pending' ORDER BY priority DESC, id LIMIT ?",
        (args.max,),
    ).fetchall()
    if not rows:
        print(
            json.dumps(
                {"ok": True, "drained": 0, "note": "file vide"}, ensure_ascii=False
            )
        )
        return
    for rid, _ in rows:
        conn.execute("UPDATE m6_tampon_queue SET status='running' WHERE id=?", (rid,))
    conn.commit()

    done = []
    slots = max(1, min(args.workers, cfg["m6_parallel_slots"]))
    with ThreadPoolExecutor(max_workers=slots) as pool:
        # conn=None : chaque worker ouvre SA connexion. Une connexion sqlite3 créée dans
        # le thread principal ne peut pas être utilisée par un thread fils.
        futures = {pool.submit(process, cfg, None, d, rid): rid for rid, d in rows}
        for fut in as_completed(futures):
            rid = futures[fut]
            try:
                pkg = fut.result()
                done.append(
                    {
                        "id": rid,
                        "served_by": pkg["served_by"],
                        "chewed_on": pkg["chewed_on"],
                        "blocs": pkg["blocs_ajoutes"],
                        "mem": pkg["mem_atom"],
                        "s": pkg["elapsed_s"],
                    }
                )
            except Exception as exc:
                conn.execute(
                    "UPDATE m6_tampon_queue SET status='error', error=?, ts_out=? WHERE id=?",
                    (str(exc)[:300], now(), rid),
                )
                conn.commit()
                done.append({"id": rid, "error": str(exc)[:200]})
    print(
        json.dumps(
            {
                "ok": True,
                "drained": len(done),
                "results": done,
                "pending_restant": pending_count(conn),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def cmd_once(cfg, args):
    conn = db_conn()
    pkg = process(cfg, conn, " ".join(args.demande))
    if args.json:
        print(json.dumps(pkg, ensure_ascii=False, indent=2))
        return
    print(f"📥 demande      : {pkg['demande']}")
    print(f"⚙️  mâché sur    : {pkg['chewed_on']}")
    print(f"🧠 synthèse par : {pkg['served_by']} (0 token)")
    print(
        f"📚 biblio       : {len(pkg['biblio_auto'])} blocs sûrs, "
        f"{len(pkg['biblio_sensibles'])} sensibles écartés"
    )
    print(
        f"🔧 shells       : {pkg['shells_detectes_total']} détectés, retenus "
        f"{', '.join(pkg['shells_retenus']) or '—'}"
    )
    print(
        f"➕ auto-rempli  : {pkg['blocs_ajoutes']} nouveaux blocs · mem={pkg['mem_atom']}"
    )
    print(f"⏱️  {pkg['elapsed_s']}s\n")
    for k, v in pkg["mesures"].items():
        print(f"── mesure[{k}]\n{v}\n")
    print("── synthèse\n" + (pkg["synthese"] or "(aucun backend n'a répondu)"))


def cmd_tools(cfg, args):
    conn = db_conn()
    tools = detect_shell_tools(conn, refresh=args.refresh)
    by_origin, by_danger = {}, {}
    for t in tools:
        by_origin[t["origin"]] = by_origin.get(t["origin"], 0) + 1
        by_danger[t["danger"]] = by_danger.get(t["danger"], 0) + 1
    print(
        json.dumps(
            {
                "ok": True,
                "total": len(tools),
                "par_origine": by_origin,
                "par_danger": by_danger,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def cmd_backends(cfg, args):
    """Santé des backends — SANS parler aux endpoints LLM (loi A1).

    Le tampon n'a pas le droit de sonder /v1/... lui-même : il demande à `jarvis doctor`
    (checks actifs, aucun appel LLM, donc zéro quota consommé) puis fait UN aller-retour
    par la gateway pour prouver que la chaîne d'inférence répond de bout en bout.
    """
    doctor = subprocess.run(
        [os.path.join(ROOT, "bin", "jarvis"), "doctor"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    t0 = time.time()
    backend, txt = ask_via_agent("Réponds exactement: OK", timeout=180, max_tokens=12)
    print(
        json.dumps(
            {
                "ok": bool(txt),
                "cout": "0 token (backends locaux uniquement, via la brique agent)",
                "gateway": {
                    "backend_effectif": backend,
                    "reponse": (txt or "")[:60],
                    "elapsed_s": round(time.time() - t0, 1),
                },
                "doctor_exit": doctor.returncode,
                "doctor": [ln for ln in doctor.stdout.splitlines() if ln.strip()],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def cmd_classe(cfg, args):
    """Classe une intention en texte libre sur la bibliothèque — sans ssh, sans LLM.

    Point d'entrée pour le déploiement multi-agent : un agent reçoit une intention,
    appelle ceci, et obtient des blocs déjà classés par danger. Instantané.

    Pourquoi ce point d'entrée existe alors que `bin/bloc.sh` fait « déjà » ça : bloc.sh
    cherche la PHRASE ENTIÈRE en sous-chaîne, donc il rend ∅ dès qu'il y a plusieurs mots
    (mesuré le 2026-07-30 : « placement gpu ollama » → ∅, « temperature ventilateur
    carte » → ∅, alors qu'ici les deux rendent 5 blocs). Le score est un recouvrement de
    tokens : bien meilleur rappel, précision moindre — « carte » ramène
    « CARTE-MENTALE-API-CERFA ». À lire comme une PRÉSÉLECTION à trier, jamais comme une
    réponse. Et jamais comme une autorisation d'exécuter : seuls les 🟢 sont éligibles.
    """
    conn = db_conn()
    demande = " ".join(args.intention)
    auto, sensibles = biblio_route(demande, args.top, tuple(cfg["danger_auto"]))
    outils = match_tools(
        detect_shell_tools(conn), demande, args.top, tuple(cfg["danger_auto"])
    )
    res = {
        "intention": demande,
        "tokens": sorted(tokenize(demande)),
        "blocs_surs": auto,
        "blocs_sensibles": [
            {k: b[k] for k in ("nom", "source", "danger")} for b in sensibles
        ],
        "outils_shell": [{"nom": t["name"], "origine": t["origin"]} for t in outils],
        "avertissement": "présélection par recouvrement de tokens : à trier, pas une réponse",
    }
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return
    print(f"🔎 « {demande} »  →  tokens {res['tokens']}")
    for b in auto:
        print(f"  {b['danger']} [{b['source']}] {b['nom']}")
        print(f"      {b['bloc'][:100]}")
    if sensibles:
        print(
            "  écartés (non auto-exécutables) : "
            + ", ".join(f"{b['danger']}{b['nom']}" for b in sensibles[:6])
        )
    if outils:
        print("  shells : " + ", ".join(t["name"] for t in outils))


def cmd_status(cfg, args):
    conn = db_conn()
    st = dict(
        conn.execute(
            "SELECT status, COUNT(*) FROM m6_tampon_queue GROUP BY status"
        ).fetchall()
    )
    tools = conn.execute("SELECT COUNT(*) FROM agentic_shell_tools").fetchone()[0]
    blocs = 0
    try:
        with open(BLOCS_INDEX, encoding="utf-8", errors="replace") as fh:
            blocs = sum(1 for _ in fh) - 1
    except OSError:
        pass
    print(
        json.dumps(
            {
                "ok": True,
                "file": st,
                "shells_detectes": tools,
                "blocs_bibliotheque": blocs,
                "config": CONFIG if os.path.exists(CONFIG) else "défauts",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def main():
    ap = argparse.ArgumentParser(
        description="M6 tampon — encaisse, mâche sur M6, remplit la biblio, grave en mem"
    )
    sub = ap.add_subparsers(dest="action", required=True)

    p = sub.add_parser("enqueue", help="Tanker une ou plusieurs demandes")
    p.add_argument("demande", nargs="+")
    p.add_argument("--priority", type=int, default=5)
    p.set_defaults(fn=cmd_enqueue)

    p = sub.add_parser("drain", help="Traiter la file en parallèle sur les slots M6")
    p.add_argument("--max", type=int, default=8)
    p.add_argument("--workers", type=int, default=4)
    p.set_defaults(fn=cmd_drain)

    p = sub.add_parser(
        "once", help="Pipeline complet sur une demande, sans passer par la file"
    )
    p.add_argument("demande", nargs="+")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_once)

    p = sub.add_parser("tools", help="Registre des shells agentiques auto-détectés")
    p.add_argument("--refresh", action="store_true")
    p.set_defaults(fn=cmd_tools)

    p = sub.add_parser(
        "classe", help="Classer une intention sur la bibliothèque (sans ssh, sans LLM)"
    )
    p.add_argument("intention", nargs="+")
    p.add_argument("--top", type=int, default=6)
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_classe)

    p = sub.add_parser("backends", help="Santé des backends 0-token")
    p.set_defaults(fn=cmd_backends)

    p = sub.add_parser(
        "status", help="État de la file, des outils et de la bibliothèque"
    )
    p.set_defaults(fn=cmd_status)

    args = ap.parse_args()
    args.fn(load_config(), args)


if __name__ == "__main__":
    main()
