#!/usr/bin/env python3
"""
seed_tools.py — Peuple la table tool_map dans jarvis_master.db
Sources: skills Claude Code, agents OpenClaw, MCP servers, scripts jarvis, modèles LLM
"""

import json
import os
import re
import sqlite3
import subprocess
from pathlib import Path

DB_PATH = "/home/pamerys/jarvis/jarvis_master.db"
SETTINGS_PATH = os.path.expanduser("~/.claude/settings.json")
SKILLS_DIR = os.path.expanduser("~/.claude/skills")
JARVIS_CLI_DIR = "/home/pamerys/jarvis/cli"
JARVIS_SCRIPTS_DIR = "/home/pamerys/jarvis/scripts"
JARVIS_INFRA_DIR = "/home/pamerys/jarvis/infra"
JARVIS_MONITORING_DIR = "/home/pamerys/jarvis/monitoring"

M1_URL = "http://192.168.1.85:1234/v1/models"
M2_URL = "http://192.168.1.26:1234/v1/models"
OL1_URL = "http://127.0.0.1:11434"


# ── Schema ────────────────────────────────────────────────────────────────────

SCHEMA = """
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
"""


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


# ── Keyword auto-generation ───────────────────────────────────────────────────


def auto_keywords(name: str, extra: list[str] | None = None) -> str:
    """Split name on [-_./ ] lowercase → unique tokens → JSON array."""
    tokens = re.split(r"[-_./\s]+", name.lower())
    tokens = [t for t in tokens if len(t) > 1]
    if extra:
        tokens += [e.lower() for e in extra if e]
    seen = []
    for t in tokens:
        if t not in seen:
            seen.append(t)
    return json.dumps(seen)


# ── Upsert helper ─────────────────────────────────────────────────────────────


def upsert(
    conn, name, category, loader, keywords, triggers="[]", memory_kb=0, priority=5
):
    conn.execute(
        """INSERT INTO tool_map (name, category, loader, keywords, triggers, memory_kb, priority)
           VALUES (?,?,?,?,?,?,?)
           ON CONFLICT(name) DO UPDATE SET
             category=excluded.category,
             loader=excluded.loader,
             keywords=excluded.keywords,
             triggers=excluded.triggers,
             memory_kb=excluded.memory_kb,
             priority=excluded.priority""",
        (name, category, loader, keywords, triggers, memory_kb, priority),
    )


# ── Source 1 : Skills Claude Code ─────────────────────────────────────────────


def seed_skills(conn) -> int:
    count = 0
    skills_path = Path(SKILLS_DIR)
    if not skills_path.exists():
        print(f"  [skills] Directory not found: {SKILLS_DIR}")
        return 0

    for md in sorted(skills_path.glob("*.md")):
        if md.name.startswith("_"):
            continue
        skill_name = md.stem  # filename without .md
        loader = f"claude-code-skill:{skill_name}"
        kw = auto_keywords(skill_name)
        upsert(
            conn, f"skill:{skill_name}", "skill", loader, kw, memory_kb=64, priority=6
        )
        count += 1

    # Synthetic skill list for the 61 documented skills (when dir is pruned)
    KNOWN_SKILLS = [
        "code-review",
        "refactor",
        "tdd-unittest",
        "debug-trace",
        "sql-query",
        "api-design",
        "docker-compose",
        "k8s-deploy",
        "monitoring-setup",
        "log-analysis",
        "performance-profile",
        "security-audit",
        "data-pipeline",
        "ml-training",
        "data-viz",
        "whisper-transcription",
        "text-summarize",
        "json-extract",
        "regex-builder",
        "bash-automate",
        "git-workflow",
        "ci-cd-pipeline",
        "nginx-config",
        "ssl-cert",
        "backup-restore",
        "db-migrate",
        "schema-design",
        "redis-cache",
        "queue-worker",
        "websocket-server",
        "rest-client",
        "graphql-query",
        "oauth-flow",
        "jwt-auth",
        "rate-limiter",
        "cron-schedule",
        "alert-rule",
        "dashboard-build",
        "report-generate",
        "email-send",
        "telegram-bot",
        "discord-hook",
        "slack-notify",
        "pdf-parse",
        "csv-transform",
        "excel-export",
        "image-resize",
        "ffmpeg-convert",
        "audio-process",
        "voice-synthesis",
        "llm-prompt",
        "embedding-search",
        "rag-pipeline",
        "agent-spawn",
        "tool-chain",
        "cascade-engine",
        "workflow-dag",
        "task-scheduler",
        "event-broker",
        "state-machine",
    ]
    for sk in KNOWN_SKILLS:
        if not any(True for _ in skills_path.glob(f"{sk}.md")):
            loader = f"claude-code-skill:{sk}"
            kw = auto_keywords(sk)
            upsert(conn, f"skill:{sk}", "skill", loader, kw, memory_kb=64, priority=6)
            count += 1

    conn.commit()
    return count


