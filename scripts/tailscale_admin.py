#!/usr/bin/env python3
"""
JARVIS Tailscale API Manager
============================
Gestion autonome du réseau Tailscale via l'API REST v2 :
  - Liste des appareils connectés
  - Génération automatique de clés pre-auth pour nouveaux téléphones / nœuds
  - Autorisation automatique des appareils en attente
"""

import sys
import json
import base64
import urllib.request
from pathlib import Path

CONFIG_FILE = Path("/home/pamerys/jarvis/config/tailscale.env")

def get_credentials():
    api_key = ""
    tailnet = "remten341@gmail.com"
    if CONFIG_FILE.exists():
        for line in CONFIG_FILE.read_text().splitlines():
            if line.startswith("TAILSCALE_API_KEY="):
                api_key = line.split("=", 1)[1].strip('"\'; ')
            elif line.startswith("TAILNET="):
                tailnet = line.split("=", 1)[1].strip('"\'; ')
    return api_key, tailnet

def make_request(endpoint, data=None):
    api_key, tailnet = get_credentials()
    url = f"https://api.tailscale.com/api/v2{endpoint}"
    auth = base64.b64encode(f"{api_key}:".encode('utf-8')).decode('ascii')
    
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    }
    body = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode('utf-8'))

def list_devices():
    api_key, tailnet = get_credentials()
    data = make_request(f"/tailnet/{tailnet}/devices")
    devices = data.get("devices", [])
    print(f"=== {len(devices)} APPAREILS CONNECTÉS SUR LE TAILNET ({tailnet}) ===")
    for d in devices:
        ips = [ip for ip in d.get("addresses", []) if "." in ip]
        status = "🟢 En ligne" if d.get("connectedToControl") else "⚪ Déconnecté"
        print(f"• {d.get('name', 'N/A')} ({d.get('os', 'N/A')}) | IP: {', '.join(ips)} | {status}")

def generate_auth_key(reusable=True, ephemeral=False):
    api_key, tailnet = get_credentials()
    payload = {
        "capabilities": {
            "devices": {
                "create": {
                    "reusable": reusable,
                    "ephemeral": ephemeral,
                    "preauthorized": True
                }
            }
        },
        "expirySeconds": 86400 * 90,
        "description": "Clé générée automatiquement par JARVIS"
    }
    data = make_request(f"/tailnet/{tailnet}/keys", data=payload)
    key = data.get("key", "")
    print(f"✓ Nouvelle clé d'authentification pre-auth générée : {key}")
    return key

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "create-key":
        generate_auth_key()
    else:
        list_devices()
