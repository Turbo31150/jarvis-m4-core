#!/usr/bin/env python3
"""
ingest_notebook_url.py — Ingestion du Google Notebook dans la base de connaissances JARVIS
Télécharge et indexe le contenu d'un Google Notebook via son URL publique.
"""
import os
import json
import sqlite3
import requests
from datetime import datetime

NOTEBOOK_URL = "https://notebook.google.com/notebook/387a16bf-55b9-495c-b8af-dd7417d59b72"
DB_PATH = os.path.expanduser("~/jarvis/jarvis_master.db")
SAVE_DIR = os.path.expanduser("~/jarvis/data")
os.makedirs(SAVE_DIR, exist_ok=True)

print(f"=== 📓 INGESTION GOOGLE NOTEBOOK ===")
print(f"URL: {NOTEBOOK_URL}")
print(f"Timestamp: {datetime.now().isoformat()}")

# Récupération du contenu via requête HTTP
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 JARVIS-Bot/1.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

notebook_id = "387a16bf-55b9-495c-b8af-dd7417d59b72"
content_extracted = ""
status = "pending"

try:
    # Tentative 1: accès direct
    r = requests.get(NOTEBOOK_URL, headers=headers, timeout=15, allow_redirects=True)
    print(f"  → HTTP Status: {r.status_code}")
    
    if r.status_code == 200:
        html_content = r.text
        # Extraction du texte pertinent
        import re
        # Nettoyer le HTML - extraire les textes
        text_clean = re.sub(r'<[^>]+>', ' ', html_content)
        text_clean = re.sub(r'\s+', ' ', text_clean).strip()
        
        if len(text_clean) > 100:
            content_extracted = text_clean[:50000]  # Limiter à 50k chars
            status = "ingested"
            print(f"  → Contenu extrait: {len(content_extracted)} caractères")
        else:
            print(f"  → Contenu trop court ou vide (redirection login ?)")
            status = "auth_required"
    elif r.status_code in (301, 302, 303, 307, 308):
        redirect = r.headers.get('Location', '')
        print(f"  → Redirection: {redirect} (probablement auth Google requise)")
        status = "auth_required"
    else:
        print(f"  → Erreur HTTP {r.status_code}")
        status = f"error_{r.status_code}"
        
except Exception as e:
    print(f"  → Exception: {e}")
    status = "network_error"

# Sauvegarde du résultat dans un fichier local
meta = {
    "url": NOTEBOOK_URL,
    "notebook_id": notebook_id,
    "status": status,
    "extracted_chars": len(content_extracted),
    "timestamp": datetime.now().isoformat(),
    "note": (
        "IMPORTANT: Google Notebook LM nécessite une authentification Google. "
        "Pour ingérer le contenu, utiliser la commande: "
        "'notebooklm-aspire up && notebooklm-aspire aspire 387a16' via le script CDP "
        "qui exploite les cookies de session Chrome existants. "
        "Le script est à ~/jarvis/bin/notebooklm-cdp.py"
    )
}

meta_path = os.path.join(SAVE_DIR, f"notebook_{notebook_id}_meta.json")
with open(meta_path, "w") as f:
    json.dump(meta, f, indent=2, ensure_ascii=False)
print(f"  → Meta sauvegardé: {meta_path}")

if content_extracted:
    content_path = os.path.join(SAVE_DIR, f"notebook_{notebook_id}_content.txt")
    with open(content_path, "w") as f:
        f.write(content_extracted)
    print(f"  → Contenu sauvegardé: {content_path}")

# Log dans jarvis_master.db
try:
    # WAL : un seul écrivain à la fois sur une base très sollicitée,
    # il faut attendre au lieu d'échouer sur "database is locked".
    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.execute("PRAGMA busy_timeout=120000")
    conn.execute("""
        INSERT INTO web_ingested_docs (url, title, content, status, ingested_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET
            status=excluded.status,
            content=excluded.content,
            ingested_at=excluded.ingested_at
    """, (
        NOTEBOOK_URL,
        f"Google Notebook {notebook_id}",
        content_extracted[:10000] if content_extracted else meta["note"],
        status,
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()
    print(f"  → Loggé dans jarvis_master.db (web_ingested_docs)")
except Exception as e:
    # La table n'existe peut-être pas, créons-la
    try:
        # WAL : un seul écrivain à la fois sur une base très sollicitée,
        # il faut attendre au lieu d'échouer sur "database is locked".
        conn = sqlite3.connect(DB_PATH, timeout=120)
        conn.execute("PRAGMA busy_timeout=120000")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS web_ingested_docs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE,
                title TEXT,
                content TEXT,
                status TEXT,
                ingested_at TEXT
            )
        """)
        conn.execute("""
            INSERT INTO web_ingested_docs (url, title, content, status, ingested_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                status=excluded.status,
                content=excluded.content,
                ingested_at=excluded.ingested_at
        """, (
            NOTEBOOK_URL,
            f"Google Notebook {notebook_id}",
            content_extracted[:10000] if content_extracted else meta["note"],
            status,
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
        print(f"  → Table créée + loggé dans jarvis_master.db")
    except Exception as e2:
        print(f"  → Erreur SQL: {e2}")

print(f"\n{'='*50}")
print(f"STATUS FINAL: {status}")
if status == "auth_required":
    print("⚠️  Google Notebook nécessite une session Google active.")
    print("   → Procédure manuelle: lancer Chrome CDP avec profil connecté")
    print("   → Commande: ~/labo/bibliotheque/series/notebooklm-aspire.sh up")
    print("   → Puis: ~/labo/bibliotheque/series/notebooklm-aspire.sh aspire 387a16")
elif status == "ingested":
    print(f"✅ SUCCÈS: {len(content_extracted)} caractères indexés")
print(f"{'='*50}")
