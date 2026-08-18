#!/usr/bin/env python3
"""
auto_post_linkedin_comments.py — Publication Autonome Directe des Commentaires LinkedIn
=====================================================================================
Utilise Chrome DevTools Protocol (CDP) / BrowserOS pour poster automatiquement
les 4 commentaires sur-mesure sur les publications cibles.
"""

import os
import sys
import json
import sqlite3
import urllib.request

DB = os.path.expanduser("~/jarvis/jarvis_master.db")
CDP_PORT = 9222

print("=== 🚀 PUBLICATION AUTONOME DIRECTE DES COMMENTAIRES LINKEDIN ===")

# 1. Verification connexion Chrome CDP / BrowserOS
try:
    with urllib.request.urlopen(
        f"http://127.0.0.1:{CDP_PORT}/json/version", timeout=3
    ) as r:
        version_data = json.loads(r.read().decode())
        print(f"✅ BrowserOS CDP actif : {version_data.get('Browser', 'Chrome')}")
except Exception:
    print("ℹ️ Mode BrowserOS CDP autonome actif sur port 9222.")

# 2. Ingestion des 4 commentaires prêts à publier
commentaires = [
    {
        "post_id": "P001",
        "sujet": "Cluster LLM 6 GPUs M1",
        "texte": "Impressionnante démonstration de puissance ! La répartition de la charge VRAM sur 6 GPUs permet d'atteindre des temps de réponse sous les 50ms sans aucun appel cloud souverain.",
    },
    {
        "post_id": "P002",
        "sujet": "PassCerfa & Mairie OMEGA",
        "texte": "L'automatisation des formulaires CERFA via des agents souverains simplifie drastiquement le suivi administratif et accélère le traitement des dossiers citoyens.",
    },
    {
        "post_id": "P003",
        "sujet": "Sécurité SQLite WAL & Backup SSD",
        "texte": "Le mode WAL couplé aux sauvegardes binaires à chaud assure une intégrité totale des données. Un standard DevSecOps indispensable pour les bases locales !",
    },
    {
        "post_id": "P004",
        "sujet": "RAG Multi-Dépôts NotebookLM",
        "texte": "L'indexation vectorielle sémantique de plus de 5 000 documents offre un confort de recherche inégalé pour les équipes techniques et juridiques.",
    },
]

# 3. Publication effective et enregistrement en base maître
#
# ⚠️ CE SCRIPT NE PUBLIAIT RIEN. Il faisait `time.sleep(0.5)`, affichait
# « ✅ Posté » et gravait en base status=PUBLIÉ_EN_AUTONOME / method=CDP_BROWSEROS
# / done / score=100. Aucun appel CDP n'était émis. 156 tâches de ce type
# polluaient jarvis_master.db en se faisant passer pour de l'activité réelle.
#
# Deux règles maintenant appliquées :
#   1. la publication LinkedIn est un EFFET DE BORD EXTERNE : elle relève de
#      `jarvis publish` (draft-first, approbation humaine liée au hash), pas
#      d'un script autonome qui poste sans validation ;
#   2. tant que le CDP LinkedIn n'est pas réellement câblé et vérifié, on
#      REFUSE plutôt que de simuler. Un faux succès est pire qu'une panne :
#      il est indétectable en aval et fausse toutes les statistiques.


def _cdp_disponible(port):
    """Preuve réelle : un onglet LinkedIn est-il pilotable ?"""
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/json/list", timeout=4
        ) as r:
            cibles = json.loads(r.read())
        return any("linkedin.com" in (t.get("url") or "") for t in cibles)
    except Exception:
        return False


if not _cdp_disponible(CDP_PORT):
    print(f"⛔ Aucun onglet LinkedIn pilotable sur CDP :{CDP_PORT}.", file=sys.stderr)
    print(
        "   Rien n'a été publié, et RIEN n'est gravé en base — l'ancienne version",
        file=sys.stderr,
    )
    print(
        "   enregistrait ici 4 commentaires « PUBLIÉ_EN_AUTONOME » sans rien envoyer.",
        file=sys.stderr,
    )
    print(
        "   Pour publier réellement : ouvrir LinkedIn dans le navigateur CDP, puis",
        file=sys.stderr,
    )
    print(
        "   passer par `jarvis publish stage/approve/commit` (effet de bord = A4).",
        file=sys.stderr,
    )
    sys.exit(3)

try:
    c = sqlite3.connect(DB)
    for cmt in commentaires:
        print(f"➡️ Publication CDP sur Post {cmt['post_id']} ({cmt['sujet']})...")
        # NOTE : l'envoi CDP réel reste à implémenter (Input.insertText + clic
        # sur le bouton « Publier »). Tant qu'il ne l'est pas, on sort en
        # erreur plutôt que de graver un succès.
        print("   ⛔ envoi CDP non implémenté — aucune tâche gravée.", file=sys.stderr)
        c.close()
        sys.exit(3)

    c.commit()
    c.close()
    print(
        "\n🔥 PUBLICATION EN LIGNE ACCOMPLIE ! LES 4 COMMENTAIRES SONT DÉPLOYÉS SUR LINKEDIN !"
    )
except Exception as e:
    print(f"Erreur SQL log: {e}")
