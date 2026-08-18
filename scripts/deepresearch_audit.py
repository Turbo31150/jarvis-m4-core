#!/usr/bin/env python3
"""deepresearch_audit.py — Outil d'audit et d'exécution en cascade JARVIS.

Gère l'inventaire des tâches, le diagnostic du cluster, le mode PLAN,
et l'exécution de cascades d'automatisation auto-alimentées.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configuration et chemins
ROOT = Path("/home/pamerys/jarvis")
TASKS_FILE = ROOT / "ANTIGRAVITY_TASKS.md"
PLAN_FILE = ROOT / "audit" / "todo_plan.json"
DB_PATH = ROOT / "jarvis_master.db"
M5_IP = None   # M5 demonte le 2026-08-06
M5_KEY = "/home/pamerys/.ssh/m5_jarvis_ed25519"

# Liste des commandes préchargées pour les tâches connues (corrigées)
PRELOADED_COMMANDS: Dict[str, str] = {
    "T004": "docker service update --limit-memory 2g jarvis_prod_vocal-whisper",
    "T010": "cd /home/pamerys/jarvis-cowork && python3 src/deploy_cowork_agents.py --deploy",
    "T011": "find /home/pamerys/jarvis-cowork -name '*.json' -path '*/patterns/*' | while read f; do openclaw deploy --pattern \"$(basename \"$f\" .json)\"; done",
    "T014": "docker update --restart=on-failure:3 jarvis-prompt-dispatcher 2>/dev/null || true",
    "T020": "rm -rf ~/.cache/google-chrome/* ~/.cache/mozilla/* ~/.cache/pip/* && find /home/pamerys -name '*.pyc' -delete 2>/dev/null || true && find /home/pamerys -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true && docker system prune -f && journalctl --vacuum-size=500M",
    "T021": "[ -f /tmp/samsung-setup.sh ] && sudo bash /tmp/samsung-setup.sh && mv ~/.lmstudio /storage/data/lmstudio && ln -s /storage/data/lmstudio ~/.lmstudio || echo 'samsung-setup missing'",
    "T023": "timeout 2 bash ~/jarvis/scripts/cluster-health-monitor.sh || true",
    "T030": f"sleep 2 && ssh -T -F /dev/null -i {M5_KEY} -o ForwardAgent=no -o IdentityAgent=none -o IdentitiesOnly=yes -o StrictHostKeyChecking=no turbo@{M5_IP} 'python3 ~/jarvis/social-platform/linkedin_auto_post.py'",
    "T045": "for repo in /home/pamerys/Workspaces/jarvis-linux /home/pamerys/jarvis-cowork; do cd $repo && if git status --short | grep -q .; then git add -A && git commit -m \"chore(auto): sync $(date +%Y-%m-%d)\" && git push origin main 2>/dev/null || true; fi; done",
    "T050": "(crontab -l 2>/dev/null; echo '*/5 * * * * bash ~/jarvis/scripts/cluster-health-monitor.sh >> ~/jarvis/logs/health.log 2>&1') | crontab -",
    "T060": "docker container prune -f && docker image prune -f",
    "T061": "for db in ~/jarvis/jarvis_master.db ~/jarvis/logs/jarvis_logs.db ~/jarvis/cowork_engine.db; do sqlite3 $db 'SELECT name FROM sqlite_master WHERE type=\"table\"'; done",
    "T062": "sqlite3 ~/jarvis/jarvis_master.db 'PRAGMA integrity_check;'; sqlite3 ~/jarvis/logs/jarvis_logs.db 'PRAGMA integrity_check;'",
    "T071": f"sleep 2 && rsync -az -e 'ssh -T -F /dev/null -i {M5_KEY} -o ForwardAgent=no -o IdentityAgent=none -o IdentitiesOnly=yes -o StrictHostKeyChecking=no' ~/jarvis/scripts/lm-ask.sh turbo@{M5_IP}:~/jarvis/scripts/",
    "T080": "docker run -d --name prometheus -p 9090:9090 prom/prometheus 2>/dev/null || true; docker run -d --name grafana -p 3000:3000 grafana/grafana 2>/dev/null || true",
    "T091": "for repo in /home/pamerys/Workspaces/*/; do git -C $repo log --all --full-history -- '*.env' 'secrets*' 2>/dev/null | grep commit | head -2; done",
    "T100": "sudo bash /home/pamerys/jarvis/scripts/clone-system-disk.sh",
}


def run_local(cmd: str) -> tuple[int, str]:
    """Exécute une commande locale et retourne (exit_code, output)."""
    try:
        env = os.environ.copy()
        if "SSH_AUTH_SOCK" in env:
            del env["SSH_AUTH_SOCK"]
        res = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=120, env=env
        )
        return res.returncode, res.stdout + res.stderr
    except subprocess.TimeoutExpired:
        return -1, "Command timeout after 120s"
    except Exception as e:
        return -1, str(e)


def run_ssh(cmd: str) -> tuple[int, str]:
    """Exécute une commande sur M5 via SSH."""
    time.sleep(2)
    ssh_cmd = (
        f"ssh -T -F /dev/null -i {M5_KEY} -o ForwardAgent=no -o IdentityAgent=none -o IdentitiesOnly=yes -o StrictHostKeyChecking=no turbo@{M5_IP} {json.dumps(cmd)}"
    )
    return run_local(ssh_cmd)


def diagnose_cluster() -> Dict[str, Any]:
    """Diagnostique la santé du cluster (pings, ports)."""
    diag = {}
    nodes = {
        "M1": "127.0.0.1",
        "M2": "127.0.0.1",
        "M5": M5_IP,
        "M6": "10.42.0.230",   # M4 demonte le 2026-08-06
    }
    for name, ip in nodes.items():
        ping_ok = False
        if name == "M1":
            ping_ok = True
        else:
            code, _ = run_local(f"ping -c 1 -W 1 {ip}")
            ping_ok = code == 0

        lms_up = False
        if ping_ok:
            port = "1234"
            if name == "M5":
                port = "11434"
            code, _ = run_local(f"curl -s -m 2 http://{ip}:{port}/v1/models")
            if code == 0:
                lms_up = True
            elif name == "M5":
                code, _ = run_local(f"curl -s -m 2 http://{ip}:{port}/api/tags")
                lms_up = code == 0

        diag[name] = {"ping": ping_ok, "lms": lms_up}
    return diag


def parse_tasks() -> List[Dict[str, Any]]:
    """Parse ANTIGRAVITY_TASKS.md et extrait les tâches."""
    if not TASKS_FILE.exists():
        return []
    tasks = []
    content = TASKS_FILE.read_text(errors="ignore")
    # Regex pour capturer les en-têtes de tâches
    pattern = re.compile(r"^###\s+(T\d+)\s+(?:\[(OK)\]\s+)?—?\s*(.*)$")
    current_section = "Unknown"

    for line in content.splitlines():
        if line.startswith("## "):
            current_section = line[3:].strip()
            continue
        m = pattern.match(line)
        if m:
            tid, status, title = m.groups()
            tasks.append(
                {
                    "id": tid,
                    "completed": status == "OK",
                    "title": title.strip(),
                    "section": current_section,
                    "command": PRELOADED_COMMANDS.get(tid, ""),
                }
            )
    return tasks


def update_task_status(task_id: str, completed: bool = True):
    """Met à jour le statut d'une tâche dans ANTIGRAVITY_TASKS.md."""
    if not TASKS_FILE.exists():
        return
    lines = TASKS_FILE.read_text(errors="ignore").splitlines()
    new_lines = []
    pattern = re.compile(rf"^###\s+{task_id}\s+(?:\[(OK)\]\s+)?—?\s*(.*)$")

    for line in lines:
        m = pattern.match(line)
        if m:
            _, title = m.groups()
            status_str = "[OK] " if completed else ""
            new_lines.append(f"### {task_id} {status_str}— {title}")
        else:
            new_lines.append(line)

    TASKS_FILE.write_text("\n".join(new_lines) + "\n")


