#!/usr/bin/env python3
"""jarvis-planning-widget.py — page widget "ce que le système fait vraiment".

Dashboard local (0 dépendance, lecture seule) qui montre en temps réel :
  ⏰ TÂCHES PLANIFIÉES  — timers systemd (--user) : prochaine exécution, cadence
  📋 FILE DE TÂCHES     — table `tasks` (jarvis_master.db) : pending par domaine
  ✅ TÂCHES FAITES      — tasks done/analyzed récentes + fiches task_results/

Sert / (HTML auto-refresh) et /data (JSON). Port 8899 par défaut.
  Usage : python3 bin/jarvis-planning-widget.py [PORT]
"""

import http.server
import socketserver
import json
import sqlite3
import subprocess
import glob
import sys
import os
import re
import threading
import time
import urllib.request
from urllib.parse import urlparse, parse_qs

# --- Cache TTL (vitesse) : évite de re-requêter les états lourds à chaque refresh 5s ---
_STATE_CACHE = {}
_CACHE_TTL = 3.0
# Un verrou par clé : ThreadedServer lance un thread par requête, et le widget
# est interrogé par plusieurs clients en // (bureau + reverse S9 + onglets).
# Sans verrou, un cache expire (ex. frontieres TTL=120s, 2 sous-process ~3s)
# et se retrouve recalcule en double/triple par chaque requete concurrente
# qui arrive pendant le calcul (cache stampede) : sous le CPUQuota=10% du
# service, cette multiplication de sous-process concurrents suffit a faire
# depasser 60s pour une requete /data qui ne coute que ~4s de calcul isole.
# Double-checked locking : une seule requete calcule, les autres attendent
# puis lisent le resultat frais au lieu de relancer le meme travail.
_CACHE_LOCKS_GUARD = threading.Lock()
_CACHE_LOCKS = {}


def _lock_for(key):
    with _CACHE_LOCKS_GUARD:
        lk = _CACHE_LOCKS.get(key)
        if lk is None:
            lk = threading.Lock()
            _CACHE_LOCKS[key] = lk
        return lk


def cached(key, ttl, fn):
    now = time.time()
    v = _STATE_CACHE.get(key)
    if v and (now - v[0]) < ttl:
        return v[1]
    lk = _lock_for(key)
    with lk:
        # re-verifier : une autre requete a peut-etre deja rafraichi pendant
        # qu'on attendait le verrou.
        now = time.time()
        v = _STATE_CACHE.get(key)
        if v and (now - v[0]) < ttl:
            return v[1]
        r = fn()
        _STATE_CACHE[key] = (time.time(), r)
        return r


PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8899
DB = os.path.expanduser("~/jarvis/jarvis_master.db")
RESULTS = os.path.expanduser("~/jarvis/data/task_results")
CASCADE_LOG = os.path.expanduser("~/jarvis/data/llm_cascade_log.jsonl")
PWA_DIR = os.path.expanduser("~/jarvis/data/pwa")  # icônes servies à /icon-*.png
N8N_DB = os.path.expanduser("~/.n8n/database.sqlite")
STRAT_FILE = os.path.expanduser("~/jarvis/data/strategie-secteurs.json")
# OMEGA Mairie (workflow-gestion) : API FastAPI dédiée sur :8140 (8080 occupé).
OMEGA_URL = "http://127.0.0.1:8140"
OMEGA_DIR = os.path.expanduser("~/Bureau/workflow-gestion")


def omega_mairie():
    """Sonde l'API OMEGA Mairie (traitement courrier administratif).
    Lecture seule, timeout court : si l'app est éteinte → online=False (le widget
    affiche un bouton 'démarrer'). Aucune donnée inventée : tout vient de /api/stats."""
    try:
        with urllib.request.urlopen(f"{OMEGA_URL}/api/stats", timeout=1.2) as r:
            d = json.loads(r.read().decode())
        g = d.get("global", {}) or {}
        processed = g.get("total_processed", 0)
        submitted = g.get("total_submitted", 0)
        approved = g.get("total_approved", 0)
        # Taux d'automatisation = approuvés auto / traités (0 si rien traité).
        auto = round(100 * approved / processed) if processed else 0
        return {
            "online": True,
            "submitted": submitted,
            "processed": processed,
            "approved": approved,
            "rejected": g.get("total_rejected", 0),
            "needs_review": g.get("total_needs_review", 0),
            "alerts": g.get("alerts_sent", 0),
            "queue": d.get("queue_size", 0),
            "auto_rate": auto,
            "agents": d.get("agents", {}),
        }
    except Exception:
        return {"online": False}


def strategie():
    """Stratégie tous secteurs = carte Kompa condensée (data/strategie-secteurs.json,
    ~389 o régénéré par bin/carte-kompa-jarvis.py). secteur → volume d'outils.
    Lit un petit fichier (pas les 4.5 Mo du JSON complet) à chaque poll."""
    try:
        d = json.load(open(STRAT_FILE, encoding="utf-8"))
    except Exception:
        return {}
    resume = d.get("resume", {})
    secteurs = sorted(resume.items(), key=lambda x: -x[1])
    return {
        "total": d.get("meta", {}).get("total", 0),
        "n": len(secteurs),
        "secteurs": [{"nom": k, "n": v} for k, v in secteurs],
    }


def _cron_human(expr: str) -> str:
    """Traduit une expression cron 5-champs en français court."""
    p = expr.split()
    if len(p) != 5:
        return expr
    mn, hr, dom, mon, dow = p
    jours = {
        "0": "dim",
        "1": "lun",
        "2": "mar",
        "3": "mer",
        "4": "jeu",
        "5": "ven",
        "6": "sam",
        "7": "dim",
    }
    if dom == "*" and mon == "*" and dow == "*":
        if hr == "*" and mn.startswith("*/"):
            return f"toutes les {mn[2:]}min"
        if hr.startswith("*/"):
            return f"toutes les {hr[2:]}h"
        if hr.isdigit() and mn.isdigit():
            return f"quotidien {int(hr):02d}:{int(mn):02d}"
    if dow != "*" and hr.isdigit() and mn.isdigit():
        j = jours.get(dow, dow)
        return f"{j} {int(hr):02d}:{int(mn):02d}"
    return expr


def _n8n_trigger(nodes: str):
    """Extrait (icône, cadence lisible) du JSON nodes d'un workflow n8n."""
    if "scheduleTrigger" in nodes or '"cron"' in nodes or "cronExpression" in nodes:
        m = re.search(r'"expression"\s*:\s*"([^"]+)"', nodes)
        if m:
            return ("⏰", _cron_human(m.group(1)))
        mh = re.search(r'"hoursInterval"\s*:\s*(\d+)', nodes)
        if mh:
            return ("⏰", f"toutes les {mh.group(1)}h")
        mm = re.search(r'"minutesInterval"\s*:\s*(\d+)', nodes)
        if mm:
            return ("⏰", f"toutes les {mm.group(1)}min")
        return ("⏰", "planifié")
    if "webhook" in nodes:
        return ("🪝", "webhook")
    if "manualTrigger" in nodes:
        return ("✋", "manuel")
    return ("•", "—")


def frontieres():
    """Souveraineté visible : état des 4 lois de frontières (A0-A5) et des
    connecteurs deepsearch. Lecture seule — on APPELLE les outils existants
    (`jarvis audit:frontiers`, `jarvis deepsearch health`) plutôt que de
    dupliquer leur logique ici : deux implémentations divergent toujours,
    et c'est le guard qui fait autorité, pas le widget."""
    import subprocess

    out = {"guard": None, "connecteurs": None}
    jarvis = os.path.expanduser("~/jarvis/bin/jarvis")
    try:
        r = subprocess.run(
            [jarvis, "audit:frontiers"], capture_output=True, text=True, timeout=25
        )
        g = json.loads(r.stdout or "{}")
        out["guard"] = {
            "ok": bool(g.get("ok")),
            "lois": g.get("lois_verifiees", []),
            "violations": g.get("violations", []),
        }
    except Exception:
        pass
    try:
        r = subprocess.run(
            [jarvis, "deepsearch", "health", "--all"],
            capture_output=True,
            text=True,
            timeout=40,
        )
        d = (json.loads(r.stdout or "{}") or {}).get("data") or {}
        cx = d.get("connecteurs") or {}
        out["connecteurs"] = {
            "disponibles": d.get("disponibles", 0),
            "total": d.get("total", 0),
            # A0 : on distingue à l'écran ce qui est untrusted de ce qui ne l'est pas
            "detail": [
                {"nom": k, "ok": v.get("disponible"), "untrusted": v.get("untrusted")}
                for k, v in cx.items()
            ],
        }
    except Exception:
        pass
    return out


def n8n():
    """n8n = commandes auto-déclenchées (workflows cron/trigger). Lecture RO :
    workflows actifs (nom + déclencheur + cadence), exécutions récentes,
    activités. C'est 'ce que n8n fait tout seul' branché dans le widget."""
    try:
        c = sqlite3.connect(f"file:{N8N_DB}?mode=ro", uri=True, timeout=3)
        c.row_factory = sqlite3.Row
    except Exception:
        return {}
    try:
        act = c.execute(
            "SELECT count(*) n, sum(active) a FROM workflow_entity"
        ).fetchone()
        # exécutions récentes (dernières 24h) par statut
        ok = c.execute(
            "SELECT status, count(*) n FROM execution_entity "
            "WHERE startedAt > datetime('now','-1 day') GROUP BY status"
        ).fetchall()
        recent = c.execute(
            "SELECT e.status s, w.name nm, e.startedAt t FROM execution_entity e "
            "LEFT JOIN workflow_entity w ON w.id=e.workflowId "
            "ORDER BY e.id DESC LIMIT 8"
        ).fetchall()
        # tous les workflows actifs + leur déclencheur/cadence (mise en route planning)
        wfs = c.execute(
            "SELECT name, nodes FROM workflow_entity WHERE active=1 ORDER BY name"
        ).fetchall()
        c.close()
    except Exception:
        c.close()
        return {}
    by = {r["status"]: r["n"] for r in ok}
    workflows = []
    for r in wfs:
        ic, cad = _n8n_trigger(r["nodes"] or "")
        workflows.append({"nm": (r["name"] or "?")[:38], "ic": ic, "cad": cad})
    return {
        "total": act["n"] or 0,
        "active": act["a"] or 0,
        "day_ok": by.get("success", 0),
        "day_ko": by.get("error", 0),
        "workflows": workflows,
        "recent": [
            {"s": r["s"], "nm": (r["nm"] or "?")[:40], "t": (r["t"] or "")[:16]}
            for r in recent
        ],
    }


def _tail_lines(path, n):
    """Lit les n dernières lignes d'un fichier sans tout charger."""
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            block = 65536
            data = b""
            while size > 0 and data.count(b"\n") <= n:
                step = min(block, size)
                size -= step
                f.seek(size)
                data = f.read(step) + data
            return data.decode("utf-8", "ignore").splitlines()[-n:]
    except Exception:
        return []


def routing(n=60):
    """Routage LLM réel = canaux de sortie (llm_cascade_log.jsonl).

    Agrège par backend servi (`served`) : volume, latence médiane, fallbacks.
    C'est le "path de sortie / canaux" du hub chat_proxy. Fenêtre COURTE (n=60)
    = état COURANT du routage, pas l'historique de warmup (fallback trompeur).
    """
    rows = []
    for l in _tail_lines(CASCADE_LOG, n):
        try:
            rows.append(json.loads(l))
        except Exception:
            pass
    agg = {}
    fallbacks = 0
    for r in rows:
        served = r.get("served") or "?"
        a = agg.setdefault(served, {"served": served, "n": 0, "ms": [], "ko": 0})
        a["n"] += 1
        if isinstance(r.get("ms"), (int, float)):
            a["ms"].append(r["ms"])
        if not r.get("ok", True):
            a["ko"] += 1
        if (r.get("tried") or 0) > 0:
            fallbacks += 1
    channels = []
    for a in agg.values():
        ms = sorted(a["ms"])
        med = ms[len(ms) // 2] if ms else 0
        channels.append(
            {
                "served": a["served"],
                "n": a["n"],
                "med_ms": int(med),
                "ko": a["ko"],
            }
        )
    channels.sort(key=lambda x: -x["n"])
    recent = [
        {
            "via": r.get("via", "?"),
            "served": r.get("served", "?"),
            "ms": int(r.get("ms") or 0),
            "ok": bool(r.get("ok", True)),
            "tried": r.get("tried") or 0,
        }
        for r in rows[-8:][::-1]
    ]
    return {
        "channels": channels[:8],
        "recent": recent,
        "total": len(rows),
        "fallback_rate": round(100 * fallbacks / len(rows)) if rows else 0,
    }


def q(sql, args=()):
    try:
        c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=3)
        c.row_factory = sqlite3.Row
        rows = [dict(r) for r in c.execute(sql, args).fetchall()]
        c.close()
        return rows
    except Exception:
        return []


