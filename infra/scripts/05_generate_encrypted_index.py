#!/usr/bin/env python3
"""
JARVIS — Phase 5 : Génération de l'index chiffré global (jarvis_encrypted_index)
Chiffrement Fernet (symétrique AES-128-CBC). Clé stockée dans jarvis_security_keys.
Exécuter : python3 /home/pamerys/jarvis/infra/scripts/05_generate_encrypted_index.py

Dépendances : pip install cryptography
"""

import sqlite3
import json
import os
import sys
from datetime import datetime

try:
    from cryptography.fernet import Fernet
except ImportError:
    print("[ERR] pip install cryptography manquant")
    sys.exit(1)

DB = "/home/pamerys/jarvis/data/jarvis.db"
KEY_FILE = "/home/pamerys/jarvis/backups/ssh-access/.jarvis_index_key"

# --- Cluster endpoints statiques (non containers) ---
STATIC_ENDPOINTS = [
    {
        "label": "M1-LMStudio",
        "node": "M1",
        "category": "llm",
        "data": {
            "host": "192.168.1.85",
            "port": 1234,
            "proto": "http",
            "url": "http://192.168.1.85:1234/v1",
            "key_env": "LM_STUDIO_1_KEY",
        },
    },
    {
        "label": "M2-LMStudio",
        "node": "M2",
        "category": "llm",
        "data": {
            "host": "192.168.1.26",
            "port": 1234,
            "proto": "http",
            "url": "http://192.168.1.26:1234/v1",
            "key_env": "LM_STUDIO_2_KEY",
        },
    },
    {
        "label": "M3-LMStudio",
        "node": "M3",
        "category": "llm",
        "data": {
            "host": "192.168.1.113",
            "port": 1234,
            "proto": "http",
            "url": "http://192.168.1.113:1234/v1",
            "key_env": "LM_STUDIO_3_KEY",
        },
    },
    {
        "label": "OL1-Ollama",
        "node": "M1",
        "category": "llm",
        "data": {
            "host": "127.0.0.1",
            "port": 11434,
            "proto": "http",
            "url": "http://127.0.0.1:11434",
        },
    },
    {
        "label": "M2-SSH",
        "node": "M2",
        "category": "remote",
        "data": {"host": "192.168.1.26", "port": 22, "proto": "ssh", "user": "turbo"},
    },
    {
        "label": "M3-SSH",
        "node": "M3",
        "category": "remote",
        "data": {"host": "192.168.1.113", "port": 22, "proto": "ssh", "user": "turbo"},
    },
    {
        "label": "WIN-RDP",
        "node": "WIN",
        "category": "remote",
        "data": {
            "host": "192.168.1.x",
            "port": 3389,
            "proto": "rdp",
            "note": "Windows 1280283457 — mettre IP réelle",
        },
    },
    {
        "label": "jarvis-n8n",
        "node": "M1",
        "category": "container",
        "data": {
            "host": "127.0.0.1",
            "port": 56785678,
            "proto": "http",
            "url": "http://127.0.0.1:56785678",
        },
    },
    {
        "label": "jarvis-valise-dashboard",
        "node": "M1",
        "category": "container",
        "data": {"host": "127.0.0.1", "port": 18850, "proto": "http"},
    },
    {
        "label": "jarvis-lumen-token",
        "node": "M1",
        "category": "container",
        "data": {"host": "127.0.0.1", "port": 30013001, "proto": "http"},
    },
    {
        "label": "jarvis-browseros",
        "node": "M1",
        "category": "container",
        "data": {"host": "127.0.0.1", "port": 91089108, "proto": "http"},
    },
    {
        "label": "jarvis-prod-n8n",
        "node": "M1",
        "category": "container",
        "data": {
            "host": "10.0.1.66",
            "port": 5678,
            "proto": "http",
            "network": "jarvis_prod_jarvis-net",
        },
    },
    {
        "label": "jarvis-prod-postgres",
        "node": "M1",
        "category": "container",
        "data": {
            "host": "10.0.1.22",
            "port": 5432,
            "proto": "postgres",
            "network": "jarvis_prod_jarvis-net",
        },
    },
]


