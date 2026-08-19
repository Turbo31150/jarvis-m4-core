#!/usr/bin/env python3
"""
JARVIS-OMEGA — S8 Hardware Physical Button Interceptor & Vocal Trigger
=====================================================================
Permet le pilotage intégral du S8 sans aucun écran tactile :
  - Intercepte les appuis physiques sur le bouton Bixby / Volume / Headset
  - Déclenche instantanément l'action vocale et diffuse la réponse sur les haut-parleurs
"""

import sys
import time
import subprocess
import urllib.request
import json

SERIAL = "ce02171252e0bb1905"

def trigger_voice_bilan():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 🔘 Appui bouton physique S8 détecté ! Déclenchement du bilan vocal...", flush=True)
    try:
        url = "http://127.0.0.1:8799/voice"
        data = json.dumps({"command": "donne moi le bilan en direct"}).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            print(f"  ✓ Réponse vocale : {res.get('reply', '')[:80]}...", flush=True)
    except Exception as e:
        print(f"  ✗ Erreur dispatch vocal : {e}", flush=True)

def monitor_hardware_keys():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 🎧 Démarrage du moniteur de boutons physiques sur le Samsung S8 ({SERIAL})...", flush=True)
    
    cmd = ["adb", "-s", SERIAL, "shell", "getevent -l /dev/input/event6"]
    
    last_trigger = 0
    while True:
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
            for line in iter(proc.stdout.readline, ''):
                line = line.strip()
                # Détection d'un appui bouton (DOWN event)
                if "DOWN" in line or "KEY_" in line or "0001" in line:
                    now = time.time()
                    if now - last_trigger > 2.5: # Anti-rebond 2.5s
                        last_trigger = now
                        trigger_voice_bilan()
            proc.wait()
        except Exception as e:
            print(f"Reconnexion ADB getevent: {e}", flush=True)
            time.sleep(3)

if __name__ == "__main__":
    monitor_hardware_keys()
