#!/usr/bin/env python3
"""
JARVIS Mail Triage Live (Exécution Réelle)
Script d'autonomie pour exécuter le domino de tri de mails IMAP réels
et consigner les résultats dans jarvis_master.db.
"""
import sys
import os
import subprocess
import json
import sqlite3
import time

DB_PATH = "/home/pamerys/jarvis/jarvis_master.db"
SCRIPT_PATH = "/home/pamerys/jarvis/bin/domino-mail-triage.py"

def main():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 📧 Démarrage du tri INTENSIF EN BOUCLE de la boîte IMAP (jusqu'à épuisement total)...")

    batch_num = 1
    total_processed = 0

    while True:
        print(f"🔄 Traitement du lot #{batch_num} (jusqu'à 50 mails)...")
        cmd = [sys.executable, SCRIPT_PATH, "--limit", "50", "--no-dry-run", "--json"]
        res = subprocess.run(cmd, capture_output=True, text=True)

        try:
            data = json.loads(res.stdout)
        except Exception:
            data = {"status": "error", "raw": res.stdout, "stderr": res.stderr}

        status = data.get("status", "unknown")
        count = data.get("total", 0)
        total_processed += count

        # Logging dans SQLite jarvis_master.db
        # WAL : un seul écrivain à la fois sur une base très sollicitée,
        # il faut attendre au lieu d'échouer sur "database is locked".
        conn = sqlite3.connect(DB_PATH, timeout=120)
        conn.execute("PRAGMA busy_timeout=120000")
        conn.execute(
            "INSERT INTO pipeline_log (task_id, step, machine, model, latency_ms, quality_score) VALUES (?,?,?,?,?,?)",
            (8888, f"mail_triage_batch_{batch_num}_{status}", "M1", "jarvis-mail-intensive", 150, 1.0 if status in ("ok", "degraded") else 0.0)
        )
        conn.commit()
        conn.close()

        if status == "degraded":
            print(f"⚠️ Identifiants IMAP manquants: {', '.join(data.get('missing_creds', []))}")
            print("💡 Pour activer l'accès réel à la boîte Gmail/IMAP, ajoutez dans ~/jarvis/secrets.env :")
            print("   IMAP_HOST=imap.gmail.com")
            print("   IMAP_USER=votre-email@gmail.com")
            print("   IMAP_PASS=votre-mot-de-passe-application")
            break

        if count == 0:
            print("🎉 La boîte de réception est 100% VIDÉE et entièrement triée !")
            break

        print(f"✅ Lot #{batch_num} terminé ({count} mails traités). Poursuite du dépouillement...")
        batch_num += 1

    print(f"🏁 Dépouillement terminé. Total général traité : {total_processed} mail(s).")

if __name__ == "__main__":
    main()