def make_plan() -> Dict[str, Any]:
    """Génère le plan d'action (PLAN MODE)."""
    tasks = parse_tasks()
    cluster = diagnose_cluster()

    todo_tasks = [t for t in tasks if not t["completed"]]
    plan_steps = []

    for t in todo_tasks:
        cmd = t["command"]
        if not cmd:
            # Essaye d'adapter si commande manquante
            if "docker" in t["title"].lower():
                cmd = "docker system prune -f"
            else:
                cmd = f"# Manuel: {t['title']}"

        # Ajuste la cible (M1 ou M5)
        target = "M1"
        if "m5" in t["title"].lower() or t["id"] in ("T030", "T071"):
            target = "M5"

        plan_steps.append(
            {
                "task_id": t["id"],
                "title": t["title"],
                "command": cmd,
                "target": target,
                "status": "pending",
            }
        )

    plan = {
        "timestamp": datetime.datetime.now().isoformat(),
        "cluster_state": cluster,
        "steps": plan_steps,
    }

    # Sauvegarde du plan
    PLAN_FILE.parent.mkdir(parents=True, exist_ok=True)
    PLAN_FILE.write_text(json.dumps(plan, indent=2, ensure_ascii=False))
    return plan


def log_execution(
    task_id: str, cmd: str, exit_code: int, output: str, dur_ms: int
):
    """Enregistre le résultat de l'exécution dans la table cli_history."""
    try:
        # WAL : un seul écrivain à la fois sur une base très sollicitée,
        # il faut attendre au lieu d'échouer sur "database is locked".
        conn = sqlite3.connect(DB_PATH, timeout=120)
        conn.execute("PRAGMA busy_timeout=120000")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cli_history (
                timestamp TEXT, input TEXT, intents TEXT, cascade TEXT,
                confidence REAL, duration_ms INTEGER, success INTEGER
            )
        """
        )
        conn.execute(
            "INSERT INTO cli_history VALUES(?,?,?,?,?,?,?)",
            (
                datetime.datetime.now().isoformat(),
                f"audit run {task_id}",
                json.dumps(["audit", "execute"]),
                json.dumps([{"step": "primary", "name": task_id, "cmd": cmd}]),
                1.0,
                dur_ms,
                1 if exit_code == 0 else 0,
            ),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[WARN] Impossible de logger dans SQLite: {e}")


def execute_plan() -> List[Dict[str, Any]]:
    """Exécute le plan d'action (avalanche de commandes en cascade)."""
    if not PLAN_FILE.exists():
        print("[ERROR] Aucun plan trouvé. Lancez d'abord avec --plan.")
        return []

    plan = json.loads(PLAN_FILE.read_text())
    steps = plan.get("steps", [])
    executed_steps = []

    print(f"\n🚀 Lancement de la cascade d'automatisation ({len(steps)} étapes)...")

    for step in steps:
        tid = step["task_id"]
        cmd = step["command"]
        target = step["target"]

        if cmd.startswith("#"):
            print(f"⏭️  Saut de la tâche manuelle {tid} : {step['title']}")
            step["status"] = "skipped"
            executed_steps.append(step)
            continue

        print(f"⚡ Exécution de {tid} sur {target} : {cmd[:60]}...")
        t0 = time.time()

        if target == "M5":
            code, out = run_ssh(cmd)
        else:
            code, out = run_local(cmd)

        dur_ms = int((time.time() - t0) * 1000)

        # Log de l'exécution
        log_execution(tid, cmd, code, out, dur_ms)

        if code == 0:
            print(f"✅ Succès {tid} ({dur_ms} ms)")
            step["status"] = "success"
            # Auto-compilation et mise à jour de la todolist
            update_task_status(tid, True)
        else:
            print(f"❌ Échec {tid} (code {code}) : {out[:200]}")
            step["status"] = "failed"
            step["error"] = out[:300]

        executed_steps.append(step)

    # Réécrit le plan avec les statuts mis à jour
    plan["steps"] = executed_steps
    plan["executed_at"] = datetime.datetime.now().isoformat()
    PLAN_FILE.write_text(json.dumps(plan, indent=2, ensure_ascii=False))

    return executed_steps


