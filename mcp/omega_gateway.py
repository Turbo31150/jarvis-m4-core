#!/usr/bin/env python3
"""JARVIS OMEGA — MCP Gateway.

Agrège N serveurs MCP stdio derrière UN seul endpoint HTTP (Streamable HTTP).
Les outils sont exposés préfixés par leur serveur d'origine : `board__board_search`.

  python3 omega_gateway.py --port 18810 [--config ~/.mcp.json] [--only board,manus]

Aucune dépendance hors stdlib. Les serveurs enfants sont démarrés à la demande
et gardés chauds ; un enfant mort est relancé au prochain appel, jamais masqué.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PROTOCOL = "2024-11-05"
SEP = "__"  # sépare le nom du serveur du nom de l'outil
TIMEOUT_ENFANT = 300


class Enfant:
    """Un serveur MCP stdio, maintenu chaud, interrogé en JSON-RPC ligne à ligne."""

    def __init__(self, nom: str, spec: dict):
        self.nom = nom
        self.cmd = [spec["command"], *spec.get("args", [])]
        self.env = {**os.environ, **spec.get("env", {})}
        self.proc: subprocess.Popen | None = None
        self.mid = 0
        self.verrou = threading.Lock()
        self.outils: list[dict] = []
        self.erreur: str | None = None

    def _vivant(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def _demarrer(self) -> None:
        self.proc = subprocess.Popen(
            self.cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
            env=self.env,
        )
        self._appel_brut(
            "initialize",
            {
                "protocolVersion": PROTOCOL,
                "capabilities": {},
                "clientInfo": {"name": "jarvis-omega-gateway", "version": "1.0.0"},
            },
        )

    def _appel_brut(self, methode: str, params: dict | None = None):
        assert self.proc and self.proc.stdin and self.proc.stdout
        self.mid += 1
        req = {"jsonrpc": "2.0", "id": self.mid, "method": methode}
        if params is not None:
            req["params"] = params
        self.proc.stdin.write(json.dumps(req) + "\n")
        self.proc.stdin.flush()
        fin = time.time() + TIMEOUT_ENFANT
        while time.time() < fin:
            ligne = self.proc.stdout.readline()
            if not ligne:
                raise RuntimeError(f"{self.nom}: flux fermé (serveur mort)")
            try:
                rep = json.loads(ligne)
            except json.JSONDecodeError:
                continue  # bruit sur stdout : on ignore, on n'échoue pas
            if rep.get("id") == self.mid:
                if "error" in rep:
                    raise RuntimeError(f"{self.nom}: {rep['error'].get('message')}")
                return rep.get("result")
        raise TimeoutError(f"{self.nom}: pas de réponse en {TIMEOUT_ENFANT}s")

    def appel(self, methode: str, params: dict | None = None):
        with self.verrou:
            if not self._vivant():
                self._demarrer()
            try:
                return self._appel_brut(methode, params)
            except (RuntimeError, TimeoutError, BrokenPipeError):
                # Une relance, une seule : si ça retombe, l'erreur remonte telle quelle.
                self._demarrer()
                return self._appel_brut(methode, params)

    def recenser(self) -> list[dict]:
        try:
            res = self.appel("tools/list") or {}
            self.outils = res.get("tools", [])
            self.erreur = None
        except Exception as exc:  # noqa: BLE001
            self.outils = []
            self.erreur = f"{type(exc).__name__}: {exc}"
        return self.outils


class Passerelle:
    def __init__(self, config: Path, only: list[str] | None):
        brut = json.loads(config.read_text())
        serveurs = brut.get("mcpServers", brut)
        self.enfants: dict[str, Enfant] = {}
        for nom, spec in serveurs.items():
            if only and nom not in only:
                continue
            if spec.get("type") in ("sse", "streamableHttp") or "url" in spec:
                continue  # fédération HTTP : hors périmètre de cette version
            court = nom.replace("jarvis-", "").replace("-", "_")
            self.enfants[court] = Enfant(nom, spec)

    def outils(self) -> list[dict]:
        agg = []
        for court, enf in self.enfants.items():
            for o in enf.recenser():
                copie = dict(o)
                copie["name"] = f"{court}{SEP}{o['name']}"
                copie["description"] = f"[{court}] {o.get('description', '')}"
                agg.append(copie)
        return agg

    def appeler(self, nom: str, args: dict):
        if SEP not in nom:
            raise ValueError(f"Nom non qualifié : {nom} (attendu serveur{SEP}outil)")
        court, outil = nom.split(SEP, 1)
        enf = self.enfants.get(court)
        if enf is None:
            raise ValueError(f"Serveur inconnu : {court}")
        return enf.appel("tools/call", {"name": outil, "arguments": args})

    def sante(self) -> dict:
        return {
            "serveurs": {
                c: {
                    "commande": e.cmd[0],
                    "vivant": e._vivant(),
                    "outils": len(e.outils),
                    "erreur": e.erreur,
                }
                for c, e in self.enfants.items()
            }
        }


PASSERELLE: Passerelle | None = None
JETON: str | None = None


class Serveur(ThreadingHTTPServer):
    # Sans ceci, un redémarrage rapide échoue en "Address already in use"
    # tant que la socket précédente est en TIME_WAIT.
    allow_reuse_address = True
    daemon_threads = True


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *a):  # silence : journalisation via systemd
        pass

    def _envoyer(self, code: int, corps: dict) -> None:
        data = json.dumps(corps).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _autorise(self) -> bool:
        """Le jeton passe par X-Omega-Token, PAS par Authorization.

        Raison : quand le gateway est exposé derrière un tunnel qui impose son
        propre basic-auth (traffic policy ngrok), l'en-tête Authorization est
        déjà pris. Deux authentifications, deux en-têtes distincts.
        """
        if not JETON:
            return True
        if self.headers.get("X-Omega-Token", "") == JETON:
            return True
        return self.headers.get("Authorization", "") == f"Bearer {JETON}"

    def do_GET(self):
        if self.path == "/sante":
            assert PASSERELLE
            self._envoyer(200, PASSERELLE.sante())
        else:
            self._envoyer(404, {"erreur": "route inconnue"})

    def do_POST(self):
        if self.path.rstrip("/") not in ("/mcp", ""):
            self._envoyer(404, {"erreur": "route inconnue"})
            return
        if not self._autorise():
            self._envoyer(401, {"erreur": "jeton absent ou invalide"})
            return
        taille = int(self.headers.get("Content-Length", 0))
        try:
            req = json.loads(self.rfile.read(taille) or "{}")
        except json.JSONDecodeError:
            self._envoyer(400, {"erreur": "JSON invalide"})
            return

        mid, methode = req.get("id"), req.get("method")
        assert PASSERELLE

        if methode == "initialize":
            res = {
                "protocolVersion": PROTOCOL,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "jarvis-omega", "version": "1.0.0"},
            }
        elif methode == "tools/list":
            res = {"tools": PASSERELLE.outils()}
        elif methode == "tools/call":
            p = req.get("params", {})
            try:
                res = PASSERELLE.appeler(p.get("name", ""), p.get("arguments") or {})
            except Exception as exc:  # noqa: BLE001
                self._envoyer(
                    200,
                    {
                        "jsonrpc": "2.0",
                        "id": mid,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"ERREUR {type(exc).__name__}: {exc}",
                                }
                            ],
                            "isError": True,
                        },
                    },
                )
                return
        elif methode in ("notifications/initialized", "initialized"):
            self.send_response(202)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        else:
            self._envoyer(
                200,
                {
                    "jsonrpc": "2.0",
                    "id": mid,
                    "error": {
                        "code": -32601,
                        "message": f"méthode inconnue : {methode}",
                    },
                },
            )
            return

        self._envoyer(200, {"jsonrpc": "2.0", "id": mid, "result": res})


def main() -> None:
    global PASSERELLE, JETON
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=18810)
    ap.add_argument("--config", default=str(Path.home() / ".mcp.json"))
    ap.add_argument("--only", help="liste de serveurs, séparés par des virgules")
    args = ap.parse_args()

    JETON = os.environ.get("OMEGA_TOKEN") or None
    PASSERELLE = Passerelle(
        Path(args.config), args.only.split(",") if args.only else None
    )
    print(
        f"JARVIS OMEGA gateway :{args.port}/mcp — {len(PASSERELLE.enfants)} serveur(s) : "
        f"{', '.join(PASSERELLE.enfants)}",
        file=sys.stderr,
        flush=True,
    )
    if not JETON:
        print(
            "ATTENTION : OMEGA_TOKEN non posé — endpoint SANS authentification.",
            file=sys.stderr,
            flush=True,
        )
    Serveur(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
