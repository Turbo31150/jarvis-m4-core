#!/usr/bin/env python3
"""
JARVIS Voice Widget — Overlay flottant ultra-simple
Raccourci → Enregistre → Transcrit → Clipboard (+ fichier optionnel)

Usage : python3 voice_widget.py
        python3 voice_widget.py --hotkey "ctrl+alt+r" --lang fr --save ~/Documents/
"""

import argparse
import io
import os
import subprocess
import threading
import time
import tkinter as tk
import wave
from pathlib import Path

import numpy as np
import pynput.keyboard as pk
import pyperclip
import requests

# ── Config par défaut ─────────────────────────────────────────────────────────

WHISPER_URL = "http://127.0.0.1:9743/v1/audio/transcriptions"
DEFAULT_HOTKEY = "ctrl+alt+r"
DEFAULT_LANG = "fr"
SAMPLE_RATE = 16000
CHANNELS = 1
TRANSLATE_CMD = os.path.expanduser("~/jarvis/scripts/lm-ask.sh")


def _ecran_primaire(largeur_totale, hauteur_totale):
    """Rectangle (x, y, largeur, hauteur) de l'ecran primaire selon xrandr.

    Sans cela, un multi-ecran aux hauteurs ou offsets differents fait sortir le
    widget de la zone visible : le bureau X global peut mesurer 3840x1179 alors
    qu'aucun ecran n'affiche la ligne y=1099.
    Repli sur le bureau entier si xrandr est absent ou muet (Wayland pur, etc.).
    """
    try:
        sortie = subprocess.run(
            ["xrandr", "--query"], capture_output=True, text=True, timeout=5
        ).stdout
        for ligne in sortie.splitlines():
            if " connected" not in ligne or "primary" not in ligne:
                continue
            for mot in ligne.split():
                if "x" in mot and "+" in mot:
                    taille, ox, oy = mot.split("+")
                    lg, ht = taille.split("x")
                    return int(ox), int(oy), int(lg), int(ht)
    except Exception:
        pass
    return 0, 0, largeur_totale, hauteur_totale


# ── Parse args ────────────────────────────────────────────────────────────────

parser = argparse.ArgumentParser()
parser.add_argument("--hotkey", default=DEFAULT_HOTKEY)
parser.add_argument(
    "--pos",
    default=None,
    help="position forcee 'X,Y' (sinon bas-droite ecran primaire)",
)
parser.add_argument("--lang", default=DEFAULT_LANG, help="fr|en|auto")
parser.add_argument("--translate", action="store_true", help="Traduire en français")
parser.add_argument("--save", default="", help="Dossier de sauvegarde (optionnel)")
args = parser.parse_args()

# ── État global ───────────────────────────────────────────────────────────────

state = {"mode": "idle"}  # idle | recording | processing
audio_buffer: list = []
record_thread = None
stop_event = threading.Event()


# ── Widget GTK minimal ────────────────────────────────────────────────────────