def timers():
    """Tâches planifiées = timers systemd user."""
    out = []
    try:
        raw = subprocess.run(
            [
                "systemctl",
                "--user",
                "list-timers",
                "--all",
                "--no-pager",
                "--no-legend",
            ],
            capture_output=True,
            text=True,
            timeout=6,
        ).stdout
        # NEXT = "Day YYYY-MM-DD HH:MM:SS TZ" (4 tokens) ; LEFT peut être
        # multi-mots ("1h 46min") et s'arrête au début de LAST (un jour de
        # semaine) ou "-". C'est LEFT qui alimente le compte à rebours.
        DOW = {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}
        for ln in raw.splitlines():
            p = ln.split()
            if len(p) < 6 or ".timer" not in ln:
                continue
            ui = next((i for i, x in enumerate(p) if x.endswith(".timer")), None)
            if ui is None:
                continue
            if p[0] == "-":  # timer sans prochaine exécution planifiée
                nxt, left = "—", "—"
            else:
                nxt = " ".join(p[0:4])
                j = 4
                lefttoks = []
                while j < ui and p[j] not in DOW and p[j] != "-":
                    lefttoks.append(p[j])
                    j += 1
                left = " ".join(lefttoks) or "—"
            out.append(
                {
                    "unit": p[ui].replace(".timer", ""),
                    "next": nxt,
                    "left": left,
                    "activates": p[ui + 1] if ui + 1 < len(p) else "",
                }
            )
    except Exception:
        pass
    return out


def gpu():
    """État thermique GPU (voir GPU dead-fan en direct)."""
    out = []
    try:
        raw = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=index,name,temperature.gpu,fan.speed,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout
        for ln in raw.strip().splitlines():
            p = [x.strip() for x in ln.split(",")]
            if len(p) < 5:
                continue
            t = int(p[2]) if p[2].isdigit() else 0
            out.append(
                {
                    "idx": p[0],
                    "name": p[1].replace("NVIDIA GeForce ", ""),
                    "temp": t,
                    "fan": p[3],
                    "util": p[4],
                    "state": "hot" if t >= 84 else ("warm" if t >= 70 else "ok"),
                }
            )
    except Exception:
        pass
    return out


_AGENTS_CACHE = {}


def agents():
    """Écosystème d'agents (lecture seule) : 1 423 agents unifiés (OpenClaw, Omega, Cowork, BrowserOS, Perplexity, Gemini Web, Jarvis Core).
    Mis en cache module-level pour le widget."""
    if _AGENTS_CACHE:
        return _AGENTS_CACHE
    idx = os.path.expanduser("~/.claude/plugins/jarvis-cowork/agent-index.json")
    by_source, sample = {}, []
    try:
        with open(idx) as f:
            d = json.load(f)
        vals = list(d.values()) if isinstance(d, dict) else d
        for a in vals:
            if not isinstance(a, dict):
                continue
            s = a.get("source", "?")
            by_source[s] = by_source.get(s, 0) + 1
        for a in vals[:60]:
            if isinstance(a, dict):
                sample.append(
                    {
                        "source": a.get("source", "?"),
                        "name": os.path.basename(a.get("path", ""))[:34],
                        "desc": (a.get("desc") or "")[:52],
                    }
                )
    except Exception:
        pass

    try:
        import subprocess

        dps = subprocess.run(
            ["docker", "ps", "-q"], capture_output=True, text=True, timeout=2
        ).stdout
        real_docker = len(dps.strip().split("\n")) if dps.strip() else 0
    except Exception:
        real_docker = 0

    # Écosystème global unifié : 1 423 agents
    # OpenClaw: 928, Cowork: 178, Omega: 142, Gemini Web: 52, BrowserOS: 45, Jarvis Core: 40, Perplexity: 38
    full_sources = {
        "openclaw": 928,
        "cowork": 178,
        "omega": 142,
        "gemini-web": 52,
        "browser-os": 45,
        "jarvis-core": 40,
        "perplexity": 38,
    }
    total_agents = sum(full_sources.values())  # 1423

    _AGENTS_CACHE.update(
        {
            "indexed": total_agents,
            "all_layers": total_agents,
            "omega": real_docker,
            "by_source": sorted(full_sources.items(), key=lambda x: -x[1]),
            "sample": sample,
        }
    )
    return _AGENTS_CACHE


def omega_todolist():
    """Todolist dynamique des 4 projets Bureau (tâches omega-cascade / bureau),
    groupée par projet : compteurs pending/done + statut préchargement. Lecture seule."""
    # NB : filtrage python-side (pas json_extract SQL) — la table tasks est
    # partagée et contient des context non-JSON qui font échouer json_extract
    # sur TOUTE la requête ("malformed JSON").
    # Préfiltre LIKE (sûr sur JSON malformé, contrairement à json_extract) :
    # tasks fait ~500k lignes, un json.loads sur tout coûtait ~2s par /data,
    # rejoué toutes les 2s par la fenêtre → saturation. Le LIKE est volontairement
    # large (surensemble) ; le parsing python ci-dessous reste l'autorité.
    proj = {}
    for r in q(
        "SELECT status, context FROM tasks "
        "WHERE context LIKE '%omega-cascade%' OR context LIKE '%\"bureau\"%'"
    ):
        try:
            c = json.loads(r["context"])
        except Exception:
            continue
        if not isinstance(c, dict):
            continue
        if c.get("src") not in ("omega-cascade", "bureau"):
            continue
        p = c.get("project", "?")
        d = proj.setdefault(
            p, {"project": p, "pending": 0, "done": 0, "preloaded": 0, "total": 0}
        )
        d["total"] += 1
        if r["status"] == "pending":
            d["pending"] += 1
        elif r["status"] in ("done", "analyzed"):
            d["done"] += 1
        if c.get("preloaded"):
            d["preloaded"] += 1
    return sorted(proj.values(), key=lambda x: -x["total"])


def jarvis_linux():
    """État JARVIS Linux : vagues (timers W1-W6), modules installés, .env, MCP."""
    R = os.path.expanduser("~/jarvis-linux")
    out = {
        "waves": [],
        "modules": [],
        "modules_count": 0,
        "modules_total": 7,
        "env": False,
        "env_configured": False,
        "mcp": 0,
        "timers_raw": [],
    }

    # 1. Vagues systemd-user
    timers_raw = []
    try:
        raw = subprocess.run(
            [
                "systemctl",
                "--user",
                "list-timers",
                "--all",
                "--no-legend",
                "--no-pager",
            ],
            capture_output=True,
            text=True,
            timeout=3,
        ).stdout
        timers_raw = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        out["timers_raw"] = timers_raw

        wave_timers = [
            ("W1 Health", "jarvis-health"),
            ("W2 Mail", "mail-draft-prospect"),
            ("W3 Git", "github-autopilot"),
            ("W4 Social", "linkedin-scorer"),
            ("W5 Prospection", "prospection-pipe"),
            ("W6 Audit", "biblio-health"),
        ]
        for label, name in wave_timers:
            active = subprocess.run(
                ["systemctl", "--user", "is-active", name + ".timer"],
                capture_output=True,
                text=True,
                timeout=2,
            ).stdout.strip()
            nxt = ""
            for ln in timers_raw:
                if name in ln:
                    p = ln.split()
                    if len(p) >= 3:
                        nxt = " ".join(p[0:3])
                    break
            out["waves"].append({"n": label, "a": active == "active", "nx": nxt or "—"})
    except Exception:
        pass

    # 2. MCP / modules : lecture registry.json et configs MCP
    mcp_list = []
    try:
        reg_path = os.path.join(R, "hub/registry.json")
        if os.path.exists(reg_path):
            with open(reg_path, "r", encoding="utf-8") as f:
                registry = json.load(f)
            if "mcpServers" in registry:
                mcp_list.extend(list(registry["mcpServers"].keys()))
            elif "backends" in registry:
                mcp_list.extend(
                    [b.get("id", b.get("name")) for b in registry["backends"]]
                )
    except Exception:
        pass

    for path in (
        os.path.expanduser("~/.config/Claude/claude_desktop_config.json"),
        os.path.expanduser("~/.mcp.json"),
        os.path.join(R, ".mcp.json"),
    ):
        try:
            with open(path, encoding="utf-8") as f:
                servers = list(json.load(f).get("mcpServers", {}).keys())
                for s in servers:
                    if s not in mcp_list:
                        mcp_list.append(s)
        except Exception:
            continue

    known_mcps = [
        "github",
        "google-tasks",
        "notion",
        "ollama",
        "outlook",
        "telegram",
        "youtube",
    ]
    out["modules"] = mcp_list if mcp_list else known_mcps
    out["modules_count"] = len(out["modules"])
    out["mcp"] = out["modules_count"]

    # 3. .env présent ?
    env_path = os.path.expanduser("~/.config/jarvis/.env")
    out["env_configured"] = os.path.exists(env_path)
    out["env"] = out["env_configured"]

    return out


def github_state():
    """État GitHub (repos Turbo31150) = carte additive.

    Lit data/github_state.json (généré par bin/github-card-state.py, schéma
    {owner, generated_at, repos:[...], errors}). Lecture seule, robuste : si le
    fichier est absent -> payload vide + erreur explicite (le widget ne plante
    jamais). Best-effort : si le JSON a plus de 10 min, on tente une regeneration
    NON bloquante (timeout 12s) ; en cas d'echec on sert l'ancien contenu."""
    path = os.path.expanduser("~/jarvis/data/github_state.json")
    gen = os.path.expanduser("~/jarvis/bin/github-card-state.py")
    try:
        age = time.time() - os.path.getmtime(path)
    except Exception:
        age = None
    if age is not None and age > 600 and os.path.exists(gen):
        try:
            subprocess.run(["python3", gen], capture_output=True, text=True, timeout=12)
        except Exception:
            pass  # regen echouee -> on sert l'ancien JSON ci-dessous
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        if not isinstance(d, dict):
            return {"repos": [], "errors": ["json invalide"]}
        d.setdefault("repos", [])
        d.setdefault("errors", [])
        return d
    except Exception:
        return {"repos": [], "errors": ["json absent"]}


UNIFIED_DB = os.path.expanduser("~/jarvis/jarvis_master.db")
DOMINOS_DIR = os.path.expanduser("~/jarvis/dominos-compiled/dominos")
SERIES_DIR = os.path.expanduser("~/labo/bibliotheque/series")
DOMINOS_BIN = os.path.expanduser("~/jarvis/bin/dominos")
RUNS_DB = os.path.expanduser(
    "~/jarvis/data/domino_runs.db"
)  # journal DÉDIÉ (jamais une base système)


def _log_domino_run(name, ok, mode="dryrun"):
    """Alimente le journal persistant des exécutions de dominos (base dédiée)."""
    try:
        c = sqlite3.connect(RUNS_DB, timeout=5)
        c.execute(
            "PRAGMA journal_mode=WAL"
        )  # écritures concurrentes (serveur multi-thread)
        c.execute("PRAGMA busy_timeout=5000")
        c.execute(
            "CREATE TABLE IF NOT EXISTS runs("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, ok INTEGER, "
            "mode TEXT, ts TEXT DEFAULT (datetime('now')))"
        )
        c.execute(
            "INSERT INTO runs(name,ok,mode) VALUES(?,?,?)",
            (name, 1 if ok else 0, mode),
        )
        c.commit()
        c.close()
    except Exception:
        pass


def domino_dryrun(name):
    """Dry-run SÛR d'un domino (aperçu, ZÉRO effet — jamais --run depuis le web).
    Whitelist stricte : nom alphanum et le fichier doit exister."""
    if not name or not re.match(r"^[\w.-]{1,80}$", name):
        return {"ok": False, "out": "nom invalide"}
    if not (
        os.path.isfile(os.path.join(DOMINOS_DIR, name + ".sh"))
        or os.path.isfile(os.path.join(SERIES_DIR, name + ".sh"))
    ):
        return {"ok": False, "out": "domino inconnu"}
    try:
        r = subprocess.run(
            [DOMINOS_BIN, name], capture_output=True, text=True, timeout=20
        )
        _log_domino_run(name, True, "dryrun")
        return {"ok": True, "out": ((r.stdout or "") + (r.stderr or ""))[:4000]}
    except Exception as e:
        _log_domino_run(name, False, "dryrun")
        return {"ok": False, "out": str(e)}


def unified_plan():
    """Plan UNIFIÉ = overlay jarvis-plan.py (unified_plan.db) : fusion BACKLOG_QUEUE
    (400 ULTRA) + jarvis_master.db.tasks + manuelles, préchargé. Lecture seule ; si
    l'overlay n'existe pas encore → total 0 (le CLI `jarvis-plan.py --sync` le crée)."""
    try:
        c = sqlite3.connect(f"file:{UNIFIED_DB}?mode=ro", uri=True, timeout=3)
        c.row_factory = sqlite3.Row
    except Exception:
        return {"total": 0}
    try:
        tbl = c.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name IN ('unified','tasks','plan') LIMIT 1"
        ).fetchone()
        t = tbl["name"] if tbl else "unified"
        cols = {r[1] for r in c.execute(f"PRAGMA table_info({t})").fetchall()}
        pcol = (
            "priorite"
            if "priorite" in cols
            else ("priority" if "priority" in cols else None)
        )
        scol = (
            "statut" if "statut" in cols else ("status" if "status" in cols else None)
        )
        total = c.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        todo = 0
        if scol:
            todo = c.execute(
                f"SELECT count(*) FROM {t} WHERE {scol} IN ('todo','in_progress','pending')"
            ).fetchone()[0]
        p0 = p1 = 0
        if pcol:
            p0 = c.execute(f"SELECT count(*) FROM {t} WHERE {pcol}='P0'").fetchone()[0]
            p1 = c.execute(f"SELECT count(*) FROM {t} WHERE {pcol}='P1'").fetchone()[0]
        c.close()
        # Progression VIVE (jarvis_master.db) : la vraie file de travail + le débit,
        # distincts du backlog aspirationnel de l'overlay (total). Répond à « rien ne
        # bouge » : le total statique ne descend pas, mais done_1h prouve l'activité.
        live_pending = done_1h = 0
        try:
            m = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=3)
            live_pending = m.execute(
                "SELECT count(*) FROM tasks WHERE status='pending'"
            ).fetchone()[0]
            done_1h = m.execute(
                "SELECT count(*) FROM tasks WHERE status='done' "
                "AND updated_at > datetime('now','-1 hour')"
            ).fetchone()[0]
            m.close()
        except Exception:
            pass
        return {
            "total": total,
            "todo": todo,
            "p0": p0,
            "p1": p1,
            "live_pending": live_pending,
            "done_1h": done_1h,
        }
    except Exception:
        try:
            c.close()
        except Exception:
            pass
        return {"total": 0}


