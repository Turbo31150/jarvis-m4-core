#!/usr/bin/env python3
"""JARVIS Voice Widget
Alt+X (maintenu) → enregistre → relâché → Whisper :8789 → colle au curseur
Session log + compilation Qwen (OL1 qwen3:1.7b) + export Lumen
"""

import base64
import json
import os
import subprocess
import tempfile
import threading
import tkinter as tk
from datetime import datetime
from http.client import HTTPConnection
from pathlib import Path

from pynput import keyboard

# ── Config ────────────────────────────────────────────────────────────────────
WHISPER_HOST = "127.0.0.1"
WHISPER_PORT = 8789
LANGUAGE = "fr"
# LM Studio local (qwen3.5-9b) → fallback Ollama (qwen3:1.7b)
LMS_URL = "http://127.0.0.1:1234"
LMS_MODEL = "qwen/qwen3.5-9b"
OLLAMA_URL = "http://127.0.0.1:11434"
QWEN_MODEL = "qwen3:1.7b"
LOG_DIR = Path.home() / "jarvis" / "voice_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
SESSION_FILE = LOG_DIR / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

# ── Global state ──────────────────────────────────────────────────────────────
_recording = False
_arecord_proc = None
_wav_path = None
_session_log = []
_pressed = set()
_widget = None