class VoiceWidget:
    COLORS = {
        "idle": ("#0a0e14", "#00d4ff", "🎙  " + args.hotkey.upper()),
        "recording": ("#1a0000", "#ff4444", "⏹  ENREGISTREMENT..."),
        "processing": ("#0a0a00", "#ffaa00", "⏳  TRANSCRIPTION..."),
        "done": ("#001a00", "#00e676", "✓  COPIÉ"),
        "error": ("#1a0000", "#ff6666", "✗  ERREUR"),
    }

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("JARVIS Voice")
        self.root.overrideredirect(True)  # sans bordure
        self.root.attributes("-topmost", True)  # toujours au-dessus
        self.root.attributes("-alpha", 0.92)
        self.root.configure(bg="#0a0e14")
        self.root.resizable(False, False)

        # Position : coin bas-droite de l'ECRAN PRIMAIRE.
        # winfo_screenwidth/height renvoient le bureau X entier (tous écrans
        # réunis, ici 3840x1179). S'y fier place le widget hors de toute zone
        # visible dès que les écrans ont des hauteurs ou des offsets différents.
        px, py, pw, ph = _ecran_primaire(
            self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        )
        if args.pos:
            x, y = (int(v) for v in args.pos.split(","))
        else:
            x, y = px + pw - 340, py + ph - 80
        self.root.geometry(f"320x56+{x}+{y}")

        # Layout
        self.frame = tk.Frame(self.root, bg="#0a0e14", padx=10, pady=6)
        self.frame.pack(fill="both", expand=True)

        self.btn = tk.Button(
            self.frame,
            text="🎙",
            font=("Courier", 18),
            bg="#0a0e14",
            fg="#00d4ff",
            bd=0,
            activebackground="#1a2a3a",
            activeforeground="#00d4ff",
            cursor="hand2",
            command=self.toggle,
        )
        self.btn.pack(side="left", padx=(0, 8))

        self.label = tk.Label(
            self.frame,
            text=args.hotkey.upper(),
            font=("Consolas", 10),
            bg="#0a0e14",
            fg="#00d4ff",
            anchor="w",
        )
        self.label.pack(side="left", fill="x", expand=True)

        self.close_btn = tk.Button(
            self.frame,
            text="×",
            font=("Courier", 12),
            bg="#0a0e14",
            fg="#4a6a8a",
            bd=0,
            activebackground="#0a0e14",
            activeforeground="#ff4444",
            cursor="hand2",
            command=self.root.destroy,
        )
        self.close_btn.pack(side="right")

        # Drag
        self.frame.bind("<ButtonPress-1>", self._drag_start)
        self.frame.bind("<B1-Motion>", self._drag_move)
        self.label.bind("<ButtonPress-1>", self._drag_start)
        self.label.bind("<B1-Motion>", self._drag_move)
        self._drag_x = self._drag_y = 0

        # Raccourci global. pynput passe par X11 : pas de lecture de /dev/input,
        # donc pas d'exigence de root — contrairement à `keyboard`, qui faisait
        # échouer le service utilisateur sur ImportError au démarrage.
        # Le callback arrive depuis un thread d'écoute ; Tk n'est pas thread-safe,
        # on repasse donc par after(0, …) pour exécuter toggle dans sa boucle.
        combi = "+".join(
            f"<{p}>" if p in ("ctrl", "alt", "shift", "cmd") else p
            for p in args.hotkey.lower().split("+")
        )
        self._ecoute = pk.GlobalHotKeys(
            {combi: lambda: self.root.after(0, self.toggle)}
        )
        self._ecoute.daemon = True
        self._ecoute.start()

        self.set_state("idle")

    def _drag_start(self, e):
        self._drag_x, self._drag_y = e.x_root, e.y_root

    def _drag_move(self, e):
        dx = e.x_root - self._drag_x
        dy = e.y_root - self._drag_y
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")
        self._drag_x, self._drag_y = e.x_root, e.y_root

    def set_state(self, mode, text=""):
        bg, fg, default_text = self.COLORS.get(mode, self.COLORS["idle"])
        display = text or default_text
        self.root.configure(bg=bg)
        self.frame.configure(bg=bg)
        self.btn.configure(bg=bg, fg=fg, activebackground=bg)
        self.label.configure(bg=bg, fg=fg, text=display)
        self.close_btn.configure(bg=bg)
        # Icone mic
        if mode == "recording":
            self._pulse_task()

    def _pulse_task(self):
        if state["mode"] != "recording":
            return
        cur = self.btn.cget("fg")
        next_col = "#ff4444" if cur == "#0a0e14" else "#0a0e14"
        self.btn.configure(fg=next_col)
        self.root.after(500, self._pulse_task)

    def toggle(self):
        if state["mode"] == "idle":
            self.start_recording()
        elif state["mode"] == "recording":
            self.stop_recording()

    def start_recording(self):
        global audio_buffer, record_thread
        state["mode"] = "recording"
        audio_buffer = []
        stop_event.clear()
        self.root.after(0, lambda: self.set_state("recording"))
        record_thread = threading.Thread(target=_record_loop, daemon=True)
        record_thread.start()

    def stop_recording(self):
        state["mode"] = "processing"
        stop_event.set()
        self.root.after(0, lambda: self.set_state("processing"))
        threading.Thread(target=self._transcribe, daemon=True).start()

    def _transcribe(self):
        try:
            # Assembler le buffer audio
            audio = (
                np.concatenate(audio_buffer, axis=0)
                if audio_buffer
                else np.zeros((100,), dtype=np.float32)
            )
            audio_int16 = (audio * 32767).astype(np.int16)

            # Écrire WAV en mémoire
            buf = io.BytesIO()
            with wave.open(buf, "wb") as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(audio_int16.tobytes())
            buf.seek(0)

            # Appel API Whisper JARVIS
            params = {"language": args.lang} if args.lang != "auto" else {}
            resp = requests.post(
                WHISPER_URL,
                files={"file": ("audio.wav", buf, "audio/wav")},
                data=params,
                timeout=60,
            )
            resp.raise_for_status()
            text = resp.json().get("text", "").strip()

            if not text:
                self._done("", error="Silence ou erreur")
                return

            # Traduction optionnelle
            if args.translate and text:
                try:
                    result = subprocess.run(
                        ["bash", TRANSLATE_CMD, f"Traduis en français: {text}"],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    text = result.stdout.strip() or text
                except Exception:
                    pass

            # Clipboard
            pyperclip.copy(text)

            # Sauvegarde fichier
            if args.save:
                save_dir = Path(args.save).expanduser()
                save_dir.mkdir(parents=True, exist_ok=True)
                ts = time.strftime("%Y%m%d_%H%M%S")
                (save_dir / f"voice_{ts}.txt").write_text(text + "\n", encoding="utf-8")

            self._done(text)

        except Exception as exc:
            self._done("", error=str(exc)[:60])

    def _done(self, text, error=""):
        state["mode"] = "idle"
        if error:
            self.root.after(0, lambda: self.set_state("error", f"✗  {error}"))
            self.root.after(3000, lambda: self.set_state("idle"))
        else:
            short = text[:35] + "…" if len(text) > 35 else text
            self.root.after(0, lambda: self.set_state("done", f"✓  {short}"))
            self.root.after(3000, lambda: self.set_state("idle"))

    def run(self):
        self.root.mainloop()


# ── Boucle d'enregistrement ───────────────────────────────────────────────────


def _record_loop():
    import sounddevice as sd

    def callback(indata, frames, time_info, status):
        if not stop_event.is_set():
            audio_buffer.append(indata.copy().flatten())

    with sd.InputStream(
        samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="float32", callback=callback
    ):
        stop_event.wait()


# ── Lancement ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"JARVIS Voice Widget — {args.hotkey.upper()} pour enregistrer")
    print(f"API Whisper : {WHISPER_URL}")
    if args.save:
        print(f"Sauvegarde  : {args.save}")
    app = VoiceWidget()
    app.run()
