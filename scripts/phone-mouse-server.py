#!/usr/bin/env python3
"""phone-mouse-server.py — reçoit les événements souris de l'APK Android → xdotool (X11).

Protocole : lignes JSON sur TCP (port 8770).
  {"t":"m","dx":5,"dy":3}          -> déplacement relatif du curseur
  {"t":"c","b":"left|right|mid"}   -> clic (option "n":2 -> double-clic)
  {"t":"d","b":"left","st":"down"} -> bouton maintenu (drag) : down puis up
                                      = déplacer une fenêtre / sélectionner
  {"t":"s","n":1|-1}               -> molette (scroll)
USB  : adb reverse tcp:8770 tcp:8770  → l'app se connecte à 127.0.0.1:8770.
WiFi : l'app vise l'IP LAN du PC.
"""

import socket
import json
import subprocess
import os
import threading
import hmac
import hashlib

# Sécurité : loopback par défaut (mode USB via `adb reverse` = 127.0.0.1).
# Pour le mode LAN/WiFi, définir PHONE_MOUSE_HOST=0.0.0.0 ET PHONE_MOUSE_TOKEN=<secret>
# — un hôte non-loopback SANS token est refusé (pas d'injection anonyme).
HOST = os.environ.get("PHONE_MOUSE_HOST", "127.0.0.1")
PORT = int(os.environ.get("PHONE_MOUSE_PORT", "8770"))
TOKEN = os.environ.get("PHONE_MOUSE_TOKEN", "")
DEBUG = os.environ.get("PHONE_MOUSE_DEBUG", "") not in (
    "",
    "0",
)  # trace chaque geste reçu
ENV = {**os.environ, "DISPLAY": os.environ.get("DISPLAY", ":0")}


def _is_loopback(h):
    return h in ("127.0.0.1", "::1", "localhost")


def _require_token():
    # token exigé dès qu'on écoute au-delà du loopback
    return not _is_loopback(HOST)


def xdo(*a):
    subprocess.run(
        ["xdotool", *a], env=ENV, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )


# Média sans gsd-media-keys : les keysyms XF86Audio* sont des no-op quand le daemon
# média du bureau est absent. On agit directement : volume via wpctl, lecture via
# playerctl (MPRIS). Les autres touches (Left/Right/F5/Return...) restent en xdotool.
_SINK = "@DEFAULT_AUDIO_SINK@"
_VOL = {
    "XF86AudioRaiseVolume": ["wpctl", "set-volume", _SINK, "5%+"],
    "XF86AudioLowerVolume": ["wpctl", "set-volume", _SINK, "5%-"],
    "XF86AudioMute": ["wpctl", "set-mute", _SINK, "toggle"],
}
_PLAY = {
    "XF86AudioPlay": "play-pause",
    "XF86AudioNext": "next",
    "XF86AudioPrev": "previous",
}


