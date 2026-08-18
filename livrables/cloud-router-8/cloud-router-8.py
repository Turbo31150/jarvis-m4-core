#!/usr/bin/env python3
"""cloud-router-8.py — Routeur round-robin fan-out sur les N cles Ollama Cloud (cible: 8 cles Remi).

Objectif : traiter une LISTE de prompts EN PARALLELE en repartissant la charge sur
plusieurs cles API Ollama Cloud (une cle par worker), 100 % deporte sur ollama.com
=> 0 chaleur sur le M4 (aucune inference locale n'est lancee ici).

SECURITE (regles dures) :
  - Aucune cle n'est jamais ecrite en dur dans ce fichier.
  - Les cles sont lues depuis l'environnement ou un fichier hors-git, jamais affichees.
  - Les logs n'exposent QUE l'index de cle (key#0..N), jamais sa valeur.
  - RGPD : ne pas router de donnees nominatives eleves (voir docs/CLOUD-ROUTER-8.md).

Source des cles (priorite decroissante) :
  1. env  OLLAMA_CLOUD_KEYS      -> N cles separees par virgule / espace / retour ligne
  2. fichier  ~/.ollama/cloud_keys  -> une cle par ligne (# = commentaire)
  3. fallback single-key : env OLLAMA_API_KEY, sinon ~/.ollama/cloud.env, sinon
     ~/.ollama/cloud_api_key  (compat scripts existants ollama-cloud*.sh)

Endpoint : https://ollama.com/api/chat  (Authorization: Bearer <cle>)
Modele cloud GRATUIT par defaut : gpt-oss:120b  (parametrable via --model / OLLAMA_CLOUD_MODEL)

Usage :
  python3 cloud-router-8.py --prompts prompts.txt --out results.jsonl
  python3 cloud-router-8.py --selftest            # 1 mini-appel par cle -> qui repond (200/401/429)
  echo -e "prompt A\\nprompt B" | python3 cloud-router-8.py --out out.jsonl
  python3 cloud-router-8.py --prompts p.txt --out r.jsonl --model gpt-oss:20b-cloud --workers 8
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Iterable

CLOUD_HOST = os.environ.get("OLLAMA_CLOUD_HOST", "https://ollama.com").rstrip("/")
CHAT_PATH = "/api/chat"
DEFAULT_MODEL = os.environ.get("OLLAMA_CLOUD_MODEL", "gpt-oss:120b")
KEYS_FILE = Path(
    os.environ.get(
        "OLLAMA_CLOUD_KEYS_FILE", str(Path.home() / ".ollama" / "cloud_keys")
    )
)
MAX_KEYS = 8  # cible : les 8 cles de Remi

_print_lock = threading.Lock()


def log(msg: str) -> None:
    """Journal de progression sur stderr (jamais de cle)."""
    with _print_lock:
        print(msg, file=sys.stderr, flush=True)


# --------------------------------------------------------------------------- #
# Chargement des cles (jamais affichees)
# --------------------------------------------------------------------------- #
def _split_keys(blob: str) -> list[str]:
    raw = blob.replace(",", "\n").split("\n")
    out: list[str] = []
    for line in raw:
        k = line.strip()
        if k and not k.startswith("#"):
            out.append(k)
    return out


def _read_single_key_from_env_file(path: Path) -> str | None:
    """Extrait OLLAMA_API_KEY d'un fichier .env (compat ollama-cloud-profile.sh)."""
    try:
        for line in path.read_text().splitlines():
            line = line.strip().lstrip("export ").strip()
            if line.startswith("OLLAMA_API_KEY="):
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                if val:
                    return val
    except OSError:
        return None
    return None


def load_keys() -> list[str]:
    """Retourne la liste dedupliquee des cles, sans jamais les afficher."""
    keys: list[str] = []

    env_keys = os.environ.get("OLLAMA_CLOUD_KEYS", "")
    if env_keys.strip():
        keys = _split_keys(env_keys)

    if not keys and KEYS_FILE.is_file():
        keys = _split_keys(KEYS_FILE.read_text())

    if not keys:  # fallback single-key
        single = os.environ.get("OLLAMA_API_KEY", "").strip()
        if not single:
            single = (
                _read_single_key_from_env_file(Path.home() / ".ollama" / "cloud.env")
                or ""
            )
        if not single:
            try:
                single = (Path.home() / ".ollama" / "cloud_api_key").read_text().strip()
            except OSError:
                single = ""
        if single:
            keys = [single]

    # dedup en gardant l'ordre
    seen: set[str] = set()
    uniq = [k for k in keys if not (k in seen or seen.add(k))]
    return uniq[:MAX_KEYS]