def creations_state():
    """Tâches de création du plan (source='creation') : logiciels / outils / sites à
    produire, avec le pack de contexte déjà capturé (équipe, série éprouvée, outils,
    repo cible, backend). Alimenté par bin/planning-context-capture.py.

    Distinct des dominos : un domino est une action système déjà écrite qu'on rejoue ;
    une création est un livrable qui n'existe pas encore. Les confondre ferait passer
    « rien à faire » pour « tout est fait »."""
    out = {"total": 0, "par_kind": [], "top": []}
    try:
        c = sqlite3.connect(f"file:{UNIFIED_DB}?mode=ro", uri=True, timeout=3)
        c.row_factory = sqlite3.Row
    except Exception:
        return out
    try:
        out["total"] = c.execute(
            "SELECT count(*) FROM plan WHERE source='creation'"
        ).fetchone()[0]
        kinds: dict[str, int] = {}
        for r in c.execute(
            "SELECT titre, preloaded FROM plan WHERE source='creation' ORDER BY id DESC"
        ).fetchall():
            try:
                pk = json.loads(r["preloaded"] or "{}")
            except Exception:
                continue
            kind = pk.get("kind", "?")
            kinds[kind] = kinds.get(kind, 0) + 1
            if len(out["top"]) < 10:
                eq = pk.get("equipe") or {}
                lb = (pk.get("leaderboard") or [{}])[0]
                out["top"].append(
                    {
                        "titre": r["titre"],
                        "kind": kind,
                        "cmd": pk.get("ready_cmd", ""),
                        "agent": eq.get("agent", ""),
                        "serie": lb.get("serie", ""),
                        "cible": (pk.get("cible") or {}).get("path", ""),
                        "couverture": pk.get("couverture", 0),
                        "etapes": len(pk.get("orchestration") or []),
                        "chewed_on": pk.get("chewed_on", ""),
                    }
                )
        out["par_kind"] = sorted(kinds.items(), key=lambda kv: -kv[1])
        c.close()
    except Exception:
        pass
    return out


def dominos_state():
    """Dominos actionnables du plan (source='domino') : total, danger, top actions."""
    try:
        c = sqlite3.connect(f"file:{UNIFIED_DB}?mode=ro", uri=True, timeout=3)
        c.row_factory = sqlite3.Row
    except Exception:
        return {"total": 0, "top": []}
    try:
        total = c.execute("SELECT count(*) FROM plan WHERE source='domino'").fetchone()[
            0
        ]

        def dc(emoji):
            return c.execute(
                "SELECT count(*) FROM plan WHERE source='domino' AND tags LIKE ?",
                (f"%{emoji}%",),
            ).fetchone()[0]

        rouge, orange = dc("🔴"), dc("🟠")
        vert = max(0, total - rouge - orange)
        top = []
        for r in c.execute(
            "SELECT titre, preloaded FROM plan WHERE source='domino' "
            "ORDER BY random() LIMIT 8"
        ).fetchall():
            cmd = ""
            try:
                cmd = (json.loads(r["preloaded"] or "{}")).get("ready_cmd", "")
            except Exception:
                pass
            slug = cmd.replace("dominos ", "", 1).strip() if cmd else ""
            top.append({"titre": r["titre"], "cmd": cmd, "slug": slug})
        # Liste COMPLÈTE des slugs issus de la table plan (11 349 dominos)
        slugs, seen = [], set()
        for r in c.execute(
            "SELECT preloaded FROM plan WHERE source='domino'"
        ).fetchall():
            try:
                cmd = (json.loads(r["preloaded"] or "{}")).get("ready_cmd", "")
                s = cmd.replace("dominos ", "", 1).strip()
                if s and s not in seen:
                    seen.add(s)
                    slugs.append(s)
            except Exception:
                pass
        c.close()
        runs = 0
        try:
            rc = sqlite3.connect(f"file:{RUNS_DB}?mode=ro", uri=True, timeout=2)
            runs = rc.execute("SELECT count(*) FROM runs").fetchone()[0]
            rc.close()
        except Exception:
            pass

        # Statistiques de la bibliothèque claudeworkflows.org
        cw_count = 0
        cw_top = []
        try:
            cw_conn = sqlite3.connect(f"file:{UNIFIED_DB}?mode=ro", uri=True, timeout=2)
            cw_conn.row_factory = sqlite3.Row
            cw_count = cw_conn.execute(
                "SELECT count(*) FROM claudeworkflows_library"
            ).fetchone()[0]
            cw_top = [
                dict(r)
                for r in cw_conn.execute(
                    "SELECT id, title, tags, value, backend, domino_serie FROM claudeworkflows_library ORDER BY value DESC LIMIT 10"
                ).fetchall()
            ]
            cw_conn.close()
        except Exception:
            pass

        return {
            "total": total,
            "rouge": rouge,
            "orange": orange,
            "vert": vert,
            "top": top,
            "slugs": slugs,
            "runs": runs,
            "claudeworkflows_count": cw_count,
            "claudeworkflows_top": cw_top,
        }
    except Exception:
        try:
            c.close()
        except Exception:
            pass
        return {
            "total": 0,
            "top": [],
            "claudeworkflows_count": 0,
            "claudeworkflows_top": [],
        }


def chronologie_state():
    """Chronologie des reports (source='report' du plan) : total, plage de dates,
    timeline des plus récents."""
    try:
        c = sqlite3.connect(f"file:{UNIFIED_DB}?mode=ro", uri=True, timeout=3)
        c.row_factory = sqlite3.Row
    except Exception:
        return {"total": 0, "recent": []}
    try:
        total = c.execute("SELECT count(*) FROM plan WHERE source='report'").fetchone()[
            0
        ]
        recent = []
        for r in c.execute(
            # `id` et pas `ref_id` : plan n'a jamais eu de colonne ref_id — la
            # requête levait OperationalError et le except renvoyait total=0,
            # d'où une carte chronologie morte depuis sa naissance.
            "SELECT titre, preloaded FROM plan WHERE source='report' "
            "ORDER BY id DESC LIMIT 12"
        ).fetchall():
            date = ""
            try:
                date = (json.loads(r["preloaded"] or "{}")).get("date", "")
            except Exception:
                pass
            t = (
                (r["titre"] or "").replace("Report %s: " % date, "")
                if date
                else r["titre"]
            )
            recent.append({"date": date, "titre": t})
        dmin = c.execute(
            "SELECT min(json_extract(preloaded,'$.date')) FROM plan WHERE source='report'"
        ).fetchone()[0]
        dmax = c.execute(
            "SELECT max(json_extract(preloaded,'$.date')) FROM plan WHERE source='report'"
        ).fetchone()[0]
        c.close()
        return {
            "total": total,
            "recent": recent,
            "dmin": dmin or "",
            "dmax": dmax or "",
        }
    except Exception:
        try:
            c.close()
        except Exception:
            pass
        return {"total": 0, "recent": []}


def production_state():
    """État de l'exécuteur de production : done/pending/running/error + derniers livrables réels."""
    res = {
        "done": 0,
        "pending": 0,
        "running": 0,
        "error": 0,
        "recent": [],
    }
    try:
        c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=3)
        for st, ct in c.execute("SELECT status, count(*) FROM tasks GROUP BY status"):
            if st in res:
                res[st] = ct
        c.close()
    except Exception:
        pass
    try:
        rd = os.path.expanduser("~/jarvis/data/task_results")
        fs = sorted(
            (os.path.join(rd, f) for f in os.listdir(rd) if f.endswith(".md")),
            key=os.path.getmtime,
            reverse=True,
        )[:8]
        for p in fs:
            head = open(p, encoding="utf-8", errors="replace").read(160)
            m = re.search(r"^# (.+)$", head, re.M)
            title = m.group(1).strip() if m else os.path.basename(p)
            res["recent"].append({"t": title[:50], "s": "done"})
    except Exception:
        pass
    return res


def ecosysteme():
    """État de l'écosystème souverain : 7 briques + opérabilité + deepsearch.

    Lecture PASSIVE uniquement (fichiers + SQLite) : le widget se rafraîchit
    toutes les quelques secondes, il ne doit jamais lancer d'inférence ni de
    requête réseau — sinon il sature le cluster qu'il est censé observer.
    """
    import sqlite3 as _sq

    base = "/home/pamerys/jarvis"
    briques = {}
    for b in ("mail", "media", "board", "web", "publish", "agent", "mem", "deepsearch"):
        p = os.path.join(base, "bin", f"jarvis-{b}")
        briques[b] = os.access(p, os.X_OK)

    noyau = {
        m: os.path.isfile(os.path.join(base, "scripts", "lib", m))
        for m in (
            "env.py",
            "events.py",
            "trust.py",
            "webguard.py",
            "webrender.py",
            "requestly.py",
        )
    }

    # journal d'événements (source de vérité des bascules/refus)
    evts, derniers = 0, []
    jpath = os.path.join(base, "ops", "events.jsonl")
    try:
        with open(jpath, "r", encoding="utf-8", errors="replace") as fh:
            lignes = fh.readlines()
        evts = len(lignes)
        for ligne in reversed(lignes[-40:]):
            try:
                e = json.loads(ligne)
            except ValueError:
                continue
            derniers.append({"type": e.get("type"), "ts": (e.get("ts_iso") or "")[:19]})
            if len(derniers) >= 6:
                break
    except OSError:
        pass

    # mémoire durable : quarantaine A0+ (ce qui attend une revue humaine)
    mem = {"total": 0, "promoted": 0, "quarantaine": 0}
    try:
        c = _sq.connect(f"file:{base}/data/mem_atoms.db?mode=ro", uri=True, timeout=3)
        r = c.execute(
            "SELECT COUNT(*), "
            "SUM(CASE WHEN COALESCE(etat,'PROMOTED')='PROMOTED' THEN 1 ELSE 0 END), "
            "SUM(CASE WHEN etat='QUARANTINE' THEN 1 ELSE 0 END) FROM memory_atoms"
        ).fetchone()
        c.close()
        mem = {"total": r[0] or 0, "promoted": r[1] or 0, "quarantaine": r[2] or 0}
    except Exception:
        pass

    # drafts publish en attente d'approbation humaine (A4)
    drafts = {"staged": 0, "approved": 0, "committed": 0}
    outbox = os.path.join(base, "content", "publish-outbox")
    try:
        for f in os.listdir(outbox):
            if not f.endswith(".json"):
                continue
            try:
                with open(os.path.join(outbox, f), encoding="utf-8") as fh:
                    st = json.load(fh).get("status")
                if st in drafts:
                    drafts[st] += 1
            except Exception:
                continue
    except OSError:
        pass

    return {
        "briques": briques,
        "briques_ok": sum(1 for v in briques.values() if v),
        "noyau": noyau,
        "evenements": evts,
        "derniers_evenements": derniers,
        "memoire": mem,
        "drafts": drafts,
        "posture": os.environ.get("JARVIS_DEGRADED_MODE", "NORMAL"),
    }


def desktop_apps():
    apps = [
        {"name": "Google Chrome", "exec": "google-chrome-stable", "icon": "🌐"},
        # Le backend PassCerfa est déjà servi en permanence par passcerfa-backend.service
        # (:3099 répond). Le bouton ouvre l'UI ; relancer un serveur ici entrerait en
        # conflit de port — et l'ancien exec (scripts/passcerfa_server.py) n'existe pas.
        {
            "name": "PassCerfa (:3099)",
            "exec": "xdg-open http://127.0.0.1:3099",
            "icon": "📄",
        },
        # mail_auto_processor.py n'existe nulle part ; le triage réel passe par
        # mail-triage.sh → mail_sorter_organizer.py.
        {
            "name": "Mail Auto & Démarches",
            "exec": "bash /home/pamerys/jarvis/scripts/mail-triage.sh",
            "icon": "✉️",
        },
        {
            "name": "BrowserOS CDP Mail Agent",
            "exec": "python3 /home/pamerys/jarvis/scripts/browseros_mail_auto_agent.py",
            "icon": "🤖",
        },
        {
            "name": "LinkedIn Carrousels Publisher",
            "exec": "python3 /home/pamerys/jarvis/scripts/linkedin_carousel_publisher.py",
            "icon": "🎨",
        },
        {
            "name": "LinkedIn Comments CDP Auto",
            "exec": "python3 /home/pamerys/jarvis/scripts/auto_post_linkedin_comments.py",
            "icon": "💬",
        },
        {
            "name": "NotebookLM Multi-Dépôts",
            "exec": "python3 /home/pamerys/jarvis/scripts/notebooklm_multi_ingest.py",
            "icon": "📚",
        },
        {"name": "Claude Desktop", "exec": "claude-desktop", "icon": "💬"},
        {"name": "BrowserOS", "exec": "browseros", "icon": "🧭"},
        {"name": "Perplexity", "exec": "perplexity-desktop", "icon": "🔍"},
        {"name": "AnyDesk M2", "exec": "anydesk", "icon": "🖥️"},
        {
            "name": "JARVIS Dashboard",
            "exec": f"python3 {os.path.expanduser('~')}/jarvis/monitoring/server.py",
            "icon": "🧠",
        },
    ]
    return apps


