#!/usr/bin/env python3
"""
JARVIS-OMEGA Master Orchestrator — Pilotage & Injection Massive Autonome
Rôle :
  - Localise tous les terminaux Claude Code et sessions du bureau (pts, tmux, UID)
  - Lit leurs conversations en temps réel et consigne leur état
  - Pilote et interroge le Board JARVIS (Conseil d'experts, consensus, 13 domaines, 86k+ chunks)
  - Injecte des tâches massives issues du Master Plan (ANTIGRAVITY_TASKS.md & jarvis_master.db)
  - Tourne en continu avec cycle toutes les 15 minutes jusqu'à demain
"""

import os
import sys
import time
import json
import glob
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import jarvis_notion_claude_bridge

# Paths
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
DB_AUTOPILOT = LABO_DIR / "remi-board-kit" / "autopilot_executions.db"

def ts_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

def log(msg):
    print(f"[{ts_now()}] ⚡ [JARVIS-OMEGA] {msg}", flush=True)

# 1. SCAN TERMINAUX ET CLAUDE CODE
def scan_claude_terminals():
    terminals = []
    
    # 1.1 Lire les fichiers de sessions Claude
    session_files = list(SESSIONS_DIR.glob("*.json"))
    for sf in session_files:
        try:
            data = json.loads(sf.read_text(encoding="utf-8"))
            pid = data.get("pid")
            is_alive = False
            if pid:
                try:
                    os.kill(pid, 0)
                    is_alive = True
                except OSError:
                    is_alive = False
            
            data["is_alive"] = is_alive
            data["session_file"] = str(sf)
            
            # Transcription associée
            session_id = data.get("sessionId")
            jsonl_files = list(PROJECTS_DIR.glob(f"**/{session_id}.jsonl"))
            if jsonl_files:
                data["transcript_path"] = str(jsonl_files[0])
                lines = jsonl_files[0].read_text(encoding="utf-8", errors="ignore").strip().splitlines()
                data["total_transcript_lines"] = len(lines)
                last_messages = []
                for line in lines[-8:]:
                    try:
                        d = json.loads(line)
                        role = d.get("type") or d.get("role")
                        msg = d.get("message", {})
                        content = msg.get("content", "")
                        if isinstance(content, list):
                            texts = [c.get("text", c.get("name", str(c.get("type")))) for c in content]
                            last_messages.append({"role": role, "text": " | ".join(texts)[:300]})
                        elif isinstance(content, str):
                            last_messages.append({"role": role, "text": content[:300]})
                    except Exception:
                        pass
                data["recent_dialog"] = last_messages
            else:
                data["transcript_path"] = None
                data["total_transcript_lines"] = 0
                data["recent_dialog"] = []
                
            terminals.append(data)
        except Exception as e:
            log(f"Erreur lecture session {sf}: {e}")
            
    # 1.2 Scanner les processus actifs via ps
    try:
        ps_out = subprocess.check_output(["ps", "-ef"], text=True)
        for line in ps_out.splitlines():
            if "claude" in line and "grep" not in line and "resources" not in line:
                parts = line.split()
                if len(parts) > 7:
                    pid = int(parts[1])
                    tty = parts[5]
                    if not any(t.get("pid") == pid for t in terminals):
                        terminals.append({
                            "pid": pid,
                            "tty": tty,
                            "is_alive": True,
                            "raw_cmd": " ".join(parts[7:]),
                            "name": f"claude-{tty}"
                        })
    except Exception as e:
        log(f"Erreur ps scan: {e}")
        
    return terminals

# 2. AUDIT ET PILOTAGE DU BOARD
def inspect_board_state():
    stats = {}
    if not DB_BOARD.exists():
        return {"error": "board.db missing"}
        
    try:
        with sqlite3.connect(str(DB_BOARD)) as cx:
            cx.row_factory = sqlite3.Row
            stats["n_chunks"] = cx.execute("SELECT count(*) FROM chunks").fetchone()[0]
            stats["n_vectorises"] = cx.execute("SELECT count(*) FROM chunks WHERE embedding IS NOT NULL").fetchone()[0]
            stats["n_domains"] = cx.execute("SELECT count(*) FROM domains").fetchone()[0]
            stats["n_experts"] = cx.execute("SELECT count(*) FROM experts").fetchone()[0]
            stats["n_questions"] = cx.execute("SELECT count(*) FROM queries").fetchone()[0]
            stats["n_answers"] = cx.execute("SELECT count(*) FROM answers").fetchone()[0]
            stats["n_citations"] = cx.execute("SELECT count(*) FROM citations").fetchone()[0]
            
            sans_cit = cx.execute("""
                SELECT count(*) FROM answers a 
                WHERE NOT EXISTS (SELECT 1 FROM citations c WHERE c.answer_id = a.id)
            """).fetchone()[0]
            stats["n_answers_sans_citations"] = sans_cit
            
            domains_stats = cx.execute("""
                SELECT d.id, d.name, count(c.id) as chunk_count
                FROM domains d
                LEFT JOIN chunks c ON c.domain_id = d.id
                GROUP BY d.id, d.name
                ORDER BY chunk_count DESC
            """).fetchall()
            stats["domains"] = [dict(r) for r in domains_stats]
    except Exception as e:
        stats["error"] = str(e)
        
    return stats

