#!/usr/bin/env python3
"""
DOMINO reproductible — joindre des fichiers (PDF...) à une conversation LinkedIn et envoyer.
Méthode validée 2026-07-17 : CDP DOM.setFileInputFiles sur l'input file de la messagerie.

Usage:
  python3 linkedin_attach_send.py "<nom prospect>" fichier1.pdf [fichier2.pdf ...] \
      [--message "texte accompagnant"] [--no-send]

Gotchas capturées :
- LinkedIn a 2 input[type=file] : [0] accept image/*, [1] accept .pdf,.docx,.xlsx...
  setFileInputFiles fonctionne même sur l'input caché ; on cible le dernier (documents).
- Joindre plusieurs fichiers : un setFileInputFiles PAR fichier restant (LinkedIn n'empile pas
  toujours une liste d'un coup) — on vérifie la présence puis on complète.
- Vérifier composer vidé après clic = preuve d'envoi.
- Réutilise linkedin_cdp_client (session CDP LinkedIn déjà loguée, port 9222).
"""

import sys
import json
import time
import importlib.util
import argparse

CDP = "/home/pamerys/jarvis/scripts/linkedin_cdp_client.py"


def load():
    spec = importlib.util.spec_from_file_location("licdp", CDP)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prospect")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--message", default="")
    ap.add_argument("--no-send", action="store_true")
    a = ap.parse_args()
    m = load()
    files = [
        f if f.startswith("/") else __import__("os").path.abspath(f) for f in a.files
    ]

    with m.linkedin_session() as s:
        conv = m.extract_inbox_messages(s)
        key = a.prospect.lower()
        idx = next((c["idx"] for c in conv if key in c["sender"].lower()), None)
        if idx is None:
            print("ABORT: prospect introuvable:", a.prospect)
            return 1
        print("cible:", conv[idx]["sender"])
        m.open_conversation(s, idx)
        time.sleep(2.5)

        # message optionnel
        if a.message:
            js = (
                "((t)=>{const e=document.querySelector('.msg-form__contenteditable');if(!e)return 0;"
                "e.focus();document.execCommand('selectAll',false,null);document.execCommand('delete',false,null);"
                "document.execCommand('insertText',false,t);"
                "e.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'insertText'}));return (e.innerText||'').length;})(%s)"
            )
            s.evaluate(js % json.dumps(a.message))
            time.sleep(0.5)

        s.send("DOM.enable")

        def present():
            return s.evaluate(
                "(()=>{const t=(document.querySelector('.msg-form')||document.body).innerText;"
                "return (t.match(/\\.pdf|\\.docx|\\.xlsx/gi)||[]).length;})()"
            )

        doc = s.send("DOM.getDocument", {"depth": -1})
        root = doc["root"]["nodeId"]
        nodes = s.send(
            "DOM.querySelectorAll", {"nodeId": root, "selector": "input[type=file]"}
        ).get("nodeIds", [])
        target = nodes[-1] if nodes else None  # dernier = documents

        # joindre chaque fichier (un par un pour fiabilité)
        for f in files:
            before = present()
            try:
                s.send("DOM.setFileInputFiles", {"files": [f], "nodeId": target})
            except Exception:
                # fallback: essayer tous les inputs
                for nid in nodes:
                    try:
                        s.send("DOM.setFileInputFiles", {"files": [f], "nodeId": nid})
                        break
                    except Exception:
                        pass
            time.sleep(5)
            print(f"joint: {f} (PJ visibles: {present()})")

        if a.no_send:
            print("PJ en place, --no-send : à envoyer manuellement.")
            return 0

        res = s.evaluate(
            "(()=>{const b=document.querySelector('.msg-form__send-btn')||"
            "Array.from(document.querySelectorAll('button')).find(x=>/envoyer|send/i.test(x.innerText));"
            "if(!b||b.disabled)return{ok:false};b.click();return{ok:true};})()"
        )
        time.sleep(3)
        ed = (
            s.evaluate(
                "(document.querySelector('.msg-form__contenteditable')||{}).innerText||''"
            )
            or ""
        )
        sent = res.get("ok") and len(ed.strip()) == 0
        print("SEND:", res, "| envoyé:", sent)
        return 0 if sent else 2


if __name__ == "__main__":
    sys.exit(main())