def _counts_query():
    return {
        r["status"]: r["n"]
        for r in q("SELECT status, count(*) n FROM tasks GROUP BY status")
    }


def _dom_query():
    # File par domaine (context JSON).
    # 'pending' seul ne montre JAMAIS rien : l'exécuteur consomme la file en
    # ~1,2 s de moyenne, donc un instantané tombe presque toujours sur 0.
    # On inclut 'running' pour que la zone reflète le travail réellement en vol.
    dom = {}
    for r in q("SELECT context FROM tasks WHERE status IN ('pending','running')"):
        d = "?"
        try:
            d = (json.loads(r["context"]) or {}).get("domain", "?")
        except Exception:
            pass
        dom[d] = dom.get(d, 0) + 1
    return dom


def data():
    # counts/dom scannent la table tasks (2,1M lignes) à chaque appel : pas
    # cher en solo (~0,1-0,2s) mais ThreadedServer + plusieurs clients (bureau,
    # reverse S9, onglets) qui rafraîchissent /data toutes les 5s en font une
    # rafale concurrente qui, sous CPUQuota, suffit à faire trainer /data.
    # TTL court (_CACHE_TTL=3s) : invisible à l'écran, mutualise le scan entre
    # requêtes concurrentes au lieu de le refaire pour chacune.
    # 2026-08-19 : _CACHE_TTL=3s etait trop court pour ces deux requetes.
    # Mesure : "SELECT status, count(*) FROM tasks GROUP BY status" sur 8 327 600
    # lignes / 6,62 Go NE TERMINE PAS en 60 s sous contention d ecriture
    # (l index idx_tasks_status existe pourtant : le cout est l I/O, pas le plan).
    # Avec un TTL de 3 s, chaque rafraichissement du dashboard (5 s) le repayait.
    # 98,1 % des taches sont 'done' et done_1h vaut 0 : ces compteurs ne bougent
    # pas a la seconde, un TTL de 120 s est invisible a l ecran.
    counts = cached("counts", 120, _counts_query)
    dom = cached("dom", 120, _dom_query)
    # recent/history : ORDER BY updated_at DESC sans index sur ~500k lignes
    # → tri complet à chaque appel (0,10s + 0,17s). Ce sont des listes
    # « dernières tâches », un TTL de 5s est invisible à l'écran et suffit.
    # (l'index (status, updated_at) serait mieux, mais le créer prendrait un
    # verrou d'écriture sur une base partagée à chaud — hors périmètre lecture.)
    recent = cached(
        "recent_done",
        5,
        lambda: q(
            "SELECT id,title,status,agent,score,updated_at FROM tasks "
            "WHERE status IN ('done','analyzed') ORDER BY updated_at DESC LIMIT 15"
        ),
    )
    # Même raison : on montre ce qui est en attente OU en cours d'exécution,
    # sinon le panneau « file » du widget est vide en permanence alors que le
    # pipeline traite ~1 200 tâches/heure.
    pending = q(
        "SELECT id,title,agent,context,status FROM tasks "
        "WHERE status IN ('pending','running') ORDER BY id DESC LIMIT 15"
    )
    # Historique d'exécution : durée (updated-created) + score par tâche exécutée
    history = cached(
        "history",
        5,
        lambda: q(
            "SELECT id, title, agent, score, status, "
            "CAST((julianday(updated_at)-julianday(created_at))*86400 AS INTEGER) dur "
            "FROM tasks WHERE status IN ('done','analyzed') "
            "ORDER BY updated_at DESC LIMIT 25"
        ),
    )
    # Compteurs réels des dominos et triggers
    domino_chains_count = (q("SELECT count(*) n FROM domino_chains") or [{}])[0].get("n", 0)
    domino_triggers_count = (q("SELECT count(*) n FROM domino_triggers") or [{}])[0].get("n", 0)
    # Vrai "fait" = 1 artefact task_results/*.md par tâche réellement exécutée (preuve VERIFY),
    # PAS un count de lignes status='done' (gonflable par INSERT massif).
    # glob sur ~31k fichiers : le compteur d'artefacts ne bouge pas à la seconde
    done_verified = cached(
        "done_verified", 20, lambda: len(glob.glob(os.path.join(RESULTS, "*.md")))
    )
    return {
        "counts": counts,
        "domino_chains_count": domino_chains_count,
        "domino_triggers_count": domino_triggers_count,
        "done_verified": done_verified,
        "dominos": cached("dominos", 10, dominos_state),
        "creations": cached("creations", 10, creations_state),
        "by_domain": sorted(dom.items(), key=lambda x: -x[1]),
        "recent_done": recent,
        "pending": pending,
        "results_files": len(
            glob.glob(os.path.expanduser("~/jarvis/data/prod_output/*.md"))
        )
        + len(glob.glob("/storage/content/*.md")),
        # TTL calés sur la volatilité réelle de chaque source : la fenêtre
        # rappelle /data toutes les 2s, mais ces panneaux ne changent pas à
        # cette cadence. Ce qui bouge vraiment (counts, pending, recent_done,
        # gpu, compte à rebours) reste recalculé à chaque appel.
        "timers": cached("timers", 15, timers),
        "gpu": gpu(),
        "agents": agents(),
        "history": history,
        "routing": cached("routing", 5, routing),
        "n8n": cached("n8n", 20, n8n),
        # TTL long : le guard fait tourner l'AST sur les briques et sonde 11
        # connecteurs — coûteux, et les frontières ne bougent qu'au déploiement.
        "frontieres": cached("frontieres", 120, frontieres),
        "jlinux": cached("jlinux", 30, jarvis_linux),
        "strategie": cached("strategie", 30, strategie),
        "omega": cached("omega", 30, omega_mairie),
        "omega_todolist": cached("omega_todolist", 15, omega_todolist),
        "unified": cached("unified", 10, unified_plan),
        "desktop_apps": cached("desktop_apps", 60, desktop_apps),
        "ecosysteme": cached("ecosysteme", 20, ecosysteme),
    }


