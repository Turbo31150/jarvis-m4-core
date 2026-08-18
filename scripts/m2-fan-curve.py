#!/usr/bin/env python3
"""
M2 Fan Curve Controller — courbe agressive pour stabilité sous charge LLM
Quadro RTX 4000 : shutdown=97°C, slowdown=94°C, max_op=92°C, target=83°C
Courbe : temp → fan%
  <50°C → 35%
  55°C  → 50%
  65°C  → 70%
  75°C  → 85%
  80°C  → 95%
  >85°C → 100%
"""

import time
import subprocess

CURVE = [(50, 35), (55, 50), (65, 70), (75, 85), (80, 95), (85, 100)]
CHECK_SEC = 10
GPU_COUNT = 3


def get_fan_pct(temp):
    for t, f in reversed(CURVE):
        if temp >= t:
            return f
    return CURVE[0][1]


def get_gpu_stats():
    out = subprocess.check_output(
        [
            "nvidia-smi",
            "--query-gpu=index,temperature.gpu,fan.speed,power.draw",
            "--format=csv,noheader,nounits",
        ]
    ).decode()
    stats = []
    for line in out.strip().split("\n"):
        parts = [x.strip() for x in line.split(",")]
        stats.append(
            {
                "idx": int(parts[0]),
                "temp": int(parts[1]),
                "fan": int(parts[2]),
                "power": float(parts[3]),
            }
        )
    return stats


def set_fan(idx, pct):
    display = ":0"
    subprocess.run(
        [
            "nvidia-settings",
            "-a",
            f"[gpu:{idx}]/GPUFanControlState=1",
            "-a",
            f"[fan:{idx}]/GPUTargetFanSpeed={pct}",
            "--display",
            display,
        ],
        capture_output=True,
    )


def fmt(stats):
    return " | ".join(
        f"GPU{s['idx']} {s['temp']}°C fan={s['fan']}% {s['power']:.0f}W" for s in stats
    )


print(f"[FAN CTRL] Start — check every {CHECK_SEC}s", flush=True)
print(f"[CURVE] {CURVE}", flush=True)

while True:
    try:
        stats = get_gpu_stats()
        for s in stats:
            target = get_fan_pct(s["temp"])
            if abs(s["fan"] - target) > 5:
                set_fan(s["idx"], target)
                print(
                    f"[GPU{s['idx']}] {s['temp']}°C → fan {s['fan']}%→{target}%",
                    flush=True,
                )
        print(f"  {fmt(stats)}", flush=True)
    except Exception as e:
        print(f"[ERR] {e}", flush=True)
    time.sleep(CHECK_SEC)