# ── Whisper client ────────────────────────────────────────────────────────────
def transcribe(wav_path: str) -> str:
    with open(wav_path, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode()
    payload = json.dumps(
        {"audio": audio_b64, "format": "wav", "language": LANGUAGE}
    ).encode()
    try:
        conn = HTTPConnection(WHISPER_HOST, WHISPER_PORT, timeout=30)
        conn.request("POST", "/", payload, {"Content-Type": "application/json"})
        data = json.loads(conn.getresponse().read())
        return data.get("text", "").strip()
    except Exception as e:
        return f"[ERR: {e}]"


# ── Qwen compile ──────────────────────────────────────────────────────────────
def compile_with_qwen(entries: list) -> str:
    if not entries:
        return ""
    text_block = "\n".join(f"[{e['ts'][11:16]}] {e['text']}" for e in entries)
    prompt = (
        f"Session vocale ({len(entries)} entrées). "
        f"Résumé structuré bullet points par thème:\n\n{text_block}"
    )
    # Essai LM Studio qwen3.5-9b d'abord
    try:
        payload = json.dumps(
            {
                "model": LMS_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "Tu es JARVIS. Résume en français, concis.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "max_tokens": 400,
                "enable_thinking": False,
            }
        ).encode()
        conn = HTTPConnection("127.0.0.1", 1234, timeout=30)
        conn.request(
            "POST",
            "/v1/chat/completions",
            payload,
            {"Content-Type": "application/json"},
        )
        data = json.loads(conn.getresponse().read())
        msg = data["choices"][0]["message"]
        text = msg.get("content") or msg.get("reasoning_content", "")
        return text.strip()
    except Exception:
        pass
    # Fallback Ollama qwen3:1.7b (think=false obligatoire)
    try:
        payload = json.dumps(
            {
                "model": QWEN_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "Tu es JARVIS. Résume en français, concis.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "think": False,
                "options": {"num_predict": 400},
            }
        ).encode()
        conn = HTTPConnection("127.0.0.1", 11434, timeout=60)
        conn.request("POST", "/api/chat", payload, {"Content-Type": "application/json"})
        data = json.loads(conn.getresponse().read())
        return data["message"]["content"].strip()
    except Exception as e:
        return f"[Qwen indisponible: {e}]"


# ── Audio ─────────────────────────────────────────────────────────────────────
def start_recording():
    global _arecord_proc, _wav_path
    _wav_path = tempfile.mktemp(suffix=".wav")
    _arecord_proc = subprocess.Popen(
        ["arecord", "-f", "S16_LE", "-r", "16000", "-c", "1", _wav_path],
        stderr=subprocess.DEVNULL,
    )


def stop_recording():
    global _arecord_proc
    if _arecord_proc:
        _arecord_proc.terminate()
        try:
            _arecord_proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            _arecord_proc.kill()
        _arecord_proc = None


# ── Paste ─────────────────────────────────────────────────────────────────────
def paste_text(text: str):
    if not text or text.startswith("[ERR"):
        return
    import time

    time.sleep(0.12)
    subprocess.run(
        ["xdotool", "type", "--clearmodifiers", "--delay", "20", text],
        stderr=subprocess.DEVNULL,
    )


# ── Session export ────────────────────────────────────────────────────────────
def save_session():
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(_session_log, f, ensure_ascii=False, indent=2)
    # Export texte brut pour Lumen
    txt_path = SESSION_FILE.with_suffix(".txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        for e in _session_log:
            f.write(f"[{e['ts'][11:19]}] {e['text']}\n")
    return str(txt_path)


# ── Widget ────────────────────────────────────────────────────────────────────
PALETTE = {
    "bg": "#0d0e10",
    "surf": "#131519",
    "border": "#2e333d",
    "green": "#00d4aa",
    "red": "#ef4444",
    "blue": "#4a9eff",
    "text": "#e2e4e9",
    "muted": "#7a7f8a",
    "record": "#c0392b",
    "process": "#1a4a7a",
    "ok": "#0a3a2a",
}


class VoiceWidget:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.expanded = False
        self._dx = self._dy = 0

        root.title("JARVIS Voice")
        root.wm_attributes("-topmost", True)
        root.wm_attributes("-alpha", 0.92)
        root.overrideredirect(True)
        root.configure(bg=PALETTE["border"])

        self._build()
        root.geometry("250x72+60+60")

    def _build(self):
        # Outer frame (border effect)
        self.outer = tk.Frame(self.root, bg=PALETTE["border"], padx=1, pady=1)
        self.outer.pack(fill=tk.BOTH, expand=True)

        # Main frame
        self.main = tk.Frame(self.outer, bg=PALETTE["bg"], padx=8, pady=5)
        self.main.pack(fill=tk.BOTH, expand=True)

        # Title bar
        bar = tk.Frame(self.main, bg=PALETTE["bg"])
        bar.pack(fill=tk.X)
        bar.bind("<ButtonPress-1>", self._drag_start)
        bar.bind("<B1-Motion>", self._drag_motion)

        self.dot = tk.Label(
            bar, text="⬡", font=("monospace", 11), fg=PALETTE["green"], bg=PALETTE["bg"]
        )
        self.dot.pack(side=tk.LEFT)

        tk.Label(
            bar,
            text=" JARVIS Voice",
            font=("monospace", 9, "bold"),
            fg=PALETTE["text"],
            bg=PALETTE["bg"],
        ).pack(side=tk.LEFT)

        tk.Button(
            bar,
            text="…",
            font=("monospace", 9),
            fg=PALETTE["muted"],
            bg=PALETTE["bg"],
            bd=0,
            activebackground=PALETTE["surf"],
            activeforeground=PALETTE["text"],
            command=self._toggle_expand,
        ).pack(side=tk.RIGHT, padx=(0, 4))
        tk.Button(
            bar,
            text="×",
            font=("monospace", 10),
            fg=PALETTE["muted"],
            bg=PALETTE["bg"],
            bd=0,
            activebackground=PALETTE["bg"],
            activeforeground=PALETTE["red"],
            command=self.root.destroy,
        ).pack(side=tk.RIGHT)

        # Status row
        self.status_var = tk.StringVar(value="Alt+X → parler")
        self.status_lbl = tk.Label(
            self.main,
            textvariable=self.status_var,
            font=("monospace", 8),
            fg=PALETTE["muted"],
            bg=PALETTE["bg"],
            anchor="w",
        )
        self.status_lbl.pack(fill=tk.X, pady=(3, 0))

        # Last text
        self.text_var = tk.StringVar(value="")
        tk.Label(
            self.main,
            textvariable=self.text_var,
            font=("monospace", 8),
            fg=PALETTE["text"],
            bg=PALETTE["bg"],
            anchor="w",
            wraplength=230,
        ).pack(fill=tk.X)

        # Expand panel (hidden by default)
        self.panel = tk.Frame(self.main, bg=PALETTE["surf"], padx=6, pady=4)

        # Session counter
        self.count_var = tk.StringVar(value="0 entrées")
        tk.Label(
            self.panel,
            textvariable=self.count_var,
            font=("monospace", 8),
            fg=PALETTE["muted"],
            bg=PALETTE["surf"],
            anchor="w",
        ).pack(fill=tk.X)

        btn_frame = tk.Frame(self.panel, bg=PALETTE["surf"])
        btn_frame.pack(fill=tk.X, pady=(3, 0))

        tk.Button(
            btn_frame,
            text="Compiler (Qwen)",
            font=("monospace", 8),
            fg=PALETTE["text"],
            bg=PALETTE["border"],
            bd=0,
            activebackground=PALETTE["surf"],
            command=self._compile,
        ).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(
            btn_frame,
            text="Exporter",
            font=("monospace", 8),
            fg=PALETTE["text"],
            bg=PALETTE["border"],
            bd=0,
            activebackground=PALETTE["surf"],
            command=self._export,
        ).pack(side=tk.LEFT)
        tk.Button(
            btn_frame,
            text="Vider",
            font=("monospace", 8),
            fg=PALETTE["muted"],
            bg=PALETTE["border"],
            bd=0,
            activebackground=PALETTE["surf"],
            command=self._clear,
        ).pack(side=tk.RIGHT)

        # Compile result
        self.compile_var = tk.StringVar(value="")
        tk.Label(
            self.panel,
            textvariable=self.compile_var,
            font=("monospace", 7),
            fg=PALETTE["green"],
            bg=PALETTE["surf"],
            anchor="w",
            wraplength=220,
            justify=tk.LEFT,
        ).pack(fill=tk.X, pady=(3, 0))

    def set_state(self, s: str, text: str = ""):
        colors = {
            "idle": (PALETTE["bg"], PALETTE["muted"], "Alt+X → parler"),
            "recording": (PALETTE["record"], "#fff", "● Enregistrement…"),
            "processing": (PALETTE["process"], PALETTE["blue"], "⟳ Transcription…"),
            "success": (PALETTE["ok"], PALETTE["green"], "✓ Collé"),
            "error": (PALETTE["bg"], PALETTE["red"], "✗ Erreur"),
        }
        bg, fg, label = colors.get(s, colors["idle"])
        self.main.config(bg=bg)
        for w in self.main.winfo_children():
            try:
                w.config(bg=bg)
            except:
                pass
        self.dot.config(fg=PALETTE["green"] if s == "idle" else fg)
        self.status_var.set(label)
        self.status_lbl.config(fg=fg)
        if text:
            self.text_var.set(text[:55] + ("…" if len(text) > 55 else ""))
        self.root.update_idletasks()

    def add_entry(self, text: str):
        _session_log.append({"ts": datetime.now().isoformat(), "text": text})
        self.count_var.set(f"{len(_session_log)} entrée(s)")

    def _toggle_expand(self):
        self.expanded = not self.expanded
        if self.expanded:
            self.panel.pack(fill=tk.X, pady=(4, 0))
            self.root.geometry(f"250x150+{self.root.winfo_x()}+{self.root.winfo_y()}")
        else:
            self.panel.pack_forget()
            self.root.geometry(f"250x72+{self.root.winfo_x()}+{self.root.winfo_y()}")

    def _compile(self):
        if not _session_log:
            self.compile_var.set("(session vide)")
            return
        self.compile_var.set("⟳ Qwen en cours…")
        self.root.update_idletasks()

        def _run():
            result = compile_with_qwen(_session_log)
            # Save compile result alongside session
            compile_path = SESSION_FILE.with_suffix(".compile.txt")
            with open(compile_path, "w", encoding="utf-8") as f:
                f.write(result)
            short = result[:120] + ("…" if len(result) > 120 else "")
            self.root.after(0, lambda: self.compile_var.set(short))

        threading.Thread(target=_run, daemon=True).start()

    def _export(self):
        path = save_session()
        self.compile_var.set(f"✓ {path}")

    def _clear(self):
        _session_log.clear()
        self.count_var.set("0 entrées")
        self.text_var.set("")
        self.compile_var.set("")

    def _drag_start(self, e):
        self._dx, self._dy = e.x, e.y

    def _drag_motion(self, e):
        x = self.root.winfo_x() + e.x - self._dx
        y = self.root.winfo_y() + e.y - self._dy
        self.root.geometry(f"+{x}+{y}")


# ── Hotkey pipeline ───────────────────────────────────────────────────────────
def _on_recording_done():
    global _wav_path
    _widget.root.after(0, lambda: _widget.set_state("processing"))
    text = transcribe(_wav_path)
    try:
        os.unlink(_wav_path)
    except FileNotFoundError:
        pass
    _wav_path = None

    if text and not text.startswith("[ERR"):
        _widget.root.after(0, lambda: _widget.add_entry(text))
        paste_text(text)
        _widget.root.after(0, lambda: _widget.set_state("success", text))
        _widget.root.after(2500, lambda: _widget.set_state("idle"))
    else:
        _widget.root.after(0, lambda: _widget.set_state("error", text))
        _widget.root.after(3000, lambda: _widget.set_state("idle"))


def _make_listener():
    pressed = set()

    def on_press(key):
        global _recording
        pressed.add(key)
        alt = any(
            k in pressed
            for k in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r)
        )
        try:
            x = keyboard.KeyCode.from_char("x") in pressed
        except Exception:
            x = False
        if alt and x and not _recording:
            _recording = True
            _widget.root.after(0, lambda: _widget.set_state("recording"))
            start_recording()

    def on_release(key):
        global _recording
        alt_keys = {keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r}
        try:
            x_key = keyboard.KeyCode.from_char("x")
        except Exception:
            x_key = None
        if (key in alt_keys or key == x_key) and _recording:
            _recording = False
            stop_recording()
            threading.Thread(target=_on_recording_done, daemon=True).start()
        pressed.discard(key)

    return keyboard.Listener(on_press=on_press, on_release=on_release)


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    global _widget
    root = tk.Tk()
    _widget = VoiceWidget(root)
    listener = _make_listener()
    listener.start()
    try:
        root.mainloop()
    finally:
        listener.stop()


if __name__ == "__main__":
    main()