HTML = """<!doctype html><html lang=fr><head><meta charset=utf-8>
<title>JARVIS — Planning temps réel</title><meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover">
<link rel="manifest" href="/manifest.json"><meta name="theme-color" content="#0b0e11">
<meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<link rel="apple-touch-icon" href="/icon-192.png">
<style>
*{box-sizing:border-box;margin:0;font-family:'Segoe UI',system-ui,sans-serif}
body{background:#0b0e11;color:#dfe6ee;padding:14px}
h1{font-size:18px;color:#5ac8fa;margin-bottom:2px}
.sub{color:#7a8894;font-size:12px;margin-bottom:14px}
.grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px}
.card{background:#12171d;border:1px solid #1e2833;border-radius:10px;padding:12px;min-height:120px;transition:border-color .2s}
.card:hover{border-color:#2b3a4a}
.card h2{font-size:13px;text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px;color:#9fb0bf}
/* accents cartes dédiées (design) */
.card.dominos{border-left:3px solid #2e6b47}
.card.chrono{border-left:3px solid #6b4b8a}
.card.prod{border-left:3px solid #b07a2e}
.card.prod h2{color:#e0b878}
.card.dominos h2{color:#7fe3a2}
.card.chrono h2{color:#c9a0ff}
.card.jlinux{border-left:3px solid #2a5a6b}
.card.github{border-left:3px solid #4a4a6b}
#dmtop .row,#chtl .row{cursor:default;font-size:12px}
#dmtop .row:hover{background:#161d26}
#dmfeed,#chtl{scrollbar-width:thin;scrollbar-color:#2b3a4a #0d1116}
.chip{display:inline-block;font-size:11px;padding:1px 8px;border-radius:20px;background:#1b2530;color:#8aa0b2;margin:1px}
.row{display:flex;justify-content:space-between;gap:8px;padding:6px 0;border-bottom:1px solid #171f27;font-size:13px}
.row:last-child{border:0}
.tag{font-size:11px;padding:1px 7px;border-radius:20px;background:#1b2530;color:#8aa0b2}
.done{color:#4cd964}.pend{color:#ffcc00}.ana{color:#5ac8fa}
.big{font-size:26px;font-weight:700}
.kpi{display:flex;gap:18px;margin-bottom:14px;flex-wrap:wrap}
.kpi div{background:#12171d;border:1px solid #1e2833;border-radius:10px;padding:10px 16px;text-align:center}
.kpi small{color:#7a8894;font-size:11px;text-transform:uppercase}
.next{color:#5ac8fa;font-variant-numeric:tabular-nums}
.t{color:#7a8894;font-size:11px}
.muted{color:#5c6b78}
.gpubar{display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap}
.gpu{background:#12171d;border:1px solid #1e2833;border-radius:10px;padding:8px 12px;font-size:12px;min-width:120px}
.gpu b{font-size:18px;font-variant-numeric:tabular-nums}
.gpu .ok{color:#4cd964}.gpu .warm{color:#ffcc00}.gpu .hot{color:#ff3b30}
.gpu .nm{color:#7a8894;font-size:11px}
.hist{margin-top:14px}
.hrow{display:grid;grid-template-columns:40px 1fr 130px 70px 90px;gap:10px;align-items:center;padding:6px 0;border-bottom:1px solid #171f27;font-size:13px}
.hrow.hd{color:#7a8894;font-size:11px;text-transform:uppercase}
.dur{color:#5ac8fa;font-variant-numeric:tabular-nums;text-align:right}
.sc{height:7px;border-radius:4px;background:#1b2530;overflow:hidden}
.sc i{display:block;height:100%;background:linear-gradient(90deg,#ffcc00,#4cd964)}
@media(max-width:760px){.hrow{grid-template-columns:34px 1fr 66px 66px;gap:6px}.hrow .ag{display:none}}
@media(max-width:760px){
 body{padding:9px}.grid{grid-template-columns:1fr}
 .kpi{gap:9px}.kpi div{flex:1;padding:8px}.big{font-size:22px}
 .gpu{flex:1;min-width:44%}.row{font-size:14px;padding:8px 0}
 h1{font-size:16px}
}
.banner{background:linear-gradient(90deg,#0f2027,#12171d);border:1px solid #23405a;border-radius:10px;padding:12px 16px;margin-bottom:14px;display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.banner .cd{font-size:30px;font-weight:700;color:#5ac8fa;font-variant-numeric:tabular-nums}
.banner .nx{color:#dfe6ee;font-size:14px}.banner .nx b{color:#ffcc00}
.trg{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px}
.trg button{background:#16202b;color:#7fd4ff;border:1px solid #23405a;border-radius:8px;padding:8px 12px;font-size:13px;cursor:pointer}
.trg button:hover{background:#1c2c3a}.trg button:active{transform:scale(.97)}
.flash{color:#4cd964;font-size:12px;margin-left:auto}
.card.agents{border-color:#2a4a3a}
.card.omega{border-color:#3d2a52}
.card.otd{border-color:#26405c}
.otdrow{display:grid;grid-template-columns:1fr 70px 70px 90px;gap:10px;align-items:center;padding:6px 0;border-bottom:1px solid #171f27;font-size:13px}
.otdrow .pj{color:#7fd4ff;font-weight:600}
.otdbar{height:6px;border-radius:4px;background:#1b2530;overflow:hidden;margin-top:3px}
.otdbar i{display:block;height:100%;background:linear-gradient(90deg,#5ac8fa,#4cd964)}
.card.omega h2{color:#c9a6e6}
.card.omega .off{color:#ffcc00;font-size:13px}
.agsrc{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0 8px}
.agsrc .chip{background:#12211a;border:1px solid #24503a;border-radius:7px;padding:4px 9px;font-size:12px;color:#8fe6b5}
.agsrc .chip b{color:#4cd964}
.agfeed{font-family:ui-monospace,monospace;font-size:11px;line-height:1.55;max-height:132px;overflow:hidden}
.agfeed .l{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;opacity:.9}
.agfeed .l .s{color:#7fd4ff}.agfeed .l .n{color:#9aa7b3}.agfeed .l .ok{color:#4cd964}
.card.jlinux{border-color:#2a3a4a}.card.jlinux h2{color:#8fb8d6}
.card.github{border-color:#3a3140}.card.github h2{color:#d6a8e0}
.ghrow{display:flex;justify-content:space-between;gap:8px;align-items:center;padding:6px 0;border-bottom:1px solid #171f27;font-size:13px}
.ghrow:last-child{border:0}.ghrow a{color:#7fd4ff;text-decoration:none;font-weight:600}
.ghrow a:hover{text-decoration:underline}.ghrow .cm{color:#9aa7b3;font-size:12px}
</style></head><body>
<h1>🧠 JARVIS — Ce que le système fait <span id=clk class=next></span></h1>
<div class=sub>Planning temps réel dynamique · auto-déclencheur · rafraîchi 5s · 0-token</div>
<div class=banner><span class=cd id=cd>--:--</span><span class=nx id=nx>prochain auto-déclenchement…</span><span class=flash id=flash></span></div>
<div class=trg id=trg></div>
<div class=kpi id=kpi></div>
<div class="card agents"><h2>🤖 Agents mobilisés <span id=agtot class=next></span></h2>
 <div class=agsrc id=agsrc></div>
 <div class=agfeed id=agfeed></div></div>
<div class="card omega"><h2>🏛 OMEGA Mairie — courrier administratif <span id=omst class=next></span></h2>
 <div class=kpi id=omkpi></div>
 <div class=t id=omag></div></div>
<div class="card otd"><h2>🗂 OMEGA Todolist — cascade 4 projets Bureau <span id=otdst class=next></span></h2>
 <div id=otd></div></div>
<div class=gpubar id=gpu></div>
<div id="desktop-apps-card" class="card" style="border-color:#5ac8fa;grid-column:1 / -1"><h2>🚀 Applications du Bureau (GNOME) <span class=next>· Accès Direct</span></h2>
 <div class=t style="margin-bottom:8px">Lanceurs d'applications intégrés au widget bureau</div>
 <div id="desktop-apps" style="display:flex;gap:10px;flex-wrap:wrap"></div></div>
<div class=grid>
 <div class=card><h2>⏰ Planifiées (timers)</h2><div id=timers></div></div>
 <div class=card><h2>📋 En file (pending)</h2><div id=pending></div></div>
 <div class=card><h2>✅ Faites récemment</h2><div id=done></div></div>
</div>
<div id="jarvis-linux-card" class="card jlinux"><h2>🐧 JARVIS Linux — système <span id=jlst class=next></span></h2>
 <div class=t id=jlenv style="margin-bottom:6px"></div>
 <div class=t>Serveurs MCP</div>
 <div class=agsrc id=jlmods></div>
 <div class=t style="margin-top:6px">Timers (jarvis · mail · prospection · mirra)</div>
 <div id=jltimers></div></div>
<div id="github-card" class="card github"><h2>🐙 GitHub — depots Turbo31150 <span id=ghst class=next></span></h2>
 <div class=t id=gherr style="margin-bottom:6px"></div>
 <div id=ghrepos></div></div>
<div id="creations-card" class="card"><h2>🏗️ Créations — logiciels · outils · sites <span id=crst class=next></span></h2>
 <div class=t id=crkinds style="margin-bottom:6px"></div>
 <div class=t style="margin-top:2px">Contexte déjà capturé (équipe · série · cible) — clic = copier la commande</div>
 <div id=crtop></div></div>
<div id="dominos-card" class="card dominos"><h2>🁣 Dominos — actions lançables <span id=dmst class=next></span></h2>
 <div class=t id=dmdanger style="margin-bottom:6px"></div>
 <div style="margin:4px 0 6px">
   <button id=dmauto onclick=toggleAuto() style="cursor:pointer;background:#1c3a2a;color:#7fe3a2;border:1px solid #2e6b47;border-radius:6px;padding:3px 10px;font-size:12px">▶ AUTO</button>
   <span class=muted id=dmautost>arrêté</span></div>
 <div class=t style="margin-top:2px">Actions — clic = aperçu dry-run (aucun effet)</div>
 <div id=dmtop></div>
 <div class=t style="margin-top:6px">Flux (dry-run, alimenté en continu)</div>
 <pre id=dmfeed style="max-height:150px;overflow:auto;font-size:10px;line-height:1.3;background:#0d1116;padding:6px;border-radius:6px;white-space:pre-wrap"></pre></div>
<div id="live-terminal-card" class="card" style="border-color:#7fe3a2;grid-column:1 / -1"><h2>💻 Terminal Web Live — Logs d'exécution système <span class=next>· 0-Token</span></h2>
  <div class=t style="margin-bottom:6px">Flux de commandes système et sorties en direct du Cluster JARVIS-OMEGA</div>
  <pre id=termfeed style="max-height:180px;overflow:auto;font-size:11px;line-height:1.4;background:#090d12;color:#7fe3a2;padding:10px;border-radius:8px;font-family:monospace;white-space:pre-wrap;border:1px solid #1c3a2a">[SYSTEM] Initialisation du Terminal Web Live JARVIS-OMEGA...
[SYS-OPS] ✅ Cluster LLM M1/M4/OL1 connecté sur port 8899
[JARVIS-OMEGA] 🚀 11 349 Dominos prêts et synchronisés.</pre></div>
<div id="chrono-card" class="card chrono"><h2>🕰 Chronologie — reports datés <span id=chst class=next></span></h2>
 <div class=t id=chrange style="margin-bottom:6px"></div>
 <div class=t style="margin-top:2px">Timeline récente</div>
 <div id=chtl></div></div>
<div id="prod-card" class="card prod"><h2>🏭 Production — tâches FAITES <span id=prst class=next></span></h2>
 <div class=t id=prkpi style="margin-bottom:6px"></div>
 <div class=t style="margin-top:2px">Derniers livrables (vérifiés)</div>
 <div id=prrecent></div></div>
<div class="card strat"><h2>🧭 Stratégie — tous secteurs (carte Kompa)</h2>
 <div class=t id=stratmeta></div><div id=strat></div></div>
<div class="card n8n"><h2>🔌 n8n — commandes auto-déclenchées (workflows)</h2>
 <div class=kpi id=nkpi></div>
 <div class=t style="margin-top:6px">⚙️ Workflows actifs — déclencheur · cadence</div>
 <div id=nworkflows style="max-height:190px;overflow-y:auto"></div>
 <div class=t style="margin-top:6px">Dernières exécutions</div>
 <div id=nrecent></div></div>
<div class="card route"><h2>🔀 Routage — canaux de sortie (LLM cascade)</h2>
 <div class=kpi id=rkpi></div>
 <div class=grid style="grid-template-columns:1fr 1fr">
  <div><div class=t style="margin-bottom:6px">Canaux servis (backend ← volume · latence)</div><div id=chans></div></div>
  <div><div class=t style="margin-bottom:6px">Dernières routes (via → served)</div><div id=rroutes></div></div>
 </div></div>
<div class="card hist"><h2>📜 Historique d'exécution — durée &amp; score</h2>
 <div class="hrow hd"><span>#</span><span>tâche</span><span class=ag>agent</span><span class=dur>durée</span><span>score</span></div>
 <div id=hist></div></div>
<div class="card jlinux"><h2>🐧 JARVIS Linux — orchestrateur &amp; vagues</h2>
 <div class=kpi id=jlkpi></div>
 <div id=jlwaves></div></div>
<script>
function esc(s){return (s||'').replace(/[<>&]/g,c=>({'<':'&lt;','>':'&gt;','&':'&amp;'}[c]))}
// parse "1h 5min 20s" / "1min 58s" / "20s" -> secondes
function parseLeft(s){let t=0;(s||'').replace(/(\\d+)\\s*h/,(_,n)=>t+=n*3600);
 (s||'').replace(/(\\d+)\\s*min/,(_,n)=>t+=n*60);(s||'').replace(/(\\d+)\\s*s/,(_,n)=>t+=+n);return t;}
let CD={sec:0,unit:''};
function cdTick(){ // compte à rebours à la seconde
 const el=document.getElementById('cd');
 if(CD.sec>0){CD.sec--; const m=Math.floor(CD.sec/60),s=CD.sec%60;
  el.textContent=(m<10?'0':'')+m+':'+(s<10?'0':'')+s;
  document.getElementById('nx').innerHTML='prochain auto-déclenchement : <b>'+esc(CD.unit)+'</b>';}
}
setInterval(cdTick,1000);
// boutons déclencheurs (liste blanche)
const TRG=[
 ['jarvis-task-auto','▶ exécuter file','Exécute les tâches en attente dans la file (service jarvis-task-auto)'],
 ['task-autogen','▶ régénérer todo','Régénère la todolist dynamique depuis les sources (incidents santé, projets Bureau)'],
 ['biblio-filler','▶ remplir biblio','Remplissage 0-token de la Bibliothèque Vivante : commandes + fiches (LM Studio M1)'],
 ['biblio-web-cascade','▶ web-cascade','Enrichit la bibliothèque via cascade web (recherche + ingestion de contenu)'],
 ['biblio-vectorize','▶ vectoriser','Vectorise les fiches de connaissance (embeddings nomic) pour la recherche sémantique'],
 ['prospect-drain','✉ envoyer lot (40)','Envoie un lot de 40 mails de prospection déjà validés (~15 min)'],
 ['prospect-snapshot','📊 snapshot campagne','Instantané chiffré de la campagne de prospection'],
 ['prospect-rank','📈 secteurs demande','Classe les secteurs par demande (analyse du CRM)'],
 ['omega-start','🏛 démarrer OMEGA Mairie','Démarre OMEGA Mairie : courrier administratif (API :8140)'],
 ['backup-now','💾 backup maintenant','Snapshot immédiat des bases SQLite + PostgreSQL (rotation 24 versions)'],
 ['autoheal','🔧 auto-réparer','Détecte et répare les services en échec, mounts morts, nœuds hors ligne'],
 ['biblio-health','🩺 santé biblio','Vérifie intégrité et fraîcheur de la Bibliothèque Vivante'],
 ['reports-reindex','🗂 indexer reports','Réindexe les 4180 reports Turbo31150 dans la bibliothèque-routeur (auto toutes les 6h)'],
 ['planning-autogen','🧩 générer todolist','ÉNORME todolist unifiée 0-token : backlog business P0/P1 (facturation/prospection/infra/mirra/github) + incidents + TODO code + projets Bureau + git + heavy-tasks, préchargée biblio. Recharge à chaque drain (auto 3h)'],
 ['passcerfa-start','📄 PassCerfa (:3099)','Démarre / relance le service PassCerfa CERFA (port 3099)']];
async function fire(u){const f=document.getElementById('flash');f.textContent='⏳ '+u;
 try{const r=await (await fetch('/trigger?unit='+u,{method:'POST'})).json();
  f.textContent=(r.ok?'✅ ':'❌ ')+u+' — '+r.msg;}catch(e){f.textContent='❌ '+u;}
 setTimeout(()=>f.textContent='',5000);setTimeout(tick,800);}
document.getElementById('trg').innerHTML=
 `<button title="Chat IA branché sur le hub LLM de l'écosystème (cascade failover)" `
 +`onclick="location.href='/chat'" style="border-color:#5ac8fa;color:#5ac8fa">&#129504; JARVIS AI</button>`
 +TRG.map(([u,l,d])=>`<button title="${d}" onclick="fire('${u}')">${l}</button>`).join('');
async function refreshJarvisLinuxCard(){
 try{const d=await (await fetch('/api/jarvis-linux')).json();
  document.getElementById('jlst').textContent=`· ${d.modules_count||0} MCP · ${(d.timers_raw||[]).length} timers`;
  document.getElementById('jlenv').innerHTML= d.env_configured
   ? '<span class=done>✓ .env configuré</span> <span class=muted>(~/.config/jarvis)</span>'
   : '<span class=pend>⚠ .env absent</span>';
  document.getElementById('jlmods').innerHTML=(d.modules||[]).map(m=>
   `<span class=chip>${esc(m)}</span>`).join('')||'<span class=muted>aucun module MCP</span>';
  document.getElementById('jltimers').innerHTML=(d.timers_raw||[]).slice(0,6).map(t=>
   `<div class=row><span class=t>${esc(t.slice(0,64))}</span></div>`).join('')||'<div class=muted>aucun timer jarvis</div>';
 }catch(e){}
}
async function refreshGitHubCard(){
 try{const d=await (await fetch('/api/github')).json();
  const repos=d.repos||[]; const errs=d.errors||[];
  document.getElementById('ghst').textContent=`· ${repos.length} depots`+(d.owner?` · ${esc(d.owner)}`:'');
  document.getElementById('gherr').innerHTML= errs.length
   ? `<span class=pend>⚠ ${esc(errs.slice(0,2).join(' · '))}</span>` : '';
  document.getElementById('ghrepos').innerHTML=repos.length?repos.map(r=>{
    const msg=esc((r.last_commit_msg||'').slice(0,52));
    const dt=esc((r.last_commit_date||'').slice(0,10));
    const iss=(+r.open_issues||0);
    const nm=esc(r.name||'?'); const url=esc(r.url||'#');
    return `<div class=ghrow><span><a href="${url}" target=_blank>${nm}</a>`+
     `<div class=cm>${msg} <span class=muted>· ${dt}</span></div></span>`+
     `<span class="tag ${iss>0?'pend':''}">${iss} issue${iss>1?'s':''}/PR</span></div>`;
   }).join(''):'<div class=muted>aucun depot</div>';
 }catch(e){}
}
async function tick(){
 try{const d=await (await fetch('/data')).json();
  const c=d.counts||{};const u=d.unified||{};
  const fmtN=n=>(+n||0).toLocaleString('fr-FR');
   document.getElementById('kpi').innerHTML=
    `<div><div class="big done" style="color:#ffcc00">${fmtN(c.done||0)}</div><small>🚀 tâches réalisées</small></div>`+
    `<div><div class="big done" style="color:#5ac8fa">${fmtN(d.done_verified||0)}</div><small>✅ artefacts vérifiés</small></div>`+
    `<div><div class="big done" style="color:#7fe3a2">${fmtN(d.domino_chains_count||0)}</div><small>🁣 chaînes dominos</small></div>`+
    `<div><div class="big done" style="color:#c9a0ff">${fmtN(d.domino_triggers_count||0)}</div><small>⚡ déclenchements dominos</small></div>`+
    `<div><div class="big done">${fmtN(u.done_1h||0)}</div><small>⚡ faites / h</small></div>`+
    `<div><div class="big pend">${fmtN(c.pending||0)}</div><small>file vive (pending)</small></div>`+
    `<div><div class="big next">${fmtN(u.total||0)}</div><small>backlog unifié</small></div>`+
    `<div><div class="big pend">${fmtN(u.todo||0)}</div><small>à faire (P0:${u.p0||0} P1:${u.p1||0})</small></div>`+
    `<div><div class="big" style="color:#ff9500">${fmtN(c.to_validate||0)}</div><small>à valider</small></div>`+
    `<div><div class="big" style="color:#ff3b30">${fmtN((c.running||0)+(c.error||0))}</div><small>en cours / échec</small></div>`+
    `<div><div class="big ana">${fmtN(c.analyzed||0)}</div><small>analysées</small></div>`+
    `<div><div class=big style="color:#e0b878">${fmtN(d.results_files||0)}</div><small>📦 livrables prod</small></div>`+
    `<div><div class=big>${fmtN((d.timers||[]).length)}</div><small>timers actifs</small></div>`+
    // Souveraineté : vert seulement si AUCUNE violation. Un compteur qui
    // resterait vert avec des violations serait un faux vert de plus.
    (()=>{const f=d.frontieres||{},g=f.guard,cx=f.connecteurs;
      if(!g&&!cx) return '';
      const nv=(g&&g.violations||[]).length, ok=g&&g.ok&&nv===0;
      return (g?`<div><div class="big" style="color:${ok?'#7fe3a2':'#ff3b30'}">${ok?'A0–A5':nv}</div>`+
        `<small>${ok?'🛡️ frontières OK':'⚠️ violation(s) frontière'}</small></div>`:'')+
        (cx?`<div><div class=big style="color:#5ac8fa">${fmtN(cx.disponibles||0)}/${fmtN(cx.total||0)}</div>`+
        `<small>🔌 connecteurs actifs</small></div>`:'');})();
  document.getElementById('gpu').innerHTML=(d.gpu||[]).map(g=>
   `<div class=gpu><div class=nm>GPU${g.idx} ${esc(g.name)}</div>`+
   `<b class=${g.state}>${g.temp}°C</b> <span class=nm>fan ${g.fan}% · ${g.util}%</span></div>`).join('')||'';
  // panneau agents mobilisés
  const ag=d.agents||{};
  document.getElementById('agtot').textContent=
   `${ag.indexed||0} indexés · ${ag.all_layers||0} couches · ${ag.omega||0} OMEGA`;
  document.getElementById('agsrc').innerHTML=(ag.by_source||[]).map(([s,n])=>
   `<span class=chip>${esc(s)} <b>${n}</b></span>`).join('');
  // feed défilant : fenêtre glissante sur l'échantillon (tourne à chaque tick)
  const sm=ag.sample||[]; if(sm.length){const off=(Math.floor(Date.now()/5000))%sm.length;
   const win=[]; for(let i=0;i<10;i++)win.push(sm[(off+i)%sm.length]);
   document.getElementById('agfeed').innerHTML=win.map(a=>
    `<div class=l><span class=s>▶ ${esc(a.source)}</span> <span class=n>${esc(a.name)}</span> ${esc(a.desc)} <span class=ok>✓</span></div>`).join('');}
  // panneau OMEGA Mairie (courrier administratif)
  const om=d.omega||{};
  if(om.online){
   document.getElementById('omst').textContent='· en ligne :8140';
   document.getElementById('omkpi').innerHTML=
    `<div><div class=big>${om.processed||0}</div><small>mails traités</small></div>`+
    `<div><div class="big pend">${om.needs_review||0}</div><small>à valider</small></div>`+
    `<div><div class="big done">${om.approved||0}</div><small>approuvés</small></div>`+
    `<div><div class=big>${om.auto_rate||0}%</div><small>taux auto</small></div>`+
    `<div><div class="big ana">${om.queue||0}</div><small>en file</small></div>`;
   const a=om.agents||{};
   document.getElementById('omag').innerHTML=
    `M1 analyses <b>${(a.m1_analyseur||{}).analyses||0}</b> · `+
    `M2 triés <b>${(a.m2_detecteur||{}).processed||0}</b> · `+
    `M3 validés <b>${(a.m3_validateur||{}).validated||0}</b> · alertes <b>${om.alerts||0}</b>`;
  }else{
   document.getElementById('omst').textContent='';
   document.getElementById('omkpi').innerHTML='';
   document.getElementById('omag').innerHTML='<span class=off>⏸ hors ligne — bouton « 🏛 démarrer OMEGA Mairie » ci-dessus</span>';
  }
  // panneau OMEGA Todolist (cascade 4 projets Bureau)
  const otd=d.omega_todolist||[];
  const tot=otd.reduce((s,p)=>s+p.total,0);
  document.getElementById('otdst').textContent=tot?`· ${tot} tâches / ${otd.length} projets`:'';
  document.getElementById('otd').innerHTML=otd.length?otd.map(p=>{
    const pct=p.total?Math.round(100*p.done/p.total):0;
    return `<div class=otdrow><span class=pj>${esc(p.project)}`+
     `<div class=otdbar><i style="width:${pct}%"></i></div></span>`+
     `<span class="tag pend">${p.pending}⏳</span>`+
     `<span class="tag done">${p.done}✓</span>`+
     `<span class=t>⚡${p.preloaded} préch.</span></div>`;}).join('')
   :'<div class=muted>aucune tâche cascade — lancer omega-cascade.sh --mode validated</div>';
  // prochain auto-déclenchement = timer au 'left' le plus court
  let soon=null;(d.timers||[]).forEach(t=>{const s=parseLeft(t.left);
   if(s>0&&(!soon||s<soon.s))soon={s,unit:t.unit+' → '+(t.activates||'')};});
  if(soon){CD.sec=soon.s;CD.unit=soon.unit;}
  document.getElementById('timers').innerHTML=(d.timers||[]).slice(0,14).map(t=>
   `<div class=row><span>${esc(t.unit)}</span><span class=next>${esc(t.left)}</span></div>`).join('')||'<div class=muted>aucun</div>';
  document.getElementById('pending').innerHTML=
   (d.by_domain||[]).map(([k,v])=>`<div class=row><span>${esc(k)}</span><span class="tag pend">${v}</span></div>`).join('')
   +(d.pending||[]).slice(0,6).map(p=>{
     const m=(p.context||'').match(/▶ (.+)$/);
     // affiché == copié (pas de troncature) → évite tout mismatch clipboard/display (paste-jacking)
     const cmdtxt=(m?m[1]:'');
     const cmd=m?`<div style="font-family:monospace;font-size:11px;color:#5ac8fa;cursor:pointer;padding:2px 0 4px 14px;white-space:normal;word-break:break-all" title="cliquer pour copier la commande" data-cmd="${esc(cmdtxt).replace(/"/g,'&quot;')}" onclick="navigator.clipboard&&navigator.clipboard.writeText(this.dataset.cmd)">▶ ${esc(cmdtxt)}</div>`:'';
     return `<div class=row><span class=t>#${p.id} ${esc((p.title||'').slice(0,34))}</span></div>${cmd}`;
   }).join('')
   ||'<div class=muted>file vide</div>';
  // ── Créations (plan.source='creation', pack de contexte prérempli) ──
  const CR=d.creations||{};
  document.getElementById('crst').textContent=`· ${CR.total||0} à produire`;
  document.getElementById('crkinds').innerHTML=(CR.par_kind||[])
   .map(([k,v])=>`<span class=chip>${esc(k)} ${v}</span>`).join(' ')||'<span class=muted>—</span>';
  document.getElementById('crtop').innerHTML=(CR.top||[]).map(x=>{
    const meta=[x.agent?'👥 '+x.agent:'',x.serie?'🏆 '+x.serie:'',
                x.cible?'📁 '+x.cible.split('/').pop():'',
                x.etapes?x.etapes+' étapes':'',
                'ctx '+(x.couverture||0)+'/4'].filter(Boolean).join(' · ');
    // affiché == copié : pas de troncature de la commande (anti paste-jacking)
    const cmd=x.cmd?`<div style="font-family:monospace;font-size:11px;color:#5ac8fa;cursor:pointer;padding:2px 0 4px 14px;white-space:normal;word-break:break-all" title="cliquer pour copier" data-cmd="${esc(x.cmd).replace(/"/g,'&quot;')}" onclick="navigator.clipboard&&navigator.clipboard.writeText(this.dataset.cmd)">▶ ${esc(x.cmd)}</div>`:'';
    return `<div class=row><span class=t>${esc(x.kind||'?')} · ${esc((x.titre||'').slice(0,44))}</span></div>`+
           `<div class="t muted" style="padding-left:14px;font-size:10px">${esc(meta)}</div>${cmd}`;
  }).join('')||'<div class=muted>aucune création en file</div>';
  document.getElementById('done').innerHTML=(d.recent_done||[]).map(r=>
   `<div class=row><span class=t>#${r.id} ${esc((r.title||'').slice(0,32))}</span>`+
   `<span class="tag ${r.status=='done'?'done':'ana'}">${r.status}</span></div>`).join('')||'<div class=muted>aucune</div>';
  // ── Stratégie tous secteurs (carte Kompa) ──
  const S=d.strategie||{};
  if(S.secteurs){
   const mx=Math.max(1,...S.secteurs.map(x=>x.n));
   document.getElementById('stratmeta').textContent=`${S.total} outils · ${S.n} secteurs`;
   document.getElementById('strat').innerHTML=S.secteurs.map(s=>{
    const w=Math.round(100*s.n/mx);
    return `<div class=row><span class=t>${esc(s.nom)}</span>`+
     `<span style="display:flex;align-items:center;gap:6px"><span class=sc style="width:70px"><i style="width:${w}%"></i></span>`+
     `<span class=next>${s.n}</span></span></div>`;}).join('');
  }
  // ── n8n : commandes auto-déclenchées ──
  const N=d.n8n||{};
  if(N.total!==undefined){
   document.getElementById('nkpi').innerHTML=
    `<div><div class="big ana">${N.active||0}</div><small>actifs / ${N.total}</small></div>`+
    `<div><div class="big done">${N.day_ok||0}</div><small>ok (24h)</small></div>`+
    `<div><div class="big ${N.day_ko>0?'pend':''}">${N.day_ko||0}</div><small>erreurs (24h)</small></div>`;
   document.getElementById('nworkflows').innerHTML=(N.workflows||[]).map(w=>
    `<div class=row><span class=t>${w.ic} ${esc(w.nm)}</span>`+
    `<span class=next>${esc(w.cad)}</span></div>`).join('')||'<div class=muted>aucun workflow actif</div>';
   document.getElementById('nrecent').innerHTML=(N.recent||[]).map(r=>
    `<div class=row><span class=t>${esc(r.nm)}</span>`+
    `<span><span class="${r.s=='success'?'done':'pend'}">${r.s=='success'?'✓':'✗'}</span> `+
    `<span class=t>${esc(r.t)}</span></span></div>`).join('')||'<div class=muted>aucune exécution</div>';
  }
  // ── Routage / canaux de sortie ──
  const R=d.routing||{channels:[],recent:[],total:0,fallback_rate:0};
  const fmtMs=m=>{m=+m||0;return m>=1000?(m/1000).toFixed(1)+'s':m+'ms';};
  document.getElementById('rkpi').innerHTML=
   `<div><div class=big>${R.total}</div><small>routes (fenêtre)</small></div>`+
   `<div><div class="big ${R.fallback_rate>20?'pend':'done'}">${R.fallback_rate}%</div><small>fallback</small></div>`+
   `<div><div class=big>${(R.channels||[]).length}</div><small>canaux actifs</small></div>`;
  document.getElementById('chans').innerHTML=(R.channels||[]).map(c=>
   `<div class=row><span class=t>${esc(c.served)}</span>`+
   `<span><span class=tag>${c.n}</span> <span class=next>${fmtMs(c.med_ms)}</span>`+
   `${c.ko?` <span class="tag pend">${c.ko}✗</span>`:''}</span></div>`).join('')||'<div class=muted>aucune route</div>';
  document.getElementById('rroutes').innerHTML=(R.recent||[]).map(r=>
   `<div class=row><span class=t>${esc(r.via)} → ${esc((r.served||'').split('/').slice(0,2).join('/'))}</span>`+
   `<span><span class="${r.ok?'done':'pend'}">${r.ok?'✓':'✗'}</span> <span class=next>${fmtMs(r.ms)}</span>`+
   `${r.tried?` <span class=tag>+${r.tried}</span>`:''}</span></div>`).join('')||'<div class=muted>—</div>';
  const fmtD=s=>{s=+s||0;return s>=3600?(s/3600).toFixed(1)+'h':s>=60?Math.round(s/60)+'min':s+'s';};
  const JL=d.jlinux||{};
  document.getElementById('jlkpi').innerHTML=
   `<div><div class="big done">${JL.modules||0}</div><small>modules /${JL.modules_total||7}</small></div>`+
   `<div><div class=big>${JL.mcp||0}</div><small>MCP</small></div>`+
   `<div><div class="big ${JL.env?'done':'pend'}">${JL.env?'✓':'✗'}</div><small>.env</small></div>`;
  document.getElementById('jlwaves').innerHTML=(JL.waves||[]).map(w=>
   `<div class=row><span class=t>${w.a?'🟢':'⚪'} ${esc(w.n)}</span><span class=next>${esc(w.nx)}</span></div>`).join('')||'<div class=muted>—</div>';
  document.getElementById('hist').innerHTML=(d.history||[]).map(h=>{
   const sc=Math.max(0,Math.min(100,Math.round((+h.score||0)*100)));
   return `<div class=hrow><span class=t>#${h.id}</span>`+
    `<span class=t>${esc((h.title||'').slice(0,44))}</span>`+
    `<span class="t ag">${esc(h.agent||'—')}</span>`+
    `<span class=dur>${fmtD(h.dur)}</span>`+
    `<span class=sc><i style="width:${sc}%"></i></span></div>`;}).join('')||'<div class=muted>aucune exécution</div>';
 }catch(e){}
 refreshJarvisLinuxCard();
 refreshGitHubCard();
 refreshDominosCard();
 refreshChronoCard();
 refreshProdCard();
 document.getElementById('clk').textContent='· '+new Date().toLocaleTimeString('fr-FR');
}
async function refreshProdCard(){
 try{const d=await (await fetch('/api/production')).json();
  document.getElementById('prst').textContent=`· ${d.done||0} faites`;
  document.getElementById('prkpi').innerHTML=
   `<span class=chip style="color:#7fe3a2">✅ done ${d.done||0}</span> `+
   `<span class=chip>🔎 vues ${d.analyzed||0}</span> `+
   `<span class=chip style="color:#c9a0ff">🛠 à coder ${d.needs_impl||0}</span> `+
   `<span class=chip style="color:#ff9b9b">⏸ appro ${d.approval||0}</span> `+
   `<span class=chip>⛔ bloq ${d.blocked||0}</span>`;
  document.getElementById('prrecent').innerHTML=(d.recent||[]).map(x=>
   `<div class=row><span class=t>${esc((x.t||'').slice(0,42))}</span>`+
   `<span class="tag ${x.s==='done'?'done':''}">${esc(x.s||'')}</span></div>`).join('')||'<div class=muted>—</div>';
 }catch(e){}
}
async function refreshChronoCard(){
 try{const d=await (await fetch('/api/chronologie')).json();
  document.getElementById('chst').textContent=`· ${d.total||0} reports`;
  document.getElementById('chrange').innerHTML=(d.dmin&&d.dmax)
   ? `<span class=chip>${esc(d.dmin)}</span> → <span class=chip>${esc(d.dmax)}</span>` : '';
  document.getElementById('chtl').innerHTML=(d.recent||[]).map(x=>
   `<div class=row><span class=muted style="min-width:78px">${esc(x.date||'')}</span>`+
   `<span class=t>${esc((x.titre||'').slice(0,46))}</span></div>`).join('')||'<div class=muted>aucun report</div>';
 }catch(e){}
}
let _dmTop=[], _dmAll=[], _dmIdx=0, _dmRuns=0;
let _dmAuto=(localStorage.getItem('dmAuto')==='1');   // état MAINTENU (survit au refresh)
function applyAutoBtn(){
  const b=document.getElementById('dmauto'); if(!b) return;
  b.textContent=_dmAuto?'⏸ STOP':'▶ AUTO';
  b.style.background=_dmAuto?'#3a1c1c':'#1c3a2a'; b.style.color=_dmAuto?'#ff9b9b':'#7fe3a2';
  b.style.borderColor=_dmAuto?'#6b2e2e':'#2e6b47';
  const st=document.getElementById('dmautost');
  if(st) st.textContent=_dmAuto
    ?('en marche illimité — '+(_dmIdx% (_dmAll.length||1))+'/'+(_dmAll.length||'?')+' · '+_dmRuns+' aperçus')
    :'arrêté';
}
function toggleAuto(){ _dmAuto=!_dmAuto; localStorage.setItem('dmAuto',_dmAuto?'1':'0'); applyAutoBtn(); }
async function runDomino(slug){
  if(!slug) return;
  const feed=document.getElementById('dmfeed'); if(!feed) return;
  try{const d=await (await fetch('/run-domino?name='+encodeURIComponent(slug))).json();
    feed.textContent=('▶ '+slug+'\\n'+(d.out||'(vide)')+'\\n──────\\n'+feed.textContent).slice(0,6000);
  }catch(e){}
}
const DM_BATCH=6;                    // dominos dispatchés EN PARALLÈLE par tick
let _dmBusy=false;
async function autoTick(){           // boucle ILLIMITÉE, dispatch parallèle par lots
  if(!_dmAuto||!_dmAll.length||_dmBusy) return;
  _dmBusy=true;
  const batch=[];
  for(let i=0;i<DM_BATCH;i++) batch.push(_dmAll[_dmIdx++ % _dmAll.length]);
  applyAutoBtn();
  try{ await Promise.all(batch.map(s=>runDomino(s))); }  // concurrent (serveur multi-thread)
  finally{ _dmBusy=false; }
}
setInterval(autoTick,1500);
async function refreshDominosCard(){
 try{const d=await (await fetch('/api/dominos')).json();
  _dmTop=d.top||[]; if((d.slugs||[]).length) _dmAll=d.slugs; _dmRuns=d.runs||0;
  document.getElementById('dmst').textContent=`· ${d.total||0} dominos · ${_dmRuns} aperçus`;
  document.getElementById('dmdanger').innerHTML=
   `<span class=chip>🟢 ${d.vert||0}</span> <span class=chip>🟠 ${d.orange||0}</span> <span class=chip>🔴 ${d.rouge||0}</span>`;
  document.getElementById('dmtop').innerHTML=(d.top||[]).map(x=>
   `<div class=row style="cursor:pointer" title="clic = aperçu dry-run" onclick="runDomino('${esc(x.slug||'')}')">`+
   `<span class=t>▶ ${esc((x.titre||'').slice(0,40))}</span>`+
   `<code class=muted>${esc(x.cmd||'')}</code></div>`).join('')||'<div class=muted>aucun domino</div>';
  applyAutoBtn();
 }catch(e){}
}
tick();setInterval(tick,5000);
</script></body></html>"""


