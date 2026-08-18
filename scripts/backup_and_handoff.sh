#!/usr/bin/env bash
# ==============================================================================
# JARVIS — backup_and_handoff.sh
# Sauvegarde complète des bases SQLite et préparation du handoff de fin de session
# ==============================================================================

set -euo pipefail

BACKUP_DATE=$(date +%F_%H-%M)
BACKUP_DIR="/home/pamerys/jarvis/backups/${BACKUP_DATE}"

echo "=== DÉBUT SAUVEGARDE COMPLÈTE ==="
mkdir -p "${BACKUP_DIR}"
echo "Dossier de sauvegarde : ${BACKUP_DIR}"

# 1. Sauvegarde propre des bases SQLite via .backup (évite les locks)
databases=(
  "/home/pamerys/jarvis/jarvis_master.db"
  "/home/pamerys/jarvis/data/etoile.db"
  "/home/pamerys/jarvis/cowork_engine.db"
  "/home/pamerys/jarvis/jarvis.db"
)

for db in "${databases[@]}"; do
  if [ -f "${db}" ]; then
    name=$(basename "${db}")
    echo "  → Sauvegarde de ${name}..."
    sqlite3 "${db}" ".backup '${BACKUP_DIR}/${name}'"
    echo "  ✓ ${name} sauvegardée."
  else
    echo "  ✗ Base de données introuvable : ${db}"
  fi
done

# 2. Compression des sauvegardes du jour
echo "Compression des sauvegardes..."
tar -czf "/home/pamerys/jarvis/backups/backup_sql_${BACKUP_DATE}.tar.gz" -C "/home/pamerys/jarvis/backups" "${BACKUP_DATE}"
rm -rf "${BACKUP_DIR}"
echo "✓ Fichier compressé créé : /home/pamerys/jarvis/backups/backup_sql_${BACKUP_DATE}.tar.gz"

# 3. Synchronisation Git
echo "Synchronisation Git du repo jarvis..."
cd /home/pamerys/jarvis
git add -A
git commit -m "chore(backup): auto-backup sqlite databases and session state ${BACKUP_DATE}" || true
git push origin jarvis-core-clean 2>/dev/null || true
echo "✓ Sync Git terminée."

# 4. Écriture du Handoff
echo "Génération du rapport de fin de session..."
# Création des buffers temporaires s'ils n'existent pas
mkdir -p /home/pamerys/.remember
NOW="/home/pamerys/.remember/now.md"
TODAY="/home/pamerys/.remember/today-$(date +%F).md"

{
  echo "- Création de l'action de régularisation micro-entreprise dans action_validation"
  echo "- Préparation des documents d'immatriculation INPI dans /tmp/ (passeport, attestation domicile, non-condamnation)"
  echo "- Redirection de Chrome en DISPLAY=:0 avec remote debugging port 9222 pour le login INPI"
  echo "- Sauvegarde complète (svg full) des bases de données SQL du cluster"
} > "$NOW"

bash /home/pamerys/jarvis/scripts/session-handoff.sh
echo "✓ Rapport remember.md généré."
echo "=== SAUVEGARDE COMPLÈTE TERMINÉE ==="
