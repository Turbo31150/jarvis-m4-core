#!/usr/bin/env python3
"""
JARVIS-OMEGA — Direct Double Publisher (New Post + Live Viral Comment)
======================================================================
"""

import os
import sys
import time
import shutil
import sqlite3
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

DB_MASTER = Path("/home/pamerys/jarvis/jarvis_master.db")
CHROME_PROFILE_SRC = Path("/home/pamerys/.config/google-chrome/Profile 10")
TMP_PROFILE_DIR = Path("/tmp/chrome_franck_session")

POST_CONTENT = """🔥 Pourquoi les directions d'ingénierie et DSI basculent massivement vers l'IA souveraine On-Premise en 2026.

Face à l'explosion des coûts d'API Cloud et aux contraintes strictes de la directive NIS2 et de l'EU AI Act, l'internalisation des modèles devient l'unique standard viable :
✅ Inférence locale 0 ms sur GPU dédiés (modèles 9B à 35B quantisés)
✅ Recherche documentaire hybride RRF à citation vérifiée [n] sans hallucination
✅ Zéro transmission réseau hors du périmètre sécurisé (mode avion complet)

Chez JARVIS OS, nos systèmes multi-agents traitent plus de 70 000 opérations quotidiennes sans aucune rente cloud.

👉 DSI & Directeurs R&D : prêt à internaliser vos modèles de fondation ? Échangeons en commentaire.

#IASouveraine #NIS2 #OnPremise #MultiAgents #JARVIS #TechLeadership"""

COMMENT_CONTENT = """Excellente analyse. En 2026, l'architecture IA souveraine On-Premise et la conformité NIS2 sont devenues le premier levier de rentabilité et de protection des données d'ingénierie."""

def prepare_cloned_profile():
    if TMP_PROFILE_DIR.exists():
        shutil.rmtree(TMP_PROFILE_DIR, ignore_errors=True)
    default_dir = TMP_PROFILE_DIR / "Default"
    default_dir.mkdir(parents=True, exist_ok=True)
    
    for item in ["Cookies", "Network", "Local Storage", "Session Storage", "IndexedDB"]:
        src = CHROME_PROFILE_SRC / item
        dst = default_dir / item
        if src.exists():
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
    print("✓ Profil Chrome authentifié de Franck prêt !")

async def publish_double():
    prepare_cloned_profile()
    
    print("🌐 Lancement du navigateur Playwright...")
    async with async_playwright() as p:
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir=str(TMP_PROFILE_DIR),
            headless=False,
            channel="chrome",
            args=[
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-blink-features=AutomationControlled"
            ],
            viewport={"width": 1400, "height": 900},
            locale="fr-FR"
        )
        
        page = browser_context.pages[0] if browser_context.pages else await browser_context.new_page()
        print("➔ Navigation sur https://www.linkedin.com/feed/...")
        await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(4)
        
        # 1. Publier un Nouveau Post en Haut du Fil
        print("➔ Scroll to top et focus sur la création de post...")
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(1)
        
        # Trouver la boîte 'Commencer un post'
        start_post = await page.query_selector("div.e9f5153c, div.share-box-feed-entry, button.share-box-feed-entry__trigger")
        if start_post:
            await start_post.click()
            await asyncio.sleep(2)
            editor = await page.wait_for_selector("div[role='textbox'], div.ql-editor", timeout=5000)
            if editor:
                print("✓ Éditeur modal ouvert, saisie du post d'autorité...")
                await editor.click()
                await page.keyboard.insert_text(POST_CONTENT)
                await asyncio.sleep(2)
                
                pub_btn = await page.wait_for_selector("button:has-text('Publier'), button.share-actions__primary-action", timeout=5000)
                if pub_btn:
                    print("🚀 Clic 'Publier' pour le post...")
                    await pub_btn.click()
                    await asyncio.sleep(5)
                    print("🎉 POST PRINCIPAL PUBLIÉ SUR VOTRE PROFIL !")
                    
        # 2. Commenter le premier post d'actualité visible
        print("➔ Recherche de la zone commentaire sur le fil d'actualité...")
        comment_trigger = await page.query_selector("button[aria-label*='Commenter'], button:has-text('Commenter')")
        if comment_trigger:
            await comment_trigger.click()
            await asyncio.sleep(2)
            comment_input = await page.query_selector("div.comments-comment-box__editor, div.ql-editor, div[role='textbox']")
            if comment_input:
                print("✓ Zone commentaire trouvée, saisie...")
                await comment_input.click()
                await page.keyboard.insert_text(COMMENT_CONTENT)
                await asyncio.sleep(1)
                
                # Soumission par Ctrl+Enter
                await page.keyboard.press("Control+Enter")
                await asyncio.sleep(3)
                print("🎉 COMMENTAIRE EXPERT PUBLIÉ EN DIRECT !")

        await page.screenshot(path="/tmp/linkedin_final_proof.png")
        print("📸 Capture finale enregistrée dans /tmp/linkedin_final_proof.png")
        
        await asyncio.sleep(3)
        await browser_context.close()
        shutil.rmtree(TMP_PROFILE_DIR, ignore_errors=True)

if __name__ == "__main__":
    asyncio.run(publish_double())
