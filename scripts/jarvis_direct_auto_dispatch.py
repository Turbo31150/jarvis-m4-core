#!/usr/bin/env python3
"""
JARVIS-OMEGA — Direct Instant Dispatcher (Zéro Rétention / Zéro Attente)
========================================================================
Dès qu'un livrable (post LinkedIn, devis B2B, candidature) est compilé et prêt :
1. Envoi et publication instantanée sans attente
2. Pilotage Playwright / SMTP / BrowserOS
3. Mise à jour immédiate du statut en base
4. Purge des fichiers temporaires (Zéro Déchet)
"""

import os
import sys
import time
import shutil
import sqlite3
import datetime
import asyncio
import subprocess
from pathlib import Path
from playwright.async_api import async_playwright

DB_MASTER = Path("/home/pamerys/jarvis/jarvis_master.db")
CHROME_PROFILE_SRC = Path("/home/pamerys/.config/google-chrome/Profile 10")
TMP_PROFILE_DIR = Path("/tmp/chrome_franck_direct_dispatch")

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

async def dispatch_next_queued_post():
    with sqlite3.connect(str(DB_MASTER), timeout=30) as cx:
        cx.row_factory = sqlite3.Row
        row = cx.execute("""
            SELECT id, theme, hook, content 
            FROM linkedin_content_stream 
            WHERE status IN ('READY', 'QUEUED') 
            ORDER BY id ASC LIMIT 1
        """).fetchone()
        
    if not row:
        print("ℹ️ Aucun post en file d'attente. Système en écoute active...")
        return False
        
    post_id = row["id"]
    theme = row["theme"]
    content = row["content"]
    
    print(f"⚡ [EXPÉDITION DIRECTE] Dépilement immédiat du Post #{post_id} : '{theme}'")
    prepare_cloned_profile()

    publie_ok = False
    motif_echec = "clic Publier jamais atteint"

    try:
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
            await page.goto("https://www.linkedin.com/feed/?shareActive=true", wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(4)
            
            editor = await page.wait_for_selector("div.ql-editor, div[contenteditable='true']", timeout=8000)
            if editor:
                await editor.click()
                await page.keyboard.insert_text(content)
                await asyncio.sleep(2)
                
                pub_btn = await page.wait_for_selector("button.share-actions__primary-action, button:has-text('Publier')", timeout=6000)
                if pub_btn:
                    await pub_btn.click()
                    await asyncio.sleep(6)
                    publie_ok = True
                    motif_echec = ""
                    print(f"🚀 [EXPÉDIÉ EN DIRECT] Post #{post_id} publié sur LinkedIn !")

            await browser_context.close()
            shutil.rmtree(TMP_PROFILE_DIR, ignore_errors=True)
    except Exception as e:
        motif_echec = f"exception Playwright: {e}"
        print(f"⚠️ Exception Playwright traitée: {e}")

    # Validation en base — le statut reflete la REALITE mesuree, pas l'intention.
    statut = 'DISPATCHED_DIRECT_LIVE' if publie_ok else 'ECHEC_PUBLICATION'
    with sqlite3.connect(str(DB_MASTER), timeout=30) as cx:
        cx.execute("""
            UPDATE linkedin_content_stream
            SET status=?, created_at=CURRENT_TIMESTAMP
            WHERE id=?
        """, (statut, post_id))

    if publie_ok:
        print(f"✓ Post #{post_id} validé avec le statut 'DISPATCHED_DIRECT_LIVE'.")
    else:
        print(f"✗ Post #{post_id} NON publié — statut 'ECHEC_PUBLICATION' ({motif_echec}).")
    return publie_ok

def clean_temp():
    os.system("rm -f /tmp/*.png /tmp/*.xml /tmp/*.3gp /tmp/*.wav /tmp/*.mp3 2>/dev/null")

def run_once_or_loop():
    loop_mode = "--loop" in sys.argv
    print("==================================================================")
    print("🚀 [DIRECT AUTO-DISPATCH] EXPÉDITION IMMÉDIATE DES LIVRABLES PRÊTS")
    print("==================================================================")
    
    if not loop_mode:
        asyncio.run(dispatch_next_queued_post())
        clean_temp()
    else:
        print("🔄 Mode écoute et envoi continu en arrière-plan activé...")
        while True:
            try:
                has_dispatched = asyncio.run(dispatch_next_queued_post())
                clean_temp()
                time.sleep(30 if has_dispatched else 60)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"⚠️ Erreur boucle: {e}")
                time.sleep(10)

if __name__ == "__main__":
    run_once_or_loop()
