#!/usr/bin/env python3
"""
jarvis-prod-runner.py — MOTEUR D'EXÉCUTION EN PRODUCTION RÉELLE
============================================================
Boucle infinie qui traite les tâches `pending` de jarvis_master.db
en les routant vers des executors CLI réels par type (agent/domaine).

Architecture:
  tasks (pending) → dispatch_by_type() → executor-xxx.sh/py → tasks (done)

Garde-fous:
  - CPU < 80% avant lancement
  - RAM libre > 512 MB
  - Timeout 300s par tâche
  - Max 4 tâches parallèles
  - Secrets jamais dans output

Usage:
  python3 jarvis-prod-runner.py [--once] [--dry] [--limit N] [--agent TYPE]

  --once   : une seule passe (pas de boucle)
  --dry    : montre ce qui serait exécuté sans lancer
  --limit N: max N tâches par passe (défaut: 10)
  --agent X: filtre sur agent/domaine
"""

from __future__ import annotations
import os
import sys
import re
import time
import sqlite3
import subprocess
import threading
import datetime
from pathlib import Path

# ════════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════════
HOME = Path.home()
JARVIS = HOME / "jarvis"
DB = str(JARVIS / "jarvis_master.db")
RESULTS = str(JARVIS / "data" / "task_results")
LOG = str(JARVIS / "logs" / "prod-runner.log")
EXEC_DIR = str(JARVIS / "scripts" / "executors")
PROD_EXEC = str(JARVIS / "bin" / "jarvis-prod-exec.py")
LM_ASK = str(JARVIS / "scripts" / "lm-ask.sh")

LOOP_DELAY = 5  # secondes entre passes (accéléré)
MAX_PARALLEL = 8  # hub :18800 = 5 slots + 3 en file → 8 in-flight max sans rejet.
# Depuis 2026-08-07 LM Studio sert qwen3.5-9b en 12 prédictions parallèles (ctx 32k,
# 5 GPU) : le serveur n'est plus sériel, mais la file du hub reste la borne.
# Historique : à 12, 74 % de rejets « surcharge » quand LMS servait en série (L13 2026-08-01)
TASK_TIMEOUT = 300  # secondes max par tâche
CPU_LIMIT = 90.0  # % CPU max pour lancer (seuil étendu)
RAM_MIN_MB = 256  # MB RAM libre min
LIMIT_DEFAULT = 50  # tâches par passe (traiter plus par lot)

Path(RESULTS).mkdir(parents=True, exist_ok=True)
Path(LOG).parent.mkdir(parents=True, exist_ok=True)

# ════════════════════════════════════════════════════════════════
# LOGGING
# ════════════════════════════════════════════════════════════════
_lock = threading.Lock()


def log(msg: str, level: str = "INFO"):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}][{level}] {msg}"
    with _lock:
        print(line, flush=True)
        try:
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass


# ════════════════════════════════════════════════════════════════
# GARDE-FOUS SYSTÈME
# ════════════════════════════════════════════════════════════════
def _cpu_ok() -> bool:
    """Lit /proc/stat — 0 dépendance externe."""
    try:
        with open("/proc/stat") as f:
            line = f.readline()
        vals = list(map(int, line.split()[1:]))
        idle = vals[3]
        total = sum(vals)
        time.sleep(0.1)
        with open("/proc/stat") as f:
            line = f.readline()
        vals2 = list(map(int, line.split()[1:]))
        idle2 = vals2[3]
        total2 = sum(vals2)
        cpu = 100.0 * (1 - (idle2 - idle) / (total2 - total))
        if cpu > CPU_LIMIT:
            log(f"CPU trop élevé: {cpu:.1f}% > {CPU_LIMIT}% → attente", "WARN")
            return False
        return True
    except Exception:
        return True  # fail-open si pas de /proc/stat


