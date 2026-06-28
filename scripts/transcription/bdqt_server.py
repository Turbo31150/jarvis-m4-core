#!/usr/bin/env python3
"""BDQT HTTP microservice — expose la qualité-transcription à n8n (et autres).

Bind 0.0.0.0:8790 (joignable depuis les conteneurs docker via 172.17.0.1).
Endpoints :
  GET  /health                      -> {"status":"ok", ...stats}
  POST /correct  {text, context?}   -> {"corrected": "...", "rules": [...]}
  POST /rebuild  {enrich?:bool, restart?:bool}
                                    -> relance bdqt_rebuild.sh (boucle apprentissage)
                                       + restart optionnel du serveur Whisper
Non-régression : si bdqt_core/la base manquent, /correct renvoie le texte inchangé.
"""

import json
import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(__file__))
import bdqt_core as core  # noqa: E402

HOST = os.environ.get("BDQT_HTTP_HOST", "0.0.0.0")
PORT = int(os.environ.get("BDQT_HTTP_PORT", "8790"))
HERE = os.path.dirname(os.path.abspath(__file__))


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
            args = ["bash", os.path.join(HERE, "bdqt_rebuild.sh")]
            if body.get("enrich"):
                args.append("--enrich")
            try:
                r = subprocess.run(args, capture_output=True, text=True, timeout=600)
                restarted = False
                if body.get("restart"):
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
