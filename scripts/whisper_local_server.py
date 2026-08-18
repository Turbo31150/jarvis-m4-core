#!/usr/bin/env python3
"""Serveur Whisper STT local pour M4 (autonome, CPU-only, identité pamerys).

Contrat attendu par voice_widget.py :
  POST 127.0.0.1:8789  body JSON {"audio": <base64 wav>, "format":"wav", "language":"fr"}
  → réponse JSON {"text": "..."}

Modèle : faster-whisper (en cache HF offline). Défaut large-v3-turbo, fallback tiny.
Réglable via env JARVIS_WHISPER_MODEL / JARVIS_WHISPER_DEVICE / JARVIS_WHISPER_COMPUTE.
"""

import base64
import json
import os
import sys
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from faster_whisper import WhisperModel

# --- BDQT : qualité transcription (initial_prompt + post-correction) ---------
# Non-régression : si le module/la base manquent, le serveur fonctionne comme avant.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "transcription"))
try:
    import bdqt_core as _bdqt
except Exception as _e:  # pragma: no cover
    _bdqt = None
    print(f"[bdqt] désactivé ({_e})", flush=True)

POSTCORRECT = os.environ.get("BDQT_POSTCORRECT", "1") == "1"
PROMPT_CONTEXT = os.environ.get("BDQT_PROMPT_CONTEXT", "general")


def _load_initial_prompt():
    if not _bdqt or not os.path.exists(_bdqt.DB_PATH):
        return None
    try:
        conn = _bdqt.get_conn()
        row = conn.execute(
            "SELECT text FROM prompt_snippets WHERE context=? AND active=1",
            (PROMPT_CONTEXT,),
        ).fetchone()
        conn.close()
        return row["text"] if row else None
    except Exception:
        return None


INITIAL_PROMPT = _load_initial_prompt()
print(
    f"[bdqt] initial_prompt={'oui' if INITIAL_PROMPT else 'non'} | "
    f"post-correction={'on' if (POSTCORRECT and _bdqt) else 'off'}",
    flush=True,
)

HOST = os.environ.get("JARVIS_WHISPER_HOST", "127.0.0.1")
PORT = int(os.environ.get("JARVIS_WHISPER_PORT", "8789"))
MODEL_NAME = os.environ.get("JARVIS_WHISPER_MODEL", "large-v3-turbo")
DEVICE = os.environ.get("JARVIS_WHISPER_DEVICE", "cpu")
COMPUTE = os.environ.get("JARVIS_WHISPER_COMPUTE", "int8")

print(f"[whisper] chargement modèle {MODEL_NAME} ({DEVICE}/{COMPUTE})…", flush=True)
try:
    model = WhisperModel(MODEL_NAME, device=DEVICE, compute_type=COMPUTE)
except Exception as e:
    print(f"[whisper] échec {MODEL_NAME} ({e}) → fallback tiny", flush=True)
    MODEL_NAME = "tiny"
    model = WhisperModel("tiny", device=DEVICE, compute_type=COMPUTE)
print(f"[whisper] prêt sur {HOST}:{PORT} — modèle {MODEL_NAME}", flush=True)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass  # silencieux

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        # healthcheck
        self._send(200, {"status": "ok", "model": MODEL_NAME})

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length))
            audio_b64 = payload.get("audio", "")
            lang = payload.get("language") or "fr"
            if lang in ("auto", "", None):
                lang = None
            raw = base64.b64decode(audio_b64)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as f:
                f.write(raw)
                f.flush()
                segments, _ = model.transcribe(
                    f.name,
                    language=lang,
                    vad_filter=True,
                    beam_size=1,
                    initial_prompt=INITIAL_PROMPT,
                )
                text = "".join(s.text for s in segments).strip()
            # post-correction BDQT (corrections exactes + phonétique)
            if POSTCORRECT and _bdqt and text:
                try:
                    text, _rules = _bdqt.correct(text, context=PROMPT_CONTEXT)
                except Exception:
                    pass
            self._send(200, {"text": text})
        except Exception as e:
            self._send(500, {"text": "", "error": str(e)})


if __name__ == "__main__":
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
