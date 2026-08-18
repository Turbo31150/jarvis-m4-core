#!/usr/bin/env python3
"""Pilote Facebook via CDP — session réelle du profil cloné, aucune API tierce.

Usage :
    fb-cdp.py whoami                     # vérifie que la session est connectée
    fb-cdp.py search "<requête>"         # liste les groupes correspondants
    fb-cdp.py join <url-du-groupe>       # demande d'adhésion (une seule)
    fb-cdp.py shot <fichier.png>         # capture d'écran de l'onglet courant

Prudence délibérée : `join` traite UN groupe par appel et impose un délai.
Facebook restreint les comptes qui enchaînent les adhésions en rafale.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request

import websocket  # websocket-client

CDP = "http://127.0.0.1:9333"


def _target() -> str:
    tabs = json.load(urllib.request.urlopen(f"{CDP}/json/list", timeout=10))
    pages = [t for t in tabs if t.get("type") == "page"]
    if not pages:
        raise SystemExit("aucun onglet ouvert")
    return pages[0]["webSocketDebuggerUrl"]


class Tab:
    def __init__(self) -> None:
        self.ws = websocket.create_connection(_target(), timeout=60)
        self.n = 0

    def call(self, method: str, **params):
        self.n += 1
        self.ws.send(json.dumps({"id": self.n, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self.n:
                if "error" in msg:
                    raise RuntimeError(msg["error"])
                return msg.get("result", {})

    def js(self, expr: str):
        r = self.call(
            "Runtime.evaluate",
            expression=expr,
            returnByValue=True,
            awaitPromise=True,
        )
        return r.get("result", {}).get("value")

    def goto(self, url: str, wait: float = 6.0):
        self.call("Page.enable")
        self.call("Page.navigate", url=url)
        time.sleep(wait)

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


def whoami(tab: Tab):
    tab.goto("https://www.facebook.com/me", wait=7)
    info = tab.js(
        """(() => {
            const m = document.cookie.match(/c_user=(\\d+)/);
            return JSON.stringify({
                url: location.href,
                titre: document.title,
                connecte: !/login|checkpoint/.test(location.href),
                uid: m ? m[1] : null,
            });
        })()"""
    )
    print(info)


def search(tab: Tab, query: str):
    from urllib.parse import quote

    tab.goto(f"https://www.facebook.com/search/groups/?q={quote(query)}", wait=9)
    # défilement pour charger davantage de résultats
    for _ in range(4):
        tab.js("window.scrollBy(0, 1400)")
        time.sleep(2.0)
    out = tab.js(
        """(() => {
            const vus = new Set(), res = [];
            for (const a of document.querySelectorAll('a[href*="/groups/"]')) {
                const m = a.href.match(/facebook\\.com\\/groups\\/([^/?]+)/);
                if (!m) continue;
                const id = m[1];
                if (vus.has(id) || id === 'feed' || id === 'discover') continue;
                const bloc = a.closest('div[role="article"]') || a.parentElement?.parentElement;
                const txt = (bloc?.innerText || a.innerText || '').trim();
                if (!txt) continue;
                vus.add(id);
                res.push({ id, url: 'https://www.facebook.com/groups/' + id,
                           texte: txt.split('\\n').slice(0, 4).join(' · ').slice(0, 220) });
            }
            return JSON.stringify(res.slice(0, 40));
        })()"""
    )
    print(out)


def join(tab: Tab, url: str):
    tab.goto(url, wait=8)
    res = tab.js(
        """(() => {
            const cibles = [...document.querySelectorAll('div[role="button"],a[role="button"],span')]
                .filter(e => /^(Rejoindre le groupe|Rejoindre|Join group|Join)$/i.test((e.innerText||'').trim()));
            if (!cibles.length) return JSON.stringify({ok:false, raison:'bouton Rejoindre introuvable (déjà membre ?)'});
            cibles[0].click();
            return JSON.stringify({ok:true, clique:(cibles[0].innerText||'').trim()});
        })()"""
    )
    print(res)
    time.sleep(3)


def shot(tab: Tab, path: str):
    import base64

    r = tab.call("Page.captureScreenshot", format="png")
    open(path, "wb").write(base64.b64decode(r["data"]))
    print(path)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    cmd = sys.argv[1]
    tab = Tab()
    try:
        if cmd == "whoami":
            whoami(tab)
        elif cmd == "search":
            search(tab, sys.argv[2])
        elif cmd == "join":
            join(tab, sys.argv[2])
        elif cmd == "shot":
            shot(tab, sys.argv[2])
        else:
            raise SystemExit(__doc__)
    finally:
        tab.close()


if __name__ == "__main__":
    main()
