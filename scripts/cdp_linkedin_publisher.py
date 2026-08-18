#!/usr/bin/env python3
"""
cdp_linkedin_publisher.py — Publication réelle sur LinkedIn via Chrome DevTools Protocol (Port 9222).
Pilote l'instance Chrome active de l'utilisateur sans déconnexion de session.
"""

import sys
import json
import time
import asyncio
import urllib.request
from pathlib import Path
import websockets

CDP_HTTP = "http://127.0.0.1:9222"

async def cdp_send(ws, method, params=None):
    msg_id = int(time.time() * 1000) % 1000000
    payload = {"id": msg_id, "method": method, "params": params or {}}
    await ws.send(json.dumps(payload))
    while True:
        res = await ws.recv()
        data = json.loads(res)
        if data.get("id") == msg_id:
            return data.get("result", {})

async def post_to_linkedin(text: str):
    print("🌐 [CDP] Recherche de la page principale LinkedIn dans Chrome (Port 9222)...")
    req = urllib.request.urlopen(f"{CDP_HTTP}/json")
    tabs = json.load(req)
    
    target_tab = None
    for t in tabs:
        if t.get("type") == "page" and "linkedin.com" in t.get("url", ""):
            target_tab = t
            break
            
    if not target_tab:
        print("⚠️ Aucun onglet LinkedIn existant trouvé. Ouverture d'un nouvel onglet feed...")
        req_new = urllib.request.urlopen(f"{CDP_HTTP}/json/new?https://www.linkedin.com/feed/")
        target_tab = json.load(req_new)
        await asyncio.sleep(4)

    ws_url = target_tab.get("webSocketDebuggerUrl")
    if not ws_url:
        print("❌ Impossible de récupérer la WebSocket CDP.")
        return False

    print(f"🔗 [CDP] Connexion à la page : {target_tab.get('title', '')} (ID: {target_tab.get('id')})")
    async with websockets.connect(ws_url) as ws:
        cur_url = target_tab.get("url", "")
        if "linkedin.com/feed" not in cur_url:
            print("🧭 [CDP] Navigation vers https://www.linkedin.com/feed/...")
            await cdp_send(ws, "Page.navigate", {"url": "https://www.linkedin.com/feed/"})
            await asyncio.sleep(5)

        # 2. Injecter le script d'ouverture et d'écriture du post
        js_code = f"""
        (async () => {{
            // Attendre le chargement complet du feed
            await new Promise(r => setTimeout(r, 3000));

            // Trouver et cliquer sur le trigger du post (différents sélecteurs LinkedIn)
            let trigger = document.querySelector('button.share-box-feed-entry__trigger') ||
                          document.querySelector('div.share-box-feed-entry__top-bar') ||
                          document.querySelector('.share-box-feed-entry__wrapper') ||
                          Array.from(document.querySelectorAll('button, div[role="button"]')).find(b => {{
                              const txt = (b.innerText || b.getAttribute('aria-label') || '').toLowerCase();
                              return txt.includes('commencer un post') || txt.includes('start a post') || txt.includes('rédiger un post') || txt.includes('partager');
                          }});

            if (trigger) {{
                trigger.click();
                await new Promise(r => setTimeout(r, 2500));
            }}

            // Trouver l'éditeur dans le modal
            let editor = document.querySelector('div.editor-content div.ql-editor') ||
                         document.querySelector('div.editor-content div[contenteditable="true"]') ||
                         document.querySelector('div.ql-editor') ||
                         document.querySelector('div[role="textbox"]');

            if (editor) {{
                editor.focus();
                // Insertion de texte propre
                document.execCommand('insertText', false, {json.dumps(text)});
                
                // Chercher le bouton Publier pour être prêt
                const publishBtn = Array.from(document.querySelectorAll('button')).find(b => {{
                    const txt = (b.innerText || '').trim().toLowerCase();
                    return txt === 'publier' || txt === 'post';
                }});

                return {{
                    status: "ready_and_filled",
                    message: "Texte inséré avec succès dans le modal de publication LinkedIn",
                    publish_button_found: Boolean(publishBtn)
                }};
            }} else {{
                return {{
                    status: "editor_not_found",
                    message: "Éditeur non trouvé après ouverture du modal"
                }};
            }}
        }})()
        """
        
        print("✍️ [CDP] Injection du texte dans l'éditeur LinkedIn...")
        res = await cdp_send(ws, "Runtime.evaluate", {
            "expression": js_code,
            "awaitPromise": True,
            "returnByValue": True
        })
        
        result_val = res.get("result", {}).get("value", {})
        print(f"📋 [CDP Résultat] {json.dumps(result_val, ensure_ascii=False)}")
        return True

def main():
    if len(sys.argv) < 2:
        # Lire le dernier post buffer
        buf = Path("/home/pamerys/jarvis/content_buffer/latest_social_post.md")
        if buf.exists():
            text = buf.read_text(encoding='utf-8')
        else:
            text = "Test de publication réelle JARVIS AI."
    else:
        text = " ".join(sys.argv[1:])

    asyncio.run(post_to_linkedin(text))

if __name__ == "__main__":
    main()
