#!/usr/bin/env python3
"""
JARVIS Master CLI — TodoList dynamique + keyword→action dispatcher
Agent: OMEGA-DEV / JARVIS Cluster
DB: /home/pamerys/jarvis/jarvis_master.db
"""

import argparse
import sqlite3
import subprocess
import sys
import os
import time

# ── Task Metrics ──────────────────────────────────────────────────────────────
import importlib.util as _ilu
import pathlib as _pl


def _load_task_metrics():
    spec = _ilu.spec_from_file_location(
        "task_metrics",
        _pl.Path("/home/turbo/jarvis/monitoring/task_metrics.py"),
    )
    if spec is None:
        raise ImportError("Cannot locate task_metrics.py")
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


DB_PATH = "/home/pamerys/jarvis/jarvis_master.db"
LM_ASK = os.path.expanduser("~/.local/bin/claudelm")
CASCADE_PY = "/home/turbo/jarvis/cli/cascade.py"


def _load_audit_cmd():
    spec = _ilu.spec_from_file_location(
        "audit_commands",
        _pl.Path(__file__).resolve().parent / "audit_commands.py",
    )
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.cmd_audit


cmd_audit = _load_audit_cmd()

# ---------------------------------------------------------------------------
# DB Bootstrap
# ---------------------------------------------------------------------------


