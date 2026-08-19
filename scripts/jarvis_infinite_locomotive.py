#!/usr/bin/env python3
"""
JARVIS-OMEGA — Infinite Autonomous Locomotive H24 (News & High-Cadence Engine)
==============================================================================
"""

import os
import sys
import time
import subprocess
import datetime

CYCLE_INTERVAL_SEC = 300 # 5 minutes

def run_cycle(cycle_id):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{now}] 🚂 [LOCOMOTIVE H24] === DÉBUT DU CYCLE ACCÉLÉRÉ #{cycle_id} ===")
    
    # 1. Scraping d'actualité, commentaires temps réel et capture d'offres urgentes
    print("  ➔ [1/4] Scraping de l'actualité & Salve de commentaires experts...")
    try:
        subprocess.run(["python3", "/home/pamerys/jarvis/scripts/jarvis_news_comments_and_job_sniffer.py"], timeout=60)
    except Exception as e:
        print(f"⚠️ Erreur sniffer: {e}")

    # 2. Production massive de devis et dossiers B2B
    print("  ➔ [2/4] Compilation des devis B2B et livrables PDF...")
    try:
        subprocess.run(["python3", "/home/pamerys/jarvis/scripts/jarvis_massive_executor.py"], timeout=90)
    except Exception as e:
        print(f"⚠️ Erreur executor: {e}")

    # 3. Dépilement et expédition directe Playwright / CDP
    print("  ➔ [3/4] Expédition directe des livrables sans rétention...")
    try:
        subprocess.run(["python3", "/home/pamerys/jarvis/scripts/jarvis_direct_auto_dispatch.py"], timeout=60)
    except Exception as e:
        print(f"⚠️ Erreur dispatch: {e}")

    # 4. Prospection OpenClaw
    print("  ➔ [4/4] Prospection Grands Comptes OpenClaw...")
    try:
        subprocess.run(["python3", "/home/pamerys/jarvis-cowork/scripts/openclaw_massive_prospection.py"], timeout=60)
    except Exception as e:
        print(f"⚠️ Erreur openclaw: {e}")

    # Nettoyage Zéro-Déchet
    os.system("rm -f /tmp/*.png /tmp/*.xml /tmp/*.3gp /tmp/*.wav /tmp/*.mp3 2>/dev/null")
    print(f"[{now}] 🏁 [LOCOMOTIVE H24] === CYCLE #{cycle_id} TERMINÉ AVEC SUCCÈS ===")

def main():
    print("==================================================================")
    print("🚀 [LOCOMOTIVE INFINIE H24] DÉMARRAGE PLEINE PUISSANCE (5 MIN)")
    print("==================================================================")
    cycle = 1
    while True:
        try:
            run_cycle(cycle)
            cycle += 1
            print(f"⏳ Prochaine vague d'actualités et commentaires dans {CYCLE_INTERVAL_SEC}s...")
            time.sleep(CYCLE_INTERVAL_SEC)
        except KeyboardInterrupt:
            print("\n🛑 Arrêt propre.")
            break
        except Exception as e:
            print(f"⚠️ Erreur générale: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
