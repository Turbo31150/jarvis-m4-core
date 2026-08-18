"""cdp.py — Canal Chrome DevTools Protocol (WebSocket) partagé.

Réutilise l'approche validée de bin/cdp-inspect.py : on ouvre le WebSocket d'un
onglet Chrome lancé avec --remote-debugging-port et on envoie des commandes CDP.
C'est le SEUL module qui parle au navigateur ; tout le reste travaille sur les
données qu'il renvoie (couplage faible, cœur/adaptateur).
"""

import json
import time
import base64
import requests
import websocket

WS_CLOSED = (
    websocket.WebSocketConnectionClosedException,
    websocket.WebSocketTimeoutException,
    ConnectionError,
    OSError,
)


class CDP:
    """Adaptateur bas niveau vers un onglet Chrome via CDP (avec reconnexion auto).

    Chrome peut fermer le WebSocket lors d'une navigation cross-site (process-swap) :
    on retient l'id du target pour rouvrir le canal sur le MÊME onglet et rejouer.
    """

    def __init__(self, base="http://127.0.0.1:9223", match="", target=None):
        self.base = base.rstrip("/")
        t = target or self._target(match)
        if not t:
            raise SystemExit(
                f"aucun onglet CDP sur {self.base} (Chrome --remote-debugging-port ?)"
            )
        self._tid = t.get("id")
        self._connect(t["webSocketDebuggerUrl"])
        self._i = 0
        for m in ("Runtime.enable", "DOM.enable", "Page.enable", "Network.enable"):
            self.cmd(m)

    @staticmethod
    def list_tabs(base="http://127.0.0.1:9223"):
        """Liste tous les onglets (targets type=page) avec leur identité."""
        base = base.rstrip("/")
        return [
            {
                "id": t.get("id"),
                "url": t.get("url", ""),
                "title": t.get("title", ""),
                "type": t.get("type"),
                "webSocketDebuggerUrl": t.get("webSocketDebuggerUrl"),
            }
            for t in requests.get(f"{base}/json/list", timeout=5).json()
            if t.get("type") == "page" and t.get("webSocketDebuggerUrl")
        ]

    def _connect(self, ws_url):
        # timeout borné : un onglet muet ne bloque pas > 12 s par commande
        self.ws = websocket.create_connection(ws_url, max_size=None, timeout=12)

    def _target(self, match=""):
        pages = [
            t
            for t in requests.get(f"{self.base}/json/list", timeout=5).json()
            if t.get("type") == "page"
        ]
        for t in pages:
            if match and match in t.get("url", ""):
                return t
        return pages[0] if pages else None

    def reconnect(self, tries=4):
        """Rouvre le WS sur le même onglet (par id), sinon sur le premier onglet."""
        try:
            self.ws.close()
        except Exception:
            pass
        for _ in range(tries):
            try:
                pages = [
                    t
                    for t in requests.get(f"{self.base}/json/list", timeout=5).json()
                    if t.get("type") == "page"
                ]
                t = next((p for p in pages if p.get("id") == self._tid), None) or (
                    pages[0] if pages else None
                )
                if t:
                    self._tid = t.get("id")
                    self._connect(t["webSocketDebuggerUrl"])
                    for m in ("Runtime.enable", "Page.enable", "Network.enable"):
                        self._send(m)
                    return True
            except Exception:
                pass
            time.sleep(1.0)
        return False

    def _send(self, method, params=None):
        """Envoi + attente de la réponse (sans reconnexion) — usage interne."""
        self._i += 1
        mid = self._i
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        while True:
            r = json.loads(self.ws.recv())
            if r.get("id") == mid:
                return r.get("result", {})

    def cmd(self, method, params=None):
        """Commande résiliente : reconnecte + rejoue une fois si le WS tombe."""
        try:
            return self._send(method, params)
        except WS_CLOSED:
            if self.reconnect():
                try:
                    return self._send(method, params)
                except WS_CLOSED:
                    return {}
            return {}

    def evl(self, expr):
        """Évalue du JS dans la page (comme la console DevTools).

        awaitPromise=False : nos expressions sont des lectures DOM synchrones ;
        attendre une promesse pouvait geler jusqu'à 45 s sur un onglet ayant une
        promesse pendante (cause du blocage en mode multi-onglets). timeout=10 s.
        """
        r = self.cmd(
            "Runtime.evaluate",
            {
                "expression": expr,
                "returnByValue": True,
                "awaitPromise": False,
                "timeout": 10000,
            },
        )
        return r.get("result", {}).get("value")

    def events(self, secs):
        """Collecte les événements CDP (Network, Page…) pendant `secs` secondes."""
        out, end = [], time.time() + secs
        self.ws.settimeout(1.0)
        while time.time() < end:
            try:
                r = json.loads(self.ws.recv())
            except WS_CLOSED:
                break  # WS tombé (process-swap) → on arrête proprement
            except Exception:
                continue
            if "method" in r:
                out.append(r)
        try:
            self.ws.settimeout(12)
        except Exception:
            pass
        return out

    def navigate(self, url, wait=3.0):
        try:
            self.cmd("Page.navigate", {"url": url})
        except WS_CLOSED:
            self.reconnect()
        time.sleep(wait)

    def screenshot_png(self):
        r = self.cmd("Page.captureScreenshot", {"format": "png"})
        return base64.b64decode(r["data"]) if r.get("data") else b""

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


# Générateur récursif : traverse le DOM + TOUS les shadow roots (le « code source » réel).
WALK = (
    "function* w(r){for(const e of r.querySelectorAll('*')){"
    "yield e;if(e.shadowRoot)yield* w(e.shadowRoot);}}"
)