# --------------------------------------------------------------------------- #
# Appel HTTP cloud
# --------------------------------------------------------------------------- #
class KeyDead(Exception):
    """Cle morte/invalide (401/403) — a retirer de la rotation."""


class RateLimited(Exception):
    """429 — basculer sur la cle suivante."""


def _post_chat(prompt: str, key: str, model: str, timeout: float) -> str:
    payload = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{CLOUD_HOST}{CHAT_PATH}",
        data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            raise KeyDead(f"HTTP {e.code}") from e
        if e.code == 429 or 500 <= e.code < 600:
            raise RateLimited(f"HTTP {e.code}") from e
        raise
    msg = data.get("message") or {}
    content = msg.get("content")
    if content is None:
        raise RuntimeError(f"reponse sans message.content: {str(data)[:200]}")
    return content


def call_with_rotation(
    prompt: str,
    key_ring: list[str],
    dead: set[int],
    start_idx: int,
    model: str,
    timeout: float,
    retries: int,
) -> tuple[str, int]:
    """Essaie les cles vivantes a partir de start_idx, backoff sur 429/5xx. Retourne (texte, key_idx)."""
    n = len(key_ring)
    last_err = "aucune cle vivante"
    for hop in range(n):
        idx = (start_idx + hop) % n
        if idx in dead:
            continue
        backoff = 1.0
        for attempt in range(retries + 1):
            try:
                return _post_chat(prompt, key_ring[idx], model, timeout), idx
            except KeyDead as e:
                dead.add(idx)
                log(f"  [key#{idx}] MORTE ({e}) -> retiree de la rotation")
                last_err = str(e)
                break  # cle suivante
            except RateLimited as e:
                last_err = str(e)
                if attempt < retries:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                log(f"  [key#{idx}] 429/5xx persistant -> cle suivante")
                break  # cle suivante
            except Exception as e:  # timeout, parse, reseau
                last_err = str(e)
                if attempt < retries:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                break
    raise RuntimeError(f"echec sur toutes les cles: {last_err}")


# --------------------------------------------------------------------------- #
# Batch parallele
# --------------------------------------------------------------------------- #
def _prompt_id(p: str) -> str:
    return hashlib.sha1(p.encode("utf-8")).hexdigest()[:12]


def _load_done(out_path: Path) -> set[str]:
    """Idempotence : ids deja traites (succes) dans le JSONL de sortie."""
    done: set[str] = set()
    if out_path.is_file():
        for line in out_path.read_text().splitlines():
            try:
                rec = json.loads(line)
                if rec.get("ok"):
                    done.add(rec["id"])
            except (json.JSONDecodeError, KeyError):
                continue
    return done


