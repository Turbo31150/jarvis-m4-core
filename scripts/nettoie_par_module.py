#!/usr/bin/env python3
"""Passe 2 du nettoyage des chiffres — par module, avec rotation de clés.

La passe 1 traitait chaque formation d'un bloc. À partir du 49e fichier, les
échecs sont arrivés en rafale : sous charge soutenue, Ollama Cloud tronque la
réponse au lieu de renvoyer un 429. Deux remèdes, appliqués ici :

  1. Découper par module. Six requêtes courtes passent là où une longue est
     tronquée, et un module raté ne fait plus perdre toute la formation.
  2. Faire tourner plusieurs clés. Les quotas sont par clé : chaque appel prend
     la suivante, et un 429 écarte la clé fautive pendant une minute.

Le contrôle reste déterministe : après réécriture, le même détecteur regex
recompte sur la sortie. Le modèle n'est jamais cru sur parole.

Clés : une par ligne dans ~/.ollama/cloud_keys (sinon la clé unique habituelle).

Usage : python3 nettoie_par_module.py [workers] [--only <slug>] [--limit N]
"""

import itertools
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

SRC = Path("/home/pamerys/jarvis/data/forge")
DST = Path("/home/pamerys/jarvis/data/forge_propre")
KEYS_FILE = Path.home() / ".ollama" / "cloud_keys"
KEY_FILE_SIMPLE = Path.home() / ".ollama" / "cloud_api_key"
LOG = Path("/home/pamerys/jarvis/data/nettoyage-module.log")
URL = "https://ollama.com/v1/chat/completions"
MODELE = os.environ.get("OLLAMA_CLOUD_MODEL", "gpt-oss:120b")

MOTIFS = [
    r"\b\d+(?:[.,]\d+)?\s*%",
    r"[<>≤≥]\s*\d+(?:[.,]\d+)?\s*(?:ms|s|min|h)\b",
    r"\b\d+(?:[.,]\d+)?\s*(?:ms|Go|Mo|GB|MB|tok/s|tokens/s)\b",
    r"\bperplexit[ée]\s*[<>≤≥=]?\s*\d+",
    r"\b(?:x|×)\s?\d+(?:[.,]\d+)?\s*(?:plus|fois)",
]

CONSIGNE = (
    "Tu es relecteur editorial. Retire de ce passage toutes les affirmations "
    "chiffrees invérifiables (pourcentages de gain, latences, scores de "
    "benchmark, facteurs multiplicatifs). Ne les remplace par AUCUN autre "
    "chiffre. Reformule pour que la phrase reste juste sans le chiffre. "
    "Preserve integralement le markdown, les titres et le code. Rends le "
    "passage complet, rien d'autre."
)

_lock = threading.Lock()
_done = 0


def charger_cles():
    """Plusieurs clés si le fichier existe, sinon la clé unique."""
    if KEYS_FILE.exists():
        cles = [k.strip() for k in KEYS_FILE.read_text().splitlines() if k.strip()]
        if cles:
            return cles
    if KEY_FILE_SIMPLE.exists():
        k = KEY_FILE_SIMPLE.read_text().strip()
        if k:
            return [k]
    k = os.environ.get("OLLAMA_API_KEY", "").strip()
    return [k] if k else []


CLES = charger_cles()
_cycle = itertools.cycle(range(len(CLES))) if CLES else None
_ecartees: dict[int, float] = {}  # index de clé -> instant de réhabilitation
_cle_lock = threading.Lock()


def prochaine_cle():
    """Clé suivante, en sautant celles écartées pour cause de 429."""
    with _cle_lock:
        for _ in range(len(CLES)):
            i = next(_cycle)
            if _ecartees.get(i, 0) < time.time():
                return i, CLES[i]
        return 0, CLES[0]  # toutes écartées : on retente quand même


def ecarter(i, secondes=60):
    with _cle_lock:
        _ecartees[i] = time.time() + secondes


def claims(txt):
    return sum(len(re.findall(m, txt, re.I)) for m in MOTIFS)


def log(msg):
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    try:
        with LOG.open("a") as f:
            f.write(line + "\n")
    except OSError:
        pass


