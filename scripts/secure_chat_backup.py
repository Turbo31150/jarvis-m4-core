#!/usr/bin/env python3
"""
JARVIS Secure Chat Backup
==========================

Pipeline : ~/.claude/projects/**/*.jsonl → sanitize tokens → SQLite chat_history → GitHub privé

Usage :
  ./secure_chat_backup.py scan                     # Liste sessions + count secrets
  ./secure_chat_backup.py sanitize SESSION_FILE    # Crée copie sans tokens
  ./secure_chat_backup.py import [--days 7]        # Import N derniers jours en SQL
  ./secure_chat_backup.py rotate-check             # Liste secrets à révoquer
  ./secure_chat_backup.py git-push REPO_URL        # Push sanitized → GitHub privé
"""

import argparse
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

DB = "/home/pamerys/jarvis/jarvis_master.db"
CLAUDE_DIR = Path.home() / ".claude" / "projects"
SANITIZED_DIR = Path.home() / "jarvis" / "chat_history" / "sanitized"

# Regex patterns pour secrets connus (ordre = priorité)
SECRET_PATTERNS = [
    # Notion integration tokens
    (re.compile(r"ntn_[A-Za-z0-9]{40,}"), "NOTION_TOKEN"),
    # Mirr API keys
    (re.compile(r"mrr_live_[a-f0-9]{60,}"), "MIRR_TOKEN"),
    # Telegram bot tokens (digits:base64)
    (re.compile(r"\b\d{9,12}:[A-Za-z0-9_-]{30,}\b"), "TELEGRAM_BOT_TOKEN"),
    # Google AI Studio (Gemini) keys
    (re.compile(r"AIzaSy[A-Za-z0-9_-]{30,}"), "GEMINI_API_KEY"),
    # GitHub PAT
    (re.compile(r"ghp_[A-Za-z0-9]{30,}"), "GITHUB_PAT"),
    (re.compile(r"github_pat_[A-Za-z0-9_]{60,}"), "GITHUB_PAT_FINE"),
    # Anthropic
    (re.compile(r"sk-ant-[A-Za-z0-9_-]{50,}"), "ANTHROPIC_KEY"),
    # OpenAI
    (re.compile(r"sk-[A-Za-z0-9]{40,}"), "OPENAI_KEY"),
    # AWS
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS_ACCESS_KEY"),
    # Generic high-entropy strings ≥32 chars after = sign (cautious)
    # (re.compile(r"=([A-Za-z0-9+/]{40,})"), "GENERIC_SECRET"),  # too aggressive — disabled
]


def sanitize_text(text: str) -> tuple[str, dict]:
    """Replace secrets in-place. Returns (sanitized_text, {pattern_name: count})."""
    counts = {}
    for pattern, name in SECRET_PATTERNS:

        def _replace(m):
            counts[name] = counts.get(name, 0) + 1
            value = m.group(0)
            h = hashlib.sha256(value.encode()).hexdigest()[:8]
            return f"[REDACTED:{name}:{h}]"

        text = pattern.sub(_replace, text)
    return text, counts


def cmd_scan():
    """List all Claude session JSONL files + count secrets in each."""
    sessions = list(CLAUDE_DIR.rglob("*.jsonl"))
    print(f"📁 {len(sessions)} sessions JSONL dans {CLAUDE_DIR}")
    total_secrets = {}
    sample_size = min(20, len(sessions))
    print(f"🔍 Scan {sample_size} dernières sessions...")
    sessions_sorted = sorted(sessions, key=lambda p: p.stat().st_mtime, reverse=True)
    for f in sessions_sorted[:sample_size]:
        try:
            content = f.read_text(errors="ignore")
        except Exception:
            continue
        _, counts = sanitize_text(content)
        if counts:
            print(f"  ⚠️  {f.name}: {counts}")
            for k, v in counts.items():
                total_secrets[k] = total_secrets.get(k, 0) + v
    print(f"\n🚨 TOTAL secrets exposés (top {sample_size} sessions) : {total_secrets}")


def cmd_sanitize(session_file: str):
    """Create sanitized copy of one JSONL file."""
    src = Path(session_file).expanduser()
    if not src.exists():
        # Search recursively in claude projects
        matches = list(
            CLAUDE_DIR.rglob(
                session_file
                if session_file.endswith(".jsonl")
                else f"{session_file}.jsonl"
            )
        )
        if matches:
            src = matches[0]
    if not src.exists():
        print(f"❌ Not found: {session_file}", file=sys.stderr)
        return 1
    SANITIZED_DIR.mkdir(parents=True, exist_ok=True)
    dst = SANITIZED_DIR / src.name
    content = src.read_text(errors="ignore")
    sanitized, counts = sanitize_text(content)
    dst.write_text(sanitized)
    print(f"✅ Sanitized → {dst} ({sum(counts.values())} secrets masked: {counts})")
    return 0