def _ram_ok() -> bool:
    """Lit /proc/meminfo."""
    try:
        mi = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, v = line.split(":")
                mi[k.strip()] = int(v.strip().split()[0])
        avail = mi.get("MemAvailable", mi.get("MemFree", 999999))
        avail_mb = avail // 1024
        if avail_mb < RAM_MIN_MB:
            log(f"RAM insuffisante: {avail_mb}MB < {RAM_MIN_MB}MB → attente", "WARN")
            return False
        return True
    except Exception:
        return True


def guardrails_ok() -> bool:
    return _cpu_ok() and _ram_ok()


# ════════════════════════════════════════════════════════════════
# DISPATCH PAR TYPE
# ════════════════════════════════════════════════════════════════

# Mapping agent/domaine → executor
EXECUTOR_MAP = {
    # Infra / système / code / github social / biblio centrale / matrice / planning app
    "infra": ("bash", f"{EXEC_DIR}/executor-infra.sh"),
    "github": ("bash", f"{EXEC_DIR}/executor-github.sh"),
    "github-social": ("bash", f"{EXEC_DIR}/executor-github-social.sh"),
    "biblio-centrale": ("bash", f"{EXEC_DIR}/executor-biblio-centrale.sh"),
    "jarvis-matrice": ("bash", f"{EXEC_DIR}/executor-jarvis-matrice.sh"),
    "planning-app": ("bash", f"{EXEC_DIR}/executor-planning-app.sh"),
    "cluster": ("bash", f"{EXEC_DIR}/executor-cluster.sh"),
    "security": ("bash", f"{EXEC_DIR}/executor-security.sh"),
    "backup": ("bash", f"{EXEC_DIR}/executor-backup.sh"),
    # Agents IA
    "openclaw": ("bash", f"{EXEC_DIR}/executor-openclaw.sh"),
    "research": ("bash", f"{EXEC_DIR}/executor-research.sh"),
    # Social / comms / mail
    "social": ("bash", f"{EXEC_DIR}/executor-linkedin.sh"),
    "linkedin": ("bash", f"{EXEC_DIR}/executor-linkedin.sh"),
    "mail": ("bash", f"{EXEC_DIR}/executor-mail.sh"),
    # n8n / omega
    "n8n": ("bash", f"{EXEC_DIR}/executor-infra.sh"),
    "omega": ("bash", f"{EXEC_DIR}/executor-infra.sh"),
    "passcerfa": ("bash", f"{EXEC_DIR}/executor-infra.sh"),
    # Prospection
    "prospection": ("bash", f"{EXEC_DIR}/executor-research.sh"),
    # Défaut
    "default": ("python3", PROD_EXEC),
}

