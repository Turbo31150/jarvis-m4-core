#!/usr/bin/env python3
"""
Publication en direct sur le compte LinkedIn officiel de Franck Delmas
via Chrome CDP (Port 9222).
"""

import sys
import json
import time
import asyncio
import urllib.request
import websockets

CDP_PORT = 9222

POST_TEXT = """🔥 Pourquoi les équipes d'ingénierie et de direction adoptent l'IA souveraine On-Premise en 2026.

Face aux exigences de la directive NIS2 et du nouvel EU AI Act, internaliser ses modèles d'IA devient le standard de confiance :
✅ Inférence locale 0 ms sur GPU dédiés (modèles ouverts 9B à 35B quantisés)
✅ Zéro exfiltration réseau (fonctionnement certifié en mode avion)
✅ Zéro coût récurrent d'API Cloud

Chez JARVIS OS, nos systèmes multi-agents spécialisés automatisent des dizaines de milliers de tâches critiques par jour sans aucune dépendance extérieure.

👉 DSI, RSSI, Directeurs R&D : quelle est votre feuille de route pour 2026 ? Échangeons en commentaire.

#IASouveraine #NIS2 #OnPremise #Cybersécurité #MultiAgents #JARVIS #TechLeadership #Innovation2026"""

async def cdp_call(ws, method, params=None, msg_id=1):
    req = {"id": msg_id, "method": method, "params": params or {}}
    await ws.send(json.dumps(req))
    while True:
        res = await ws.recv()
        data = json.loads(res)
        if data.get("id") == msg_id:
            return data.get("result", {})

async def post_live():
    print("🌐 [CDP FRANCK DELMAS] Connexion à l'instance Chrome active sur port 9222...")
    req = urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json")
    tabs = json.load(req)
    
    target_tab = None
    for t in tabs:
        if t.get("type") == "page":
            target_tab = t
            break
            
    if not target_tab:
        print("❌ Aucun onglet de page trouvé.")
        return False
        
    ws_url = target_tab.get("webSocketDebuggerUrl")
    print(f"🔗 Connexion à l'onglet : {target_tab.get('title')} ({target_tab.get('url')})")
    
    async with websockets.connect(ws_url) as ws:
        print("🧭 Navigation vers https://www.linkedin.com/feed/...")
        await cdp_call(ws, "Page.navigate", {"url": "https://www.linkedin.com/feed/"}, msg_id=10)
        
        # Attendre le chargement
        await asyncio.sleep(5)
        
        # Script d'ouverture du modal et écriture
        js_inject = f"""
        (async () => {{
            // Attendre le feed
            await new Promise(r => setTimeout(r, 2000));
            
            // Trouver le bouton "Commencer un post"
            const buttons = Array.from(document.querySelectorAll('button, div[role="button"]'));
            const startBtn = buttons.find(b => {{
                const txt = (b.innerText || b.getAttribute('aria-label') || '').toLowerCase();
                return txt.includes('commencer un post') || txt.includes('start a post') || txt.includes('rédiger') || txt.includes('partager un');
            }});
            
            if (startBtn) {{
                startBtn.click();
                await new Promise(r => setTimeout(r, 2500));
            }}
            
            // Trouver le champ éditeur
            const editor = document.querySelector('div.ql-editor') ||
                           document.querySelector('div.editor-content div[contenteditable="true"]') ||
                           document.querySelector('div[role="textbox"]');
                           
            if (editor) {{
                editor.focus();
                document.execCommand('insertText', false, {json.dumps(POST_TEXT)});
                await new Promise(r => setTimeout(r, 2000));
                
                // Trouver le bouton publier
                const postBtns = Array.from(document.querySelectorAll('button'));
                const publishBtn = postBtns.find(b => {{
                    const txt = (b.innerText || '').trim().toLowerCase();
                    return txt === 'publier' || txt === 'post';
                }});
                
                if (publishBtn && !publishBtn.disabled) {{
                    publishBtn.click();
                    return {{ status: "SUCCESS_PUBLISHED", message: "Post officiel Franck Delmas publié avec succès !" }};
                }} else {{
                    return {{ status: "READY_IN_MODAL", message: "Post injecté dans l'éditeur, prêt à l'envoi." }};
                }}
            }}
            
            return {{ status: "FEED_INSPECTED", title: document.title, url: window.location.href }};
        }})()
        """
        
        print("✍️ Injection du post officiel de Franck Delmas...")
        eval_res = await cdp_call(ws, "Runtime.evaluate", {
            "expression": js_inject,
            "awaitPromise": True,
            "returnByValue": True
        }, msg_id=20)
        
        result_val = eval_res.get("result", {}).get("value", {})
        print(f"📋 Résultat d'exécution : {json.dumps(result_val, ensure_ascii=False, indent=2)}")

if __name__ == "__main__":
    asyncio.run(post_live())
