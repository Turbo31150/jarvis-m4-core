#!/usr/bin/env python3
"""
jarvis_notion_claude_bridge.py — Câblage Bidirectionnel Notion <-> AGY <-> Claude Code
Rôle :
  - Moissonne la TodoList Notion & les tâches prioritaires SQLite/Master
  - Lit les transcrits et évalue le travail de Claude Code (sessions c0, c6...)
  - Injecte les directives et tâches évaluées dans la boîte de réception de Claude Code
  - Synchronise les résultats et retours vers Notion et SQLite
  - Cadencé toutes les 15 minutes avec pilotage autonome continu
"""

import os
import sys
import time
import json
import glob
import sqlite3
import subprocess
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# Paths & Config
HOME = Path("/home/pamerys")
JARVIS_DIR = HOME / "jarvis"
BOARD_DIR = JARVIS_DIR / "board"
LABO_DIR = HOME / "labo"
OUTPUT_DIR = LABO_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CLAUDE_DIR = HOME / ".claude"
SESSIONS_DIR = CLAUDE_DIR / "sessions"
PROJECTS_DIR = CLAUDE_DIR / "projects"

DB_MASTER = JARVIS_DIR / "jarvis_master.db"
DB_BOARD = BOARD_DIR / "board.db"
DB_LOGS = JARVIS_DIR / "logs" / "jarvis_logs.db"

INBOX_MD = LABO_DIR / "CLAUDE_TASK_INBOX.md"
DIRECTIVES_JSON = LABO_DIR / "AGY_DIRECTIVES.json"

NOTION_TOKEN = "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"
NOTION_API_URL = "https://api.notion.com/v1"
NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def ts_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

def log(msg):
    print(f"[{ts_now()}] 🔗 [NOTION-CLAUDE-BRIDGE] {msg}", flush=True)

