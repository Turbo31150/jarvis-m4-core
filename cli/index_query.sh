#!/usr/bin/env bash
# index_query.sh — Requêtes rapides disk_index + mindmap
# Usage: index_query.sh <cmd> [arg]
# Commandes: find <name> | ext <ext> | node <name> | heavy | machines | tag <tag> | recent [N]

DB="/home/turbo/jarvis/jarvis_master.db"

cmd="${1:-help}"
arg="${2:-}"

sqlite3_json() {
    sqlite3 -json "$DB" "$1" 2>/dev/null
}

case "$cmd" in
  find)
    sqlite3_json "SELECT machine, path, size_kb, modified_at, tags FROM disk_index WHERE name LIKE '%${arg}%' LIMIT 100;"
    ;;
  ext)
    arg="${arg#.}"  # strip leading dot if present
    sqlite3_json "SELECT machine, path, size_kb, modified_at FROM disk_index WHERE ext='.${arg}' OR ext='${arg}' ORDER BY modified_at DESC LIMIT 200;"
    ;;
  node)
    sqlite3_json "SELECT node, type, machine, status, connects_to, description, last_seen FROM mindmap WHERE node LIKE '%${arg}%';"
    ;;
  heavy)
    sqlite3_json "SELECT machine, path, size_kb, modified_at FROM disk_index WHERE size_kb > 102400 ORDER BY size_kb DESC LIMIT 50;"
    ;;
  machines)
    sqlite3_json "SELECT machine, COUNT(*) AS files, SUM(size_kb) AS total_kb FROM disk_index GROUP BY machine ORDER BY files DESC;"
    ;;
  tag)
    sqlite3_json "SELECT machine, path, size_kb, modified_at FROM disk_index WHERE tags='${arg}' ORDER BY modified_at DESC LIMIT 200;"
    ;;
  recent)
    n="${arg:-20}"
    sqlite3_json "SELECT machine, path, size_kb, modified_at, tags FROM disk_index ORDER BY modified_at DESC LIMIT ${n};"
    ;;
  types)
    sqlite3_json "SELECT type, COUNT(*) AS count FROM mindmap GROUP BY type ORDER BY count DESC;"
    ;;
  status)
    sqlite3_json "SELECT node, status, machine FROM mindmap ORDER BY status, node;"
    ;;
  count)
    sqlite3_json "SELECT machine, ext, COUNT(*) AS n FROM disk_index GROUP BY machine, ext ORDER BY n DESC LIMIT 30;"
    ;;
  help|*)
    cat <<EOF
Usage: index_query.sh <cmd> [arg]
  find <name>     Cherche par nom de fichier (LIKE %name%)
  ext <ext>       Tous fichiers avec cette extension (ex: py, db)
  tag <tag>       Fichiers par tag: script/db/config/log/model
  node <name>     Infos composant mindmap (LIKE %name%)
  heavy           Fichiers >100MB
  machines        Résumé par machine (count + total KB)
  recent [N]      N fichiers modifiés récemment (défaut: 20)
  types           Types de nœuds mindmap
  status          Statut tous composants mindmap
  count           Distribution machine/ext
EOF
    ;;
esac