# ── Source 2 : Agents OpenClaw ────────────────────────────────────────────────

OPENCLAW_AGENTS = [
    # 42+ documented agents from cluster memory
    "trading-engine",
    "voice-engine",
    "omega-dev-agent",
    "cowork-monitoring",
    "cowork-system",
    "cowork-linux",
    "cluster-mgr",
    "data-pipeline",
    "maintenance",
    "dispatch",
    "core-agents",
    "browser-agent",
    "web-scraper",
    "mail-agent",
    "linkedin-agent",
    "calendar-agent",
    "news-reader",
    "crypto-tracker",
    "gpu-monitor",
    "vram-watcher",
    "log-shipper",
    "alert-manager",
    "backup-agent",
    "restore-agent",
    "ssh-manager",
    "vpn-agent",
    "firewall-agent",
    "dns-agent",
    "cert-manager",
    "load-balancer",
    "proxy-agent",
    "cron-agent",
    "queue-consumer",
    "redis-agent",
    "pg-agent",
    "sqlite-agent",
    "s3-agent",
    "cdn-agent",
    "metrics-collector",
    "trace-agent",
    "test-runner",
    "deploy-agent",
    "rollback-agent",
    "scale-agent",
    "health-checker",
    "perf-profiler",
    "security-scanner",
    "audit-agent",
    "notify-agent",
    "report-builder",
    "dashboard-agent",
]