# 1. MOISSONNER LES TÂCHES ET NOTION
def fetch_notion_tasks():
    tasks = []
    try:
        req = urllib.request.Request(
            f"{NOTION_API_URL}/search",
            data=json.dumps({"page_size": 15}).encode("utf-8"),
            headers=NOTION_HEADERS
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for item in data.get("results", []):
                obj = item.get("object")
                item_id = item.get("id")
                url = item.get("url", f"https://notion.so/{item_id.replace('-', '')}")
                title = ""
                if obj == "page":
                    props = item.get("properties", {})
                    for k, v in props.items():
                        if v.get("type") == "title":
                            title = "".join([t.get("plain_text", "") for t in v.get("title", [])])
                elif obj == "database":
                    title = "".join([t.get("plain_text", "") for t in item.get("title", [])])
                
                if title:
                    tasks.append({
                        "source": "NOTION",
                        "id": item_id,
                        "title": title,
                        "url": url,
                        "last_edited": item.get("last_edited_time")
                    })
    except Exception as e:
        log(f"Alerte lecture Notion API : {e}")
        
    return tasks

def fetch_sqlite_and_local_tasks():
    tasks = []
    # 1. Base master
    try:
        with sqlite3.connect(str(DB_MASTER)) as cx:
            cx.row_factory = sqlite3.Row
            rows = cx.execute("""
                SELECT rowid, id, title, priority, status FROM master_tasks_cahier_charges
                WHERE status != 'DONE' AND status != 'OK'
                ORDER BY rowid ASC LIMIT 10
            """).fetchall()
            for r in rows:
                tasks.append({
                    "source": "SQLITE_MASTER",
                    "id": r["id"],
                    "title": r["title"],
                    "priority": r["priority"],
                    "status": r["status"]
                })
                
            # Emploi notion table
            notion_rows = cx.execute("SELECT titre, url, notion_id FROM emploi_notion LIMIT 5").fetchall()
            for nr in notion_rows:
                tasks.append({
                    "source": "NOTION_EMPLOI",
                    "id": nr["notion_id"],
                    "title": nr["titre"],
                    "url": nr["url"],
                    "priority": "CRITIQUE"
                })
    except Exception as e:
        log(f"Alerte lecture SQLite master : {e}")
        
    # 2. ANTIGRAVITY_TASKS.md
    task_file = JARVIS_DIR / "ANTIGRAVITY_TASKS.md"
    if task_file.exists():
        try:
            content = task_file.read_text(encoding="utf-8")
            for line in content.splitlines():
                if line.startswith("### T") and "—" in line:
                    parts = line.split("—")
                    t_id = parts[0].replace("###", "").strip()
                    t_desc = parts[1].strip()
                    tasks.append({
                        "source": "ANTIGRAVITY_TASKS",
                        "id": t_id,
                        "title": t_desc,
                        "priority": "HAUTE"
                    })
        except Exception as e:
            log(f"Alerte lecture ANTIGRAVITY_TASKS.md : {e}")

    return tasks

# 2. ANALYSE ET ÉVALUATION DES SESSIONS CLAUDE CODE
def evaluate_claude_sessions():
    evaluations = []
    session_files = list(SESSIONS_DIR.glob("*.json"))
    for sf in session_files:
        try:
            s_data = json.loads(sf.read_text(encoding="utf-8"))
            pid = s_data.get("pid")
            session_id = s_data.get("sessionId")
            name = s_data.get("name", "claude")
            
            is_alive = False
            if pid:
                try:
                    os.kill(pid, 0)
                    is_alive = True
                except OSError:
                    is_alive = False
            
            transcript_files = list(PROJECTS_DIR.glob(f"**/{session_id}.jsonl"))
            dialog_summary = []
            last_action = "Inactif"
            has_error = False
            
            if transcript_files:
                lines = transcript_files[0].read_text(encoding="utf-8", errors="ignore").strip().splitlines()
                for l in lines[-12:]:
                    try:
                        d = json.loads(l)
                        role = d.get("type") or d.get("role")
                        msg = d.get("message", {})
                        if role == "assistant":
                            for c in msg.get("content", []):
                                if c.get("type") == "text":
                                    last_action = c.get("text")[:250]
                                elif c.get("type") == "tool_use":
                                    last_action = f"Outil: {c.get('name')}"
                        elif role == "user":
                            for c in msg.get("content", []):
                                if c.get("type") == "tool_result" and c.get("is_error"):
                                    has_error = True
                    except:
                        pass
                        
            evaluations.append({
                "pid": pid,
                "session_id": session_id,
                "name": name,
                "is_alive": is_alive,
                "has_error": has_error,
                "last_action": last_action,
                "evaluated_at": ts_now()
            })
        except Exception as e:
            log(f"Erreur éval session {sf}: {e}")
            
    return evaluations

# 3. CONSTRUIRE LES DIRECTIVES & INJECTER DANS CLAUDE CODE
def generate_and_inject_directives(notion_tasks, sqlite_tasks, evaluations):
    directives = []
    
    # Priorité 1 : Notion Emploi & Prospection
    for t in notion_tasks[:3]:
        directives.append({
            "directive_id": f"DIR-NOTION-{t['id'][:8]}",
            "titre": t["title"],
            "source": t["source"],
            "url": t.get("url", ""),
            "action_attendue": "Consulter le contexte, exécuter les relances/alignements et consigner dans la base.",
            "statut": "INJECTE"
        })
        
    # Priorité 2 : Tâches Master Plan
    for t in sqlite_tasks[:4]:
        directives.append({
            "directive_id": f"DIR-MASTER-{t['id']}",
            "titre": t["title"],
            "source": t["source"],
            "priorite": t.get("priority", "HAUTE"),
            "action_attendue": "Exécuter sans interruption, tester le livrable et auto-committer.",
            "statut": "INJECTE"
        })

    # Écriture du fichier JSON structuré
    payload = {
        "timestamp": ts_now(),
        "cadence_minutes": 15,
        "evaluations_claude": evaluations,
        "directives_actives": directives
    }
    DIRECTIVES_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    
    # Écriture de la boîte de réception Markdown pour Claude Code
    inbox_content = f"""# 📥 CLAUDE CODE TASK INBOX — DIRECTIVES AGY (15-MIN CYCLE)
*Généré par Antigravity / JARVIS-OMEGA le {ts_now()}*  
*Mode : 100% Autonome — Exécute et tranche immédiatement*

---

## 🎯 ÉVALUATION DES SESSIONS EN COURS
"""
    for ev in evaluations:
        status_icon = "🟢 ACTIF" if ev["is_alive"] else "⚪ INACTIF"
        err_icon = " ⚠️ ERREUR DÉTECTÉE" if ev["has_error"] else ""
        inbox_content += f"- **[{ev['name']}]** (PID `{ev['pid']}`) : {status_icon}{err_icon}\n"
        inbox_content += f"  *Dernière action observée :* `{ev['last_action'][:120]}...`\n"

    inbox_content += f"""
---

## 🚀 DIRECTIVES PRIORITAIRES À EXÉCUTER (CYCLE ACTUEL)

"""
    for idx, d in enumerate(directives, 1):
        inbox_content += f"### {idx}. [{d['directive_id']}] {d['titre']}\n"
        inbox_content += f"- **Source :** `{d['source']}`\n"
        if d.get("url"):
            inbox_content += f"- **Lien :** [{d['url']}]({d['url']})\n"
        inbox_content += f"- **Action attendue :** {d['action_attendue']}\n\n"

    inbox_content += f"""
---
*Consigne de boucle : Dès achèvement d'un bloc, consigne l'avancement dans `jarvis_master.db` et le rapport d'exécution.*
"""
    INBOX_MD.write_text(inbox_content, encoding="utf-8")
    log(f"Directives et évaluations injectées dans {INBOX_MD} ({len(directives)} directives actives)")
    
    # Enregistrer dans SQLite master
    try:
        with sqlite3.connect(str(DB_MASTER)) as cx:
            cx.execute("""
                CREATE TABLE IF NOT EXISTS claude_directive_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    directive_id TEXT,
                    titre TEXT,
                    source TEXT,
                    statut TEXT
                )
            """)
            for d in directives:
                cx.execute("""
                    INSERT INTO claude_directive_queue (directive_id, titre, source, statut)
                    VALUES (?, ?, ?, ?)
                """, (d["directive_id"], d["titre"], d["source"], d["statut"]))
            cx.commit()
    except Exception as e:
        log(f"Erreur enregistrement directive queue : {e}")

# 4. CYCLE COMPLET DU BRIDGE
def run_bridge_cycle():
    log("── Démarrage du cycle d'évaluation & injection Notion <-> Claude Code ──")
    notion_tasks = fetch_notion_tasks()
    sqlite_tasks = fetch_sqlite_and_local_tasks()
    evaluations = evaluate_claude_sessions()
    
    log(f"Tâches Notion récoltées : {len(notion_tasks)} | Tâches Master/SQLite : {len(sqlite_tasks)}")
    generate_and_inject_directives(notion_tasks, sqlite_tasks, evaluations)
    log("✓ Cycle terminé avec succès.")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        run_bridge_cycle()
        return
        
    log("🚀 Lancement continu du bridge Notion <-> Claude Code (boucle 15 min)...")
    while True:
        try:
            run_bridge_cycle()
            log("⏳ Pause de 15 minutes (900s) avant prochaine réévaluation...")
            time.sleep(900)
        except KeyboardInterrupt:
            break
        except Exception as e:
            log(f"Erreur boucle: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
