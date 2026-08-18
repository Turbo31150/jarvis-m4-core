#!/usr/bin/env python3
"""BDQT HTTP microservice — expose la qualité-transcription à n8n (et autres).

Bind 127.0.0.1:8790 par défaut (localhost). /rebuild exige un token Bearer.
Endpoints :
  GET  /health                      -> {"status":"ok", ...stats}
  POST /correct  {text, context?}   -> {"corrected": "...", "rules": [...]}
  POST /rebuild  {enrich?:bool, restart?:bool}
                                    -> relance bdqt_rebuild.sh (boucle apprentissage)
                                       + restart optionnel du serveur Whisper
Non-régression : si bdqt_core/la base manquent, /correct renvoie le texte inchangé.
"""

import hmac
import json
import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(__file__))
import bdqt_core as core  # noqa: E402

# Sécurité : bind localhost par défaut (l'endpoint /rebuild exécute un script + un
# restart de service → ne JAMAIS l'exposer sans auth). Pour l'accès depuis des
# conteneurs docker, mettre BDQT_HTTP_HOST=172.17.0.1 ET configurer un token.
HOST = os.environ.get("BDQT_HTTP_HOST", "127.0.0.1")
PORT = int(os.environ.get("BDQT_HTTP_PORT", "8790"))
HERE = os.path.dirname(os.path.abspath(__file__))

# Token partagé requis pour les actions sensibles (/rebuild). Fail-closed :
# sans token configuré, /rebuild est désactivé. Source : env ou ~/.config/bdqt/token.
_TOKEN_FILE = os.path.expanduser("~/.config/bdqt/token")


def _load_token():
    tok = os.environ.get("BDQT_HTTP_TOKEN", "").strip()
    if tok:
        return tok
    try:
        return open(_TOKEN_FILE, encoding="utf-8").read().strip()
    except OSError:
        return ""


AUTH_TOKEN = _load_token()


def _stats():
    try:
        c = core.get_conn()
        s = {
            t: c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            for t in ("lexicon", "corrections", "prompt_snippets", "transcription_log")
        }
        c.close()
        return s
    except Exception:
        return {}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _authorized(self):
        if not AUTH_TOKEN:
            return False  # fail-closed : pas de token configuré → action interdite
        hdr = self.headers.get("Authorization", "")
        prefix = "Bearer "
        provided = hdr[len(prefix) :] if hdr.startswith(prefix) else ""
        return bool(provided) and hmac.compare_digest(provided, AUTH_TOKEN)

    def _send(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path.startswith("/health"):
            self._send(
                200,
                {"status": "ok", "db": os.path.exists(core.DB_PATH), "stats": _stats()},
            )
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            body = {}
        if self.path.startswith("/correct"):
            text = body.get("text", "")
            ctx = body.get("context", "general")
            out, rules = core.correct(text, context=ctx)
            self._send(200, {"corrected": out, "rules": rules, "n": len(rules)})
        elif self.path.startswith("/rebuild"):
            if not self._authorized():
                self._send(
                    401,
                    {
                        "error": "unauthorized",
                        "hint": "Bearer token requis (BDQT_HTTP_TOKEN ou ~/.config/bdqt/token)",
                    },
                )
                return
            args = ["bash", os.path.join(HERE, "bdqt_rebuild.sh")]
            if body.get("enrich") is True:
                args.append("--enrich")
            try:
                r = subprocess.run(args, capture_output=True, text=True, timeout=600)
                restarted = False
                if body.get("restart") is True:
                    subprocess.run(
                        ["systemctl", "--user", "restart", "jarvis-whisper"],
                        timeout=60,
                        capture_output=True,
                    )
                    restarted = True
                self._send(
                    200,
                    {
                        "ok": r.returncode == 0,
                        "restarted": restarted,
                        "log": r.stdout[-1500:],
                        "stats": _stats(),
                    },
                )
            except Exception as e:
                self._send(500, {"ok": False, "error": str(e)})
        else:
            self._send(404, {"error": "not found"})


if __name__ == "__main__":
    core.ensure_schema()
    print(f"[bdqt-http] écoute sur {HOST}:{PORT} | db={core.DB_PATH}", flush=True)
    ThreadingHTTPServer((HOST, PORT), H).serve_forever()
