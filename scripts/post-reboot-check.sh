#!/usr/bin/env bash
# post-reboot-check.sh — valide la récupération GPU + système après reboot
set -uo pipefail
echo "=== GPU:3 récupéré ? (plus d'erreur modeset) ==="
sudo dmesg 2>/dev/null | grep -c "nvidia-modeset.*Error while waiting" | xargs echo "erreurs modeset depuis boot (doit être 0):"
echo "=== Xvfb D-state (doit être ~0-1) ==="
ps -eo stat,comm 2>/dev/null | awk '$1~/^D/&&$2=="Xvfb"' | wc -l
echo "=== load (doit redescendre <5) ==="; uptime | grep -oE "average.*"
echo "=== GPU tous OK ? ==="; nvidia-smi --query-gpu=index,name,temperature.gpu --format=csv,noheader 2>/dev/null
echo "=== watchdog xvfb reste OFF ? ==="; systemctl --user is-enabled lmstudio-watchdog.service 2>/dev/null
echo "=== cluster LLM ==="; LM_NO_LOCK=1 timeout 30 ~/jarvis/scripts/lm-ask.sh "OK" 2>/dev/null | head -c40
echo "=== services failed ==="; systemctl --failed --no-legend 2>/dev/null | wc -l
