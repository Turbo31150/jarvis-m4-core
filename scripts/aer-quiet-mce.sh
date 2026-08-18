#!/usr/bin/env bash
# jarvis-aer-quiet : fait taire le spam MCE "Corrected error, no action required"
# emis par la banque MCA #27 = lien GMI / Infinity Fabric die-to-die du CPU AMD.
# Source confirmee par rasdaemon : bank=27 ... "Error on GMI link"
# (Corrected error, no action required). Ce sont des erreurs corrigees recurrentes
# sur le lien Infinity Fabric interne du CPU, SANS aucun rapport avec un slot GPU,
# un riser PCIe ou un bridge : purement die-to-die (GMI).
#
# Ces erreurs corrigees polluent dmesg/rasdaemon regulierement. On desactive le
# logging de la banque MCA 27 uniquement. TOTALEMENT REVERSIBLE.
#
# /!\ AVERTISSEMENT : masquer bank27 tait AUSSI d'eventuelles VRAIES erreurs
#     Infinity Fabric (RAM / IF instable) remontees sur cette meme banque.
#     Ce mask est VOLONTAIRE, uniquement pour reduire le bruit de logs benin ;
#     en cas d'instabilite systeme, restaurer bank27 (rollback ci-dessous) pour
#     re-exposer les erreurs GMI/IF avant tout diagnostic.
#
# Valeur AVANT (a restaurer pour rollback) : bank27 = ffffffffffffffff
# Rollback : echo 0xffffffffffffffff | sudo tee /sys/devices/system/machinecheck/machinecheck0/bank27
#
# Le registre CTL de la banque MCA est partage au niveau socket => seul machinecheck0 le porte.

set -euo pipefail

BANK=/sys/devices/system/machinecheck/machinecheck0/bank27

if [[ ! -w "$BANK" ]]; then
  echo "[aer-quiet] $BANK non accessible en ecriture (root requis)" >&2
  exit 1
fi

before="$(cat "$BANK")"
echo 0 > "$BANK"
after="$(cat "$BANK")"
echo "[aer-quiet] bank27 : avant=$before apres=$after (0 = logging MCA banque 27 desactive)"
