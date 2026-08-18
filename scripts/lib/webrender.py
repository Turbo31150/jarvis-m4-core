#!/usr/bin/env python3
"""
webrender.py — second étage d'acquisition de `web` : rendu navigateur via BrowserOS (CDP).

Quand une page est une SPA JS, le fetch direct ne rend qu'une coquille vide. Ce
module pilote le Chrome headless de BrowserOS (CDP sur :9108) pour obtenir le DOM
rendu, puis rend la main — l'onglet est toujours fermé.

FRONTIÈRE A3 PRÉSERVÉE : l'URL passe par webguard.validate() AVANT toute
navigation. Ce chemin n'est pas une porte dérobée autour du SSRF-gate.

⚠ LIMITE STRUCTURELLE ASSUMÉE — À NE PAS OUBLIER : c'est le navigateur qui
résout le DNS et ouvre la socket, donc **l'épinglage d'IP est impossible sur ce
chemin**. La fenêtre TOCTOU (rebinding DNS) que `webguard.fetch` ferme par
pinning reste théoriquement ouverte ici. Le rendu est donc STRICTEMENT plus
faible que le fetch direct : ne l'utiliser que quand le fetch ne suffit pas, et
jamais comme chemin par défaut.

API : render(url, timeout=20) -> dict
Dépend de `websockets` (présent : 15.0.1). Le reste est stdlib.
"""

import json
import time
import urllib.request
import urllib.parse

from websockets.sync.client import connect

import webguard

CDP_HOST = "127.0.0.1"
CDP_PORT = 9108
CDP_BASE = f"http://{CDP_HOST}:{CDP_PORT}"
DEFAULT_TIMEOUT = 20


class RenderError(Exception):
    """Rendu impossible : CDP absent, onglet non créé, navigation en échec."""


def _cdp_http(path, method="GET"):
    req = urllib.request.Request(f"{CDP_BASE}{path}", method=method)
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        raise RenderError(f"BrowserOS CDP injoignable sur {CDP_BASE}: {exc}") from exc
    try:
        return json.loads(body) if body.strip().startswith(("{", "[")) else body
    except ValueError:
        return body


def _reecrire_ws(ws_url):
    """Remplace l'hôte:port interne annoncé par le container par l'endpoint hôte."""
    parsed = urllib.parse.urlparse(ws_url)
    return urllib.parse.urlunparse(parsed._replace(netloc=f"{CDP_HOST}:{CDP_PORT}"))


def disponible():
    """Vrai si le navigateur répond. Sert à décider d'un fallback sans lever."""
    try:
        v = _cdp_http("/json/version")
        return isinstance(v, dict) and "Browser" in v
    except RenderError:
        return False


def render(url, timeout=DEFAULT_TIMEOUT):
    """Rend une URL dans le navigateur et retourne le DOM.

    Retourne {url, html, title, moteur, duree_ms}.
    Lève webguard.SSRFBlocked si la cible est interne — le gate passe d'abord.
    """
    # A3 AVANT tout : si la cible est interne, on ne navigue même pas.
    webguard.validate(url)

    t0 = time.time()
    cible = _cdp_http(f"/json/new?{urllib.parse.quote(url, safe='')}", method="PUT")
    if not isinstance(cible, dict) or "webSocketDebuggerUrl" not in cible:
        raise RenderError(f"création d'onglet refusée par CDP: {str(cible)[:160]}")

    # BrowserOS tourne en container : CDP annonce son adresse INTERNE
    # (ws://0.0.0.0:3000/...) alors que depuis l'hôte le port est mappé sur
    # 127.0.0.1:9108. Se connecter à l'URL telle quelle donne un
    # ConnectionRefusedError trompeur, alors que /json/version répond 200.
    ws_url = _reecrire_ws(cible["webSocketDebuggerUrl"])
    target_id = cible.get("id", "")
    html, title = "", ""
    try:
        with connect(
            ws_url, open_timeout=10, close_timeout=5, max_size=64 * 1024 * 1024
        ) as ws:

            def envoyer(mid, methode, params=None):
                ws.send(
                    json.dumps({"id": mid, "method": methode, "params": params or {}})
                )

            def attendre(mid, delai):
                fin = time.time() + delai
                while time.time() < fin:
                    reste = max(0.5, fin - time.time())
                    try:
                        msg = json.loads(ws.recv(timeout=reste))
                    except TimeoutError:
                        break
                    except Exception:
                        break
                    if msg.get("id") == mid:
                        return msg
                return None

            envoyer(1, "Page.enable")
            attendre(1, 5)
            envoyer(2, "Page.navigate", {"url": url})
            nav = attendre(2, timeout)
            if nav and nav.get("result", {}).get("errorText"):
                raise RenderError(f"navigation échouée: {nav['result']['errorText']}")

            # laisse le JS peupler le DOM — pas d'attente réseau parfaite en stdlib
            time.sleep(min(3.0, timeout / 4))

            envoyer(
                3,
                "Runtime.evaluate",
                {
                    "expression": "document.documentElement.outerHTML",
                    "returnByValue": True,
                },
            )
            res = attendre(3, timeout)
            html = (((res or {}).get("result", {}) or {}).get("result", {}) or {}).get(
                "value", ""
            ) or ""

            envoyer(
                4,
                "Runtime.evaluate",
                {"expression": "document.title", "returnByValue": True},
            )
            res = attendre(4, 8)
            title = (((res or {}).get("result", {}) or {}).get("result", {}) or {}).get(
                "value", ""
            ) or ""
    finally:
        # l'onglet est TOUJOURS fermé : un rendu qui fuit des onglets finit par
        # saturer le navigateur et casser tous les rendus suivants.
        if target_id:
            try:
                _cdp_http(f"/json/close/{target_id}")
            except RenderError:
                pass

    if not html:
        raise RenderError("le navigateur n'a retourné aucun DOM")

    return {
        "url": url,
        "html": html,
        "title": title,
        "moteur": "browseros-cdp",
        "duree_ms": int((time.time() - t0) * 1000),
    }
