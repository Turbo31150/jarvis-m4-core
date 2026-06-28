#!/usr/bin/env python3
"""
JARVIS Voice Widget M4 — v2.0
Alt+X (maintenu) → enregistre → relâché → Whisper → colle au curseur

Options panel (bouton …) :
  • Langue (fr / en / auto / es / de / ar / zh / pt / ja)
  • Mode Sous-titres YouTube  → ~/jarvis/subtitles/live.srt  (OBS)
  • Auto-sauvegarde fichier
  • Traduction → français via lm-ask.sh
  • Coller automatiquement (on/off)
  • Compiler session (Qwen)
  • Export + Vider

Session log + compilation Qwen (LM Studio qwen3.5-9b → fallback Ollama qwen3:1.7b)
"""

import base64
import json
import os
import re
import signal
import subprocess
import tempfile
import threading
import tkinter as tk
from datetime import datetime
from http.client import HTTPConnection
from pathlib import Path

# pynput ne fonctionne que sous X11 ; sous Wayland on utilise SIGUSR1 (raccourci GNOME).
try:
    from pynput import keyboard

    HAS_PYNPUT = True
except Exception:
    keyboard = None
    HAS_PYNPUT = False


# ── Config ────────────────────────────────────────────────────────────────────
WHISPER_HOST = "127.0.0.1"
WHISPER_PORT = 8789
LMS_URL = "http://127.0.0.1:1234"
LMS_MODEL = "qwen/qwen3.5-9b"
OLLAMA_URL = "http://127.0.0.1:11434"
QWEN_MODEL = "qwen3:1.7b"
AUDIO_DEVICE = "plughw:1,0"  # ALC256 ASUS TUF M4
TRANSLATE_CMD = os.path.expanduser("~/jarvis/scripts/lm-ask.sh")

LOG_DIR = Path.home() / "jarvis" / "voice_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
SUBTITLE_DIR = Path.home() / "jarvis" / "subtitles"
SUBTITLE_DIR.mkdir(parents=True, exist_ok=True)
SESSION_FILE = LOG_DIR / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

LANGUAGES = ["fr", "en", "auto", "es", "de", "ar", "zh", "pt", "ja", "it"]

# ── État global ───────────────────────────────────────────────────────────────
_recording = False
_arecord_proc = None
_wav_path = None
_session_log = []
_widget = None
_subtitle_index = 0
_target_window = None  # Fenêtre active capturée au moment Alt+X (press)

# ── Paramètres modifiables depuis l'UI ───────────────────────────────────────
_settings = {
    "language": "fr",
    "auto_paste": True,
    "paste_shortcut": "ctrl+v",  # ou "ctrl+shift+v" pour les terminaux
    "translate": False,  # déprécié — remplacé par translate_to
    "translate_to": "",  # "" = aucune · "en" = anglais · "fr" = français
    "dictionary": True,  # corrections personnalisées via voice_dict.json
    "polish": False,  # correction qualité courrier (LLM) pour député/pétitions
    "subtitles": False,
    "auto_save": False,
    "save_dir": str(Path.home() / "Documents" / "transcriptions"),
}


# ── Whisper client ────────────────────────────────────────────────────────────
_NOISE_PROF = os.path.expanduser("~/jarvis/scripts/fan_noise.prof")


def _denoise(wav_path: str) -> str:
    """Débruite le wav (souffle ventilo F15) avant Whisper. sox noisered + passe-haut voix.
    Retourne le chemin nettoyé, ou l'original si sox/profil indisponible."""
    if not os.path.exists(_NOISE_PROF):
        return wav_path
    out = wav_path + ".denoised.wav"
    try:
        # highpass 120Hz (coupe le rumble ventilo) + noisered (profil souffle) + normalisation douce
        r = subprocess.run(
            [
                "sox",
                wav_path,
                out,
                "highpass",
                "120",
                "noisered",
                _NOISE_PROF,
                "0.25",
                "norm",
                "-1",
            ],
            capture_output=True,
            timeout=15,
        )
        return out if (r.returncode == 0 and os.path.exists(out)) else wav_path
    except Exception:
        return wav_path