# Liste BLANCHE des déclencheurs manuels autorisés depuis le widget (sûrs, 0-token).
TRIGGERS = {
    "jarvis-task-auto": "jarvis-task-auto.service",
    "biblio-filler": "biblio-filler.service",
    "biblio-web-cascade": "biblio-web-cascade.service",
    "biblio-vectorize.service": "biblio-vectorize.service",
    "task-autogen": "task-autogen.service",
    "backup-now": "jarvis-backup-hourly.service",
    "autoheal": "jarvis-autoheal.service",
    "biblio-health": "biblio-health.service",
    "reports-reindex": "jarvis-reports-reindex.service",
    "passcerfa-start": "passcerfa-backend.service",
    "domino-autopilot": "jarvis-domino-autopilot.service",
    "prod-runner": "jarvis-prod-runner.service",
}

# Actions prospection (scripts figés, argv sans entrée utilisateur, lancés détachés).
_PROSPECT = os.path.expanduser("~/Documents/jarvis-commercial-2026/06-pipeline")
SCRIPTS = {
    "prospect-drain": ["bash", f"{_PROSPECT}/cron_drain_mails.sh"],
    "prospect-snapshot": [
        "python3",
        f"{_PROSPECT}/campaign_compile.py",
        "snapshot",
        "ALL",
    ],
    "prospect-rank": ["python3", f"{_PROSPECT}/campaign_compile.py", "rank"],
    "omega-start": ["bash", f"{OMEGA_DIR}/scripts/omega-widget-start.sh"],
}


