#!/usr/bin/env python3
"""Monitor LM Studio performance - sortie pour conky et logs"""
import json, subprocess, urllib.request, os, sys
from datetime import datetime

API_BASE = "http://127.0.0.1:11235"

def get_models():
    try:
        with urllib.request.urlopen(f"{API_BASE}/v1/models", timeout=2) as r:
            data = json.loads(r.read())
            return [m["id"] for m in data.get("data", [])]
    except:
        return []

def get_gpu_info():
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name,memory.used,memory.total,utilization.gpu,temperature.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=3
        )
        gpus = []
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 6:
                    gpus.append({
                        "id": parts[0], "name": parts[1],
                        "mem_used": int(parts[2]), "mem_total": int(parts[3]),
                        "util": parts[4], "temp": parts[5]
                    })
        return gpus
    except:
        return []

def format_output():
    models = get_models()
    gpus = get_gpu_info()
    lines = []
    lines.append(f"LM Studio — {datetime.now().strftime('%H:%M:%S')}")
    lines.append(f"Modèles actifs: {len(models)}")
    for m in models:
        lines.append(f"  ▶ {m[:35]}")
    lines.append("GPUs:")
    for g in gpus:
        pct = round(g['mem_used']/g['mem_total']*100) if g['mem_total'] else 0
        bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
        lines.append(f"  GPU{g['id']} {g['util']}% {g['temp']}°C [{bar}] {g['mem_used']}/{g['mem_total']}MB")
    return "\n".join(lines)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "text"
    if mode == "json":
        print(json.dumps({"models": get_models(), "gpus": get_gpu_info()}, indent=2))
    else:
        print(format_output())
