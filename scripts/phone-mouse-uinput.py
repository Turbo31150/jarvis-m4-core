#!/usr/bin/env python3
"""phone-mouse-uinput.py — souris téléphone via UInput (souris virtuelle NOYAU).

Pourquoi uinput et pas xdotool : xdotool envoie des événements X synthétiques
que les gestionnaires de fenêtres n'interprètent PAS comme un vrai appui-glisser
-> impossible de sélectionner / déplacer une fenêtre. Une souris uinput est un
périphérique d'entrée réel du noyau : clic, drag de fenêtre, rubber-band,
glisser-déposer fonctionnent nativement (X11 ET Wayland).

Le pointeur (move/clic/drag/scroll/zoom-wheel) passe par uinput.
Le clavier (type/key/média) reste en xdotool/wpctl/playerctl (pas besoin de HID clavier).

Protocole (lignes JSON sur TCP :8770, identique à l'APK) :
  {"t":"m","dx":5,"dy":3}            déplacement relatif
  {"t":"c","b":"left|right|mid","n":1} clic (n=2 double)
  {"t":"d","b":"left","st":"down|up"}  bouton MAINTENU (drag) : down puis up
  {"t":"s","n":1|-1,"ax":"h"?}         molette (v/h)
  {"t":"z","d":1|-1}                   zoom (Ctrl+molette)
  {"t":"type","s":"texte"} / {"t":"key","k":"Return"}
USB : adb reverse tcp:8770 tcp:8770 -> l'app vise 127.0.0.1:8770.
"""

import socket
import json
import subprocess
import os
import threading
import hmac
import hashlib
import time
from evdev import UInput, ecodes as e

HOST = os.environ.get("PHONE_MOUSE_HOST", "127.0.0.1")
PORT = int(os.environ.get("PHONE_MOUSE_PORT", "8770"))
TOKEN = os.environ.get("PHONE_MOUSE_TOKEN", "")
DEBUG = os.environ.get("PHONE_MOUSE_DEBUG", "") not in ("", "0")
ENV = {**os.environ, "DISPLAY": os.environ.get("DISPLAY", ":0")}

# ── souris virtuelle noyau ────────────────────────────────────────────────
_CAP = {
    e.EV_REL: [e.REL_X, e.REL_Y, e.REL_WHEEL, e.REL_HWHEEL],
    e.EV_KEY: [e.BTN_LEFT, e.BTN_RIGHT, e.BTN_MIDDLE],
}
_UI = UInput(_CAP, name="phone-mouse-virtual", version=0x1)
_BTN = {"left": e.BTN_LEFT, "mid": e.BTN_MIDDLE, "right": e.BTN_RIGHT}
_lock = threading.Lock()


def _syn():
    _UI.syn()


def move(dx, dy):
    with _lock:
        if dx:
            _UI.write(e.EV_REL, e.REL_X, int(dx))
        if dy:
            _UI.write(e.EV_REL, e.REL_Y, int(dy))
        _syn()


def btn(code, val):
    with _lock:
        _UI.write(e.EV_KEY, code, 1 if val else 0)
        _syn()


def click(code, n=1):
    for _ in range(max(1, min(n, 3))):
        btn(code, 1)
        time.sleep(0.012)
        btn(code, 0)
        time.sleep(0.012)


def wheel(n, horizontal=False):
    with _lock:
        _UI.write(e.EV_REL, e.REL_HWHEEL if horizontal else e.REL_WHEEL, int(n))
        _syn()


def xdo(*a):
    subprocess.run(
        ["xdotool", *a], env=ENV, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )


# média direct (wpctl/playerctl) sinon touche X
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