def appeler(passage, max_tokens=2200):
    """Un appel, clé tournante. Renvoie (texte, nom_court_cle) ou (None, cause)."""
    i, cle = prochaine_cle()
    corps = json.dumps(
        {
            "model": MODELE,
            "messages": [
                {"role": "system", "content": CONSIGNE},
                {"role": "user", "content": passage},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.2,
        }
    ).encode()
    req = urllib.request.Request(
        URL,
        data=corps,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {cle}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            d = json.loads(r.read())
        return (d["choices"][0]["message"].get("content") or "").strip(), f"k{i}"
    except urllib.error.HTTPError as e:
        if e.code == 429:
            ecarter(i)
        return None, f"HTTP {e.code} (k{i})"
    except Exception as e:  # noqa: BLE001
        return None, f"{type(e).__name__} (k{i})"


def decouper(texte):
    """Découpe sur les titres de module ; l'entête reste avec le premier bloc."""
    parties = re.split(r"(?=^---\n\n## Module )", texte, flags=re.M)
    return [p for p in parties if p.strip()]


def traiter(nom, total):
    global _done
    src = SRC / nom
    dest = DST / nom
    # On repart de la version déjà nettoyée si elle est meilleure que l'original.
    base = (
        dest
        if dest.exists()
        and claims(dest.read_text("utf-8")) < claims(src.read_text("utf-8"))
        else src
    )
    texte = base.read_text("utf-8", errors="replace")
    avant = claims(texte)
    if avant == 0:
        with _lock:
            _done += 1
            log(f"[{_done}/{total}] ○ {src.stem} — deja propre")
        return True

    blocs, refaits, backends = decouper(texte), [], set()
    for bloc in blocs:
        if claims(bloc) == 0:
            refaits.append(bloc)
            continue
        obtenu = None
        for _ in range(4):
            txt, info = appeler(bloc)
            backends.add(info)
            # Un bloc réécrit doit rester substantiel : sinon on garde l'original.
            if txt and len(txt) > len(bloc) * 0.5:
                obtenu = txt
                break
            time.sleep(4)
        refaits.append(obtenu if obtenu else bloc)

    propre = "\n".join(refaits)
    apres = claims(propre)
    # Ne jamais régresser : on n'écrit que si on a réellement retiré des chiffres.
    if apres < avant:
        dest.write_text(propre, encoding="utf-8")
    with _lock:
        _done += 1
        marque = "✅" if apres == 0 else ("◐" if apres < avant else "⚠")
        log(
            f"[{_done}/{total}] {marque} {src.stem} — {avant} → {apres} "
            f"({len(blocs)} blocs, {','.join(sorted(backends))})"
        )
    return apres == 0


def main():
    workers = 4
    only, limit = None, None
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a.isdigit():
            workers = int(a)
        elif a == "--only" and i + 1 < len(args):
            only = args[i + 1]
        elif a == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1])

    if not CLES:
        log("❌ aucune clé Ollama Cloud trouvée")
        sys.exit(1)
    DST.mkdir(parents=True, exist_ok=True)

    # Cibles : tout fichier dont la meilleure version porte encore des chiffres.
    cibles = []
    for f in sorted(SRC.glob("*.md")):
        d = DST / f.name
        n = min(
            claims(f.read_text("utf-8", errors="replace")),
            claims(d.read_text("utf-8", errors="replace")) if d.exists() else 10**6,
        )
        if n > 0 and (not only or f.stem == only):
            cibles.append((f.name, n))
    cibles.sort(key=lambda x: -x[1])  # les plus sales d'abord
    if limit:
        cibles = cibles[:limit]

    total = len(cibles)
    if not total:
        log("🎉 Plus aucun chiffre à retirer.")
        return
    reste = sum(n for _, n in cibles)
    log(
        f"=== PASSE 2 : {total} fichiers · {reste} chiffres · {workers} workers "
        f"· {len(CLES)} clé(s) ==="
    )
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(traiter, nom, total) for nom, _ in cibles]
        for _ in as_completed(futs):
            pass
    ok = sum(1 for f in futs if f.result())
    final = sum(
        claims((DST / n).read_text("utf-8", errors="replace"))
        if (DST / n).exists()
        else claims((SRC / n).read_text("utf-8", errors="replace"))
        for n, _ in cibles
    )
    dt = int(time.time() - t0)
    log(
        f"=== FIN : {ok}/{total} propres · {reste} → {final} · {dt // 60}m{dt % 60}s ==="
    )


if __name__ == "__main__":
    main()
