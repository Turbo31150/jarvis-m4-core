#!/usr/bin/env python3
"""
M6 ARCHITECTURE BUFFER & PRE-PROCESSOR PIPELINE (MODE SECOUR FILAIRE DIRECT 10.42.0.230)
1. Reçoit l'intention / la tâche brute.
2. Interroge la BIBLIOTHÈQUE locale (bloc.sh) & les mots-clés de commande.
3. Exécute les mini-bash de pré-traitement pour 'mâcher le travail'.
4. Transmet le contexte enrichi et pré-mâché à M1 pour l'inférence ou la validation finale.
"""
import os
import sys
import json
import subprocess
import urllib.request

M6_URL = "http://10.42.0.230:11434"
ROOT = "/home/pamerys/jarvis"

def preprocess_with_library_and_bash(prompt):
    print(f"[M6-BUFFER] 📥 Reçu sur tampon M6 : '{prompt}'")
    
    # Step 1: Inspection Bibliothèque (bloc.sh)
    preprocessed_data = []
    try:
        p = subprocess.run(["bash", f"{ROOT}/bin/bloc.sh", prompt], capture_output=True, text=True, timeout=10)
        out = p.stdout.strip()
        if out and not out.startswith("∅"):
            preprocessed_data.append(f"=== BLOC BIBLIOTHÈQUE IDENTIFIÉ ===\n{out}")
            print("[M6-BUFFER] ✅ Bloc Bibliothèque trouvé et pré-extrait.")
    except Exception as e:
        print(f"[M6-BUFFER] Info bloc: {e}")

    # Step 2: Auto-détection mots-clés et mini-bash pré-traitement
    p_lower = prompt.lower()
    bash_results = []
    
    if any(k in p_lower for k in ["gpu", "nvidia", "vram"]):
        print("[M6-BUFFER] ⚙️ Détection mot-clé 'GPU' -> Mâchage bash nvidia-smi...")
        res = subprocess.run(["nvidia-smi", "--query-gpu=index,name,utilization.gpu,memory.used,memory.total", "--format=csv,noheader"], capture_output=True, text=True)
        bash_results.append(f"=== PRÉ-CALCUL GPU M1/M6 ===\n{res.stdout.strip()}")
        
    if any(k in p_lower for k in ["processus", "cpu", "load", "ram", "mémoire"]):
        print("[M6-BUFFER] ⚙️ Détection mot-clé 'SYSTEME' -> Mâchage bash uptime & memory...")
        res = subprocess.run(["uptime"], capture_output=True, text=True)
        bash_results.append(f"=== PRÉ-CALCUL CHARGE M1/M6 ===\n{res.stdout.strip()}")
        
    if any(k in p_lower for k in ["réseau", "ping", "cluster", "m1", "m4", "m6"]):
        print("[M6-BUFFER] ⚙️ Détection mot-clé 'RESEAU' -> Mâchage bash ping cluster...")
        res = subprocess.run(["ping", "-c", "1", "10.42.0.230"], capture_output=True, text=True)
        bash_results.append(f"=== PRÉ-CALCUL LIAISON FILAIRE M6 ===\n{res.stdout.strip()}")

    # Step 3: Analyse / Synthèse rapide par le modèle léger sur M6 (qwen2.5:1.5b)
    m6_summary = ""
    try:
        payload = {
            "model": "qwen2.5:1.5b",
            "prompt": f"Pré-analyse rapide pour le maître M1:\nRequête: {prompt}\nDonnées préparées: {json.dumps(bash_results)}\nFais une synthèse ultra-courte:",
            "stream": False
        }
        req = urllib.request.Request(f"{M6_URL}/api/generate", data=json.dumps(payload).encode('utf-8'), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            res_json = json.loads(resp.read().decode('utf-8'))
            m6_summary = res_json.get("response", "").strip()
            print("[M6-BUFFER] ⚡ Modèle M6 (qwen2.5:1.5b) a pré-mâché le texte.")
    except Exception as e:
        print(f"[M6-BUFFER] Info modèle M6: {e}")

    # Step 4: Assemblage du package pré-mâché prêt pour envoi à M1
    final_package = {
        "original_prompt": prompt,
        "preprocessed_biblio": "\n".join(preprocessed_data),
        "preprocessed_bash_outputs": "\n".join(bash_results),
        "m6_pre_analysis": m6_summary,
        "status": "PREPROCESSED_BY_M6_READY_FOR_M1"
    }

    print("\n=======================================================")
    print("📦 PACKAGE PRÉ-MÂCHÉ PAR M6 POUR M1 :")
    print(json.dumps(final_package, indent=2, ensure_ascii=False))
    print("=======================================================\n")
    return final_package

if __name__ == "__main__":
    prompt_in = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Vérifier l'état GPU et la charge du réseau M6"
    preprocess_with_library_and_bash(prompt_in)