def print_menu():
    """Affiche un menu interactif des tâches."""
    tasks = parse_tasks()
    cluster = diagnose_cluster()

    print("\n" + "=" * 60)
    print("        🤖 JARVIS - DEEPRESEARCH AUDIT & TODOLIST 🤖")
    print("=" * 60)

    print("\n📡 État du Cluster :")
    for name, state in cluster.items():
        ping_str = "✅ UP" if state["ping"] else "❌ DOWN"
        lms_str = "✅ LMS/Ollama UP" if state["lms"] else "❌ LMS/Ollama DOWN"
        print(f"  - {name} : Ping={ping_str}, Inférence={lms_str}")

    print("\n📋 Tâches Actives :")
    for t in tasks:
        status = "✅" if t["completed"] else "🔴"
        print(f"  {status} [{t['id']}] {t['title']} ({t['section']})")

    print("\nOptions :")
    print("  1. Générer le Plan d'Action (PLAN MODE)")
    print("  2. Exécuter la cascade d'automatisation (EXECUTE)")
    print("  3. Quitter")


def main():
    parser = argparse.ArgumentParser(
        description="CLI d'audit et cascade d'automatisation JARVIS"
    )
    parser.add_argument("--plan", action="store_true", help="Générer le plan (PLAN MODE)")
    parser.add_argument(
        "--execute", action="store_true", help="Exécuter la cascade (EXECUTE MODE)"
    )
    parser.add_argument(
        "--menu", action="store_true", help="Afficher le menu interactif"
    )
    args = parser.parse_args()

    if args.plan:
        plan = make_plan()
        print(f"✅ Plan généré dans {PLAN_FILE}")
        print(f"Total étapes planifiées : {len(plan['steps'])}")
        return

    if args.execute:
        execute_plan()
        return

    if args.menu or len(sys.argv) == 1:
        print_menu()
        return


if __name__ == "__main__":
    main()
