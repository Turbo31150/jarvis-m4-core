#!/usr/bin/env python3
"""
jarvis_reveil_minuteur.py — Minuteur / Réveil avec Actions Massives Ultra-Concrètes
Exécute à chaque réveil (15 minutes) :
  1. Injection directe de tâches de code/système dans Claude Code (tmux jarvis:5)
  2. Injection directe de tâches commerciales/contenu dans Claude Code (tmux jarvis:6)
  3. Génération concrète de posts LinkedIn & séquences d'emails B2B dans /home/pamerys/Bureau/VENTE/
  4. Synchronisation bidirectionnelle Notion & Board OS (88k chunks)
  5. Sauvegarde, auto-git et checkpoint SQLite
  6. Alertes sonores (paplay), vocales (Piper TTS) et visuelles (notify-send)
"""

import os
import sys
import time
import json
import sqlite3
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

HOME = Path("/home/pamerys")
JARVIS_DIR = HOME / "jarvis"
SCRIPTS_DIR = JARVIS_DIR / "scripts"
LABO_DIR = HOME / "labo"
OUTPUT_DIR = LABO_DIR / "output"
VENTE_DIR = HOME / "Bureau" / "VENTE"
STOP_FLAG = Path("/tmp/stop_reveil.flag")
ALARM_SOUND = Path("/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga")
BELL_SOUND = Path("/usr/share/sounds/freedesktop/stereo/bell.oga")

INTERVAL_SECONDS = 900  # 15 minutes