# ── Personnalisation : dictionnaire + qualité courrier + traduction ───────────
DICT_FILE = Path.home() / "jarvis" / "voice_dict.json"
_dict_cache = {"mtime": -1.0, "rules": []}


def apply_dictionary(text: str) -> str:
    """Corrige/personnalise la transcription via ~/jarvis/voice_dict.json.

    Le fichier est rechargé automatiquement à chaque modification (édition à chaud).
    Clés = ce que Whisper écrit, valeurs = correction. Insensible à la casse, mot
    ou expression entière. Les expressions les plus longues sont appliquées d'abord.
    """
    if not text:
        return text
    try:
        mtime = DICT_FILE.stat().st_mtime
        if mtime != _dict_cache["mtime"]:
            data = json.loads(DICT_FILE.read_text(encoding="utf-8"))
            reps = data.get("replacements", {})
            ordered = sorted(reps.items(), key=lambda kv: -len(kv[0]))
            _dict_cache["rules"] = [
                (re.compile(rf"(?<!\w){re.escape(k)}(?!\w)", re.IGNORECASE), v)
                for k, v in ordered
            ]
            _dict_cache["mtime"] = mtime
    except FileNotFoundError:
        return text
    except Exception:
        return text
    for rx, repl in _dict_cache["rules"]:
        text = rx.sub(repl, text)
    return text


def _llm_chat(system: str, user: str, max_tokens: int = 600) -> str:
    """Chat LLM local : LM Studio (qwen3.5-9b) → fallback Ollama (CPU). '' si échec."""
    try:
        payload = json.dumps(
            {
                "model": LMS_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "stream": False,
                "max_tokens": max_tokens,
                "temperature": 0.2,
                "enable_thinking": False,
            }
        ).encode()
        conn = HTTPConnection("127.0.0.1", 1234, timeout=90)
        conn.request(
            "POST",
            "/v1/chat/completions",
            payload,
            {"Content-Type": "application/json"},
        )
        data = json.loads(conn.getresponse().read())
        msg = data["choices"][0]["message"]
        out = (msg.get("content") or msg.get("reasoning_content", "")).strip()
        if out:
            return out
    except Exception:
        pass
    # Fallback Ollama — CPU forcé (whisper-server sature la VRAM 4 Go du RTX 3050).
    try:
        payload = json.dumps(
            {
                "model": QWEN_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "stream": False,
                "think": False,
                "options": {
                    "num_predict": max_tokens,
                    "num_gpu": 0,
                    "temperature": 0.2,
                },
            }
        ).encode()
        conn = HTTPConnection("127.0.0.1", 11434, timeout=120)
        conn.request("POST", "/api/chat", payload, {"Content-Type": "application/json"})
        data = json.loads(conn.getresponse().read())
        return data["message"]["content"].strip()
    except Exception:
        return ""


def polish_text(text: str) -> str:
    """Qualité courrier : corrige orthographe/grammaire/ponctuation/style, même langue."""
    if not text:
        return text
    out = _llm_chat(
        "Tu es correcteur professionnel. Corrige l'orthographe, la grammaire, la "
        "ponctuation et la mise en forme du texte dicté pour un courrier formel "
        "(destiné à un député ou une pétition). GARDE strictement la langue d'origine "
        "et le sens exact. N'ajoute aucun commentaire ni explication : renvoie "
        "UNIQUEMENT le texte corrigé.",
        text,
        max_tokens=900,
    )
    return out or text


_LANG_NAMES = {"en": "anglais", "fr": "français", "es": "espagnol", "de": "allemand"}


def translate_text(text: str, target: str) -> str:
    """Traduit vers la langue cible (registre soutenu, qualité courrier officiel)."""
    if not text or not target:
        return text
    name = _LANG_NAMES.get(target, target)
    out = _llm_chat(
        f"Tu es traducteur professionnel. Traduis fidèlement le texte ci-dessous en "
        f"{name}, dans un registre soutenu adapté à un courrier officiel. Renvoie "
        f"UNIQUEMENT la traduction, sans commentaire.",
        text,
        max_tokens=1000,
    )
    return out or text