def media(k):
    cmd = _VOL.get(k)
    if cmd is None and k in _PLAY:
        cmd = ["playerctl", _PLAY[k]]
    if cmd is None:
        return False
    subprocess.run(cmd, env=ENV, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return True


def dispatch(m):
    t = m.get("t")
    if DEBUG:
        print(f"[phone-mouse] RX {m}", flush=True)
    if t == "m":
        move(m.get("dx", 0), m.get("dy", 0))
    elif t == "c":
        click(_BTN.get(m.get("b", "left"), e.BTN_LEFT), int(m.get("n", 1)))
    elif t == "d":
        # DRAG RÉEL : bouton maintenu au niveau noyau -> le WM déplace la fenêtre /
        # sélectionne pendant que les {"t":"m"} suivants arrivent.
        btn(_BTN.get(m.get("b", "left"), e.BTN_LEFT), m.get("st", "down") == "down")
    elif t == "s":
        n = int(m.get("n", 0))
        if n:
            wheel(n, m.get("ax") == "h")
    elif t == "z":
        d = int(m.get("d", 0))
        if d:
            xdo("keydown", "ctrl")
            wheel(1 if d > 0 else -1)
            xdo("keyup", "ctrl")
    elif t == "type":
        s = m.get("s", "")
        if s:
            xdo("type", "--", s)
    elif t == "key":
        k = m.get("k", "")
        if k and not media(k):
            xdo("key", "--", k)
    else:
        return None
    return t


def _is_loopback(h):
    return h in ("127.0.0.1", "::1", "localhost")


def _require_token():
    return not _is_loopback(HOST)


def handle(conn, addr):
    print(f"[phone-mouse] connecté: {addr}", flush=True)
    authed = not _require_token()
    nonce = ""
    if not authed:
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
                if not authed:
                    exp = hmac.new(
                        TOKEN.encode(), nonce.encode(), hashlib.sha256
                    ).hexdigest()
                    if (
                        m.get("t") == "auth"
                        and TOKEN
                        and hmac.compare_digest(str(m.get("hmac", "")), exp)
                    ):
                        authed = True
                        print(f"[phone-mouse] authentifié: {addr}", flush=True)
                    else:
                        print(f"[phone-mouse] REJET auth: {addr}", flush=True)
                        return
                    continue
                dispatch(m)
    except Exception as ex:
        print(f"[phone-mouse] {addr} erreur: {ex}", flush=True)
    finally:
        # relâche tout bouton resté enfoncé (sécurité anti-drag fantôme)
        for c in _BTN.values():
            btn(c, 0)
        conn.close()
        print(f"[phone-mouse] déconnecté: {addr}", flush=True)


def bt_rfcomm_listener(channel=22):
    """Transport BLUETOOTH fiable = canal série RFCOMM/SPP (PAS le HID capricieux).
    Le S9 (app en mode BT-série) se connecte, envoie le MÊME JSON -> uinput.
    Un device Bluetooth apparié est de confiance (comme le loopback USB)."""
    try:
        srv = socket.socket(
            socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM
        )
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("00:00:00:00:00:00", channel))  # BDADDR_ANY
        srv.listen(2)
    except Exception as ex:
        print(f"[phone-mouse] RFCOMM indispo (ch{channel}): {ex}", flush=True)
        return
    # publier le service SPP pour que le téléphone le découvre
    try:
        subprocess.run(
            ["sdptool", "add", "--channel=%d" % channel, "SP"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass
    print(
        f"[phone-mouse] BLUETOOTH RFCOMM en écoute (canal {channel}, SPP)", flush=True
    )
    while True:
        try:
            conn, addr = srv.accept()
            print(f"[phone-mouse] BT connecté: {addr}", flush=True)
            threading.Thread(target=_bt_handle, args=(conn, addr), daemon=True).start()
        except Exception:
            continue


def _bt_handle(conn, addr):
    """Session RFCOMM : device apparié = de confiance, pas de challenge HMAC."""
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
                    dispatch(json.loads(line))
                except Exception:
                    continue
    except Exception as ex:
        print(f"[phone-mouse] BT {addr} erreur: {ex}", flush=True)
    finally:
        for c in _BTN.values():
            btn(c, 0)
        conn.close()
        print(f"[phone-mouse] BT déconnecté: {addr}", flush=True)


def discovery_responder():
    try:
        u = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        u.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        u.bind(("", PORT))
    except Exception as ex:
        print(f"[phone-mouse] découverte UDP indispo: {ex}", flush=True)
        return
    name = socket.gethostname()
    while True:
        try:
            data, src = u.recvfrom(256)
            if data.strip().startswith(b"PMPRO_DISCOVER"):
                u.sendto(("PMPRO_HERE %s" % name).encode(), src)
        except Exception:
            continue


def main():
    if _require_token() and not TOKEN:
        raise SystemExit("[phone-mouse] REFUS : non-loopback sans PHONE_MOUSE_TOKEN.")
    if _require_token():
        threading.Thread(target=discovery_responder, daemon=True).start()
    # Transport BLUETOOTH (RFCOMM/SPP) toujours actif en parallèle du TCP/USB,
    # sauf si désactivé explicitement (PHONE_MOUSE_BT=0).
    if os.environ.get("PHONE_MOUSE_BT", "1") not in ("", "0"):
        threading.Thread(target=bt_rfcomm_listener, daemon=True).start()
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(4)
    print(
        f"[phone-mouse] UInput souris virtuelle en écoute {HOST}:{PORT} "
        f"(DISPLAY={ENV['DISPLAY']}). USB: adb reverse tcp:{PORT} tcp:{PORT}",
        flush=True,
    )
    while True:
        conn, addr = srv.accept()
        threading.Thread(target=handle, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()
