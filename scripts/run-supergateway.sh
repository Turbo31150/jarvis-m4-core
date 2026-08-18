#!/usr/bin/env bash
# Lance supergateway depuis l'installation locale (pas de réseau requis)
export PATH="/home/pamerys/.local/bin:/home/pamerys/.gemini/antigravity-cli/bin:/home/pamerys/bin:/home/pamerys/bin:/home/pamerys/bin:/home/pamerys/.local/bin:/home/pamerys/bin:/home/pamerys/.opencode/bin:/home/pamerys/.local/bin:/home/pamerys/.local/bin:/home/pamerys/.local/bin:/home/pamerys/.local/bin:/home/pamerys/.local/bin:/home/pamerys/.bun/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin/home/pamerys/.lmstudio/bin:/snap/bin"
export NODE_PATH="/home/pamerys/.local/lib/node_modules"
exec node /home/pamerys/.local/lib/node_modules/supergateway/dist/index.js "$@"