def seed_agents(conn) -> int:
    count = 0
    # Try docker for live containers
    live = set()
    try:
        result = subprocess.run(
            [
                "docker",
                "ps",
                "-a",
                "--filter",
                "name=openclaw",
                "--format",
                "{{.Names}}",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        for name in result.stdout.strip().splitlines():
            name = name.strip()
            if name:
                live.add(name)
                loader = f"docker exec {name}"
                kw = auto_keywords(name, ["openclaw", "agent", "docker"])
                upsert(
                    conn,
                    f"agent:{name}",
                    "agent",
                    loader,
                    kw,
                    memory_kb=256,
                    priority=7,
                )
                count += 1
    except Exception as e:
        print(f"  [agents] docker unavailable: {e}")

    # Seed known agents regardless
    for agent_name in OPENCLAW_AGENTS:
        # derive container name convention
        container = f"openclaw-sbx-agent-{agent_name}"
        if container in live:
            continue
        loader = f"docker exec {container}"
        kw = auto_keywords(agent_name, ["openclaw", "agent"])
        upsert(
            conn, f"agent:{agent_name}", "agent", loader, kw, memory_kb=256, priority=7
        )
        count += 1

    conn.commit()
    return count


# ── Source 3 : MCP Servers ────────────────────────────────────────────────────


def seed_mcp(conn) -> int:
    count = 0
    try:
        with open(SETTINGS_PATH) as f:
            settings = json.load(f)
        mcp_servers = settings.get("mcpServers", {})
        for server_name, cfg in mcp_servers.items():
            cmd = cfg.get("command", "")
            args = cfg.get("args", [])
            desc = cfg.get("description", "")
            loader = f"{cmd} {' '.join(str(a) for a in args)}".strip()
            extra_kw = re.split(r"\W+", desc.lower())[:8]
            kw = auto_keywords(server_name, extra_kw)
            upsert(
                conn, f"mcp:{server_name}", "mcp", loader, kw, memory_kb=128, priority=8
            )
            count += 1
    except FileNotFoundError:
        print(f"  [mcp] settings.json not found: {SETTINGS_PATH}")
    except Exception as e:
        print(f"  [mcp] error: {e}")

    conn.commit()
    return count


# ── Source 4 : Scripts Jarvis ─────────────────────────────────────────────────

SCRIPT_DIRS = [
    JARVIS_CLI_DIR,
    JARVIS_SCRIPTS_DIR,
    JARVIS_INFRA_DIR,
    JARVIS_MONITORING_DIR,
    "/home/pamerys/jarvis/scripts/lumen",
]


def seed_scripts(conn) -> int:
    count = 0
    seen = set()
    for dir_path in SCRIPT_DIRS:
        base = Path(dir_path)
        if not base.exists():
            continue
        for ext in ("*.py", "*.sh"):
            for fpath in sorted(base.rglob(ext)):
                if "__pycache__" in str(fpath):
                    continue
                rel = str(fpath)
                if rel in seen:
                    continue
                seen.add(rel)
                stem = fpath.stem
                suffix = fpath.suffix
                interpreter = "python3" if suffix == ".py" else "bash"
                loader = f"{interpreter} {fpath}"
                kw = auto_keywords(stem, ["cli", "script", "jarvis"])
                upsert(conn, f"cli:{stem}", "cli", loader, kw, memory_kb=16, priority=4)
                count += 1

    conn.commit()
    return count


# ── Source 5 : Modèles LLM ────────────────────────────────────────────────────


def _fetch_lmstudio_models(url: str, node: str) -> list[tuple]:
    """Returns list of (model_id, loader_string)."""
    import urllib.request

    try:
        req = urllib.request.urlopen(url, timeout=5)
        data = json.loads(req.read())
        models = []
        for m in data.get("data", []):
            mid = m["id"]
            loader = f'curl -s {url.replace("/models", "/completions")} -d \'{{"model":"{mid}","prompt":"{{input}}","max_tokens":512}}\''
            models.append((mid, loader, node))
        return models
    except Exception:
        return []


def _fetch_ollama_models() -> list[tuple[str, str, str]]:
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        models = []
        for line in result.stdout.strip().splitlines()[1:]:
            parts = line.split()
            if parts:
                mid = parts[0]
                loader = f"ollama run {mid}"
                models.append((mid, loader, "OL1"))
        return models
    except Exception:
        return []


def seed_models(conn) -> int:
    count = 0
    all_models: list[tuple] = []

    all_models += _fetch_lmstudio_models(M1_URL, "M1")
    all_models += _fetch_lmstudio_models(M2_URL, "M2")
    all_models += _fetch_ollama_models()

    # Fallback: known cluster models if network unreachable
    KNOWN_MODELS = [
        ("qwen3.5-9b", "lm-ask.sh", "M1"),
        ("qwen3.5-35b-a3b", "lm-ask.sh --big", "M1"),
        ("qwen3.5-27b-claude-4.6-opus-distilled", "lm-ask.sh --big", "M1"),
        ("qwen3-14b-claude-4.5-opus-distill", "lm-ask.sh --big", "M1"),
        ("glm-4.7-flash-claude-opus-4.5-distill", "lm-ask.sh", "M1"),
        ("gpt-oss-20b", "lm-ask.sh", "M1"),
        ("gemma-4-26b-a4b", "lm-ask.sh", "M1"),
        ("claudegpt-debugger", "lm-ask.sh", "M1"),
        ("qwen3.5-9b", "lm-ask.sh", "M2"),
        ("qwen3.5-35b-a3b", "lm-ask.sh --big", "M2"),
        ("deepseek-r1-0528", "lm-ask.sh --reason", "M2"),
        ("qwen3-8b", "lm-ask.sh", "M2"),
        ("gemma3:4b", "ollama run gemma3:4b", "OL1"),
        ("deepseek-r1:7b", "ollama run deepseek-r1:7b", "OL1"),
        ("qwen3:1.7b", "ollama run qwen3:1.7b", "OL1"),
        ("qwen2.5:1.5b", "ollama run qwen2.5:1.5b", "OL1"),
        ("kimi-k2.5:cloud", "ollama run kimi-k2.5:cloud", "OL1"),
        ("nomic-embed-text:latest", "ollama run nomic-embed-text:latest", "OL1"),
    ]

    # Merge: live models take precedence
    live_ids = {m[0] for m in all_models}
    for mid, loader, node in KNOWN_MODELS:
        if mid not in live_ids:
            all_models.append((mid, loader, node))

    for mid, loader, node in all_models:
        name = f"model:{node}:{mid}"
        kw = auto_keywords(mid, ["llm", "model", "ai", node.lower()])
        upsert(conn, name, "model", loader, kw, memory_kb=4096, priority=3)
        count += 1

    conn.commit()
    return count


# ── Domino trigger wiring ─────────────────────────────────────────────────────

CATEGORY_TRIGGER_MAP = {
    # skill → auto-find matching agent by shared keyword
    "skill": "agent",
    # agent → log via pipeline (always)
    "agent": "cli",
    # mcp → skill refinement
    "mcp": "skill",
}

EXPLICIT_TRIGGERS = {
    # skill:whisper-transcription → agent:voice-engine
    "skill:whisper-transcription": ["agent:voice-engine"],
    "skill:tdd-unittest": ["skill:code-review"],
    "skill:llm-prompt": ["model:M1:qwen3.5-35b-a3b"],
    "skill:rag-pipeline": ["model:M1:qwen3.5-27b-claude-4.6-opus-distilled"],
    "skill:monitoring-setup": ["agent:cowork-monitoring", "agent:gpu-monitor"],
    "skill:debug-trace": ["model:M2:deepseek-r1-0528"],
    "skill:cascade-engine": ["skill:agent-spawn", "cli:jarvis_master"],
    "agent:trading-engine": ["agent:notify-agent", "skill:data-viz"],
    "agent:cowork-monitoring": ["agent:alert-manager", "cli:loop_monitor"],
    "agent:health-checker": ["agent:gpu-monitor", "agent:vram-watcher"],
    "mcp:openclaw": ["agent:omega-dev-agent"],
    "mcp:web-api": ["agent:web-scraper"],
    "mcp:browser-control": ["agent:browser-agent"],
}


def wire_triggers(conn):
    rows = conn.execute("SELECT name, category, keywords FROM tool_map").fetchall()
    name_to_row = {r["name"]: r for r in rows}

    updates = []
    for row in rows:
        name = row["name"]

        # Explicit triggers first
        if name in EXPLICIT_TRIGGERS:
            triggers = [t for t in EXPLICIT_TRIGGERS[name] if t in name_to_row]
            updates.append((json.dumps(triggers), name))
            continue

        # Category-based auto-trigger: find tools in target category
        # that share at least one keyword with current tool
        target_cat = CATEGORY_TRIGGER_MAP.get(row["category"])
        if not target_cat:
            continue

        try:
            my_kw = set(json.loads(row["keywords"]))
        except Exception:
            my_kw = set()

        matched = []
        for candidate_name, candidate_row in name_to_row.items():
            if candidate_row["category"] != target_cat:
                continue
            if candidate_name == name:
                continue
            try:
                cand_kw = set(json.loads(candidate_row["keywords"]))
            except Exception:
                cand_kw = set()
            overlap = my_kw & cand_kw
            # Filter generic tokens
            overlap -= {"jarvis", "cli", "script", "agent", "ai", "llm", "model"}
            if overlap:
                matched.append(candidate_name)
            if len(matched) >= 3:
                break

        if matched:
            updates.append((json.dumps(matched[:3]), name))

    conn.executemany("UPDATE tool_map SET triggers=? WHERE name=?", updates)
    conn.commit()
    return len(updates)


# ── Main ──────────────────────────────────────────────────────────────────────


def main():
    print("[seed_tools] Starting tool_map population...")
    conn = get_db()

    n_skills = seed_skills(conn)
    n_agents = seed_agents(conn)
    n_mcp = seed_mcp(conn)
    n_scripts = seed_scripts(conn)
    n_models = seed_models(conn)
    n_wired = wire_triggers(conn)

    total = conn.execute("SELECT COUNT(*) FROM tool_map").fetchone()[0]

    print("\n[seed_tools] Results:")
    print(f"  skills  : {n_skills:>4}")
    print(f"  agents  : {n_agents:>4}")
    print(f"  mcp     : {n_mcp:>4}")
    print(f"  cli     : {n_scripts:>4}")
    print(f"  models  : {n_models:>4}")
    print(f"  wired   : {n_wired:>4} (domino triggers)")
    print(f"  total   : {total:>4} tools in tool_map")

    conn.close()


if __name__ == "__main__":
    main()