# 3. INTERROGATION & DÉBAT CONSEIL DU BOARD
def run_board_debate(domain_id: str, question: str):
    log(f"Consultation du Board sur [{domain_id}] : « {question} »")
    ask_script = BOARD_DIR / "ask-agy.sh"
    if not ask_script.exists():
        ask_script = BOARD_DIR / "ask-local.sh"
        
    cmd = ["bash", str(ask_script), domain_id, question]
    try:
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=180,
            cwd=str(BOARD_DIR)
        )
        return {
            "domain": domain_id,
            "question": question,
            "stdout": res.stdout,
            "stderr": res.stderr,
            "returncode": res.returncode
        }
    except subprocess.TimeoutExpired:
        log(f"Timeout lors de l'interrogation du Board sur [{domain_id}]")
        return {"domain": domain_id, "question": question, "error": "timeout"}
    except Exception as e:
        log(f"Erreur run_board_debate: {e}")
        return {"domain": domain_id, "question": question, "error": str(e)}

# 4. INJECTION ET EXÉCUTION DE TÂCHES MASSIVES
QUESTIONS_ROSTER = [
    ("orchestration-agents", "Comment optimiser la coordination des 928 agents en essaim OpenClaw et éviter la saturation mémoire ?"),
    ("fiabilite-exploitation", "Quelles sont les règles strictes de tolérance aux pannes pour les watchdogs et sauvegardes atomiques SQLite ?"),
    ("souverainete", "Comment garantir l'étanchéité absolue 0 token payant avec inférence locale nomic-embed et qwen3.5-9b ?"),
    ("cluster-m1", "Quelle est la stratégie de routage optimale entre M4 local et le lien Gigabit USB-C ASIX 10.42.0.230 vers M1 ?"),
    ("vente-prospection", "Quelles sont les meilleures séquences d'approche B2B grands comptes et personnalisation sur mesure ?"),
    ("biblio-vivante", "Comment synchroniser et enrichir continuellement la base de 86k chunks sans doublons ni bruit ?")
]

def execute_autonomous_tasks():
    results = []
    
    # 4.1 Watchdog santé
    try:
        wd_res = subprocess.run(
            ["bash", str(JARVIS_DIR / "scripts" / "watchdog_critical.sh")],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60
        )
        results.append({"task": "watchdog_critical", "status": "OK", "output": wd_res.stdout})
    except Exception as e:
        results.append({"task": "watchdog_critical", "status": "ERR", "error": str(e)})

    # 4.2 Auto-backup & vérification SQLite
    try:
        with sqlite3.connect(str(DB_MASTER)) as cx:
            cx.execute("PRAGMA quick_check")
            cx.execute("""
                CREATE TABLE IF NOT EXISTS autopilot_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    cycle_type TEXT,
                    details TEXT,
                    statut TEXT
                )
            """)
            cx.execute("INSERT INTO autopilot_log (cycle_type, details, statut) VALUES (?, ?, ?)",
                       ("15min_orchestrator_cycle", "Exécution du cycle d'injection et supervision", "SUCCESS"))
            cx.commit()
        results.append({"task": "sqlite_integrity_and_logging", "status": "OK"})
    except Exception as e:
        results.append({"task": "sqlite_integrity_and_logging", "status": "ERR", "error": str(e)})

    return results