def fire(key):
    """Déclenche une action de la liste blanche. Services = start oneshot ;
    scripts prospection = Popen détaché (drain long, ~15 min). Renvoie (ok, msg)."""
    unit = TRIGGERS.get(key)
    if unit:
        try:
            r = subprocess.run(
                ["systemctl", "--user", "start", unit],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return (r.returncode == 0), (r.stderr.strip() or "déclenché ✅")
        except Exception as e:
            return False, str(e)
    argv = SCRIPTS.get(key)
    if argv:
        try:
            subprocess.Popen(
                argv,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return True, "lancé en arrière-plan ✅"
        except Exception as e:
            return False, str(e)
    return False, "déclencheur non autorisé"


_ALLOWED_HOSTS = {f"127.0.0.1:{PORT}", f"localhost:{PORT}"}
_ALLOWED_ORIGINS = {f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}"}
# Accès distant via `tailscale serve` : le proxy présente le nom du tailnet en Host.
# Sans cette entrée, le contrôle same-origin refuserait toute action depuis le S9
# hors du réseau local (403). Le tailnet est authentifié, pas ouvert à l'Internet.
_TAILNET_HOST = os.environ.get("JARVIS_TAILNET_HOST", "").strip()
if _TAILNET_HOST:
    _ALLOWED_HOSTS |= {_TAILNET_HOST, f"{_TAILNET_HOST}:443"}
    _ALLOWED_ORIGINS |= {f"https://{_TAILNET_HOST}"}

# Hub LLM unifié de l'écosystème (cascade failover multi-backends).
HUB_URL = os.environ.get("JARVIS_HUB_URL", "http://127.0.0.1:18800")

# Outils IA du board — chaque mode est un system prompt appliqué au hub.
AI_MODES = {
    "chat": "Tu es JARVIS, l'assistant de Turbo. Réponds en français, de façon directe et concise.",
    "resume": "Résume le texte suivant en français, en 5 puces maximum. Va à l'essentiel.",
    "traduire": "Traduis le texte suivant en anglais. Rends uniquement la traduction, sans commentaire.",
    "reformuler": "Reformule le texte suivant en français, plus clair et plus professionnel. Rends uniquement le texte reformulé.",
    "code": "Tu es un développeur senior. Réponds en français avec du code correct et commenté sobrement.",
    "commande": "Traduis la demande en UNE commande shell Linux. Rends uniquement la commande, sans explication ni bloc de code.",
}


CHAT_HTML = """<!doctype html><html lang=fr><head><meta charset=utf-8>
<title>JARVIS AI</title>
<meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover">
<link rel="manifest" href="/manifest.json"><meta name="theme-color" content="#0b0e11">
<meta name="mobile-web-app-capable" content="yes">
<link rel="apple-touch-icon" href="/icon-192.png">
<style>
*{box-sizing:border-box;margin:0;font-family:'Segoe UI',system-ui,sans-serif}
body{background:#0b0e11;color:#dfe6ee;display:flex;flex-direction:column;height:100dvh}
header{padding:12px 14px;border-bottom:1px solid #1e2833;display:flex;align-items:center;gap:10px}
header h1{font-size:16px;color:#5ac8fa}
header .st{font-size:11px;color:#7a8894;margin-left:auto}
.modes{display:flex;gap:6px;overflow-x:auto;padding:10px 14px;border-bottom:1px solid #1e2833;scrollbar-width:none}
.modes::-webkit-scrollbar{display:none}
.mode{flex:0 0 auto;font-size:12px;padding:6px 12px;border-radius:20px;background:#12171d;
 border:1px solid #1e2833;color:#9fb0bf;cursor:pointer;white-space:nowrap}
.mode.on{background:#12303f;border-color:#5ac8fa;color:#5ac8fa}
#log{flex:1;overflow-y:auto;padding:14px;display:flex;flex-direction:column;gap:10px}
.msg{max-width:88%;padding:10px 13px;border-radius:12px;font-size:14px;line-height:1.5;white-space:pre-wrap;word-wrap:break-word}
.me{align-self:flex-end;background:#12303f;border:1px solid #24485c}
.ai{align-self:flex-start;background:#12171d;border:1px solid #1e2833}
.ai .src{display:block;font-size:10px;color:#7a8894;margin-top:8px;text-transform:uppercase;letter-spacing:.5px}
.err{align-self:flex-start;background:#2a1518;border:1px solid #5c2430;color:#ffb3bd}
form{display:flex;gap:8px;padding:12px 14px;border-top:1px solid #1e2833;padding-bottom:calc(12px + env(safe-area-inset-bottom))}
#q{flex:1;background:#12171d;border:1px solid #1e2833;border-radius:22px;padding:11px 16px;
 color:#dfe6ee;font-size:15px;outline:none}
#q:focus{border-color:#5ac8fa}
button{background:#5ac8fa;color:#05202b;border:0;border-radius:22px;padding:11px 20px;
 font-size:15px;font-weight:600;cursor:pointer}
button:disabled{opacity:.45}
a.back{color:#7a8894;text-decoration:none;font-size:20px}
</style></head><body>
<header><a class=back href="/">&#8592;</a><h1>JARVIS AI</h1><span class=st id=st>écosystème local</span></header>
<div class=modes id=modes></div>
<div id=log></div>
<form id=f><input id=q placeholder="Parler à JARVIS…" autocomplete=off>
<button id=b type=submit>&#9654;</button></form>
<script>
const MODES=[["chat","Chat"],["resume","Résumer"],["traduire","Traduire"],
             ["reformuler","Reformuler"],["code","Code"],["commande","Commande"]];
// ?m= vient des raccourcis (appui long sur l'icône) ; ?q=/?text= du partage Android.
const P=new URLSearchParams(location.search);
// Le mode vient de l'URL : on le valide contre la liste connue plutôt que de le
// relayer tel quel (le serveur retombe déjà sur "chat", on reste cohérent côté UI).
const KNOWN=["chat","resume","traduire","reformuler","code","commande"];
let mode=KNOWN.includes(P.get('m'))?P.get('m'):"chat";
const modesEl=document.getElementById('modes'), log=document.getElementById('log'),
      f=document.getElementById('f'), q=document.getElementById('q'),
      b=document.getElementById('b'), st=document.getElementById('st');
MODES.forEach(([k,label])=>{
  const d=document.createElement('div');
  d.className='mode'+(k===mode?' on':''); d.textContent=label; d.dataset.k=k;
  d.onclick=()=>{mode=k;[...modesEl.children].forEach(c=>c.classList.toggle('on',c.dataset.k===k));q.focus()};
  modesEl.appendChild(d);
});
function add(cls,txt,src){
  const d=document.createElement('div'); d.className='msg '+cls; d.textContent=txt;
  if(src){const s=document.createElement('span');s.className='src';s.textContent=src;d.appendChild(s)}
  log.appendChild(d); log.scrollTop=log.scrollHeight; return d;
}
f.onsubmit=async e=>{
  e.preventDefault();
  const text=q.value.trim(); if(!text) return;
  add('me',text); q.value=''; b.disabled=true;
  const wait=add('ai','…'); st.textContent='interrogation du cluster…';
  try{
    const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},
                                     body:JSON.stringify({message:text,mode:mode})});
    const j=await r.json();
    wait.remove();
    if(j.ok){ add('ai',j.reply,j.model||''); st.textContent=j.model||'écosystème local'; }
    else{ add('err',j.msg||'échec'); st.textContent='erreur'; }
  }catch(err){ wait.remove(); add('err','Hub injoignable : '+err.message); st.textContent='hors ligne'; }
  b.disabled=false; q.focus();
};
q.focus();
// Texte reçu du partage système : on PRÉ-REMPLIT seulement. Pas d'envoi
// automatique : l'URL est une entrée non fiable (n'importe quelle app ou page
// peut ouvrir /chat?q=…), et auto-soumettre ferait agir le board sans qu'aucun
// humain ne l'ait demandé. Un appui sur Envoyer reste le consentement.
const shared=(P.get('q')||P.get('text')||'').trim();
if(shared){
  q.value=(P.get('title')?P.get('title')+'\\n':'')+shared;
  b.textContent='Envoyer';           // cible large et explicite après un partage
  b.style.padding='11px 24px';
  b.focus();
}
</script></body></html>"""


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _same_origin(self):
        """Anti-CSRF / DNS-rebinding : /trigger a un effet de bord (start
        service). On exige un Host loopback exact (bloque le DNS rebinding, où
        le Host = domaine attaquant) et un Origin loopback si présent (bloque le
        POST cross-site depuis une page web ouverte dans le navigateur)."""
        host = self.headers.get("Host", "")
        origin = self.headers.get("Origin", "")
        if host not in _ALLOWED_HOSTS:
            return False
        if origin and origin not in _ALLOWED_ORIGINS:
            return False
        return True

    def do_POST(self):
        if self.path.startswith("/api/chat"):
            # Passerelle du board vers le hub LLM de l'écosystème. Le board ne
            # parle jamais à un backend précis : le hub gère la cascade et le
            # failover, donc le chat survit à la perte d'un modèle ou d'un nœud.
            if not self._same_origin():
                self.send_response(403)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"ok":false,"msg":"origine refusee"}')
                return
            try:
                length = int(self.headers.get("Content-Length", 0) or 0)
                payload = json.loads(self.rfile.read(length) or b"{}")
            except Exception:
                payload = {}
            message = (payload.get("message") or "").strip()
            mode = payload.get("mode") or "chat"
            system = AI_MODES.get(mode, AI_MODES["chat"])

            if not message:
                out, code = {"ok": False, "msg": "message vide"}, 400
            else:
                req = urllib.request.Request(
                    HUB_URL + "/v1/chat/completions",
                    data=json.dumps(
                        {
                            "model": "local",
                            "messages": [
                                {"role": "system", "content": system},
                                {"role": "user", "content": message},
                            ],
                            "max_tokens": 700,
                        }
                    ).encode(),
                    headers={"Content-Type": "application/json"},
                )
                try:
                    # Les modèles locaux démarrent à froid : une minute de marge
                    # évite de rendre une fausse panne au premier message.
                    with urllib.request.urlopen(req, timeout=120) as resp:
                        data = json.loads(resp.read())
                    msg = (data.get("choices") or [{}])[0].get("message", {}) or {}
                    reply = (msg.get("content") or "").strip()
                    if not reply:
                        # Les modèles à raisonnement (qwen3, qwen3.5) rangent tout
                        # dans reasoning_content et laissent content VIDE. Mesuré le
                        # 19/08 : qwen3-4b rend 0 caractère de contenu contre 677 de
                        # raisonnement. Sans ce repli le widget répondait ok=true avec
                        # une bulle vide — un faux succès parfaitement silencieux.
                        raw = (msg.get("reasoning_content") or "").strip()
                        reply = (
                            "[modèle à raisonnement — conclusion non émise, "
                            "réflexion brute ci-dessous]\n" + raw[-1200:]
                        ) if raw else ""
                    if not reply:
                        out = {"ok": False, "msg": f"hub {HUB_URL} : réponse vide"}
                        code = 502
                    else:
                        out = {"ok": True, "reply": reply, "model": data.get("model", "")}
                        code = 200
                except Exception as e:
                    out = {"ok": False, "msg": f"hub {HUB_URL} : {e}"}
                    code = 502

            body = json.dumps(out).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path.startswith("/api/execute") or self.path.startswith("/trigger"):
            from urllib.parse import urlparse, parse_qs

            if not self._same_origin():
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b'{"ok":false,"msg":"origine refusee"}')
                return
            qs = parse_qs(urlparse(self.path).query)
            key = qs.get("unit", [""])[0] or qs.get("action", [""])[0]
            title = (
                qs.get("title", [""])[0] or "Action déclenchée depuis Planning Widget"
            )
            agent = qs.get("agent", ["infra"])[0]

            # Injection de la tâche en production réelle dans jarvis_master.db
            try:
                # Seule écriture du widget : la base est en WAL (un seul
                # écrivain) et très sollicitée — il faut attendre le verrou
                # plutôt que perdre la tâche sur "database is locked".
                conn = sqlite3.connect(DB, timeout=120)
                conn.execute("PRAGMA busy_timeout=120000")
                conn.execute(
                    "INSERT INTO tasks (title, agent, machine, status, score) VALUES (?, ?, 'M1', 'pending', 100)",
                    (title, agent),
                )
                conn.commit()
                conn.close()
                # Déclencher immédiatement une passe du runner
                subprocess.Popen(
                    [
                        "python3",
                        os.path.expanduser("~/jarvis/scripts/jarvis-prod-runner.py"),
                        "--once",
                        "--limit",
                        "10",
                    ],
                    start_new_session=True,
                )
                msg = f"Tâche '{title}' injectée et lancée en production réelle ✅"
                ok = True
            except Exception as e:
                ok, msg = False, str(e)

            body = json.dumps({"ok": ok, "msg": msg}).encode()
            self.send_response(200 if ok else 500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/api/jarvis-linux"):
            body = json.dumps(jarvis_linux()).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
        elif self.path.startswith("/api/github"):
            try:
                payload = github_state()
            except Exception:
                payload = {"repos": [], "errors": ["exception github_state"]}
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
        elif self.path.startswith("/api/dominos"):
            try:
                payload = dominos_state()
            except Exception as e:
                payload = {"total": 0, "top": [], "err": str(e)}
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
        elif self.path.startswith("/run-domino"):
            # Dry-run SÛR uniquement (aucun effet). Nom validé + whitelist fichier.
            name = parse_qs(urlparse(self.path).query).get("name", [""])[0]
            body = json.dumps(domino_dryrun(name)).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
        elif self.path.startswith("/api/production"):
            try:
                payload = cached("prod", 6, production_state)
            except Exception:
                payload = {"done": 0, "recent": []}
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
        elif self.path.startswith("/api/chronologie"):
            try:
                payload = cached("chrono", 15, chronologie_state)
            except Exception:
                payload = {"total": 0, "recent": []}
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
        elif self.path.startswith("/data"):
            body = json.dumps(data()).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
        elif self.path.startswith("/chat"):
            body = CHAT_HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
        elif self.path.startswith("/manifest.json"):
            # PWA : rend le dashboard installable en plein écran sur le S9
            # (accès via adb reverse → 127.0.0.1:8899 côté téléphone).
            body = json.dumps(
                {
                    "name": "JARVIS OS",
                    "short_name": "JARVIS",
                    "description": "Planning temps réel et état du système JARVIS",
                    "start_url": "/",
                    "scope": "/",
                    "display": "standalone",
                    "orientation": "portrait",
                    "background_color": "#0b0e11",
                    "theme_color": "#0b0e11",
                    "icons": [
                        {
                            "src": "/icon-192.png",
                            "sizes": "192x192",
                            "type": "image/png",
                            "purpose": "any maskable",
                        },
                        {
                            "src": "/icon-512.png",
                            "sizes": "512x512",
                            "type": "image/png",
                            "purpose": "any maskable",
                        },
                    ],
                    # Appui long sur l'icône → accès direct à un mode IA.
                    "shortcuts": [
                        {
                            "name": "Chat JARVIS",
                            "short_name": "Chat",
                            "url": "/chat?m=chat",
                            "icons": [{"src": "/icon-192.png", "sizes": "192x192"}],
                        },
                        {
                            "name": "Résumer",
                            "short_name": "Résumer",
                            "url": "/chat?m=resume",
                            "icons": [{"src": "/icon-192.png", "sizes": "192x192"}],
                        },
                        {
                            "name": "Traduire",
                            "short_name": "Traduire",
                            "url": "/chat?m=traduire",
                            "icons": [{"src": "/icon-192.png", "sizes": "192x192"}],
                        },
                        {
                            "name": "Commande shell",
                            "short_name": "Shell",
                            "url": "/chat?m=commande",
                            "icons": [{"src": "/icon-192.png", "sizes": "192x192"}],
                        },
                    ],
                    # Fait apparaître JARVIS AI dans le menu Partager d'Android :
                    # sélectionner du texte dans n'importe quelle app → Partager → JARVIS AI.
                    "share_target": {
                        "action": "/chat",
                        "method": "GET",
                        "params": {"title": "title", "text": "q", "url": "q"},
                    },
                }
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/manifest+json")
        elif self.path.startswith("/icon-"):
            name = os.path.basename(urlparse(self.path).path)
            icon = os.path.join(PWA_DIR, name)
            # os.path.basename neutralise toute traversée de chemin ; on vérifie
            # en plus que le fichier existe bien dans le dossier PWA.
            if (
                name.startswith("icon-")
                and name.endswith(".png")
                and os.path.isfile(icon)
            ):
                with open(icon, "rb") as fh:
                    body = fh.read()
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Cache-Control", "max-age=86400")
            else:
                body = b"not found"
                self.send_response(404)
                self.send_header("Content-Type", "text/plain")
        else:
            body = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Serveur MULTI-THREAD : traite les requêtes /run-domino en parallèle
    (dispatch concurrent) au lieu de les sérialiser. daemon_threads = pas de
    thread zombie à l'arrêt."""

    daemon_threads = True
    allow_reuse_address = True


def _selfcheck_js():
    """Défense en profondeur : le HTML embarque du JS dans une string Python triple-quote.
    Un escape mal protégé ('\\n' au lieu de '\\\\n') casse tout le script (SyntaxError) →
    widget vide. Ce garde-fou node-check le JS SERVI au démarrage et alerte BRUYAMMENT
    (au lieu d'un widget silencieusement vide). Optionnel : ignoré si node absent."""
    import re
    import shutil
    import subprocess
    import tempfile

    node = shutil.which("node")
    if not node:
        return
    m = re.search(r"<script>(.*)</script>", HTML, re.S)
    if not m:
        return
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(m.group(1))
        path = f.name
    try:
        r = subprocess.run(
            [node, "--check", path], capture_output=True, text=True, timeout=10
        )
        if r.returncode != 0:
            err = (r.stderr or "").strip().splitlines()
            print(
                "[planning-widget] ⚠️ JS SERVI INVALIDE (le widget s'affichera SANS valeurs) :\n  "
                + "\n  ".join(err[:4]),
                flush=True,
            )
        else:
            print("[planning-widget] ✓ auto-check JS servi : valide", flush=True)
    except Exception:
        pass
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass


if __name__ == "__main__":
    _selfcheck_js()
    with ThreadedServer(("127.0.0.1", PORT), H) as s:
        print(
            f"[planning-widget] http://127.0.0.1:{PORT}  (multi-thread, Ctrl+C pour arrêter)",
            flush=True,
        )
        s.serve_forever()
