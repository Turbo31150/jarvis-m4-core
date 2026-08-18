"""cascade.py — routeur d'inférence 0-token, déporté d'abord.

Principe (cf. CLAUDE.md) : SONDER AVANT DE ROUTER. Un backend câblé en dur peut
être mort depuis des mois — c'était le cas de M1_HOST et M2 dans ai_local.py.
Ici, aucun backend n'est supposé vivant : il est sondé, et le résultat de la
sonde est mis en cache sur disque (pas de boucle, pas de démon).

Ordre de la cascade, du moins cher au plus coûteux pour la machine :
    1. cache SQL           — 0 token, 0 chaleur, instantané
    2. backends DÉPORTÉS   — 0 token, 0 chaleur sur M4 (Rémi via Tailscale, M6 via tunnel)
    3. Ollama local M4     — 0 token mais CHAUFFE : refusé au-dessus du plafond thermique
    4. (rien)              — AIUnavailable, jamais de crash, jamais d'IA facturée

Aucune IA facturée n'est appelée ici. Aucune boucle d'inférence : tout est
déclenché à la demande.

Usage CLI :   python3 cascade.py "ma question"
              python3 cascade.py --status
Usage module : from cascade import ask, status
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

# --- Garde-fous ---------------------------------------------------------------

TEMP_CEILING_C = 82.0  # au-delà, on refuse d'inférer EN LOCAL (mémoire surchauffe M4)
PROBE_TTL_S = 60.0  # durée de validité d'une sonde, évite de re-sonder à chaque appel
PROBE_TIMEOUT_S = 4.0
GEN_TIMEOUT_S = 120.0

_HERE = Path(__file__).resolve().parent
_CACHE_DB = _HERE / "ecole.db"
_PROBE_CACHE = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / "cascade-probe.json"


class AIUnavailable(RuntimeError):
    """Aucun backend 0-token n'a pu répondre. Jamais de repli facturé."""


@dataclass(frozen=True)
class Backend:
    """Un backend LLM joignable en HTTP (Ollama ou LM Studio)."""

    nom: str
    url: str
    modele: str
    deporte: bool  # True = ne chauffe pas M4
    tiers: bool  # True = machine qui n'appartient PAS à l'utilisatrice → jamais de PII
    note: str = ""
    api: str = "ollama"  # "ollama" (/api/generate) ou "openai" (/v1/completions)


# Ordre = priorité. Déporté d'abord : la machine de l'utilisatrice ne doit pas chauffer.
# Chaque entrée a été SONDÉE et mesurée avant d'être inscrite ici (2026-08-14).
BACKENDS: tuple[Backend, ...] = (
    Backend(
        nom="remi-asus",
        url="http://100.113.121.61:11434",
        modele="gemma3:4b",
        deporte=True,
        tiers=True,
        note="Tailscale, machine de Rémi. gemma3:27b dispo pour la qualité.",
    ),
    Backend(
        nom="remi-asus-27b",
        url="http://100.113.121.61:11434",
        modele="gemma3:27b",
        deporte=True,
        tiers=True,
        note="Le plus gros modèle joignable du parc (17,4 Go). Machine de Rémi.",
    ),
    Backend(
        nom="m6-lmstudio",
        url="http://10.42.0.230:1234",
        modele="qwen/qwen3.5-9b",
        deporte=True,
        tiers=False,
        note=(
            "LM Studio sur M6, câble ethernet direct 1 Gbps (RTT 1,4 ms). "
            "Machine du foyer : seul backend déporté utilisable en nominatif. "
            "Ollama :11434 de M6 est muet — ne pas y router (mesuré 2026-08-14)."
        ),
        api="openai",
    ),
    Backend(
        nom="m4-local",
        url="http://127.0.0.1:11434",
        modele="gemma3:4b",
        deporte=False,
        tiers=False,
        note="Cette machine. Chauffe : plafonné à 82 °C.",
    ),
)

# Modèles à ne jamais utiliser pour de la génération de texte.
_MODELES_EMBEDDING = ("nomic-embed", "bge-m3", "mxbai-embed")
# qwen3/qwen2.5 en mode « thinking » renvoient un contenu vide (reasoning-runaway connu).
_MODELES_MUETS = ("qwen3:",)


# --- Sonde --------------------------------------------------------------------


def _temp_cpu() -> float:
    """Température CPU réelle, lue depuis le sysfs. 0.0 si illisible."""
    try:
        brut = Path("/sys/class/thermal/thermal_zone0/temp").read_text().strip()
        return float(brut) / 1000.0
    except (OSError, ValueError):
        return 0.0