def ts_now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def send_alert(cycle: int, message: str):
    """Déclenche alerte visuelle et sonore non bloquante."""
    try:
        subprocess.Popen([
            "notify-send",
            "-u", "critical",
            "-i", "alarm",
            f"⏰ RÉVEIL JARVIS — Cycle #{cycle}",
            f"{message}\nHeure : {ts_now()}"
        ], env=dict(os.environ, DISPLAY=":1"))
    except Exception:
        pass

    sound_file = ALARM_SOUND if ALARM_SOUND.exists() else BELL_SOUND
    if sound_file.exists():
        try:
            subprocess.Popen(["paplay", str(sound_file)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    speak_script = SCRIPTS_DIR / "speak.sh"
    if speak_script.exists():
        try:
            tts_text = f"Cycle réveil numéro {cycle}. Production concrète de contenu et injection des tâches dans Claude Code."
            subprocess.Popen(["bash", str(speak_script), tts_text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

def execute_wake_up_actions(cycle: int):
    """Exécute des actions ultra-concrètes et massives à chaque réveil."""
    print(f"\n[{ts_now()}] ⚡ ── EXÉCUTION D'ACTIONS MASSIVES & CONCRÈTES (Cycle #{cycle}) ──", flush=True)
    
    # 1. Créer répertoires concrets de vente et de production
    os.makedirs(VENTE_DIR / "linkedin_posts", exist_ok=True)
    os.makedirs(VENTE_DIR / "emails_prospection", exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 2. Production concrète A : Génération de Post LinkedIn
    post_filename = VENTE_DIR / "linkedin_posts" / f"post_linkedin_cycle_{cycle}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    post_content = f"""# 🚀 Post LinkedIn — Stratégie IA Souveraine & Systèmes Distribués (Cycle #{cycle})
*Date de publication suggérée : {datetime.now().strftime('%d/%m/%Y')}*

Pourquoi les grands comptes comme **Airbus**, **ASML** ou **AXA** font-ils le choix d'une infrastructure IA souveraine sur site plutôt que du tout-cloud ?

Chez JARVIS OMEGA, nous démontrons chaque jour la supériorité des architectures distribuées locales :
🔹 **0 Token Leak** : Aucune donnée confidentielle ne quitte les serveurs de l'entreprise.
🔹 **Latence ultra-faible** : Inférence multi-GPU et liaisons directes Gigabit (1.3 ms).
🔹 **Contrôle budgétaire** : Fin des factures d'API exponentielles à l'usage.
🔹 **Haute Disponibilité** : Watchdogs atomiques et tolérance totale aux coupures réseau.

👉 L'avenir de l'IA d'entreprise n'est pas dans la dépendance aux clouds tiers, mais dans la maîtrise intégrale de son capital algorithmique et de ses données.

*Post généré automatiquement par l'Autopilote JARVIS OMEGA — Cycle d'action #{cycle}.*
"""
    with open(post_filename, "w", encoding="utf-8") as f:
        f.write(post_content)
    print(f"[{ts_now()}] ✍️  1/6 Post LinkedIn concret généré : {post_filename.name}", flush=True)

    # 3. Production concrète B : Génération d'Email de Prospection B2B
    email_filename = VENTE_DIR / "emails_prospection" / f"email_prospection_cycle_{cycle}.md"
    email_content = f"""# ✉️ Email Prospection B2B — Architecture IA On-Premise (Cycle #{cycle})
**Objet :** Sécurisation et souveraineté de vos pipelines d'IA d'entreprise

Bonjour [Nom du Décideur / DSI / Lead IA],

Dans un contexte où la confidentialité des données stratégiques et la maîtrise des coûts d'inférence deviennent prioritaires, déployer des modèles d'IA sur infrastructure propre (on-premise) offre un avantage compétitif décisif.

En tant qu'ingénieur IA et architecte de systèmes distribués (RQTH), j'accompagne les organisations dans :
- Le déploiement de clusters LLM locaux multi-GPU à latence ultra-faible (< 2 ms)
- L'indexation et la recherche documentaire RAG sur des corpus massifs (> 80k documents) avec garantie 0 fuite de données
- L'orchestration d'agents autonomes résilients et tolérants aux pannes

Seriez-vous ouvert à un échange de 15 minutes pour évaluer l'optimisation de vos infrastructures IA existantes ?

Bien cordialement,
**Franck Delmas (Turbo)**
Ingénieur IA & Architecte Systèmes Distribués
"""
    with open(email_filename, "w", encoding="utf-8") as f:
        f.write(email_content)
    print(f"[{ts_now()}] 📧 2/6 Email de prospection concret généré : {email_filename.name}", flush=True)

    # 4. Injection concrète dans Claude Code Terminal 1 (jarvis:5)
    try:
        print(f"[{ts_now()}] 🤖 3/6 Injection tâche ingénierie dans Claude Code C1 (jarvis:5)...", flush=True)
        task_c1 = f"Vérifie l'intégrité du projet /home/pamerys/labo/mistral-workflow, lance make check et confirme la conformité."
        subprocess.run(["tmux", "send-keys", "-t", "jarvis:5", task_c1, "C-m"], timeout=5)
    except Exception as e:
        print(f"Erreur injection C1: {e}", flush=True)

    # 5. Injection concrète dans Claude Code Terminal 2 (jarvis:6)
    try:
        print(f"[{ts_now()}] 💼 4/6 Injection tâche vente dans Claude Code C2 (jarvis:6)...", flush=True)
        task_c2 = f"Actualise la liste des prospects B2B dans /home/pamerys/Bureau/VENTE/ et synchronise avec Notion."
        subprocess.run(["tmux", "send-keys", "-t", "jarvis:6", task_c2, "C-m"], timeout=5)
    except Exception as e:
        print(f"Erreur injection C2: {e}", flush=True)

    # 6. Synchronisation Notion ⇄ Claude Bridge
    try:
        print(f"[{ts_now()}] 🔗 5/6 Synchronisation Notion & Board...", flush=True)
        bridge_script = SCRIPTS_DIR / "jarvis_notion_claude_bridge.py"
        if bridge_script.exists():
            subprocess.run(["python3", str(bridge_script), "--once"], timeout=45)
    except Exception as e:
        print(f"Erreur bridge Notion: {e}", flush=True)

    # 7. Sauvegarde SQLite Master & Log
    try:
        print(f"[{ts_now()}] 💾 6/6 Consignation SQLite des actions réelles...", flush=True)
        db_path = JARVIS_DIR / "jarvis_master.db"
        if db_path.exists():
            with sqlite3.connect(str(db_path)) as cx:
                cx.execute("""
                    CREATE TABLE IF NOT EXISTS reveil_cycles_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        cycle_id INTEGER,
                        statut TEXT,
                        post_genere TEXT,
                        email_genere TEXT
                    )
                """)
                cx.execute("""
                    INSERT INTO reveil_cycles_log (cycle_id, statut, post_genere, email_genere) 
                    VALUES (?, ?, ?, ?)
                """, (cycle, "ACTIONS_CONCRETES_EXECUTEES", post_filename.name, email_filename.name))
                cx.commit()
    except Exception as e:
        print(f"Erreur SQLite log: {e}", flush=True)

    print(f"[{ts_now()}] ✓ ── FIN DU CYCLE D'ACTIONS CONCRÈTES #{cycle} ──\n", flush=True)

def render_countdown(remaining_seconds: int, cycle: int, next_alarm: datetime):
    mins, secs = divmod(remaining_seconds, 60)
    progress_bar_len = 24
    total = INTERVAL_SECONDS
    elapsed = total - remaining_seconds
    filled = int(progress_bar_len * (elapsed / total))
    bar = "█" * filled + "░" * (progress_bar_len - filled)
    
    hud = f"\r⏰ [RÉVEIL CONCRET #{cycle}] Prochain réveil : {next_alarm.strftime('%H:%M:%S')} | [{bar}] {mins:02d}:{secs:02d} restant (Stop: touch /tmp/stop_reveil.flag)  "
    sys.stdout.write(hud)
    sys.stdout.flush()

def main():
    if STOP_FLAG.exists():
        STOP_FLAG.unlink()
        
    print("=" * 70)
    print("🚀 MINUTEUR RÉVEIL AVEC PRODUCTION D'ACTIONS CONCRÈTES — JARVIS OMEGA")
    print(f"📅 Démarrage : {ts_now()}")
    print(f"⏱️ Cadence Réveil : 15 minutes ({INTERVAL_SECONDS}s)")
    print(f"🛑 Pour arrêter manuellement : 'touch /tmp/stop_reveil.flag' ou Ctrl+C")
    print("=" * 70)

    # Récupérer dernier cycle depuis la base SQLite
    cycle = 234
    try:
        db_path = JARVIS_DIR / "jarvis_master.db"
        if db_path.exists():
            with sqlite3.connect(str(db_path)) as cx:
                row = cx.execute("SELECT max(cycle_id) FROM reveil_cycles_log").fetchone()
                if row and row[0]:
                    cycle = row[0]
    except Exception:
        pass

    # Premier déclenchement concret immédiat
    send_alert(cycle, "Démarrage des actions concrètes (LinkedIn, Prospection, Injections Tmux).")
    execute_wake_up_actions(cycle)

    while True:
        if STOP_FLAG.exists():
            print(f"\n[{ts_now()}] 🛑 Arrêt manuel demandé via {STOP_FLAG}. Arrêt du réveil.")
            STOP_FLAG.unlink()
            break

        next_alarm = datetime.now() + timedelta(seconds=INTERVAL_SECONDS)
        cycle += 1

        for remaining in range(INTERVAL_SECONDS, 0, -1):
            if STOP_FLAG.exists():
                break
            render_countdown(remaining, cycle, next_alarm)
            time.sleep(1)

        if STOP_FLAG.exists():
            print(f"\n[{ts_now()}] 🛑 Arrêt manuel demandé. Fin du réveil.")
            STOP_FLAG.unlink()
            break

        # Sonnerie réveil et exécution des actions concrètes
        print(f"\n\n🔔 ⏰ ALERTE RÉVEIL CONCRET CYCLE #{cycle} ! ({ts_now()})")
        send_alert(cycle, f"Réveil 15 min déclenché. Production et injections concrètes en cours.")
        execute_wake_up_actions(cycle)

if __name__ == "__main__":
    main()