def get_db():
    # WAL : un seul écrivain à la fois sur une base très sollicitée,
    # il faut attendre au lieu d'échouer sur "database is locked".
    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.execute("PRAGMA busy_timeout=120000")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS tasks (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      parent_id INTEGER,
      title TEXT,
      context TEXT,
      status TEXT DEFAULT 'pending',
      progress INTEGER DEFAULT 0,
      agent TEXT,
      machine TEXT,
      score REAL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS keyword_actions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      keyword TEXT,
      context TEXT,
      action TEXT,
      agent TEXT,
      tools TEXT,
      priority INTEGER DEFAULT 5,
      usage_count INTEGER DEFAULT 0,
      score REAL DEFAULT 0.0,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS pipeline_log (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      task_id INTEGER,
      step TEXT,
      machine TEXT,
      model TEXT,
      input_tokens INTEGER,
      output_tokens INTEGER,
      latency_ms INTEGER,
      quality_score REAL,
      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS tool_map (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT UNIQUE,
      category TEXT,
      loader TEXT,
      keywords TEXT,
      triggers TEXT,
      memory_kb INTEGER DEFAULT 0,
      priority INTEGER DEFAULT 5,
      loaded INTEGER DEFAULT 0,
      last_used TEXT,
      usage_count INTEGER DEFAULT 0
    );
    CREATE INDEX IF NOT EXISTS idx_tool_keywords ON tool_map(keywords);
    CREATE INDEX IF NOT EXISTS idx_tool_category ON tool_map(category);
    """)
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Keyword matching
# ---------------------------------------------------------------------------


def match_keyword(title: str, conn) -> dict | None:
    """Return best matching keyword_action row for a task title."""
    rows = conn.execute(
        "SELECT * FROM keyword_actions ORDER BY priority DESC, score DESC"
    ).fetchall()
    title_lower = title.lower()
    for row in rows:
        if row["keyword"] in title_lower:
            return dict(row)
    return None


def detect_agent_for_title(title: str, conn) -> tuple[str, str]:
    """Return (agent, machine) based on keyword mapping."""
    match = match_keyword(title, conn)
    if match:
        return match["agent"] or "omega-dev-agent", match.get("machine", "M1") or "M1"
    # default
    return "omega-dev-agent", "M1"


# ---------------------------------------------------------------------------
# Sub-task generation via local LLM
# ---------------------------------------------------------------------------


def generate_subtasks(title: str, context: str) -> list[str]:
    """Ask local LLM to decompose a task into subtasks."""
    prompt = (
        f"Decompose this JARVIS task into 3-5 concrete subtasks (one per line, no numbering):\n"
        f"Task: {title}\nContext: {context or 'none'}\n"
        f"Output ONLY the subtask lines, nothing else."
    )
    try:
        result = subprocess.run(
            ["claudelm", "--no-system", prompt],
            capture_output=True,
            text=True,
            timeout=30,
        )
        lines = [l.strip() for l in result.stdout.strip().splitlines() if l.strip()]
        # Filter out lines that look like LLM noise
        lines = [l.lstrip("-•* ") for l in lines if len(l) > 5][:5]
        return lines
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Commands — Tasks
# ---------------------------------------------------------------------------


def cmd_task_add(args, conn):
    title = args.text
    context = getattr(args, "context", None) or ""
    agent, machine = detect_agent_for_title(title, conn)

    c = conn.cursor()
    c.execute(
        "INSERT INTO tasks (title, context, agent, machine) VALUES (?,?,?,?)",
        (title, context, agent, machine),
    )
    task_id = c.lastrowid

    # Bump usage count for matched keyword
    match = match_keyword(title, conn)
    if match:
        conn.execute(
            "UPDATE keyword_actions SET usage_count = usage_count + 1 WHERE id = ?",
            (match["id"],),
        )

    conn.commit()
    print(f"[+] Task #{task_id} created → agent:{agent} machine:{machine}")

    # Generate subtasks
    subtasks = generate_subtasks(title, context)
    if subtasks:
        print(f"    Subtasks generated ({len(subtasks)}):")
        for st in subtasks:
            c.execute(
                "INSERT INTO tasks (parent_id, title, agent, machine) VALUES (?,?,?,?)",
                (task_id, st, agent, machine),
            )
            sub_id = c.lastrowid
            print(f"      #{sub_id} {st}")
        conn.commit()
    else:
        print("    [LLM unavailable] No subtasks generated.")


def cmd_task_list(__, conn):
    rows = conn.execute(
        "SELECT id, parent_id, title, status, progress, agent, machine, score FROM tasks ORDER BY id"
    ).fetchall()
    if not rows:
        print("No tasks.")
        return

    BAR_WIDTH = 20

    def bar(pct):
        filled = int(BAR_WIDTH * pct / 100)
        return "[" + "#" * filled + "-" * (BAR_WIDTH - filled) + f"] {pct:3d}%"

    STATUS_COLOR = {
        "pending": "\033[33m",
        "running": "\033[36m",
        "done": "\033[32m",
        "failed": "\033[31m",
    }
    RESET = "\033[0m"

    print(
        f"{'ID':>4}  {'PAR':>4}  {'STATUS':8}  {'PROG':26}  {'AGENT':20}  {'MCH':4}  {'SCORE':5}  TITLE"
    )
    print("-" * 120)
    for r in rows:
        indent = "  " if r["parent_id"] else ""
        sc = r["score"]
        score_str = f"{sc:.1f}" if sc is not None else "  -  "
        color = STATUS_COLOR.get(r["status"], "")
        print(
            f"{r['id']:>4}  {str(r['parent_id'] or ''):>4}  "
            f"{color}{r['status']:8}{RESET}  {bar(r['progress'] or 0)}  "
            f"{(r['agent'] or ''):20}  {(r['machine'] or ''):4}  "
            f"{score_str:5}  {indent}{r['title']}"
        )


def cmd_task_run(args, conn):
    task_id = args.id
    row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    if not row:
        print(f"Task #{task_id} not found.")
        return

    title = row["title"]
    agent = row["agent"] or "omega-dev-agent"
    machine = row["machine"] or "M1"

    print(f"[RUN] Task #{task_id}: {title}")
    print(f"      Agent: {agent} | Machine: {machine}")

    # Update status
    conn.execute(
        "UPDATE tasks SET status='running', updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (task_id,),
    )
    conn.commit()

    # Dispatch decision: large tasks → M2 decomposition hint
    # Heuristic: if subtasks exist, it's "large"
    subtask_count = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE parent_id=?", (task_id,)
    ).fetchone()[0]

    if subtask_count > 0:
        target_machine = "M2"
        print(
            f"      [dispatch] Large task ({subtask_count} subtasks) → {target_machine} decomposition"
        )
    else:
        target_machine = machine

    # Log pipeline step
    # ── Métriques avant ───────────────────────────────────────────────────────
    _tm = None
    _snap_before = None
    try:
        _tm = _load_task_metrics()
        _snap_before = _tm.snapshot_before(task_id)
        print(
            f"      [metrics] before — CPU:{_snap_before['cpu_percent']}% RAM:{_snap_before['ram_mb']}MB VRAM:{_snap_before['vram_mb']}MB"
        )
    except Exception as _e:
        print(f"      [metrics] snapshot_before error: {_e}")
    t_start = time.time()
    # Simulate dispatch (real integration point for OpenClaw)
    prompt = f"Execute JARVIS task via agent {agent}: {title}"
    try:
        result = subprocess.run(
            ["claudelm", "--no-system", prompt],
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = result.stdout.strip()
        latency = int((time.time() - t_start) * 1000)
        # Naive quality score: length-based placeholder
        quality = min(1.0, len(output) / 500.0)
        conn.execute(
            "UPDATE tasks SET status='done', progress=100, score=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (round(quality * 10, 2), task_id),
        )
        conn.execute(
            """INSERT INTO pipeline_log (task_id, step, machine, model, latency_ms, quality_score)
               VALUES (?,?,?,?,?,?)""",
            (task_id, "dispatch+run", target_machine, "claudelm", latency, quality),
        )
        conn.commit()
        print(f"      [done] latency={latency}ms score={quality:.2f}")
        # ── Métriques après ─────────────────────────────────────────────────
        if _tm:
            try:
                _tm.snapshot_after(task_id, "claudelm", latency, _snap_before)
            except Exception as _e:
                print(f"      [metrics] snapshot_after error: {_e}")
        if output:
            print(f"\n--- Output ---\n{output[:1000]}\n---")
    except subprocess.TimeoutExpired:
        conn.execute(
            "UPDATE tasks SET status='failed', updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (task_id,),
        )
        conn.commit()
        print("      [TIMEOUT] Task marked failed.")
    except Exception as e:
        print(f"      [ERROR] {e}")
        conn.execute(
            "UPDATE tasks SET status='failed', updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (task_id,),
        )
        conn.commit()


def cmd_task_score(args, conn):
    task_id = args.id
    row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    if not row:
        print(f"Task #{task_id} not found.")
        return

    logs = conn.execute(
        "SELECT * FROM pipeline_log WHERE task_id=? ORDER BY timestamp DESC LIMIT 5",
        (task_id,),
    ).fetchall()

    print(f"Task #{task_id}: {row['title']}")
    print(f"  Status  : {row['status']}")
    print(f"  Progress: {row['progress']}%")
    print(f"  Score   : {row['score']}")
    print(f"  Agent   : {row['agent']} @ {row['machine']}")
    if logs:
        print("  Pipeline log:")
        for lg in logs:
            print(
                f"    [{lg['timestamp']}] step={lg['step']} "
                f"machine={lg['machine']} latency={lg['latency_ms']}ms "
                f"quality={lg['quality_score']}"
            )
    else:
        print("  No pipeline logs.")


# ---------------------------------------------------------------------------
# Commands — Loop
# ---------------------------------------------------------------------------


def cmd_loop_start(_args, _conn):
    """Foreground monitoring loop — delegates to loop_monitor.py."""
    del _args, _conn
    monitor = "/home/turbo/jarvis/cli/loop_monitor.py"
    if not os.path.exists(monitor):
        print(f"Loop monitor not found at {monitor}")
        return
    print("[LOOP] Starting auto-monitoring loop (Ctrl-C to stop)...")
    os.execv(sys.executable, [sys.executable, monitor])


def cmd_loop_debug(_args, _conn):
    """Debug mode: show each loop step without actual dispatch."""
    del _args, _conn
    monitor = "/home/turbo/jarvis/cli/loop_monitor.py"
    print("[LOOP DEBUG] Starting in debug mode...")
    os.execv(sys.executable, [sys.executable, monitor, "--debug"])


# ---------------------------------------------------------------------------
# Commands — Scan
# ---------------------------------------------------------------------------


def cmd_scan(args, conn):
    """Read DB context, propose next tasks using LLM."""
    # Gather stats
    pending = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE status='pending'"
    ).fetchone()[0]
    running = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE status='running'"
    ).fetchone()[0]
    failed = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE status='failed'"
    ).fetchone()[0]
    done = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='done'").fetchone()[0]
    recent = conn.execute(
        "SELECT title, status FROM tasks ORDER BY updated_at DESC LIMIT 5"
    ).fetchall()

    recent_str = "\n".join(f"  - [{r['status']}] {r['title']}" for r in recent)
    top_keywords = conn.execute(
        "SELECT keyword, usage_count FROM keyword_actions ORDER BY usage_count DESC LIMIT 5"
    ).fetchall()
    kw_str = ", ".join(f"{k['keyword']}({k['usage_count']})" for k in top_keywords)

    context_summary = (
        f"JARVIS task DB state:\n"
        f"  pending={pending} running={running} done={done} failed={failed}\n"
        f"Recent tasks:\n{recent_str}\n"
        f"Top keywords: {kw_str}"
    )

    print("[SCAN] Cluster context:")
    print(context_summary)

    prompt = (
        f"{context_summary}\n\n"
        f"Based on this JARVIS cluster state, suggest 3 high-priority next actions "
        f"the operator should run. Be specific, use JARVIS commands."
    )

    print("\n[SCAN] Querying LLM for suggestions...")
    try:
        result = subprocess.run(
            ["claudelm", "--no-system", prompt],
            capture_output=True,
            text=True,
            timeout=30,
        )
        suggestions = result.stdout.strip()
        if suggestions:
            print("\n[Suggestions]")
            print(suggestions)
        else:
            print("[LLM] No suggestions returned.")
    except Exception as e:
        print(f"[LLM error] {e}")


# ---------------------------------------------------------------------------
# Commands — Cascade / Tools
# ---------------------------------------------------------------------------


def _get_engine():
    """Lazy import CascadeEngine — only when cascade commands are used."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("cascade", CASCADE_PY)
    if spec is None:
        raise ImportError(f"Cannot locate cascade module at {CASCADE_PY}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.CascadeEngine(DB_PATH)


def cmd_cascade(args, _conn):
    """jarvis cascade <query> — resolve → plan → execute en cascade."""
    query = " ".join(args.query)
    engine = _get_engine()

    # 3s countdown so operator can Ctrl-C
    plan = engine.plan(query)
    if not plan:
        print("[cascade] No matching tools found for query.")
        return

    engine._print_plan(plan, dry_run=False)
    print("[cascade] Starting in 3s — Ctrl-C to abort...")
    try:
        for i in (3, 2, 1):
            print(f"  {i}...", end=" ", flush=True)
            time.sleep(1)
        print()
    except KeyboardInterrupt:
        print("\n[cascade] Aborted.")
        return

    engine.execute(plan, dry_run=False, query=query)


def cmd_plan(args, _conn):
    """jarvis plan <query> — affiche le plan domino sans exécuter (dry-run)."""
    query = " ".join(args.query)
    engine = _get_engine()
    engine.avalanche(query, dry_run=True)


def cmd_tools_list(_args, conn):
    """jarvis tools list — liste tous les outils mappés."""
    rows = conn.execute(
        "SELECT category, name, priority, usage_count, last_used FROM tool_map ORDER BY category, priority DESC, name"
    ).fetchall()
    if not rows:
        print("tool_map is empty. Run: python3 /home/turbo/jarvis/cli/seed_tools.py")
        return

    cur_cat = None
    for r in rows:
        if r["category"] != cur_cat:
            cur_cat = r["category"]
            print(f"\n  [{cur_cat.upper()}]")
        used = r["last_used"] or "never"
        print(
            f"    {r['name']:50}  pri={r['priority']}  uses={r['usage_count']}  last={used}"
        )

    total = len(rows)
    print(f"\n  Total: {total} tools")


def cmd_tools_find(args, conn):
    """jarvis tools find <term> — cherche dans tool_map."""
    term = " ".join(args.term)
    rows = conn.execute(
        """SELECT name, category, loader, keywords, priority
           FROM tool_map
           WHERE name LIKE ? OR keywords LIKE ? OR loader LIKE ?
           ORDER BY priority DESC, name
           LIMIT 30""",
        (f"%{term}%", f"%{term}%", f"%{term}%"),
    ).fetchall()
    if not rows:
        print(f"No tools matching '{term}'.")
        return
    print(f"  Found {len(rows)} tool(s) matching '{term}':")
    for r in rows:
        print(f"    [{r['category']:8}] {r['name']:45}  pri={r['priority']}")
        print(f"             loader  : {r['loader']}")
        print(f"             keywords: {r['keywords']}")


def cmd_tools_stats(_args, conn):
    """jarvis tools stats — top 10 par usage + résumé par catégorie."""
    # Per-category count
    cats = conn.execute(
        "SELECT category, COUNT(*) as n FROM tool_map GROUP BY category ORDER BY n DESC"
    ).fetchall()
    print("  By category:")
    total = 0
    for c in cats:
        print(f"    {c['category']:12}  {c['n']:>4}")
        total += c["n"]
    print(f"    {'TOTAL':12}  {total:>4}")

    # Top 10 by usage
    top = conn.execute(
        """SELECT name, category, usage_count, last_used
           FROM tool_map
           ORDER BY usage_count DESC, last_used DESC
           LIMIT 10"""
    ).fetchall()
    print("\n  Top 10 by usage:")
    for r in top:
        used = r["last_used"] or "never"
        print(
            f"    [{r['category']:8}] {r['name']:45}  uses={r['usage_count']}  last={used}"
        )


# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------


def seed_keyword_actions(conn):
    """Insert initial keyword→action mappings if table is empty."""
    count = conn.execute("SELECT COUNT(*) FROM keyword_actions").fetchone()[0]
    if count > 0:
        return

    mappings = [
        (
            "monitor",
            "cluster health check",
            "check cluster health",
            "cowork-monitoring",
            None,
            8,
        ),
        ("deploy", "service deployment", "deploy service", "cowork-system", None, 8),
        (
            "code",
            "feature implementation",
            "implement feature",
            "omega-dev-agent",
            None,
            7,
        ),
        ("debug", "issue debugging", "debug issue", "omega-dev-agent", None, 7),
        ("trading", "market analysis", "analyze market", "trading-engine", None, 9),
        ("whisper", "audio transcription", "run whisper", "voice-engine", None, 6),
        (
            "transcription",
            "audio transcription",
            "run whisper",
            "voice-engine",
            None,
            6,
        ),
        ("backup", "data backup", "run backup", "maintenance", None, 7),
        ("gpu", "GPU allocation check", "check GPU allocation", "cluster-mgr", None, 8),
        ("vram", "VRAM monitoring", "check GPU allocation", "cluster-mgr", None, 8),
        ("agent", "agent management", "manage agents", "core-agents", None, 6),
        ("pipeline", "task routing", "route task", "dispatch", None, 7),
        ("linux", "linux system operations", "sys operation", "cowork-linux", None, 6),
        ("system", "system operations", "sys operation", "cowork-linux", None, 6),
        ("sql", "database query", "query/manage DB", "data-pipeline", None, 6),
        (
            "database",
            "database management",
            "query/manage DB",
            "data-pipeline",
            None,
            6,
        ),
        (
            "antigravity",
            "antigravity app connection",
            "connect antigravity app",
            "omega-dev-agent",
            None,
            5,
        ),
        (
            "loop",
            "monitoring loop",
            "start monitoring loop",
            "omega-dev-agent",
            None,
            5,
        ),
        (
            "scoring",
            "quality scoring",
            "run quality scoring on last result",
            "omega-dev-agent",
            None,
            5,
        ),
    ]

    conn.executemany(
        """INSERT INTO keyword_actions
           (keyword, context, action, agent, tools, priority)
           VALUES (?,?,?,?,?,?)""",
        mappings,
    )
    conn.commit()
    print(f"[SEED] Inserted {len(mappings)} keyword→action mappings.")


def seed_test_tasks(conn):
    """Insert 3 example tasks for validation."""
    count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    if count > 0:
        return

    tasks = [
        (
            "Monitor cluster GPU usage on M1 and M2",
            "Daily health check",
            "cluster-mgr",
            "M1",
        ),
        (
            "Deploy whisper transcription service",
            "Voice pipeline",
            "voice-engine",
            "M2",
        ),
        (
            "Debug SQLite bridge connection timeout",
            "Data pipeline ops",
            "omega-dev-agent",
            "M1",
        ),
    ]
    for title, ctx, agent, machine in tasks:
        conn.execute(
            "INSERT INTO tasks (title, context, agent, machine) VALUES (?,?,?,?)",
            (title, ctx, agent, machine),
        )
    conn.commit()
    print("[SEED] Inserted 3 example tasks.")


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

# Sub-commands that are "known" — anything else triggers avalanche
KNOWN_CMDS = {
    "task",
    "loop",
    "scan",
    "seed",
    "cascade",
    "plan",
    "tools",
    "audit",
}


def main():
    init_db()
    conn = get_db()
    seed_keyword_actions(conn)

    # ── Single-pass avalanche: jarvis <free text> ──────────────────────────
    # Detect when first arg is not a known sub-command → cascade.avalanche
    if (
        len(sys.argv) > 1
        and sys.argv[1] not in KNOWN_CMDS
        and not sys.argv[1].startswith("-")
    ):
        free_query = " ".join(sys.argv[1:])
        engine = _get_engine()
        plan = engine.plan(free_query)
        if plan:
            engine._print_plan(plan, dry_run=False)
            print("[cascade] Executing in 3s — Ctrl-C to abort...")
            try:
                for i in (3, 2, 1):
                    print(f"  {i}...", end=" ", flush=True)
                    time.sleep(1)
                print()
                engine.execute(plan, dry_run=False, query=free_query)
            except KeyboardInterrupt:
                print("\n[cascade] Aborted.")
        else:
            print(
                f"[jarvis] No tools matched '{free_query}'. Try: jarvis tools find <term>"
            )
        conn.close()
        return

    parser = argparse.ArgumentParser(
        prog="jarvis", description="JARVIS Master CLI — dynamic task orchestration"
    )
    sub = parser.add_subparsers(dest="cmd")

    # jarvis task <sub>
    task_p = sub.add_parser("task", help="Task management")
    task_sub = task_p.add_subparsers(dest="task_cmd")

    t_add = task_sub.add_parser("add", help="Add a task")
    t_add.add_argument("text", help="Task title")
    t_add.add_argument("--context", "-c", default="", help="Optional context")

    _t_list = task_sub.add_parser("list", help="List all tasks")

    t_run = task_sub.add_parser("run", help="Run a task by ID")
    t_run.add_argument("id", type=int, help="Task ID")

    t_score = task_sub.add_parser("score", help="Show task quality score")
    t_score.add_argument("id", type=int, help="Task ID")

    # jarvis loop <sub>
    loop_p = sub.add_parser("loop", help="Loop monitoring")
    loop_sub = loop_p.add_subparsers(dest="loop_cmd")
    loop_sub.add_parser("start", help="Start auto-monitoring loop")
    loop_sub.add_parser("debug", help="Debug mode loop")

    # jarvis scan
    sub.add_parser("scan", help="Scan context and propose next tasks")

    # jarvis seed (hidden utility)
    sub.add_parser("seed", help="Insert seed test data")

    # jarvis cascade <query>
    cascade_p = sub.add_parser("cascade", help="Resolve + execute cascade domino")
    cascade_p.add_argument("query", nargs="+", help="Free-text query")

    # jarvis plan <query>
    plan_p = sub.add_parser("plan", help="Show domino plan without executing (dry-run)")
    plan_p.add_argument("query", nargs="+", help="Free-text query")

    # jarvis tools <sub>
    tools_p = sub.add_parser("tools", help="Tool registry management")
    tools_sub = tools_p.add_subparsers(dest="tools_cmd")
    tools_sub.add_parser("list", help="List all mapped tools")
    tools_find_p = tools_sub.add_parser("find", help="Search tool_map")
    tools_find_p.add_argument("term", nargs="+", help="Search term")
    tools_sub.add_parser("stats", help="Top 10 by usage + category stats")

    # jarvis audit <sub> — MODE AUDIT / DEEP RESEARCH
    audit_p = sub.add_parser(
        "audit", help="Mode audit / deep research (cascade multi-agents)"
    )
    audit_sub = audit_p.add_subparsers(dest="audit_cmd")
    for _sc in (
        "run",
        "init",
        "scan-local",
        "scan-web",
        "multi-agents",
        "report",
        "todo",
        "cascade",
    ):
        _ap = audit_sub.add_parser(_sc, help=f"audit phase: {_sc}")
        _ap.add_argument("--target", default=".", help="Dossier à auditer")
        _ap.add_argument("--topic", default="", help="Sujet de l'audit")
        _ap.add_argument(
            "--profile",
            default="full",
            choices=["tech", "business", "souverainete", "full"],
        )
        _ap.add_argument(
            "--mode", default="standard", choices=["fast", "standard", "deep"]
        )
        _ap.add_argument("--client", default="", help="Nom/id client")
        _ap.add_argument("--previous", default="", help="Rapport précédent (cascade)")
        _ap.add_argument(
            "--real-agents",
            action="store_true",
            help="Dispatcher les vrais sous-agents + consensus",
        )

    args = parser.parse_args()

    if args.cmd == "task":
        if args.task_cmd == "add":
            cmd_task_add(args, conn)
        elif args.task_cmd == "list":
            cmd_task_list(args, conn)
        elif args.task_cmd == "run":
            cmd_task_run(args, conn)
        elif args.task_cmd == "score":
            cmd_task_score(args, conn)
        else:
            task_p.print_help()

    elif args.cmd == "loop":
        if args.loop_cmd == "start":
            cmd_loop_start(args, conn)
        elif args.loop_cmd == "debug":
            cmd_loop_debug(args, conn)
        else:
            loop_p.print_help()

    elif args.cmd == "scan":
        cmd_scan(args, conn)

    elif args.cmd == "seed":
        seed_test_tasks(conn)

    elif args.cmd == "cascade":
        cmd_cascade(args, conn)

    elif args.cmd == "plan":
        cmd_plan(args, conn)

    elif args.cmd == "tools":
        if args.tools_cmd == "list":
            cmd_tools_list(args, conn)
        elif args.tools_cmd == "find":
            cmd_tools_find(args, conn)
        elif args.tools_cmd == "stats":
            cmd_tools_stats(args, conn)
        else:
            tools_p.print_help()

    elif args.cmd == "audit":
        cmd_audit(args, conn)

    else:
        parser.print_help()

    conn.close()


if __name__ == "__main__":
    main()
