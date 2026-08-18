#!/usr/bin/env python3
"""
Push-to-talk dictée vocale — JARVIS M4 (Wayland).

Maintiens la touche PTT (défaut: Ctrl DROIT) → enregistre.
Relâche → transcrit (Whisper :8789) → écrit au curseur (ydotool).

Pas de toggle, pas de fenêtre : hold-to-talk pur. Lit le clavier via evdev
(niveau noyau, marche sous Wayland). Touche réglable via env JARVIS_PTT_KEY.
"""

import base64
import json
import os
import selectors
import subprocess
import tempfile
import threading
import urllib.request

import evdev
from evdev import ecodes

PTT_KEY = getattr(ecodes, os.environ.get("JARVIS_PTT_KEY", "KEY_RIGHTCTRL"))
AUDIO_DEVICE = os.environ.get("JARVIS_AUDIO_DEVICE", "plughw:1,0")
WHISPER_URL = "http://127.0.0.1:8789/"
LANG = os.environ.get("JARVIS_LANG", "fr")

_rec_proc = None
_wav = None
_lock = threading.Lock()


def beep(kind):
    f = os.path.expanduser(f"~/jarvis/scripts/beep_{kind}.wav")
    if os.path.exists(f):
        subprocess.Popen(
            ["paplay", f], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL
        )


def start_rec():
    global _rec_proc, _wav
    with _lock:
        subprocess.run(["pkill", "-9", "-x", "arecord"], timeout=3)
        _wav = tempfile.mktemp(suffix=".wav")
        _rec_proc = subprocess.Popen(
            [
                "arecord",
                "-D",
                AUDIO_DEVICE,
                "-f",
                "S16_LE",
                "-r",
                "16000",
                "-c",
                "1",
                _wav,
            ],
            stderr=subprocess.DEVNULL,
        )
    beep("start")
    print("[ptt] ● enregistrement…", flush=True)


def stop_and_type():
    global _rec_proc, _wav
    with _lock:
        if _rec_proc:
            _rec_proc.terminate()
            try:
                _rec_proc.wait(timeout=2)
            except Exception:
                _rec_proc.kill()
            _rec_proc = None
        wav = _wav
        _wav = None
    beep("stop")
    if not wav or not os.path.exists(wav):
        print("[ptt] pas d'audio", flush=True)
        return
    print("[ptt] ⏳ transcription…", flush=True)
    try:
        b64 = base64.b64encode(open(wav, "rb").read()).decode()
        data = json.dumps({"audio": b64, "format": "wav", "language": LANG}).encode()
        req = urllib.request.Request(
            WHISPER_URL, data, {"Content-Type": "application/json"}
        )
        text = (
            json.load(urllib.request.urlopen(req, timeout=60)).get("text", "").strip()
        )
    except Exception as e:
        print(f"[ptt] err STT: {e}", flush=True)
        return
    finally:
        try:
            os.remove(wav)
        except OSError:
            pass
    if not text:
        print("[ptt] (vide)", flush=True)
        return
    print(f"[ptt] ✍️  {text!r}", flush=True)
    # Écriture AZERTY-safe sur GNOME/Mutter : COLLER via presse-papier.
    # wtype = non supporté par Mutter ; ydotool type = keycodes US → lettres mélangées sur FR.
    # wl-copy (Unicode exact) + Ctrl+V (keycodes physiques 29/47, identiques en AZERTY).
    import time

    out = text + " "
    subprocess.run(["wl-copy"], input=out.encode(), stderr=subprocess.DEVNULL)
    time.sleep(0.15)
    subprocess.run(
        ["ydotool", "key", "29:1", "47:1", "47:0", "29:0"], stderr=subprocess.DEVNULL
    )


def main():
    devs = []
    for p in evdev.list_devices():
        try:
            d = evdev.InputDevice(p)
            caps = d.capabilities()
            if ecodes.EV_KEY in caps and PTT_KEY in caps[ecodes.EV_KEY]:
                devs.append(d)
        except Exception:
            pass
    if not devs:
        print("[ptt] aucun clavier avec la touche PTT trouvé", flush=True)
        return
    sel = selectors.DefaultSelector()
    for d in devs:
        sel.register(d, selectors.EVENT_READ)
        print(f"[ptt] écoute {d.path} ({d.name})", flush=True)
    keyname = os.environ.get("JARVIS_PTT_KEY", "KEY_RIGHTCTRL")
    print(f"[ptt] PRÊT — maintiens {keyname} pour dicter (relâche = écrit)", flush=True)
    pressed = False
    while True:
        for key, _ in sel.select():
            for ev in key.fileobj.read():
                if ev.type == ecodes.EV_KEY and ev.code == PTT_KEY:
                    if ev.value == 1 and not pressed:  # press
                        pressed = True
                        start_rec()
                    elif ev.value == 0 and pressed:  # release
                        pressed = False
                        threading.Thread(target=stop_and_type, daemon=True).start()


if __name__ == "__main__":
    main()
