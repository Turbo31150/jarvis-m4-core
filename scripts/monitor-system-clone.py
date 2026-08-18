#!/usr/bin/env python3
import sys
import os
import re
import subprocess
import time
import json
from datetime import datetime, timezone
from pathlib import Path

# Ajouter le chemin vers les scripts Jarvis pour pouvoir importer util_logging
sys.path.append("/home/pamerys/jarvis/scripts")
try:
    from util_logging import get_logger, checkpoint
    logger = get_logger("jarvis.antigravity-cloning")
except ImportError:
    logger = None
    print("Warning: util_logging not found.")

LOG_DIR = Path("/home/pamerys/jarvis/logs/antigravity-cloning")
LOG_DIR.mkdir(parents=True, exist_ok=True)

def log_to_jsonl(lvl, msg):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_file = LOG_DIR / f"{today}.jsonl"
    ts = datetime.now(timezone.utc).isoformat()
    entry = {
        "ts": ts,
        "lvl": lvl,
        "svc": "jarvis.antigravity-cloning",
        "msg": msg
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"[{lvl}] {msg}")
    if logger:
        if lvl == "INFO":
            logger.info(msg)
        elif lvl == "WARNING":
            logger.warning(msg)
        elif lvl == "ERROR":
            logger.error(msg)