def cmd_import(days: int = 7):
    """Import last N days of sessions into SQLite chat_history."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    # WAL : un seul écrivain à la fois sur une base très sollicitée,
    # il faut attendre au lieu d'échouer sur "database is locked".
    con = sqlite3.connect(DB, timeout=120)
    con.execute("PRAGMA busy_timeout=120000")
    con.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_file TEXT NOT NULL,
            session_dir TEXT,
            ts_start TEXT,
            ts_end TEXT,
            message_count INTEGER,
            user_message_count INTEGER,
            assistant_message_count INTEGER,
            tool_call_count INTEGER,
            secrets_redacted INTEGER DEFAULT 0,
            secrets_breakdown TEXT,
            content_sha256 TEXT,
            imported_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(session_file)
        )
    """)
    sessions = sorted(
        CLAUDE_DIR.rglob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    imported = 0
    for f in sessions:
        mtime = datetime.fromtimestamp(f.stat().st_mtime, timezone.utc)
        if mtime < cutoff:
            continue
        try:
            content = f.read_text(errors="ignore")
        except Exception:
            continue
        sanitized, counts = sanitize_text(content)
        sha = hashlib.sha256(sanitized.encode()).hexdigest()
        # Parse JSONL stats
        msg_count = u_count = a_count = t_count = 0
        ts_start = ts_end = None
        for line in sanitized.splitlines():
            try:
                rec = json.loads(line)
                msg_count += 1
                role = (
                    rec.get("message", {}).get("role")
                    if isinstance(rec.get("message"), dict)
                    else rec.get("type")
                )
                if role == "user":
                    u_count += 1
                elif role == "assistant":
                    a_count += 1
                if "tool_use" in str(rec.get("message", "")):
                    t_count += 1
                ts = rec.get("timestamp")
                if ts:
                    if ts_start is None or ts < ts_start:
                        ts_start = ts
                    if ts_end is None or ts > ts_end:
                        ts_end = ts
            except (json.JSONDecodeError, AttributeError):
                continue
        try:
            con.execute(
                """
                INSERT OR REPLACE INTO chat_history
                (session_file, session_dir, ts_start, ts_end, message_count,
                 user_message_count, assistant_message_count, tool_call_count,
                 secrets_redacted, secrets_breakdown, content_sha256, imported_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
                (
                    f.name,
                    str(f.parent.name),
                    ts_start,
                    ts_end,
                    msg_count,
                    u_count,
                    a_count,
                    t_count,
                    sum(counts.values()),
                    json.dumps(counts),
                    sha,
                ),
            )
            imported += 1
        except Exception as e:
            print(f"  ⚠️ {f.name}: {e}")
    con.commit()
    con.close()
    print(f"✅ Imported {imported} sessions (last {days} days) into chat_history table")


def cmd_rotate_check():
    """List secrets exposed in current/recent sessions for rotation."""
    print("🚨 SECRETS À RÉVOQUER (exposés dans le chat history) :\n")
    print("Notion integrations — https://www.notion.so/my-integrations")
    print("  1. Révoquer + recréer tokens exposés")
    print("")
    print("Mirr API key — https://www.mirra.my/en/settings/api-keys")
    print("  → Delete + Create new key")
    print("")
    print("Telegram Bot — Chat avec @BotFather")
    print("  → /mybots → Bot → API Token → Revoke + nouveau token")
    print("")
    print("Gemini API — https://aistudio.google.com/apikey")
    print("  → Delete + Create new key")
    print("")
    print("GitHub PAT — https://github.com/settings/tokens")
    print("  → Si exposé : Delete + nouveau Fine-grained PAT")
    print("")
    print("Workflow rotation rapide après nouveau token :")
    print("  1. echo 'NEW_TOKEN' > ~/.config/<service>/api_key && chmod 600 $_")
    print(
        "  2. sqlite3 ~/jarvis/jarvis_master.db \"UPDATE api_keys SET key_value='NEW' WHERE service='X'\""
    )
    print("  3. systemctl restart jarvis-<svc> (si applicable)")


def cmd_git_push(repo_url: str):
    """Init git repo + push sanitized chats."""
    if not SANITIZED_DIR.exists() or not list(SANITIZED_DIR.glob("*.jsonl")):
        print(
            "❌ Aucun fichier sanitized. Lance d'abord : ./secure_chat_backup.py sanitize ..."
        )
        return 1
    os.chdir(SANITIZED_DIR.parent)
    if not (Path.cwd() / ".git").exists():
        subprocess.run(["git", "init"], check=True)
        subprocess.run(["git", "remote", "add", "origin", repo_url], check=True)
        # .gitignore strict
        gitignore = [
            "*.env",
            ".env*",
            "api_key*",
            "*token*",
            "*secret*",
            "*.key",
            "*.pem",
        ]
        (Path.cwd() / ".gitignore").write_text("\n".join(gitignore) + "\n")
    subprocess.run(["git", "add", "sanitized/"], check=True)
    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            f"backup: chat history {datetime.now().strftime('%Y-%m-%d')}",
        ],
        check=True,
    )
    subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
    print(f"✅ Pushed to {repo_url}")


def main():
    p = argparse.ArgumentParser(description="JARVIS Secure Chat Backup")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("scan")
    s = sub.add_parser("sanitize")
    s.add_argument("session_file")
    i = sub.add_parser("import")
    i.add_argument("--days", type=int, default=7)
    sub.add_parser("rotate-check")
    g = sub.add_parser("git-push")
    g.add_argument("repo_url")
    args = p.parse_args()
    if args.cmd == "scan":
        cmd_scan()
    elif args.cmd == "sanitize":
        cmd_sanitize(args.session_file)
    elif args.cmd == "import":
        cmd_import(args.days)
    elif args.cmd == "rotate-check":
        cmd_rotate_check()
    elif args.cmd == "git-push":
        cmd_git_push(args.repo_url)


if __name__ == "__main__":
    sys.exit(main() or 0)
