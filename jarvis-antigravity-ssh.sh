#!/bin/bash
# Wrapper SSH pour Antigravity pour se connecter au cluster Jarvis
# Utilise automatiquement la clé SSH de Jarvis
exec /usr/bin/ssh -i /home/pamerys/jarvis/infra/config/ssh-access/jarvis_ed25519 -o StrictHostKeyChecking=no "$@"