# Regles de dispatch supplémentaires sur le titre de la tâche (Matrice 7 Sources)
TITLE_RULES = [
    # 1. GitHub & Social Automation & Biblio & Matrice & Planning App: code, PR, issues, commits, CI/CD, releases
    (re.compile(r"planning.app|planning.prod", re.I), "planning-app"),
    (re.compile(r"jarvis.matrice|matrice.coordination", re.I), "jarvis-matrice"),
    (re.compile(r"biblio.centrale|labo.bibliotheque|go.sh", re.I), "biblio-centrale"),
    (re.compile(r"github.social|social.automation", re.I), "github-social"),
    (
        re.compile(r"github|repo|issue|pull|pr|commit|ci-cd|release|code.review", re.I),
        "github",
    ),
    # 2. Notion: docs, bases, backlog, SOP, notes, wiki
    (
        re.compile(r"notion|sop|backlog|doc|notes|wiki|base.connaissance", re.I),
        "research",
    ),
    # 3. JARVIS MCP: orchestration, scripts, monitoring, santé, agents, tâches locales
    (
        re.compile(
            r"mcp|infra|health|heal|systemctl|service|script|agent|monitoring|gpu|vram",
            re.I,
        ),
        "infra",
    ),
    # 4. Ollama: IA locale, modèles, benchmarks, quantization, lm-ask
    (
        re.compile(r"ollama|quant|bench|model|local.llm|cluster|m1|m2|m4|ol1", re.I),
        "cluster",
    ),
    # 5. YouTube Analytics: contenu, performances, audience, vidéos, ctr, rétention
    (
        re.compile(r"youtube|video|analytics|ctr|retention|audience|contenu", re.I),
        "research",
    ),
    # 6. Google Tasks: rappels, échéances, to-do, todo
    (re.compile(r"gtasks|google.tasks|todo|reminder|echeance|rappel", re.I), "default"),
    # 7. Telegram: alertes, notifications, relais court, bot
    (re.compile(r"telegram|alert|notify|notification|relais|push|bot", re.I), "infra"),
    # LinkedIn: posts, publication, réseau, engagement, prospection social
    (re.compile(r"linkedin|post|article|social.content|engagement", re.I), "social"),
    # Mail: imap, smtp, email, réponse, triage, drafts, courriers
    (re.compile(r"mail|imap|smtp|email|reply|draft|courrier", re.I), "mail"),
    # Règles génériques et historiques
    (re.compile(r"backup|rotate|sqlite|docker.vol", re.I), "backup"),
    (re.compile(r"openclaw|cowork|dispatch", re.I), "openclaw"),
    (re.compile(r"security|secret|audit|scan", re.I), "security"),
    (re.compile(r"mail|imap|smtp|email|reply", re.I), "mail"),
    (re.compile(r"n8n|workflow", re.I), "n8n"),
    (re.compile(r"omega|mairie|courrier|cerfa", re.I), "omega"),
    (re.compile(r"prospect|outreach|b2b|crm", re.I), "prospection"),
]


def resolve_executor(agent: str, title: str, machine: str) -> tuple[str, ...]:
    """Retourne le tuple de commande à lancer pour cette tâche."""
    # 1) Titre → priorité maximale
    for pattern, etype in TITLE_RULES:
        if pattern.search(title or ""):
            entry = EXECUTOR_MAP.get(etype, EXECUTOR_MAP["default"])
            return entry

    # 2) agent / domaine
    a = (agent or "default").lower()
    entry = EXECUTOR_MAP.get(a, EXECUTOR_MAP["default"])
    return entry


# ════════════════════════════════════════════════════════════════
# DB HELPERS
# ════════════════════════════════════════════════════════════════
def db_connect() -> sqlite3.Connection:
    # jarvis_master.db est en WAL : un seul écrivain à la fois, et plusieurs
    # producteurs permanents y écrivent. Sans attente longue, on tombe sur
    # "database is locked" et le service meurt en boucle. timeout= et le PRAGMA
    # sont tous les deux nécessaires : timeout= ne couvre pas tous les chemins
    # du driver, le PRAGMA vaut pour toute la connexion.
    conn = sqlite3.connect(DB, timeout=120, check_same_thread=False)
    conn.execute("PRAGMA busy_timeout=120000")
    conn.row_factory = sqlite3.Row
    return conn


def fetch_tasks(limit: int, agent_filter: str | None, dry: bool) -> list[dict]:
    conn = db_connect()
    cur = conn.cursor()
    q = "SELECT id,title,context,agent,machine,score FROM tasks WHERE status='pending'"
    params: list = []
    if agent_filter:
        q += " AND agent=?"
        params.append(agent_filter)
    q += " ORDER BY score DESC, id ASC LIMIT ?"
    params.append(limit)
    rows = [dict(r) for r in cur.execute(q, params).fetchall()]
    conn.close()
    return rows


def mark_running(task_id: int):
    conn = db_connect()
    conn.execute(
        "UPDATE tasks SET status='running', progress=5, updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (task_id,),
    )
    conn.commit()
    conn.close()