def run_batch(
    prompts: list[str],
    out_path: Path,
    model: str,
    workers: int,
    timeout: float,
    retries: int,
) -> int:
    keys = load_keys()
    if not keys:
        log(
            "ERREUR: aucune cle chargee (OLLAMA_CLOUD_KEYS / ~/.ollama/cloud_keys / OLLAMA_API_KEY)."
        )
        return 2
    dead: set[int] = set()
    workers = max(1, min(workers, len(keys)))
    log(
        f"Cles chargees: {len(keys)}/{MAX_KEYS} | workers: {workers} | modele: {model} | endpoint: {CLOUD_HOST}{CHAT_PATH}"
    )

    done = _load_done(out_path)
    todo = [(i, p) for i, p in enumerate(prompts) if _prompt_id(p) not in done]
    total = len(todo)
    if not total:
        log("Rien a faire (tous les prompts deja traites).")
        return 0
    log(f"Prompts a traiter: {total} (deja faits: {len(prompts) - total})")

    write_lock = threading.Lock()
    counter = {"n": 0}
    out_fh = out_path.open("a", encoding="utf-8")

    def work(job: tuple[int, str]) -> None:
        i, prompt = job
        rec: dict[str, Any]
        try:
            text, kidx = call_with_rotation(
                prompt, keys, dead, i % len(keys), model, timeout, retries
            )
            rec = {
                "id": _prompt_id(prompt),
                "idx": i,
                "ok": True,
                "key": kidx,
                "backend": f"ollama-cloud:{model}",
                "prompt": prompt,
                "response": text,
            }
        except Exception as e:
            rec = {
                "id": _prompt_id(prompt),
                "idx": i,
                "ok": False,
                "error": str(e),
                "backend": f"ollama-cloud:{model}",
                "prompt": prompt,
            }
        with write_lock:
            out_fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out_fh.flush()
            counter["n"] += 1
            tag = f"key#{rec.get('key')}" if rec["ok"] else "ECHEC"
            log(f"[{counter['n']}/{total}] {'OK' if rec['ok'] else 'KO'} {tag} idx={i}")

    try:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = [ex.submit(work, job) for job in todo]
            for f in as_completed(futures):
                f.result()
    finally:
        out_fh.close()

    live = len(keys) - len(dead)
    log(f"Termine. Cles vivantes en fin de run: {live}/{len(keys)}. Sortie: {out_path}")
    return 0


# --------------------------------------------------------------------------- #
# Selftest : 1 mini-appel par cle
# --------------------------------------------------------------------------- #
def selftest(model: str, timeout: float) -> int:
    keys = load_keys()
    if not keys:
        log("ERREUR: aucune cle a tester.")
        return 2
    log(
        f"Selftest sur {len(keys)}/{MAX_KEYS} cle(s) — modele {model} (deporte, 0 chaleur M4)"
    )
    alive = 0
    for idx, key in enumerate(keys):
        try:
            txt = _post_chat(f"OK{idx}", key, model, timeout)
            alive += 1
            log(f"  key#{idx}: 200 VIVANTE (repond: {txt.strip()[:40]!r})")
        except KeyDead as e:
            log(f"  key#{idx}: {e} MORTE")
        except RateLimited as e:
            log(f"  key#{idx}: {e} RATE-LIMIT (probablement vivante mais saturee)")
        except Exception as e:
            log(f"  key#{idx}: ERREUR {e}")
    log(f"RESULTAT: {alive}/{len(keys)} cle(s) repondent 200.")
    return 0


def _read_prompts(path: str | None) -> list[str]:
    if path and path != "-":
        raw = Path(path).read_text()
    else:
        raw = sys.stdin.read()
    return [ln.strip() for ln in raw.splitlines() if ln.strip()]


def main(argv: Iterable[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Routeur round-robin fan-out N cles Ollama Cloud (0 chaleur M4)."
    )
    ap.add_argument(
        "--prompts", help="fichier de prompts (1 par ligne). '-' ou vide = stdin"
    )
    ap.add_argument(
        "--out",
        default="cloud-router-results.jsonl",
        help="fichier JSONL de sortie (append, idempotent)",
    )
    ap.add_argument(
        "--model", default=DEFAULT_MODEL, help=f"modele cloud (defaut {DEFAULT_MODEL})"
    )
    ap.add_argument(
        "--workers",
        type=int,
        default=MAX_KEYS,
        help="parallelisme max (borne au nb de cles)",
    )
    ap.add_argument(
        "--timeout", type=float, default=120.0, help="timeout par appel (s)"
    )
    ap.add_argument(
        "--retries", type=int, default=2, help="retries backoff sur 429/5xx/timeout"
    )
    ap.add_argument(
        "--selftest", action="store_true", help="1 mini-appel par cle et sort"
    )
    args = ap.parse_args(list(argv) if argv is not None else None)

    if args.selftest:
        return selftest(args.model, args.timeout)

    prompts = _read_prompts(args.prompts)
    if not prompts:
        log("ERREUR: aucun prompt (fournir --prompts fichier ou via stdin).")
        return 2
    return run_batch(
        prompts, Path(args.out), args.model, args.workers, args.timeout, args.retries
    )


if __name__ == "__main__":
    raise SystemExit(main())
