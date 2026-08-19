#!/usr/bin/env python3
"""Connexion fiable à BrowserOS (browserless) via CDP.

POURQUOI CE FICHIER
-------------------
BrowserOS expose /json/version avec  webSocketDebuggerUrl = ws://0.0.0.0:3000/
C'est l'adresse d'ECOUTE interne du conteneur, pas une adresse joignable.
Playwright / puppeteer suivent cette URL telle quelle et echouent avec :
    Error: connect ECONNREFUSED 0.0.0.0:3000

CORRECTIF : se connecter directement au websocket sur le port publie,
sans passer par la decouverte /json/version :
    connect_over_cdp("ws://127.0.0.1:9108/")

Verifie le 2026-08-19 sur Chrome 151.0.7922.34 : navigation OK,
DOM lisible, upload de fichier local POSSIBLE (pas d'isolation filesystem).
"""
from playwright.sync_api import sync_playwright
import sys

ENDPOINT = "ws://127.0.0.1:9108/"

def connect(p):
    """Retourne un Browser connecte a BrowserOS."""
    return p.chromium.connect_over_cdp(ENDPOINT)

def page(b):
    """Retourne une page utilisable."""
    ctx = b.contexts[0] if b.contexts else b.new_context()
    return ctx.new_page()

def smoke() -> int:
    with sync_playwright() as p:
        try:
            b = connect(p)
        except Exception as e:
            print(f"KO connexion : {e}", file=sys.stderr)
            return 1
        print(f"OK  connexion BrowserOS — Chrome {b.version}")
        pg = page(b)
        pg.goto("https://example.com", wait_until="domcontentloaded", timeout=30000)
        print(f"OK  navigation — titre : {pg.title()}")
        try:
            pg.set_content("<input type=file id=f>")
            pg.set_input_files("#f", __file__)
            ok = pg.evaluate("()=>document.querySelector('#f').files.length")
            print(f"OK  upload fichier local : {'possible' if ok else 'refuse'}")
        except Exception as e:
            print(f"KO  upload fichier local : {str(e)[:70]}")
        pg.close(); b.close()
        return 0

if __name__ == "__main__":
    sys.exit(smoke())