def get_tmux_output():
    try:
        res = subprocess.run(
            ["sudo", "tmux", "capture-pane", "-t", "clonage-crucial", "-p"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if res.returncode == 0:
            return res.stdout
    except Exception:
        pass
    return None

def check_tmux_session():
    try:
        res = subprocess.run(
            ["sudo", "tmux", "has-session", "-t", "clonage-crucial"],
            capture_output=True,
            timeout=5
        )
        return res.returncode == 0
    except Exception:
        return False

def check_orchestrator_running():
    try:
        res = subprocess.run(
            ["pgrep", "-f", "orchestrate-m3-clone.sh"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return res.returncode == 0
    except Exception:
        return False

def parse_ddrescue_output(output):
    if not output:
        return None
    
    # Ne s'intéresser qu'à la section Current status
    status_idx = output.find("Current status")
    if status_idx != -1:
        output = output[status_idx:]
        
    data = {}
    for line in output.splitlines():
        line = line.strip()
        # Enlever les codes d'échappement ANSI
        line = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', line)
        
        if "pct rescued:" in line:
            m = re.search(r"pct rescued:\s*([0-9.]+)%", line)
            if m:
                data["pct"] = float(m.group(1))
        
        # rescued: 186040 MB, ...
        # Attention à ne matcher rescued que s'il est au début ou après des espaces/virgules,
        # pour ne pas confondre avec pct rescued
        if "rescued:" in line and "pct rescued" not in line:
            m = re.search(r"(?:^|\s)rescued:\s*([0-9.]+)\s*([a-zA-Z]+)", line)
            if m:
                data["rescued"] = f"{m.group(1)} {m.group(2)}"
                
        if "current rate:" in line:
            m = re.search(r"current rate:\s*([0-9.]+)\s*([a-zA-Z/]+)", line)
            if m:
                data["rate"] = f"{m.group(1)} {m.group(2)}"
                
        if "average rate:" in line:
            m = re.search(r"average rate:\s*([0-9.]+)\s*([a-zA-Z/]+)", line)
            if m:
                data["avg_rate"] = f"{m.group(1)} {m.group(2)}"
                
        if "remaining time:" in line:
            m = re.search(r"remaining time:\s*([a-zA-Z0-9\s]+)", line)
            if m:
                data["remaining"] = m.group(1).strip()
                
        if "run time:" in line:
            m = re.search(r"run time:\s*([a-zA-Z0-9\s]+)", line)
            if m:
                data["runtime"] = m.group(1).strip()
                
    return data if data else None

def main():
    log_to_jsonl("INFO", "Démarrage du monitoring de clonage système.")
    
    last_pct = -1.0
    consecutive_missing = 0
    
    while True:
        tmux_active = check_tmux_session()
        
        if tmux_active:
            consecutive_missing = 0
            output = get_tmux_output()
            data = parse_ddrescue_output(output)
            
            if data:
                pct = data.get("pct", 0.0)
                rescued = data.get("rescued", "N/A")
                rate = data.get("rate", "N/A")
                remaining = data.get("remaining", "N/A")
                runtime = data.get("runtime", "N/A")
                
                # N'écrire dans le fichier de log que si la progression a changé significativement ou toutes les 60s
                # Pour éviter le spam, on peut logguer si la progression augmente de >= 0.5% ou toutes les 3 minutes
                # Mais on met toujours à jour le checkpoint SQLite pour le monitoring en temps réel
                msg = f"Progression clonage : {pct}% ({rescued} écrits). Vitesse: {rate}. Temps écoulé: {runtime}. Restant: {remaining}."
                
                # Checkpoint SQLite pour le temps réel
                try:
                    checkpoint("jarvis.antigravity-cloning", "clonage_status", {
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "progression_pct": pct,
                        "rescued": rescued,
                        "rate": rate,
                        "runtime": runtime,
                        "remaining": remaining,
                        "status": "CLONING"
                    })
                except Exception as e:
                    print(f"Error updating checkpoint: {e}")
                
                # Log JSONL si progression >= 0.5% ou premier passage
                if last_pct == -1.0 or (pct - last_pct) >= 0.5:
                    log_to_jsonl("INFO", msg)
                    last_pct = pct
            else:
                # Si ddrescue s'initialise
                try:
                    checkpoint("jarvis.antigravity-cloning", "clonage_status", {
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "status": "INITIALIZING"
                    })
                except Exception:
                    pass
        else:
            consecutive_missing += 1
            # Si la session tmux n'existe pas pendant plus de 3 passages (pour éviter les faux négatifs de redémarrage de session)
            if consecutive_missing >= 3:
                # Vérifier si l'orchestrateur tourne encore
                orch_active = check_orchestrator_running()
                if orch_active:
                    log_to_jsonl("INFO", "Clonage physique par secteurs terminé. Adaptation post-clonage et configuration M3 en cours...")
                    try:
                        checkpoint("jarvis.antigravity-cloning", "clonage_status", {
                            "ts": datetime.now(timezone.utc).isoformat(),
                            "status": "POST_CLONE_ADAPTATION"
                        })
                    except Exception:
                        pass
                else:
                    # Ni tmux ni orchestrateur ne tournent, vérifier si le log d'orchestration indique la fin
                    orch_log = Path("/home/pamerys/jarvis/logs/orchestrate_m3_clone.log")
                    if orch_log.exists():
                        log_content = orch_log.read_text(encoding="utf-8")
                        if "Fin de l'orchestration et adaptation pour M3" in log_content:
                            log_to_jsonl("INFO", "Clonage et adaptation terminés à 100% avec succès. Prêt pour M3 (HP Portable) !")
                            try:
                                checkpoint("jarvis.antigravity-cloning", "clonage_status", {
                                    "ts": datetime.now(timezone.utc).isoformat(),
                                    "progression_pct": 100.0,
                                    "status": "COMPLETED"
                                })
                            except Exception:
                                pass
                            break
                        elif "ERREUR" in log_content:
                            log_to_jsonl("ERROR", "Le processus de clonage ou d'adaptation a échoué. Veuillez vérifier les logs d'orchestration.")
                            try:
                                checkpoint("jarvis.antigravity-cloning", "clonage_status", {
                                    "ts": datetime.now(timezone.utc).isoformat(),
                                    "status": "FAILED"
                                })
                            except Exception:
                                pass
                            break
                    
                    log_to_jsonl("WARNING", "Session de clonage introuvable et orchestrateur arrêté.")
                    break
        
        time.sleep(15)

if __name__ == "__main__":
    main()
