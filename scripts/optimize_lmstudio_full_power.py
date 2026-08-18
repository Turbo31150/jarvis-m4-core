import json
import os

# Fichier de config globale OpenClaw et LM Studio Integration
config_path = "/home/pamerys/.openclaw/openclaw.json"

if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        data = json.load(f)
    
    # 1. Tuning Ultra Puissance pour LM Studio M1 & M6
    lmstudio_tuning = {
        "gpu_layers": -1,                # Auto-Offload Max (Tous les layers sur GPU)
        "ctx_size": 8192,                # Taille de contexte étendue 8K
        "threads": 12,                   # Utilisation maximale des threads CPU
        "batch_size": 512,               # Batch size élevé pour vitesse maximale
        "ubatch_size": 256,              # Micro-batching optimisé
        "flash_attn": True,              # Flash Attention 2 activé
        "eval_batch_size": 512,
        "n_gpu_layers": 99,
        "keep_model_in_memory": True,    # Modèle maintenu en VRAM (Warmload permanent)
        "temperature": 0.1,              # Réponses rapides et déterministes
        "timeout_ms": 30000
    }
    
    data["lmstudio_ultra_settings"] = lmstudio_tuning
    
    for p in data.get("providers", []):
        if "lmstudio" in p.get("name", "").lower():
            p.update(lmstudio_tuning)
            
    with open(config_path, 'w') as f:
        json.dump(data, f, indent=2)
        
    print("PARAMÈTRES LM STUDIO : Réglage Ultra Puissance (GPU Offload = -1, Flash Attention = True, Warmload = True, Batch = 512) appliqué !")