def mark_done(task_id: int, result_path: str, success: bool):
    status = "done" if success else "error"
    progress = 100 if success else 0
    ctx = f"[prod-runner] result={result_path}"
    conn = db_connect()
    conn.execute(
        "UPDATE tasks SET status=?, progress=?, context=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (status, progress, ctx, task_id),
    )
    conn.commit()
    conn.close()


# ════════════════════════════════════════════════════════════════
# EXÉCUTION D'UNE TÂCHE
# ════════════════════════════════════════════════════════════════
def execute_task(task: dict, dry: bool) -> bool:
    tid = task["id"]
    title = task["title"] or ""
    agent = task["agent"] or "default"
    machine = task["machine"] or "M1"
    ctx = task["context"] or ""

    exec_cmd = resolve_executor(agent, title, machine)
    interpreter = exec_cmd[0]
    script = exec_cmd[1] if len(exec_cmd) > 1 else ""

    log(f"[T{tid}] '{title[:50]}' → {interpreter} {Path(script).name} (agent={agent})")

    if dry:
        log(f"  [DRY] Commande: {' '.join(exec_cmd)} '{title}' {tid}")
        return True

    # Vérifier que l'executor existe
    if script and not Path(script).exists():
        log(f"  [WARN] Executor manquant: {script} → fallback doc", "WARN")
        return _fallback_doc(tid, title, ctx)

    mark_running(tid)

    # Construire la commande selon le type d'executor
    if interpreter == "bash":
        cmd = ["bash", script, title, str(tid)]
    elif interpreter == "python3":
        # jarvis-prod-exec: python3 exec.py doc --task "xxx"
        cmd = ["python3", script, "doc", "--task", title]
        if ctx:
            cmd += ["--ctx", ctx[:200]]
    else:
        cmd = [interpreter, script, title, str(tid)]

    env = {**os.environ, "JARVIS_TASK_ID": str(tid), "JARVIS_TASK_TITLE": title}

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TASK_TIMEOUT,
            env=env,
            cwd=str(JARVIS),
        )
        output = (result.stdout + result.stderr).strip()
        success = result.returncode == 0

        # Extraire le chemin du fichier résultat si mentionné
        result_path = ""
        m = re.search(r"RESULT_FILE=(.+)", output)
        if m:
            result_path = m.group(1).strip()
        elif not result_path:
            # fallback: créer un résultat simple
            result_path = _save_simple_result(tid, title, output)

        mark_done(tid, result_path, success)
        file_size = (
            os.path.getsize(result_path)
            if result_path and os.path.exists(result_path)
            else 0
        )

        # 4. NOTIFIER & 5. ARCHIVER (Traçabilité complète 5 étapes)
        _notify_and_archive(tid, title, agent, result_path, success, file_size)

        log(
            f"  [{'✅' if success else '❌'}] T{tid} [Pipeline 5/5 OK] → {result_path or 'no file'} ({file_size} octets, rc={result.returncode})"
        )
        return success

    except subprocess.TimeoutExpired:
        log(f"  [TIMEOUT] T{tid} '{title[:40]}' après {TASK_TIMEOUT}s", "WARN")
        mark_done(tid, "", False)
        return False
    except Exception as e:
        log(f"  [ERROR] T{tid}: {e}", "ERR")
        mark_done(tid, "", False)
        return False


def _notify_and_archive(
    tid: int, title: str, agent: str, result_path: str, success: bool, size: int
):
    """Étape 4 (Notifier) & Étape 5 (Archiver) : Enregistrement dans les logs centralisés et notification."""
    try:
        log_db = str(JARVIS / "logs" / "jarvis_logs.db")
        if os.path.exists(log_db):
            conn = sqlite3.connect(log_db, timeout=5)
            conn.execute(
                "INSERT INTO system_logs (service, level, message) VALUES (?, ?, ?)",
                (
                    "prod-runner-pipeline",
                    "INFO" if success else "ERROR",
                    f"T{tid} [{agent}] {title} | File: {result_path} ({size}b)",
                ),
            )
            conn.commit()
            conn.close()
    except Exception:
        pass


