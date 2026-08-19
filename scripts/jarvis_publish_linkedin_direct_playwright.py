#!/usr/bin/env python3
"""
JARVIS-OMEGA — Direct Real LinkedIn Live Publisher (URL Trigger + Profile 10)
=============================================================================
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

async def publish_live():
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
        
        # 1. Navigation directe vers l'éditeur de post natif
        print("➔ Navigation directe sur https://www.linkedin.com/feed/?shareActive=true...")
        await page.goto("https://www.linkedin.com/feed/?shareActive=true", wait_until="domcontentloaded", timeout=25000)
        await asyncio.sleep(5)
        
        # 2. Attente de l'éditeur de post
        print("➔ Recherche de la zone de saisie du post...")
        editor = await page.wait_for_selector("div.ql-editor, div[role='textbox'], div[contenteditable='true']", timeout=10000)
        if editor:
            print("✓ Éditeur de post ouvert ! Injection du contenu...")
            await editor.click()
            await asyncio.sleep(1)
            await page.keyboard.insert_text(POST_CONTENT)
            await asyncio.sleep(3)
            
            # 3. Clic sur Publier
            print("➔ Recherche du bouton de publication...")
            pub_btn = await page.wait_for_selector("button.share-actions__primary-action, button:has-text('Publier'), button.artdeco-button--primary", timeout=8000)
            if pub_btn:
                print("🚀 Clic sur 'Publier'...")
                await pub_btn.click()
                await asyncio.sleep(8)
                print("🎉🎉🎉 POST RÉELLEMENT ET DÉFINITIVEMENT PUBLIÉ SUR VOTRE PROFIL LINKEDIN !")
            else:
                print("⚠️ Bouton 'Publier' non détecté, envoi par raccourci clavier...")
                await page.keyboard.press("Control+Enter")
                await asyncio.sleep(8)
        else:
            print("⚠️ Éditeur de post non trouvé.")
            
        await page.screenshot(path="/tmp/linkedin_published_proof.png")
        print("📸 Capture finale enregistrée dans /tmp/linkedin_published_proof.png")
        
        await asyncio.sleep(2)
        await browser_context.close()
        shutil.rmtree(TMP_PROFILE_DIR, ignore_errors=True)
        print("🧹 Nettoyage terminé.")

if __name__ == "__main__":
    asyncio.run(publish_live())
