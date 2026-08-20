#!/usr/bin/env bash
# Vue des conteneurs de la pile JARVIS reelle (la TOUR), pour la fenetre 3 de ttx.
#
# POURQUOI CE SCRIPT EXISTE (20/08/2026) :
# `watch -n 5 jarvis-docker ps --format "table {{.Names}}\t{{.Status}}"` NE MARCHE PAS.
# watch reassemble ses arguments en UNE chaine et la passe a `sh -c` SANS re-quoter :
# les guillemets autour du format sont perdus, `--format` recoit `table` seul et
# `{{.Names}}...` devient un argument positionnel -> la tour repond en boucle
# "docker: 'docker ps' accepts no arguments". Meme motif que la fenetre M6.
set -uo pipefail

echo "════════ SWARM JARVIS — pile de la TOUR ════════"
if ! /home/pamerys/jarvis/bin/jarvis-docker ps \
        --format 'table {{.Names}}\t{{.Status}}' 2>/tmp/swarm-watch.err; then
    echo "  ⚠ tour injoignable ou docker en erreur :"
    sed 's/^/    /' /tmp/swarm-watch.err | head -5
fi
