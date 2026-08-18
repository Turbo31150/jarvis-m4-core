#!/bin/bash
# Configuration optimisée Qwen3.5-9b pour LM Studio sur M4 (192.168.0.10)
# - GPU Max offload
# - Context length: 16384 (16k pour stabilité / pas de crash OOM VRAM)
# - Flash Attention: ON
# - MLock: Enabled
/home/pamerys/.lmstudio/bin/lms unload --all 2>/dev/null
/home/pamerys/.lmstudio/bin/lms load qwen/qwen3.5-9b --gpu max -c 16384 -y