def transcribe(wav_path: str) -> str:
    # Débruitage désactivé : la réduction de gain suffit, sox noisered détruisait la voix.
    # Réactivable si besoin via _denoise(wav_path).
    try:
        with open(wav_path, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return "[ERR: fichier audio absent]"

    lang = _settings["language"]
    payload = json.dumps(
        {"audio": audio_b64, "format": "wav", "language": lang}
    ).encode()
    try:
        conn = HTTPConnection(WHISPER_HOST, WHISPER_PORT, timeout=30)
        conn.request("POST", "/", payload, {"Content-Type": "application/json"})
        data = json.loads(conn.getresponse().read())
        text = data.get("text", "").strip()
    except Exception as e:
        return f"[ERR: {e}]"

    # Pipeline de personnalisation (du moins cher au plus cher) :
    # 1) Dictionnaire perso : corrections instantanées (vocabulaire, noms, sigles).
    if _settings.get("dictionary", True):
        text = apply_dictionary(text)
    # 2) Qualité courrier : correction orthographe/style via LLM (député/pétitions).
    if _settings.get("polish") and text:
        text = polish_text(text)
    # 3) Traduction vers langue cible (ex. dicter en FR → texte EN).
    target = _settings.get("translate_to", "")
    if target and target != lang and text:
        text = translate_text(text, target)

    return text


# ── Qwen compile ──────────────────────────────────────────────────────────────
def compile_with_qwen(entries: list) -> str:
    if not entries:
        return ""
    text_block = "\n".join(f"[{e['ts'][11:16]}] {e['text']}" for e in entries)
    prompt = (
        f"Session vocale ({len(entries)} entrées). "
        f"Résumé structuré bullet points par thème:\n\n{text_block}"
    )
    # LM Studio qwen3.5-9b
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
        return (msg.get("content") or msg.get("reasoning_content", "")).strip()
    except Exception:
        pass
    # Fallback Ollama qwen3:1.7b
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
                # num_gpu:0 → CPU forcé : whisper-server sature la VRAM 4 Go du RTX 3050,
                # le fallback Ollama planterait en cudaMalloc OOM sinon.
                "options": {"num_predict": 400, "num_gpu": 0},
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
    # Blindage : tuer tout arecord orphelin qui tiendrait encore le micro
    # (sinon "device occupé" → fichier audio absent). Évite le mic verrouillé.
    try:
        subprocess.run(["pkill", "-9", "-x", "arecord"], timeout=3)
    except Exception:
        pass
    _wav_path = tempfile.mktemp(suffix=".wav")
    _arecord_proc = subprocess.Popen(
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
            _wav_path,
        ],
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


# ── Paste / clipboard ─────────────────────────────────────────────────────────
def paste_text(text: str):
    if not text or text.startswith("[ERR"):
        return
    import time

    wayland = os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"

    # Copier dans le presse-papier (toujours, pour Ctrl+V manuel)
    if wayland:
        try:
            subprocess.run(
                ["wl-copy"], input=text.encode(), stderr=subprocess.DEVNULL, check=True
            )
        except Exception:
            pass
    else:
        try:
            subprocess.run(
                ["xclip", "-selection", "clipboard"],
                input=text.encode(),
                stderr=subprocess.DEVNULL,
                check=True,
            )
        except Exception:
            try:
                subprocess.run(
                    ["xsel", "--clipboard", "--input"],
                    input=text.encode(),
                    stderr=subprocess.DEVNULL,
                )
            except Exception:
                pass

    if _settings["auto_paste"]:
        # Attendre que Alt+X soit complètement relâché (évite les modifiers résiduels)
        time.sleep(0.25)
        if wayland:
            # GNOME/Mutter : `wtype` NE marche PAS (pas de virtual-keyboard protocol),
            # et `ydotool type` envoie des keycodes US → mélange les lettres sur AZERTY.
            # Méthode FIABLE = coller le presse-papier (déjà rempli par wl-copy plus haut),
            # indépendant du layout. Raccourci selon la cible : Ctrl+V (défaut, champs/
            # navigateur/electron) ou Ctrl+Shift+V (terminaux).
            shortcut = _settings.get("paste_shortcut", "ctrl+v")
            if shortcut == "ctrl+shift+v":
                keys = ["29:1", "42:1", "47:1", "47:0", "42:0", "29:0"]  # Ctrl+Shift+V
            else:
                keys = ["29:1", "47:1", "47:0", "29:0"]  # Ctrl+V
            pasted = False
            try:
                pasted = (
                    subprocess.run(
                        ["ydotool", "key", *keys], stderr=subprocess.DEVNULL
                    ).returncode
                    == 0
                )
            except FileNotFoundError:
                pass
            if not pasted:
                # Dernier recours : frappe directe (peut mélanger sur AZERTY)
                try:
                    subprocess.run(["ydotool", "type", text], stderr=subprocess.DEVNULL)
                except FileNotFoundError:
                    pass
        else:
            # X11 : cibler la fenêtre capturée au moment de la touche Alt+X
            cmd = ["xdotool", "type", "--clearmodifiers", "--delay", "20"]
            if _target_window:
                cmd += ["--window", _target_window]
            cmd.append(text)
            subprocess.run(cmd, stderr=subprocess.DEVNULL)


# ── Sous-titres YouTube / OBS ─────────────────────────────────────────────────
def write_subtitle(text: str):
    """Écrit un bloc SRT dans ~/jarvis/subtitles/live.srt pour OBS."""
    global _subtitle_index
    _subtitle_index += 1
    now = datetime.now()
    ts_start = now.strftime("00:%M:%S,000")
    ts_end = now.strftime(f"00:%M:%S,{min(len(text) * 80, 5000):03d}")

    srt_line = f"{_subtitle_index}\n{ts_start} --> {ts_end}\n{text}\n\n"

    srt_path = SUBTITLE_DIR / "live.srt"
    with open(srt_path, "a", encoding="utf-8") as f:
        f.write(srt_line)

    # Aussi écrire dans live.txt (format simple pour OBS Text source)
    txt_path = SUBTITLE_DIR / "live.txt"
    txt_path.write_text(text, encoding="utf-8")


# ── Auto-sauvegarde ───────────────────────────────────────────────────────────
def auto_save(text: str):
    save_dir = Path(_settings["save_dir"]).expanduser()
    save_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    (save_dir / f"voice_{ts}.txt").write_text(text + "\n", encoding="utf-8")


# ── Session export ────────────────────────────────────────────────────────────
def save_session():
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(_session_log, f, ensure_ascii=False, indent=2)
    txt_path = SESSION_FILE.with_suffix(".txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        for e in _session_log:
            f.write(f"[{e['ts'][11:19]}] {e['text']}\n")
    return str(txt_path)


# ── Palette ───────────────────────────────────────────────────────────────────
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
    "yellow": "#f0c040",
}


# ── Widget ────────────────────────────────────────────────────────────────────
class VoiceWidget:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.expanded = False
        self._dx = self._dy = 0
        self._pulse_on = False

        root.title("JARVIS Voice")
        root.wm_attributes("-topmost", True)
        root.wm_attributes("-alpha", 0.92)
        root.overrideredirect(True)
        root.configure(bg=PALETTE["border"])

        self._build()
        root.geometry("260x76+60+60")

    # ── Construction UI ───────────────────────────────────────────────────────
    def _build(self):
        self.outer = tk.Frame(self.root, bg=PALETTE["border"], padx=1, pady=1)
        self.outer.pack(fill=tk.BOTH, expand=True)

        self.main = tk.Frame(self.outer, bg=PALETTE["bg"], padx=8, pady=5)
        self.main.pack(fill=tk.BOTH, expand=True)

        # — Barre de titre —
        bar = tk.Frame(self.main, bg=PALETTE["bg"])
        bar.pack(fill=tk.X)
        bar.bind("<ButtonPress-1>", self._drag_start)
        bar.bind("<B1-Motion>", self._drag_motion)

        self.dot = tk.Label(
            bar,
            text="⬡",
            font=("monospace", 11),
            fg=PALETTE["green"],
            bg=PALETTE["bg"],
            cursor="hand2",
        )
        self.dot.pack(side=tk.LEFT)
        self.dot.bind("<Button-1>", self._toggle_record_click)

        tk.Label(
            bar,
            text=" JARVIS Voice M4",
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

        # — Statut —
        self.status_var = tk.StringVar(value="Alt+X (maintenu) → parler")
        self.status_lbl = tk.Label(
            self.main,
            textvariable=self.status_var,
            font=("monospace", 8),
            fg=PALETTE["muted"],
            bg=PALETTE["bg"],
            anchor="w",
        )
        self.status_lbl.pack(fill=tk.X, pady=(3, 0))

        # — Dernier texte —
        self.text_var = tk.StringVar(value="")
        tk.Label(
            self.main,
            textvariable=self.text_var,
            font=("monospace", 8),
            fg=PALETTE["text"],
            bg=PALETTE["bg"],
            anchor="w",
            wraplength=240,
        ).pack(fill=tk.X)

        # ── Panel étendu (options + session) ──────────────────────────────────
        self.panel = tk.Frame(self.main, bg=PALETTE["surf"], padx=6, pady=6)

        # — Section LANGUE —
        lang_row = tk.Frame(self.panel, bg=PALETTE["surf"])
        lang_row.pack(fill=tk.X, pady=(0, 4))
        tk.Label(
            lang_row,
            text="🌐 Langue :",
            font=("monospace", 8),
            fg=PALETTE["muted"],
            bg=PALETTE["surf"],
        ).pack(side=tk.LEFT)
        self._lang_var = tk.StringVar(value=_settings["language"])
        lang_menu = tk.OptionMenu(
            lang_row, self._lang_var, *LANGUAGES, command=self._on_lang_change
        )
        lang_menu.config(
            font=("monospace", 8),
            bg=PALETTE["border"],
            fg=PALETTE["text"],
            activebackground=PALETTE["surf"],
            highlightthickness=0,
            bd=0,
            width=4,
        )
        lang_menu["menu"].config(
            font=("monospace", 8), bg=PALETTE["border"], fg=PALETTE["text"]
        )
        lang_menu.pack(side=tk.LEFT, padx=(4, 0))

        # — Section TOGGLES —
        toggles = tk.Frame(self.panel, bg=PALETTE["surf"])
        toggles.pack(fill=tk.X, pady=(0, 4))

        self._paste_var = tk.BooleanVar(value=_settings["auto_paste"])
        self._dict_var = tk.BooleanVar(value=_settings.get("dictionary", True))
        self._polish_var = tk.BooleanVar(value=_settings.get("polish", False))
        self._translate_var = tk.BooleanVar(value=_settings.get("translate_to") == "fr")
        self._translate_en_var = tk.BooleanVar(
            value=_settings.get("translate_to") == "en"
        )
        self._subtitle_var = tk.BooleanVar(value=_settings["subtitles"])
        self._save_var = tk.BooleanVar(value=_settings["auto_save"])

        checks = [
            ("⌨  Coller auto", self._paste_var, self._on_paste_toggle),
            ("📖  Dictionnaire perso", self._dict_var, self._on_dict_toggle),
            ("✍  Qualité courrier (député)", self._polish_var, self._on_polish_toggle),
            ("🔤  Traduire → FR", self._translate_var, self._on_translate_toggle),
            ("🇬🇧  Traduire → EN", self._translate_en_var, self._on_translate_en_toggle),
            ("🎬  Sous-titres YouTube", self._subtitle_var, self._on_subtitle_toggle),
            ("💾  Auto-sauvegarder", self._save_var, self._on_save_toggle),
        ]
        for label, var, cmd in checks:
            cb = tk.Checkbutton(
                toggles,
                text=label,
                variable=var,
                command=cmd,
                font=("monospace", 8),
                fg=PALETTE["text"],
                bg=PALETTE["surf"],
                selectcolor=PALETTE["border"],
                activebackground=PALETTE["surf"],
                activeforeground=PALETTE["green"],
                anchor="w",
                pady=1,
            )
            cb.pack(fill=tk.X)

        # — Info sous-titres —
        self.subtitle_info = tk.Label(
            self.panel,
            text=f"  → {SUBTITLE_DIR}/live.txt  (OBS Text source)",
            font=("monospace", 7),
            fg=PALETTE["yellow"],
            bg=PALETTE["surf"],
            anchor="w",
        )

        # — Compteur session —
        sep = tk.Frame(self.panel, bg=PALETTE["border"], height=1)
        sep.pack(fill=tk.X, pady=(4, 4))

        self.count_var = tk.StringVar(value="0 entrée(s) · session")
        tk.Label(
            self.panel,
            textvariable=self.count_var,
            font=("monospace", 8),
            fg=PALETTE["muted"],
            bg=PALETTE["surf"],
            anchor="w",
        ).pack(fill=tk.X)

        # — Boutons session —
        btn_row = tk.Frame(self.panel, bg=PALETTE["surf"])
        btn_row.pack(fill=tk.X, pady=(3, 0))
        for txt, cmd in [
            ("Compiler (Qwen)", self._compile),
            ("Exporter", self._export),
            ("Vider", self._clear),
        ]:
            tk.Button(
                btn_row,
                text=txt,
                font=("monospace", 8),
                fg=PALETTE["text"],
                bg=PALETTE["border"],
                bd=0,
                activebackground=PALETTE["surf"],
                command=cmd,
            ).pack(side=tk.LEFT, padx=(0, 4))

        # — Résultat compile —
        self.compile_var = tk.StringVar(value="")
        tk.Label(
            self.panel,
            textvariable=self.compile_var,
            font=("monospace", 7),
            fg=PALETTE["green"],
            bg=PALETTE["surf"],
            anchor="w",
            wraplength=230,
            justify=tk.LEFT,
        ).pack(fill=tk.X, pady=(3, 0))

    # ── Callbacks options ─────────────────────────────────────────────────────
    def _on_lang_change(self, val):
        _settings["language"] = val
        self.status_var.set(f"Langue : {val}  · Alt+X → parler")

    def _on_paste_toggle(self):
        _settings["auto_paste"] = self._paste_var.get()

    def _on_dict_toggle(self):
        _settings["dictionary"] = self._dict_var.get()

    def _on_polish_toggle(self):
        _settings["polish"] = self._polish_var.get()
        if _settings["polish"]:
            self.status_var.set("Qualité courrier ON · Alt+X → parler")

    def _on_translate_toggle(self):
        # FR et EN mutuellement exclusifs.
        on = self._translate_var.get()
        _settings["translate_to"] = "fr" if on else ""
        if on:
            self._translate_en_var.set(False)
        self.status_var.set(
            ("Traduction → FR" if on else "Traduction OFF") + " · Alt+X"
        )

    def _on_translate_en_toggle(self):
        on = self._translate_en_var.get()
        _settings["translate_to"] = "en" if on else ""
        if on:
            self._translate_var.set(False)
        self.status_var.set(
            ("Traduction → EN" if on else "Traduction OFF") + " · Alt+X"
        )

    def _on_subtitle_toggle(self):
        _settings["subtitles"] = self._subtitle_var.get()
        if _settings["subtitles"]:
            # Réinitialiser le fichier SRT
            (SUBTITLE_DIR / "live.srt").write_text("", encoding="utf-8")
            (SUBTITLE_DIR / "live.txt").write_text("", encoding="utf-8")
            self.subtitle_info.pack(
                fill=tk.X,
                after=self.subtitle_info.master.winfo_children()[0]
                if self.subtitle_info.master.winfo_children()
                else None,
            )
            self.subtitle_info.pack(fill=tk.X)
        else:
            self.subtitle_info.pack_forget()

    def _on_save_toggle(self):
        _settings["auto_save"] = self._save_var.get()

    # ── Clic sur le ⬡ pour toggle record ─────────────────────────────────────
    def _toggle_record_click(self, _event=None):
        global _recording
        if not _recording:
            _recording = True
            self.set_state("recording")
            start_recording()
        else:
            _recording = False
            stop_recording()
            threading.Thread(target=_on_recording_done, daemon=True).start()

    # ── États visuels ─────────────────────────────────────────────────────────
    def set_state(self, s: str, text: str = ""):
        colors = {
            "idle": (PALETTE["bg"], PALETTE["muted"], "Alt+X (maintenu) → parler"),
            "recording": (
                PALETTE["record"],
                "#fff",
                "● Enregistrement…  (relâcher Alt+X)",
            ),
            "processing": (PALETTE["process"], PALETTE["blue"], "⟳ Transcription…"),
            "success": (PALETTE["ok"], PALETTE["green"], "✓ Collé"),
            "error": (PALETTE["bg"], PALETTE["red"], "✗ Erreur"),
        }
        bg, fg, label = colors.get(s, colors["idle"])
        self.main.config(bg=bg)
        for w in self.main.winfo_children():
            try:
                w.config(bg=bg)
            except Exception:
                pass
        self.dot.config(fg=PALETTE["green"] if s == "idle" else fg)
        self.status_var.set(label)
        self.status_lbl.config(fg=fg)
        if text:
            self.text_var.set(text[:58] + ("…" if len(text) > 58 else ""))
        self.root.update_idletasks()

        if s == "recording":
            self._start_pulse()
        else:
            self._stop_pulse()

    # ── Pulse animation ───────────────────────────────────────────────────────
    def _start_pulse(self):
        self._pulse_on = True
        self._pulse()

    def _stop_pulse(self):
        self._pulse_on = False
        self.dot.config(fg=PALETTE["green"])

    def _pulse(self):
        if not self._pulse_on:
            return
        cur = self.dot.cget("fg")
        self.dot.config(fg="#ff4444" if cur != "#ff4444" else "#ff8888")
        self.root.after(400, self._pulse)

    # ── Session ───────────────────────────────────────────────────────────────
    def add_entry(self, text: str):
        _session_log.append({"ts": datetime.now().isoformat(), "text": text})
        self.count_var.set(f"{len(_session_log)} entrée(s) · session")

    def _toggle_expand(self):
        self.expanded = not self.expanded
        if self.expanded:
            self.panel.pack(fill=tk.X, pady=(4, 0))
            self.root.geometry(f"260x290+{self.root.winfo_x()}+{self.root.winfo_y()}")
        else:
            self.panel.pack_forget()
            self.root.geometry(f"260x76+{self.root.winfo_x()}+{self.root.winfo_y()}")

    def _compile(self):
        if not _session_log:
            self.compile_var.set("(session vide)")
            return
        self.compile_var.set("⟳ Qwen en cours…")
        self.root.update_idletasks()

        def _run():
            result = compile_with_qwen(_session_log)
            compile_path = SESSION_FILE.with_suffix(".compile.txt")
            compile_path.write_text(result, encoding="utf-8")
            short = result[:130] + ("…" if len(result) > 130 else "")
            self.root.after(0, lambda: self.compile_var.set(short))

        threading.Thread(target=_run, daemon=True).start()

    def _export(self):
        path = save_session()
        self.compile_var.set(f"✓ {path}")

    def _clear(self):
        global _subtitle_index
        _session_log.clear()
        _subtitle_index = 0
        self.count_var.set("0 entrée(s) · session")
        self.text_var.set("")
        self.compile_var.set("")

    # ── Drag ─────────────────────────────────────────────────────────────────
    def _drag_start(self, e):
        self._dx, self._dy = e.x, e.y

    def _drag_motion(self, e):
        x = self.root.winfo_x() + e.x - self._dx
        y = self.root.winfo_y() + e.y - self._dy
        self.root.geometry(f"+{x}+{y}")


# ── Pipeline hotkey ───────────────────────────────────────────────────────────
def _on_recording_done():
    global _wav_path
    # Capture atomique : un double-toggle / appui rapide peut relancer ce handler en
    # parallèle et remettre _wav_path à None entre transcribe() et unlink() → on fige
    # le chemin dans une locale et on libère tout de suite le global.
    wav = _wav_path
    _wav_path = None
    if not wav:
        _widget.root.after(0, lambda: _widget.set_state("idle"))
        return
    _widget.root.after(0, lambda: _widget.set_state("processing"))
    text = transcribe(wav)
    try:
        os.unlink(wav)
    except (FileNotFoundError, TypeError):
        pass

    if text and not text.startswith("[ERR"):
        _widget.root.after(0, lambda: _widget.add_entry(text))

        # Sous-titres YouTube / OBS
        if _settings["subtitles"]:
            threading.Thread(target=write_subtitle, args=(text,), daemon=True).start()

        # Auto-sauvegarde
        if _settings["auto_save"]:
            threading.Thread(target=auto_save, args=(text,), daemon=True).start()

        paste_text(text)
        _widget.root.after(0, lambda: _widget.set_state("success", text))
        _widget.root.after(2500, lambda: _widget.set_state("idle"))
    elif text and text.startswith("[ERR"):
        # Vraie erreur (backend whisper injoignable…) → état error visible.
        _widget.root.after(0, lambda: _widget.set_state("error", text))
        _widget.root.after(3000, lambda: _widget.set_state("idle"))
    else:
        # Transcription vide (silence / pas de parole) → retour idle silencieux,
        # pas d'état "error" trompeur.
        _widget.root.after(0, lambda: _widget.set_state("idle"))


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
            global _target_window
            # Capturer la fenêtre AVANT de démarrer l'enregistrement
            try:
                res = subprocess.run(
                    ["xdotool", "getactivewindow"],
                    capture_output=True,
                    text=True,
                    timeout=0.5,
                )
                _target_window = res.stdout.strip() or None
            except Exception:
                _target_window = None
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
def _toggle_recording():
    """Bascule enregistrement ↔ transcription. Déclenché par SIGUSR1 (raccourci GNOME Alt+X)."""
    global _recording, _target_window
    if not _recording:
        _target_window = None  # Wayland : ydotool écrit dans la fenêtre focalisée
        _recording = True
        _widget.root.after(0, lambda: _widget.set_state("recording"))
        start_recording()
    else:
        _recording = False
        stop_recording()
        threading.Thread(target=_on_recording_done, daemon=True).start()


_sigusr1_pending = False


def main():
    global _widget, _sigusr1_pending
    root = tk.Tk()
    _widget = VoiceWidget(root)

    # SIGUSR1 : toggle déclenché par voice_widget.sh (raccourci GNOME Alt+X / Super+V).
    # tkinter bloque la livraison des signaux pendant la boucle Tk → on NE traite PAS
    # le toggle dans le handler. Le handler pose juste un flag ; un poll périodique
    # (qui garde l'interpréteur réactif) consomme le flag et bascule de façon fiable.
    def _on_sigusr1(*_a):
        global _sigusr1_pending
        _sigusr1_pending = True

    signal.signal(signal.SIGUSR1, _on_sigusr1)

    def _poll_sig():
        global _sigusr1_pending
        if _sigusr1_pending:
            _sigusr1_pending = False
            try:
                _toggle_recording()
            except Exception as e:
                print(f"[voice] toggle err: {e}", flush=True)
        root.after(
            80, _poll_sig
        )  # 80ms : réactif + garde l'interpréteur vivant pour les signaux

    root.after(80, _poll_sig)

    # Trigger UNIQUE = SIGUSR1 (raccourci GNOME Alt+X → voice_widget.sh), fiable sur
    # X11 ET Wayland. On NE démarre PAS le listener pynput : sur X11 il doublait le
    # raccourci GNOME (un appui = start pynput + stop SIGUSR1) → _wav_path None → crash.
    listener = None
    try:
        root.mainloop()
    finally:
        if listener:
            listener.stop()


if __name__ == "__main__":
    main()
