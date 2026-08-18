#!/usr/bin/env python3
"""Retire les affirmations chiffrées inventées des formations forgées.

Le modèle produit des benchmarks crédibles mais fabriqués (« perplexité ≤ 12 sur
WikiText-2 », « latence < 200 ms », « +20 % de précision »). Sur des produits
payants ce sont des promesses fausses.

Deux étages, et c'est le second qui rend l'outil digne de confiance :
  1. un LLM réécrit le texte en retirant les chiffres invérifiables ;
  2. le MÊME détecteur déterministe repasse sur sa sortie et compte ce qui
     reste. Un modèle qui promet d'avoir nettoyé n'est pas cru sur parole.

Massivement parallèle et 0-token : le calcul part sur la cascade déportée.

Usage : python3 nettoie_chiffres.py [workers] [--limit N]
"""

import re
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, "/home/pamerys/jarvis/webapp")
sys.path.insert(0, "/home/pamerys/jarvis")
import ai_local  # noqa: E402

SRC = Path("/home/pamerys/jarvis/data/forge")
DST = Path("/home/pamerys/jarvis/data/forge_propre")
LOG = Path("/home/pamerys/jarvis/data/nettoyage.log")

# Mêmes motifs que le module webapp forge.py — une seule définition de ce
# qu'est une « affirmation chiffree », sinon les deux outils divergent.
MOTIFS = [
    r"\b\d+(?:[.,]\d+)?\s*%",
    r"[<>≤≥]\s*\d+(?:[.,]\d+)?\s*(?:ms|s|min|h)\b",
    r"\b\d+(?:[.,]\d+)?\s*(?:ms|Go|Mo|GB|MB|tok/s|tokens/s)\b",
    r"\bperplexit[ée]\s*[<>≤≥=]?\s*\d+",
    r"\b(?:x|×)\s?\d+(?:[.,]\d+)?\s*(?:plus|fois)",
]

SYSTEME = (
    "Tu es relecteur editorial. Tu retires les affirmations chiffrees "
    "invérifiables d'un support de formation, SANS jamais en inventer de "
    "nouvelles et sans rien ajouter. Tu reformules la phrase pour qu'elle "
    "reste juste et lisible sans le chiffre. Tu preserves integralement la "
    "structure markdown, les titres, et tout le code. Tu rends le document "
    "complet, rien d'autre."
)

_lock = threading.Lock()
_done = 0


def claims(texte):
    n = 0
    for m in MOTIFS:
        n += len(re.findall(m, texte, re.IGNORECASE))
    return n


def log(msg):
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    try:
        with LOG.open("a") as f:
            f.write(line + "\n")
    except OSError:
        pass


def traiter(src_file, total):
    global _done
    dest = DST / src_file.name
    texte = src_file.read_text("utf-8", errors="replace")
    avant = claims(texte)

    if avant == 0:  # rien a nettoyer : on copie tel quel
        dest.write_text(texte, encoding="utf-8")
        with _lock:
            _done += 1
            log(f"[{_done}/{total}] ○ {src_file.stem} — aucun chiffre, copie")
        return True

    for _ in range(5):
        try:
            r = ai_local.generate(
                SYSTEME,
                "Retire de ce document toutes les affirmations chiffrees qui ne "
                "peuvent pas etre verifiees (pourcentages de gain, latences, "
                "scores de benchmark, facteurs multiplicatifs). Ne les remplace "
                "par AUCUN autre chiffre. Rends le document complet :\n\n" + texte,
                max_tokens=4000,
                cache=False,  # une reecriture est unique, la mettre en cache ne sert a rien
            )
            propre = r["text"].strip()
            if len(propre) < len(texte) * 0.4:
                # Sortie tronquee : garder l'original vaut mieux qu'un document ampute.
                with _lock:
                    _done += 1
                    log(
                        f"[{_done}/{total}] ⚠ {src_file.stem} — sortie trop courte, original conserve"
                    )
                dest.write_text(texte, encoding="utf-8")
                return False
            apres = claims(propre)
            dest.write_text(propre, encoding="utf-8")
            with _lock:
                _done += 1
                marque = "✅" if apres == 0 else "◐"
                log(
                    f"[{_done}/{total}] {marque} {src_file.stem} — {avant} → {apres} "
                    f"<{r['backend']}>"
                )
            return apres == 0
        except ai_local.AIUnavailable:
            time.sleep(25)
        except Exception as e:  # noqa: BLE001
            log(f"⚠ {src_file.stem} : {type(e).__name__} {e}")
            time.sleep(5)
    log(f"❌ ABANDON : {src_file.stem}")
    return False


def main():
    workers = 6
    limit = None
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a.isdigit():
            workers = int(a)
        elif a == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1])

    DST.mkdir(parents=True, exist_ok=True)
    fichiers = [f for f in sorted(SRC.glob("*.md")) if not (DST / f.name).exists()]
    if limit:
        fichiers = fichiers[:limit]
    total = len(fichiers)
    if not total:
        log("🎉 Rien a nettoyer — tout est deja traite.")
        return

    reste_avant = sum(claims(f.read_text("utf-8", errors="replace")) for f in fichiers)
    log(
        f"=== NETTOYAGE : {total} fichiers · {reste_avant} chiffres · {workers} workers ==="
    )

    from concurrent.futures import ThreadPoolExecutor, as_completed

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(traiter, f, total) for f in fichiers]
        for _ in as_completed(futs):
            pass
    ok = sum(1 for f in futs if f.result())
    reste = sum(
        claims((DST / f.name).read_text("utf-8", errors="replace"))
        for f in fichiers
        if (DST / f.name).exists()
    )
    dt = int(time.time() - t0)
    log(
        f"=== FIN : {ok}/{total} totalement propres · {reste_avant} → {reste} chiffres · {dt // 60}m{dt % 60}s ==="
    )
    log(f"    sortie : {DST}")


if __name__ == "__main__":
    main()