def load_or_create_key():
    """Charge la clé Fernet existante ou en crée une nouvelle."""
    # Vérifier d'abord en DB
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jarvis_security_keys (
            id TEXT PRIMARY KEY,
            label TEXT,
            key_b64 TEXT,
            algo TEXT DEFAULT 'fernet',
            created_at TEXT
        )
    """)
    row = cur.execute(
        "SELECT id, key_b64 FROM jarvis_security_keys WHERE label='index-master'"
    ).fetchone()
    if row:
        con.close()
        return row[0], row[1].encode()

    # Nouvelle clé
    key = Fernet.generate_key()
    key_id = f"key-index-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    now = datetime.now().isoformat()
    cur.execute(
        "INSERT INTO jarvis_security_keys (id, label, key_b64, algo, created_at) VALUES (?,?,?,?,?)",
        (key_id, "index-master", key.decode(), "fernet", now),
    )
    con.commit()
    con.close()

    # Aussi sauvegarder sur disque (backup)
    os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True)
    with open(KEY_FILE, "wb") as f:
        f.write(key)
    os.chmod(KEY_FILE, 0o600)
    print(f"[KEY] Nouvelle clé générée : {key_id} → {KEY_FILE}")
    return key_id, key


def main():
    key_id, raw_key = load_or_create_key()
    f = Fernet(raw_key)

    con = sqlite3.connect(DB)
    cur = con.cursor()
    now = datetime.now().isoformat()
    inserted = updated = 0

    # Index depuis jarvis_endpoints (containers)
    rows = cur.execute("""
        SELECT e.id, e.name, a.node, e.host, e.port, e.network, e.internal_ip,
               e.is_sensitive, e.buffer_container_name, e.isolation_network,
               a.tier, a.ssh_key_path, a.mission
        FROM jarvis_endpoints e
        LEFT JOIN jarvis_agents a ON a.id = e.id
    """).fetchall()

    for r in rows:
        blob = {
            "id": r[0],
            "host": r[3],
            "port": r[4],
            "network": r[5],
            "internal_ip": r[6],
            "is_sensitive": bool(r[7]),
            "buffer": r[8],
            "isolation_net": r[9],
            "tier": r[10],
            "ssh_key": r[11],
            "mission": r[12],
            "connect": f"docker exec -it {r[0]} bash"
            if r[7] == 0
            else f"docker exec -it buf-{r[0].replace('jarvis-', '')} bash  # via buffer",
        }
        encrypted = f.encrypt(json.dumps(blob).encode()).decode()
        ex = cur.execute(
            "SELECT id FROM jarvis_encrypted_index WHERE id=?", (r[0],)
        ).fetchone()
        if ex:
            cur.execute(
                "UPDATE jarvis_encrypted_index SET encrypted_blob=? WHERE id=?",
                (encrypted, r[0]),
            )
            updated += 1
        else:
            cur.execute(
                """
                INSERT INTO jarvis_encrypted_index (id, label, node, encrypted_blob, key_id, category, created_at)
                VALUES (?,?,?,?,?,?,?)
            """,
                (r[0], r[1], r[5] or "M1", encrypted, key_id, "container", now),
            )
            inserted += 1

    # Index endpoints statiques
    for ep in STATIC_ENDPOINTS:
        eid = f"static-{ep['label']}"
        blob = ep["data"]
        blob["label"] = ep["label"]
        encrypted = f.encrypt(json.dumps(blob).encode()).decode()
        ex = cur.execute(
            "SELECT id FROM jarvis_encrypted_index WHERE id=?", (eid,)
        ).fetchone()
        if ex:
            cur.execute(
                "UPDATE jarvis_encrypted_index SET encrypted_blob=? WHERE id=?",
                (encrypted, eid),
            )
            updated += 1
        else:
            cur.execute(
                """
                INSERT INTO jarvis_encrypted_index (id, label, node, encrypted_blob, key_id, category, created_at)
                VALUES (?,?,?,?,?,?,?)
            """,
                (eid, ep["label"], ep["node"], encrypted, key_id, ep["category"], now),
            )
            inserted += 1

    con.commit()
    total = cur.execute("SELECT COUNT(*) FROM jarvis_encrypted_index").fetchone()[0]
    con.close()

    print(
        f"[OK] Index chiffré : {inserted} nouveaux + {updated} mis à jour = {total} entrées total"
    )
    print(f"[KEY] key_id utilisée : {key_id}")
    print('[!] Pour décoder : python3 -c "')
    print("    from cryptography.fernet import Fernet; import json, sqlite3")
    print(f"    key = open('{KEY_FILE}','rb').read()")
    print("    f = Fernet(key)")
    print(f"    con = sqlite3.connect('{DB}')")
    print(
        "    rows = con.execute('SELECT label, encrypted_blob FROM jarvis_encrypted_index').fetchall()"
    )
    print('    [print(r[0], json.loads(f.decrypt(r[1].encode()))) for r in rows]"')


if __name__ == "__main__":
    main()
