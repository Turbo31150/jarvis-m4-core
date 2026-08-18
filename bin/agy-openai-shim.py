#!/usr/bin/env python3
"""Passerelle OpenAI -> agy (CLI Antigravity).

agy est un CLI en mode print, pas un serveur. Le board (board.py) parle
OpenAI. Ce shim traduit /v1/chat/completions en `agy -p --model <M>` et
rehabille la sortie au format OpenAI, ce qui permet de brancher le board sur
Gemini / Claude / GPT-OSS sans toucher a board.py.

Ne sert QUE le chat : les embeddings restent sur le noeud M6 (nomic, dim 768),
car agy n'expose pas d'embeddings. Le board separe deja les deux endpoints
(BOARD_CHAT_URL vs BOARD_LMS_URL), ce qui rend ce partage naturel.

Usage : agy-openai-shim.py [port]     (defaut 18801)
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 18801
AGY = shutil.which("agy") or os.path.expanduser("~/.local/bin/agy")
MODELE_DEFAUT = os.environ.get("AGY_DEFAULT_MODEL", "gemini-3.7-flash-medium")
# agy met ~6 s sur une question courte ; une synthese d'arbitre peut etre longue.
TIMEOUT = int(os.environ.get("AGY_TIMEOUT", "300"))

# Modeles connus, utilises seulement pour /v1/models et pour valider une
# demande. Une valeur inconnue retombe sur le defaut plutot que d'echouer :
# le board affecte des modeles par expert et peut nommer un modele LM Studio.
MODELES = [
    "gemini-3.7-flash-high",
    "gemini-3.7-flash-medium",
    "gemini-3.7-flash-low",
    "gemini-3.6-flash-high",
    "gemini-3.6-flash-medium",
    "gemini-3.6-flash-low",
    "gemini-3.5-flash-high",
    "gemini-3.5-flash-medium",
    "gemini-3.5-flash-low",
    "gemini-3.1-pro-high",
    "gemini-3.1-pro-low",
    "claude-sonnet-4-6",
    "claude-opus-4-6-thinking",
    "gpt-oss-120b-medium",
]


def aplatir(messages: list[dict]) -> str:
    """Rend la conversation en un seul prompt textuel.

    agy ne prend qu'un prompt. On prefixe les roles pour ne pas perdre la
    consigne systeme, que le board utilise pour la grille de lecture de chaque
    expert et pour la regle de citation.
    """
    morceaux = []
    for m in messages:
        role = m.get("role", "user")
        contenu = m.get("content", "")
        if isinstance(contenu, list):  # format multipart OpenAI
            contenu = "".join(p.get("text", "") for p in contenu if isinstance(p, dict))
        if not contenu:
            continue
        if role == "system":
            morceaux.append(f"[CONSIGNE]\n{contenu}")
        elif role == "assistant":
            morceaux.append(f"[ASSISTANT]\n{contenu}")
        else:
            morceaux.append(contenu)
    return "\n\n".join(morceaux)


def deshabiller_chatml(prompt: str) -> str:
    """Retire le template ChatML pose par board.py.

    board.py construit `<|im_start|>system ... <|im_start|>user ...
    <|im_start|>assistant\n<think>\n\n</think>` — un habillage destine au
    tokenizer d'un modele local. Envoye tel quel a agy, il pollue le prompt et
    peut etre recopie dans la reponse. On garde le texte, on jette les balises.
    """
    if "<|im_start|>" not in prompt:
        return prompt.strip()
    morceaux = []
    for bloc in prompt.split("<|im_start|>"):
        bloc = bloc.split("<|im_end|>")[0]
        if not bloc.strip():
            continue
        role, _, corps = bloc.partition("\n")
        role, corps = role.strip(), corps.strip()
        # Le bloc 'assistant' final est l'amorce de reponse, vide : a jeter.
        if (
            role == "assistant"
            and not corps.replace("<think>", "").replace("</think>", "").strip()
        ):
            continue
        if not corps:
            continue
        morceaux.append(f"[CONSIGNE]\n{corps}" if role == "system" else corps)
    return "\n\n".join(morceaux).strip()


def appeler_agy(prompt: str, modele: str) -> tuple[str, str | None]:
    """Retourne (texte, erreur). Erreur non nulle = echec a signaler en 502."""
    cmd = [AGY, "-p", prompt, "--model", modele, "--output-format", "text"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return "", f"agy timeout apres {TIMEOUT}s (modele {modele})"
    except OSError as e:
        return "", f"agy introuvable ou non executable : {e}"
    if r.returncode != 0:
        return "", (r.stderr or r.stdout or "agy a echoue").strip()[:500]
    return r.stdout.strip(), None


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):  # silence : le journal utile est celui du board
        pass

    def _json(self, code: int, corps: dict):
        donnees = json.dumps(corps).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(donnees)))
        self.end_headers()
        self.wfile.write(donnees)

    def do_GET(self):
        if self.path.rstrip("/").endswith("/models"):
            self._json(
                200,
                {
                    "object": "list",
                    "data": [
                        {"id": m, "object": "model", "owned_by": "antigravity"}
                        for m in MODELES
                    ],
                },
            )
        else:
            self._json(404, {"error": "route inconnue"})

    def _lire_corps(self) -> dict | None:
        try:
            n = int(self.headers.get("Content-Length", 0))
            return json.loads(self.rfile.read(n) or b"{}")
        except (ValueError, json.JSONDecodeError) as e:
            self._json(400, {"error": f"corps illisible : {e}"})
            return None

    def _completions_legacy(self):
        """Route /v1/completions : champ `prompt`, reponse `text`.

        C'est CETTE route qu'utilise board.py, pas /chat/completions. Son
        prompt arrive deja habille en template ChatML (<|im_start|>...), qu'il
        faut deshabiller : agy attend du texte, pas des balises de tokenizer.
        """
        requete = self._lire_corps()
        if requete is None:
            return
        modele = requete.get("model") or MODELE_DEFAUT
        if modele not in MODELES:
            modele = MODELE_DEFAUT
        prompt = deshabiller_chatml(requete.get("prompt", ""))
        if not prompt:
            self._json(400, {"error": "prompt vide"})
            return
        texte, erreur = appeler_agy(prompt, modele)
        if erreur:
            self._json(502, {"error": erreur})
            return
        self._json(
            200,
            {
                "id": f"agy-{int(time.time() * 1000)}",
                "object": "text_completion",
                "created": int(time.time()),
                "model": modele,
                "choices": [{"index": 0, "text": texte, "finish_reason": "stop"}],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
            },
        )

    def do_POST(self):
        route = self.path.rstrip("/")
        if route.endswith("/completions") and not route.endswith("/chat/completions"):
            self._completions_legacy()
            return
        if not route.endswith("/chat/completions"):
            self._json(
                404,
                {
                    "error": "seul /v1/completions et /v1/chat/completions sont servis (embeddings : voir M6)"
                },
            )
            return
        try:
            n = int(self.headers.get("Content-Length", 0))
            requete = json.loads(self.rfile.read(n) or b"{}")
        except (ValueError, json.JSONDecodeError) as e:
            self._json(400, {"error": f"corps illisible : {e}"})
            return

        modele = requete.get("model") or MODELE_DEFAUT
        if modele not in MODELES:
            modele = MODELE_DEFAUT  # un modele LM Studio demande -> defaut agy
        prompt = aplatir(requete.get("messages", []))
        if not prompt:
            self._json(400, {"error": "aucun message exploitable"})
            return

        texte, erreur = appeler_agy(prompt, modele)
        if erreur:
            self._json(502, {"error": erreur})
            return

        self._json(
            200,
            {
                "id": f"agy-{int(time.time() * 1000)}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": modele,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": texte},
                        "finish_reason": "stop",
                    }
                ],
                # agy ne remonte pas de comptage : valeurs a zero, jamais inventees.
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
            },
        )


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    srv.daemon_threads = True
    print(
        f"shim agy -> OpenAI sur http://127.0.0.1:{PORT}/v1 "
        f"(defaut {MODELE_DEFAUT}, timeout {TIMEOUT}s)",
        flush=True,
    )
    srv.serve_forever()
