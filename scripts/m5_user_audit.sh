#!/bin/bash
# ============================================================================
# SCRIPT D'AUDIT DES UTILISATEURS ACTIFS SUR M5
# Crée par JARVIS-OMEGA
#
# OBJECTIF:
# 1. Détecter tous les terminaux ouverts et les utilisateurs associés.
# 2. Pour chaque utilisateur, afficher sa "fiche de poste" (rôle/métier).
# 3. Les données de rôle sont lues depuis /home/pamerys/jarvis/data/user_roles.json
#
# PREREQUIS: jq (JSON processor)
# sudo apt-get install jq
# ============================================================================

set -e

ROLES_FILE="/home/pamerys/jarvis/data/user_roles.json"
HOST=$(hostname)

# --- Vérification des prérequis ---
if ! command -v jq &> /dev/null; then
    echo "ERREUR: 'jq' n'est pas installé. Veuillez l'installer (sudo apt-get install jq)." >&2
    exit 1
fi

if [ ! -f "$ROLES_FILE" ]; then
    echo "ERREUR: Le fichier des rôles $ROLES_FILE est introuvable." >&2
    exit 1
fi

echo "--- Audit des Utilisateurs Actifs sur [$HOST] ---"
echo

# --- Logique principale ---
# 'who' liste les utilisateurs connectés.
# 'awk' extrait la première colonne (noms d'utilisateur).
# 'sort -u' dédoublonne la liste.
# Le 'while' lit chaque nom d'utilisateur unique.
who | awk '{print $1}' | sort -u | while read -r user; do
    # Récupérer le profil de l'utilisateur. Si non trouvé, utiliser le profil "default".
    profile=$(jq -r --arg user "$user" '.[$user] // .default' "$ROLES_FILE")

    # Extraire les informations du profil
    role=$(echo "$profile" | jq -r '.role')
    metier=$(echo "$profile" | jq -r '.metier')

    echo "▶ Utilisateur: $user"
    echo "  ├─ Rôle (Fiche de poste): $role"
    echo "  └─ Métier: $metier"

    # Lister les terminaux ouverts pour cet utilisateur
    echo "     └─ Terminaux ouverts:"
    who | grep "^${user}\s" | while read -r line; do
        terminal=$(echo "$line" | awk '{print $2}')
        login_time=$(echo "$line" | awk '{$1=$2=""; print $0}' | sed 's/^[ 	]*//')
        echo "        ├─ $terminal (Login: $login_time)"
    done
    echo
done

echo "--- Fin de l'audit ---"
