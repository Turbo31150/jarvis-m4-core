import json
import os
import glob

# Paramètres extrêmes de performance LM Studio (CUDA, Multi-GPU, Context, Memory Lock)
extreme_settings = {
    "preset_name": "ULTRA_PERFORMANCE_JARVIS",
    "gpu_offload_ratio": 1.0,           # 100% VRAM GPU
    "n_gpu_layers": 999,                 # Force toutes les couches sur GPU
    "flash_attention_2": True,           # Flash Attention v2
    "context_length": 8192,              # Contexte étendu 8k
    "eval_batch_size": 1024,             # Batch d'évaluation poussé à 1024
    "logical_threads": 16,               # Tous les threads CPU alloués
    "use_mmap": True,                    # Memory-mapped model loading
    "use_mlock": True,                   # Lock VRAM/RAM (empêche tout swap)
    "rope_freq_scale": 1.0,
    "temperature": 0.1,
    "top_p": 0.9,
    "repeat_penalty": 1.05
}

# Ingestion dans la configuration hub local et distante
openclaw_path = "/home/pamerys/.openclaw/openclaw.json"
if os.path.exists(openclaw_path):
    with open(openclaw_path, 'r') as f:
        data = json.load(f)
    data["lmstudio_extreme"] = extreme_settings
    for p in data.get("providers", []):
        if "lmstudio" in p.get("name", "").lower() or "m1" in p.get("name", "").lower():
            p.update(extreme_settings)
    with open(openclaw_path, 'w') as f:
        json.dump(data, f, indent=2)

print("Réglages EXTRÊMES LM Studio appliqués : GPU Offload 100%, mlock=True, FlashAttention2=True, Batch=1024 !")