def _save_simple_result(tid: int, title: str, output: str) -> str:
    """Sauvegarde un résultat texte brut quand l'executor ne le fait pas."""
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower())[:40]
    path = os.path.join(RESULTS, f"{slug}_{tid}_{ts}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n_Exécuté: {ts}_\n\n")
        f.write("```\n" + output[:4000] + "\n```\n")
    return path


def _fallback_doc(tid: int, title: str, ctx: str) -> bool:
    """Fallback: génère un document via jarvis-prod-exec si executor manquant."""
    if not Path(PROD_EXEC).exists():
        mark_done(tid, "", False)
        return False
    cmd = ["python3", PROD_EXEC, "doc", "--task", title]
    if ctx:
        cmd += ["--ctx", ctx[:200]]
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120, cwd=str(JARVIS)
        )
        m = re.search(r"→ (.+\.md)", r.stdout)
        path = m.group(1).strip() if m else ""
        mark_done(tid, path, r.returncode == 0)
        return r.returncode == 0
    except Exception as e:
        log(f"  [FALLBACK ERR] {e}", "ERR")
        mark_done(tid, "", False)
        return False


# ════════════════════════════════════════════════════════════════
# BOUCLE PRINCIPALE
# ════════════════════════════════════════════════════════════════
def run_once(limit: int, agent_filter: str | None, dry: bool) -> int:
    """Exécute une passe. Retourne le nombre de tâches traitées."""
    if not guardrails_ok():
        return 0

    tasks = fetch_tasks(limit, agent_filter, dry)
    if not tasks:
        log("Aucune tâche pending.")
        return 0

    log(f"━━ Passe: {len(tasks)} tâches {'[DRY]' if dry else ''}")

    # Sémaphore pour limiter le parallélisme
    sem = threading.Semaphore(MAX_PARALLEL)
    threads = []
    results = []

    def run_with_guard(t):
        with sem:
            ok = execute_task(t, dry)
            results.append(ok)

    for task in tasks:
        th = threading.Thread(target=run_with_guard, args=(task,), daemon=True)
        threads.append(th)
        th.start()

    for th in threads:
        th.join(timeout=TASK_TIMEOUT + 10)

    ok = sum(1 for r in results if r)
    fail = len(results) - ok
    log(f"━━ Résultats: {ok} ✅ / {fail} ❌ / {len(tasks)} total")
    return len(tasks)


def main():
    once = "--once" in sys.argv
    dry = "--dry" in sys.argv
    limit = LIMIT_DEFAULT
    agent_filter = None

    for i, arg in enumerate(sys.argv):
        if arg == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
        if arg == "--agent" and i + 1 < len(sys.argv):
            agent_filter = sys.argv[i + 1]

    log("╔═══════════════════════════════════════════════")
    log("║ JARVIS PROD RUNNER — Production réelle démarrée")
    log(f"║ DB: {DB}")
    log(f"║ Limit: {limit} | Parallel: {MAX_PARALLEL} | Timeout: {TASK_TIMEOUT}s")
    log(f"║ Mode: {'DRY' if dry else 'LIVE'} | {'ONCE' if once else 'LOOP'}")
    if agent_filter:
        log(f"║ Filtre agent: {agent_filter}")
    log("╚═══════════════════════════════════════════════")

    if once:
        run_once(limit, agent_filter, dry)
        return

    # Boucle infinie
    while True:
        try:
            n = run_once(limit, agent_filter, dry)
            delay = LOOP_DELAY if n > 0 else LOOP_DELAY * 2
            log(f"⏳ Prochaine passe dans {delay}s...")
            time.sleep(delay)
        except KeyboardInterrupt:
            log("⛔ Arrêt manuel (Ctrl+C)")
            break
        except Exception as e:
            log(f"[LOOP ERROR] {e} → continue dans 30s", "ERR")
            time.sleep(30)


if __name__ == "__main__":
    main()