def _http_json(
    url: str, payload: dict | None = None, timeout: float = PROBE_TIMEOUT_S
) -> dict | None:
    """GET/POST JSON tolérant. Renvoie None au lieu de lever : la cascade doit survivre."""
    donnees = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url,
        data=donnees,
        headers={"Content-Type": "application/json"} if donnees else {},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as rep:
            return json.loads(rep.read().decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def _modeles_dispo(url: str, api: str = "ollama") -> set[str]:
    """Modèles réellement chargeables sur ce backend."""
    if api == "openai":
        rep = _http_json(f"{url}/v1/models")
        if not rep:
            return set()
        return {m.get("id", "") for m in rep.get("data", [])}
    rep = _http_json(f"{url}/api/tags")
    if not rep:
        return set()
    return {m.get("name", "") for m in rep.get("models", [])}


def _sonder(force: bool = False) -> dict[str, bool]:
    """Sonde tous les backends. Résultat mis en cache PROBE_TTL_S secondes.

    C'est le cœur du garde-fou : on ne route jamais vers un backend supposé.
    """
    if not force and _PROBE_CACHE.exists():
        try:
            cache = json.loads(_PROBE_CACHE.read_text())
            if time.time() - cache.get("ts", 0) < PROBE_TTL_S:
                return cache.get("vivants", {})
        except (OSError, json.JSONDecodeError):
            pass

    vivants: dict[str, bool] = {}
    for b in BACKENDS:
        modeles = _modeles_dispo(b.url, b.api)
        vivants[b.nom] = b.modele in modeles

    try:
        _PROBE_CACHE.write_text(json.dumps({"ts": time.time(), "vivants": vivants}))
    except OSError:
        pass
    return vivants


# --- Cache SQL ----------------------------------------------------------------


def _cache_lire(cle: str) -> str | None:
    """Lit le cache AVANT toute inférence. Base ouverte en lecture seule.

    Schéma imposé par l'existant (744 entrées déjà en base, à ne pas casser) :
    ai_cache(key, question, answer, backend, hits, ts).
    """
    if not _CACHE_DB.exists():
        return None
    try:
        con = sqlite3.connect(f"file:{_CACHE_DB}?mode=ro", uri=True, timeout=2)
        try:
            cur = con.execute("SELECT answer FROM ai_cache WHERE key = ?", (cle,))
            ligne = cur.fetchone()
            return ligne[0] if ligne and ligne[0] else None
        finally:
            con.close()
    except sqlite3.Error:
        return None


def _cache_ecrire(cle: str, question: str, reponse: str, backend: str) -> None:
    """Mémorise la réponse. Échec silencieux : le cache ne doit jamais casser l'appel."""
    try:
        con = sqlite3.connect(_CACHE_DB, timeout=5)
        try:
            con.execute(
                "CREATE TABLE IF NOT EXISTS ai_cache ("
                "key TEXT PRIMARY KEY, question TEXT, answer TEXT, "
                "backend TEXT, hits INTEGER DEFAULT 0, ts TEXT DEFAULT (datetime('now')))"
            )
            con.execute(
                "INSERT INTO ai_cache (key, question, answer, backend, hits) "
                "VALUES (?,?,?,?,0) "
                "ON CONFLICT(key) DO UPDATE SET "
                "answer=excluded.answer, backend=excluded.backend, hits=hits+1",
                (cle, question, reponse, backend),
            )
            con.commit()
        finally:
            con.close()
    except sqlite3.Error:
        pass


# --- API ----------------------------------------------------------------------


@dataclass
class Reponse:
    texte: str
    backend: str
    depuis_cache: bool
    duree_ms: int
    deporte: bool = field(default=True)


def status() -> dict[str, object]:
    """État réel de la cascade, sondé. Sert au diagnostic et à l'affichage."""
    vivants = _sonder(force=True)
    temp = _temp_cpu()
    return {
        "temperature_cpu_c": round(temp, 1),
        "plafond_thermique_c": TEMP_CEILING_C,
        "local_autorise": temp < TEMP_CEILING_C,
        "backends": [
            {
                "nom": b.nom,
                "modele": b.modele,
                "deporte": b.deporte,
                "vivant": vivants.get(b.nom, False),
                "note": b.note,
            }
            for b in BACKENDS
        ],
        "premier_utilisable": next((b.nom for b in _candidats(vivants, temp)), None),
    }


def _candidats(
    vivants: dict[str, bool], temp: float, nominatif: bool = False
) -> list[Backend]:
    """Backends utilisables, dans l'ordre.

    Deux exclusions non négociables :
      - thermique : le local est écarté au-dessus du plafond ;
      - RGPD : si le contenu est nominatif (élève, famille), tout backend TIERS
        est écarté. Voir webapp/CLAUDE.md — profil ecole, PII-ELEVES.
    """
    sortie: list[Backend] = []
    for b in BACKENDS:
        if not vivants.get(b.nom, False):
            continue
        if any(x in b.modele for x in _MODELES_EMBEDDING + _MODELES_MUETS):
            continue
        if nominatif and b.tiers:
            continue  # une appréciation d'élève ne sort jamais vers la machine d'un tiers
        if not b.deporte and temp >= TEMP_CEILING_C:
            continue  # garde-fou thermique : on préfère échouer que cuire la machine
        sortie.append(b)
    return sortie


def ask(
    prompt: str,
    max_tokens: int = 800,
    cache: bool = True,
    qualite: bool = False,
    nominatif: bool = False,
) -> Reponse:
    """Pose une question à la cascade 0-token.

    qualite=True   privilégie gemma3:27b (plus lent, meilleure rédaction).
    nominatif=True OBLIGATOIRE dès que le prompt contient un nom d'élève, de
                   famille, une appréciation ou une observation. Effets :
                   les backends tiers sont exclus, et le cache est désactivé
                   (une réponse nominative en cache deviendrait lisible par une
                   autre requête). Voir webapp/CLAUDE.md, profil ecole.

    Lève AIUnavailable si aucun backend gratuit ne répond — jamais de repli facturé.
    """
    prompt = prompt.strip()
    if not prompt:
        raise ValueError("prompt vide")

    if nominatif:
        cache = False  # non négociable : pas de PII en cache partagé

    cle = f"{max_tokens}:{qualite}:{prompt}"
    if cache:
        if (garde := _cache_lire(cle)) is not None:
            return Reponse(garde, "cache", True, 0)

    temp = _temp_cpu()
    candidats = _candidats(_sonder(), temp, nominatif=nominatif)
    if qualite:
        candidats.sort(key=lambda b: "27b" not in b.modele)

    erreurs: list[str] = []
    for b in candidats:
        t0 = time.monotonic()
        if b.api == "openai":
            # LM Studio : /v1/chat/completions part en reasoning-runaway sur les
            # qwen3 (content vide, tout le budget en reasoning_tokens — mesuré
            # 80 tokens de raisonnement pour 0 caractère). Parade éprouvée,
            # identique à scripts/lm-ask.sh : /v1/completions avec <think></think>
            # pré-fermé dans le gabarit ChatML.
            rep = _http_json(
                f"{b.url}/v1/completions",
                {
                    "model": b.modele,
                    "prompt": (
                        "<|im_start|>user\n" + prompt + "<|im_end|>\n"
                        "<|im_start|>assistant\n<think></think>\n\n"
                    ),
                    "max_tokens": max_tokens,
                    "temperature": 0.2,
                },
                timeout=GEN_TIMEOUT_S,
            )
            choix = (rep or {}).get("choices") or [{}]
            texte = (choix[0].get("text") or "").strip()
        else:
            rep = _http_json(
                f"{b.url}/api/generate",
                {
                    "model": b.modele,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": max_tokens},
                },
                timeout=GEN_TIMEOUT_S,
            )
            texte = ((rep or {}).get("response") or "").strip()
        duree = int((time.monotonic() - t0) * 1000)
        if not texte:
            erreurs.append(f"{b.nom}: vide/timeout ({duree} ms)")
            continue
        if cache:
            _cache_ecrire(cle, prompt, texte, b.nom)
        return Reponse(texte, b.nom, False, duree, b.deporte)

    detail = " | ".join(erreurs) if erreurs else "aucun backend vivant"
    if temp >= TEMP_CEILING_C:
        detail += (
            f" | local bloqué : CPU à {temp:.0f} °C (plafond {TEMP_CEILING_C:.0f})"
        )
    if nominatif:
        detail += " | mode nominatif : backends tiers écartés (RGPD)"
    raise AIUnavailable(f"cascade 0-token épuisée — {detail}")


def register(app) -> None:  # noqa: ANN001 — Flask app, typée côté appelant
    """Branche la cascade sur la webapp Pousseline (:7777)."""
    from flask import jsonify, request

    @app.route("/api/cascade", methods=["POST"])
    def _cascade_route():
        data = request.get_json(force=True) or {}
        prompt = (data.get("prompt") or "").strip()
        if not prompt:
            return jsonify({"error": "prompt vide"}), 400
        try:
            r = ask(
                prompt,
                max_tokens=int(data.get("max_tokens", 800)),
                qualite=bool(data.get("qualite", False)),
                nominatif=bool(data.get("nominatif", False)),
            )
        except AIUnavailable as e:
            return jsonify({"error": str(e)}), 503
        return jsonify(
            {
                "texte": r.texte,
                "backend": r.backend,
                "cached": r.depuis_cache,
                "duree_ms": r.duree_ms,
                "deporte": r.deporte,
            }
        )

    @app.route("/api/cascade/status", methods=["GET"])
    def _cascade_status():
        return jsonify(status())


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        print(json.dumps(status(), indent=2, ensure_ascii=False))
        sys.exit(0)
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    try:
        r = ask(" ".join(sys.argv[1:]))
    except AIUnavailable as exc:
        print(f"[KO] {exc}", file=sys.stderr)
        sys.exit(2)
    etiquette = "déporté" if r.deporte else "LOCAL (chauffe)"
    print(f"[{r.backend} · {etiquette} · {r.duree_ms} ms]\n{r.texte}")
