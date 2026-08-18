#!/usr/bin/env python3
"""
PTT press-and-hold daemon
- Maintenir Ctrl+X = enregistre micro
- Relâcher Ctrl+X = transcrit via Whisper (8789) + tape texte sous curseur via xdotool
- Court appui (< 250 ms) ignoré (anti-rebond / collision Ctrl+X copier)
"""

import base64
import json
import os
import signal
import subprocess
import tempfile
import time
import urllib.request
from pynput import keyboard

WHISPER_URL = "http://127.0.0.1:8789/"
LANG = "fr"
SAMPLE_RATE = 16000
MIN_HOLD_MS = 250
MAX_HOLD_S = 60
LOG = "/tmp/jarvis-ptt-hold.log"

state = {"ctrl": False, "rec_proc": None, "wav": None, "start_ts": 0.0}


def log(msg):
    with open(LOG, "a") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")


def notify(title, body, timeout=1500):
    subprocess.Popen(
        [
            "notify-send",
            "-t",
            str(timeout),
            "-i",
            "audio-input-microphone",
            title,
            body,
        ],
        env={**os.environ, "DISPLAY": os.environ.get("DISPLAY", ":0")},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def start_recording():
    if state["rec_proc"]:
        return
    fd, wav = tempfile.mkstemp(prefix="ptt-", suffix=".wav")
    os.close(fd)
    state["wav"] = wav
    state["start_ts"] = time.time()
    # arecord pipewire (fallback default si pas de pipewire)
    cmd = [
        "arecord",
        "-D",
        "pipewire",
        "-q",
        "-f",
        "S16_LE",
        "-r",
        str(SAMPLE_RATE),
        "-c",
        "1",
        "-d",
        str(MAX_HOLD_S),
        wav,
    ]
    try:
        state["rec_proc"] = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        log("arecord introuvable")
        return
    notify("🎙 JARVIS PTT", "Enregistrement…", 800)
    log(f"REC start → {wav}")


def stop_and_transcribe():
    proc = state["rec_proc"]
    wav = state["wav"]
    held_ms = int((time.time() - state["start_ts"]) * 1000)
    state["rec_proc"] = None
    state["wav"] = None
    if not proc:
        return
    proc.send_signal(signal.SIGINT)
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()

    if held_ms < MIN_HOLD_MS:
        log(f"hold {held_ms}ms < {MIN_HOLD_MS}ms → skip (laisse Ctrl+X passer)")
        if wav and os.path.exists(wav):
            os.unlink(wav)
        return

    try:
        size = os.path.getsize(wav) if wav and os.path.exists(wav) else 0
        if size < 4096:
            notify("⚠ JARVIS PTT", f"Audio trop court ({size}B)", 1500)
            return
        with open(wav, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode()
        payload = json.dumps(
            {"audio": audio_b64, "language": LANG, "format": "wav"}
        ).encode()
        req = urllib.request.Request(
            WHISPER_URL, data=payload, headers={"Content-Type": "application/json"}
        )
        notify("🛑 JARVIS PTT", "Transcription…", 800)
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        dt = int((time.time() - t0) * 1000)
        text = (data.get("text") or "").strip()
        log(f"transcribe {dt}ms → {text!r}")
        if not text:
            notify("⚠ JARVIS PTT", "Aucun texte", 1200)
            return
        # Tape dans la fenêtre active
        env = {**os.environ, "DISPLAY": os.environ.get("DISPLAY", ":0")}
        subprocess.run(
            ["xdotool", "type", "--clearmodifiers", "--delay", "8", "--", text],
            env=env,
            check=False,
        )
        notify("✓ JARVIS", text[:80], 1500)
    except Exception as e:
        log(f"ERR transcribe: {e}")
        notify("✗ JARVIS PTT", str(e)[:80], 2000)
    finally:
        if wav and os.path.exists(wav):
            try:
                os.unlink(wav)
            except Exception:
                pass


def on_press(key):
    if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
        state["ctrl"] = True
        return
    try:
        if state["ctrl"] and hasattr(key, "char") and key.char in ("\x18", "x", "X"):
            if not state["rec_proc"]:
                start_recording()
    except Exception:
        pass


def on_release(key):
    if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
        state["ctrl"] = False
        if state["rec_proc"]:
            stop_and_transcribe()
        return
    try:
        if hasattr(key, "char") and key.char in ("\x18", "x", "X"):
            if state["rec_proc"]:
                stop_and_transcribe()
    except Exception:
        pass


def main():
    log("=== ptt-hold-daemon start ===")
    notify("JARVIS PTT", "Ctrl+X maintenu = parler", 2000)
    with keyboard.Listener(
        on_press=on_press, on_release=on_release, suppress=False
    ) as l:
        l.join()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