def media(keysym):
    """Traduit une touche média en action réelle. True si géré, False sinon."""
    cmd = _VOL.get(keysym)
    if cmd is None and keysym in _PLAY:
        cmd = ["playerctl", _PLAY[keysym]]
    if cmd is None:
        return False
    subprocess.run(cmd, env=ENV, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return True


def dispatch(m):
    """Traduit un message JSON déjà parsé en action système (souris/clavier/média).

    Fonction pure côté E/S réseau : ne dépend que de xdo()/media(), donc mockable
    en test. Renvoie le type de message traité (ou None si inconnu/ignoré)."""
    t = m.get("t")
    if DEBUG:
        print(f"[phone-mouse] RX {m}", flush=True)
    if t == "m":
        xdo(
            "mousemove_relative",
            # PAS de --sync : contre un bord d'écran, --sync attend une
            # cible jamais atteinte et fige le serveur.
            "--",
            str(int(m.get("dx", 0))),
            str(int(m.get("dy", 0))),
        )
    elif t == "c":
        b = {"left": "1", "mid": "2", "right": "3"}.get(m.get("b", "left"), "1")
        # double-clic (sélection mot / ouverture) via "n": nombre de clics rapides
        n = max(1, min(int(m.get("n", 1)), 3))
        if n > 1:
            xdo("click", "--repeat", str(n), b)
        else:
            xdo("click", b)
    elif t == "d":
        # drag : bouton maintenu enfoncé -> déplacer une fenêtre, sélectionner
        # (rubber-band), glisser-déposer. L'app envoie "down" au début du geste,
        # puis des {"t":"m",...} pendant le maintien, puis "up" au relâcher.
        b = {"left": "1", "mid": "2", "right": "3"}.get(m.get("b", "left"), "1")
        st = m.get("st", "down")
        xdo("mousedown" if st == "down" else "mouseup", b)
    elif t == "s":
        n = int(m.get("n", 0))
        if n:
            # axe "h" (horizontal, 2 doigts lateral) = boutons 6/7 ; sinon vertical 4/5
            if m.get("ax") == "h":
                btn = "7" if n > 0 else "6"
            else:
                btn = "5" if n > 0 else "4"
            xdo("click", "--repeat", str(min(abs(n), 5)), btn)
    elif t == "z":  # zoom (pincement 2 doigts) = Ctrl + molette
        d = int(m.get("d", 0))
        if d:
            xdo("keydown", "ctrl")
            xdo("click", "--repeat", str(min(abs(d), 5)), "4" if d > 0 else "5")
            xdo("keyup", "ctrl")
    elif t == "type":  # clavier : texte tapé sur le tél
        s = m.get("s", "")
        if s:
            xdo("type", "--", s)
    elif (
        t == "key"
    ):  # média (wpctl/playerctl) sinon touche X (BackSpace, Return, F5...)
        k = m.get("k", "")
        if k and not media(k):
            xdo("key", "--", k)
    else:
        return None
    return t


def handle(conn, addr):
    print(f"[phone-mouse] connecté: {addr}", flush=True)
    # loopback (USB via adb reverse) = de confiance ; sinon challenge/response HMAC.
    authed = not _require_token()
    nonce = ""
    if not authed:
        # défi : nonce aléatoire par connexion -> l'app répond HMAC-SHA256(token, nonce).
        nonce = os.urandom(16).hex()
        try:
            conn.send(('{"t":"nonce","n":"%s"}\n' % nonce).encode())
        except Exception:
            conn.close()
            return
    buf = b""
    try:
        while True:
            data = conn.recv(2048)
            if not data:
                break
            buf += data
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                if not line.strip():
                    continue
                try:
                    m = json.loads(line)
                except Exception:
                    continue
                t = m.get("t")
                if not authed:
                    # 1er message obligatoire : {"t":"auth","hmac":"<hex>"}
                    expected = hmac.new(
                        TOKEN.encode(), nonce.encode(), hashlib.sha256
                    ).hexdigest()
                    if (
                        t == "auth"
                        and TOKEN
                        and hmac.compare_digest(str(m.get("hmac", "")), expected)
                    ):
                        authed = True
                        print(f"[phone-mouse] authentifié (HMAC): {addr}", flush=True)
                    else:
                        print(f"[phone-mouse] REJET (auth): {addr}", flush=True)
                        return
                    continue
                dispatch(m)
    except Exception as e:
        print(f"[phone-mouse] {addr} erreur: {e}", flush=True)
    finally:
        conn.close()
        print(f"[phone-mouse] déconnecté: {addr}", flush=True)


def discovery_responder():
    """Découverte auto (broadcast UDP) : l'app envoie 'PMPRO_DISCOVER', on répond
    'PMPRO_HERE <nom>'. Actif seulement en mode WiFi (non-loopback)."""
    try:
        u = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        u.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        u.bind(("", PORT))
    except Exception as e:
        print(f"[phone-mouse] découverte UDP indisponible: {e}", flush=True)
        return
    try:
        name = socket.gethostname()
    except Exception:
        name = "PC"
    print(f"[phone-mouse] découverte UDP active sur :{PORT}", flush=True)
    while True:
        try:
            data, src = u.recvfrom(256)
            if data.strip().startswith(b"PMPRO_DISCOVER"):
                u.sendto(("PMPRO_HERE %s" % name).encode(), src)
        except Exception:
            continue


def main():
    if _require_token() and not TOKEN:
        raise SystemExit(
            f"[phone-mouse] REFUS : écoute sur {HOST} (non-loopback) sans PHONE_MOUSE_TOKEN. "
            "Définis PHONE_MOUSE_TOKEN=<secret> pour le mode LAN, ou reste en 127.0.0.1 (USB)."
        )
    if _require_token():
        threading.Thread(target=discovery_responder, daemon=True).start()
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(4)
    print(
        f"[phone-mouse] serveur souris téléphone en écoute sur {HOST}:{PORT} "
        f"(DISPLAY={ENV['DISPLAY']}). USB: adb reverse tcp:{PORT} tcp:{PORT}",
        flush=True,
    )
    while True:
        conn, addr = srv.accept()
        threading.Thread(target=handle, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()