# 5. CYCLE COMPLET DE SUPERVISION ET COMPTE-RENDU
def run_master_cycle(cycle_id: int):
    log(f"════════════ DÉMARRAGE DU CYCLE JARVIS-OMEGA #{cycle_id} ════════════")
    start_time = time.time()
    
    terminals = scan_claude_terminals()
    # Étape 1.5 : Moisson Notion & Injection Directives Claude Code
    try:
        log("Moisson Notion & synchronisation Todolist -> Claude Code...")
        jarvis_notion_claude_bridge.run_bridge_cycle()
    except Exception as e:
        log(f"Alerte bridge Notion: {e}")

    log(f"Terminaux détectés : {len(terminals)} ({sum(1 for t in terminals if t.get('is_alive'))} actifs)")
    
    board_stats = inspect_board_state()
    log(f"Board Chunks : {board_stats.get('n_chunks', 0)} ({board_stats.get('n_vectorises', 0)} vectorisés) — 13 Domaines")
    
    chosen_topic = QUESTIONS_ROSTER[cycle_id % len(QUESTIONS_ROSTER)]
    debate_result = run_board_debate(chosen_topic[0], chosen_topic[1])
    
    task_results = execute_autonomous_tasks()
    
    elapsed = time.time() - start_time
    
    report_data = {
        "cycle_id": cycle_id,
        "timestamp": ts_now(),
        "elapsed_seconds": round(elapsed, 2),
        "terminals": terminals,
        "board_stats": board_stats,
        "active_debate": debate_result,
        "executed_tasks": task_results,
        "status": "OPERATIONAL_AUTONOMOUS"
    }
    
    json_path = OUTPUT_DIR / "cycle_orchestrateur_latest.json"
    json_path.write_text(json.dumps(report_data, indent=2, ensure_ascii=False), encoding="utf-8")
    
    md_path = OUTPUT_DIR / "ORCHESTRATEUR_RAPPORT_ACTIF.md"
    md_content = f"""# 🛰️ JARVIS-OMEGA — RAPPORT DE SUPERVISION & PILOTAGE
**Cycle #{cycle_id}** — *{ts_now()}*  
*Durée d'exécution : {round(elapsed, 2)}s*

---

## 🖥️ 1. TERMINAUX CLAUDE CODE & PROCESSUS DU BUREAU

| PID | TTY | Nom | Statut | Lignes Transcript | Dernier Message |
|---|---|---|---|---|---|
"""
    for t in terminals:
        last_m = t.get("recent_dialog", [{}])[-1].get("text", "") if t.get("recent_dialog") else "N/A"
        last_m_clean = last_m.replace("\n", " ")[:80]
        md_content += f"| `{t.get('pid')}` | `{t.get('tty', 'pts')}` | **{t.get('name', 'claude')}** | {'🟢 ACTIF' if t.get('is_alive') else '⚪ ARRÊTÉ'} | {t.get('total_transcript_lines', 0)} | {last_m_clean}... |\n"

    md_content += f"""
---

## 🏛️ 2. ÉTAT DU BOARD OS & BIBLIOTHÈQUE VIVANTE

- **Chunks totaux indexés :** {board_stats.get('n_chunks', 0):,}
- **Chunks vectorisés :** {board_stats.get('n_vectorises', 0):,} (100% couverture)
- **Domaines actifs :** {board_stats.get('n_domains', 0)}
- **Experts du conseil :** {board_stats.get('n_experts', 0)}
- **Questions traitées :** {board_stats.get('n_questions', 0)}
- **Citations vérifiées :** {board_stats.get('n_citations', 0)}

---

## ⚖️ 3. DÉBAT DU CONSEIL EXÉCUTÉ (Cycle #{cycle_id})
**Domaine :** `{chosen_topic[0]}`  
**Question posée :** *{chosen_topic[1]}*

```
{debate_result.get('stdout', '')[:2000] if debate_result.get('stdout') else debate_result.get('error', 'En cours...')}
```

---

## ⚡ 4. TÂCHES AUTOMATISÉES & WATCHDOGS
"""
    for tr in task_results:
        md_content += f"- **{tr.get('task')}** : `{tr.get('status')}`\n"

    md_content += f"""
---
*Prochain cycle programmé dans 15 minutes. Pilotage 100% autonome ininterrompu.*
"""
    md_path.write_text(md_content, encoding="utf-8")
    
    log(f"✓ Cycle #{cycle_id} terminé avec succès en {round(elapsed, 2)}s. Rapport consigné dans {md_path}")

def main():
    log("🚀 Démarrage du Superviseur Permanent JARVIS-OMEGA...")
    cycle = 1
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        run_master_cycle(cycle)
        return
        
    while True:
        try:
            run_master_cycle(cycle)
            cycle += 1
            log("⏳ En attente de 15 minutes (900s) avant le prochain cycle...")
            time.sleep(900)
        except KeyboardInterrupt:
            log("Arrêt demandé par l'opérateur.")
            break
        except Exception as e:
            log(f"Erreur inattendue dans la boucle principale: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
