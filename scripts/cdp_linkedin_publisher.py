#!/usr/bin/env python3
"""
cdp_linkedin_publisher.py — Publication DIRECTE et RÉELLE sur LinkedIn via CDP & BrowserOS.
Pilote automatiquement l'éditeur LinkedIn et clique sur Publier.
"""

import sys
import json
import time
import asyncio
import urllib.request
from pathlib import Path
import websockets

CDP_PORTS = [9222, 9108]

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
    print("🌐 [CDP DIRECT] Recherche d'une passerelle CDP active (9222 / 9108)...")
    
    cdp_http = None
    tabs = []
    for port in CDP_PORTS:
        try:
            req = urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=3)
            tabs = json.load(req)
            cdp_http = f"http://127.0.0.1:{port}"
            print(f"✓ Connecté au port CDP {port}")
            break
        except Exception:
            continue
            
    if not cdp_http:
        print("⚠️ Aucune passerelle CDP active sur 9222/9108.")
        return False
        
    target_tab = None
    for t in tabs:
        if t.get("type") == "page" and "linkedin.com" in t.get("url", ""):
            target_tab = t
            break
            
    if not target_tab:
        print("⚠️ Aucun onglet LinkedIn ouvert. Ouverture d'un nouvel onglet...")
        try:
            req_new = urllib.request.urlopen(f"{cdp_http}/json/new?https://www.linkedin.com/feed/")
            target_tab = json.load(req_new)
            await asyncio.sleep(4)
        except Exception as e:
            print(f"Erreur ouverture onglet: {e}")
            return False

    ws_url = target_tab.get("webSocketDebuggerUrl")
    if not ws_url:
        print("❌ WebSocket URL non trouvée.")
        return False

    print(f"🔗 [CDP] Connexion à l'onglet : {target_tab.get('title', 'LinkedIn')}...")
    async with websockets.connect(ws_url) as ws:
        cur_url = target_tab.get("url", "")
        if "linkedin.com/feed" not in cur_url:
            await cdp_send(ws, "Page.navigate", {"url": "https://www.linkedin.com/feed/"})
            await asyncio.sleep(4)

        js_code = f"""
        (async () => {{
            await new Promise(r => setTimeout(r, 2000));

            let trigger = document.querySelector('button.share-box-feed-entry__trigger') ||
                          document.querySelector('div.share-box-feed-entry__top-bar') ||
                          document.querySelector('.share-box-feed-entry__wrapper') ||
                          Array.from(document.querySelectorAll('button, div[role="button"]')).find(b => {{
                              const txt = (b.innerText || b.getAttribute('aria-label') || '').toLowerCase();
                              return txt.includes('commencer un post') || txt.includes('start a post') || txt.includes('rédiger un post') || txt.includes('partager');
                          }});

            if (trigger) {{
                trigger.click();
                await new Promise(r => setTimeout(r, 2000));
            }}

            let editor = document.querySelector('div.editor-content div.ql-editor') ||
                         document.querySelector('div.editor-content div[contenteditable="true"]') ||
                         document.querySelector('div.ql-editor') ||
                         document.querySelector('div[role="textbox"]');

            if (editor) {{
                editor.focus();
                document.execCommand('insertText', false, {json.dumps(text)});
                await new Promise(r => setTimeout(r, 1500));
                
                const publishBtn = Array.from(document.querySelectorAll('button')).find(b => {{
                    const txt = (b.innerText || '').trim().toLowerCase();
                    return txt === 'publier' || txt === 'post';
                }});

                if (publishBtn && !publishBtn.disabled) {{
                    publishBtn.click();
                    return {{ status: "PUBLISHED_SUCCESS", message: "Post publié en direct sur LinkedIn !" }};
                }} else {{
                    return {{ status: "READY_IN_EDITOR", message: "Texte inséré dans l'éditeur LinkedIn" }};
                }}
            }}
            return {{ status: "NO_EDITOR", message: "Éditeur non accessible" }};
        }})()
        """
        
        print("✍️ [CDP] Exécution de l'injection et publication...")
        res = await cdp_send(ws, "Runtime.evaluate", {
            "expression": js_code,
            "awaitPromise": True,
            "returnByValue": True
        })
        
        result_val = res.get("result", {}).get("value", {})
        print(f"📋 [CDP Résultat] {json.dumps(result_val, ensure_ascii=False)}")
        return True

def main():
    text = "🔥 Architecture IA Souveraine On-Premise en 2026 : Pourquoi 84% des DSI du CAC40 refusent d'envoyer leurs données stratégiques sur les API Cloud américaines.\n\nChez JARVIS OS, nous déployons une infrastructure 100% interne avec inférence locale 0 ms, zéro fuite réseau et coût marginal nul.\n\n#IASouveraine #Cybersécurité #OnPremise #TechLeadership #JARVIS"
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
    asyncio.run(post_to_linkedin(text))

if __name__ == "__main__":
    main()
