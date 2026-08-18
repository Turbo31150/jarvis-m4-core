#!/usr/bin/env python3
"""Forge des formations Gumroad — contenu « orfèvrerie », cascade 0-token.

Reprend le pattern éprouvé de webapp/scripts/dispatch_banque.py : fan-out de N
workers vers ai_local (cache → LM Studio M6 → Rémi → cloud → Ollama local
bridé), idempotent, retry anti-surchauffe.

Une formation = un plan détaillé + les modules rédigés, écrits en markdown dans
forge/<slug>.md. Rien n'est régénéré si le fichier existe déjà : le script se
relance sans repayer le temps machine.

Usage :
    python3 forge_formations.py [workers] [--only <slug>] [--limit N] [--plan-only]
    python3 forge_formations.py --status
"""

import argparse
import json
import sqlite3
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, "/home/pamerys/jarvis/webapp")
import ai_local  # noqa: E402

INVENTAIRE = Path("/home/pamerys/jarvis/data/gumroad_inventaire.json")
FORGE_DIR = Path("/home/pamerys/jarvis/data/forge")
LOG = Path("/home/pamerys/jarvis/data/forge.log")

# Ollama CPU est lent et le M4 chauffe : on plafonne le parallélisme et la
# taille des réponses. Le fan-out n'a de sens que si un backend déporté répond.
WORKERS_DEFAUT = 4
MAX_TOKENS_PLAN = 900
MAX_TOKENS_MODULE = 1400
MODULES_PAR_FORMATION = 5

_lock = threading.Lock()
_done = 0

SYSTEME = (
    "Tu es un concepteur pédagogique senior spécialisé en IA et développement. "
    "Tu écris en français, dense et concret, sans remplissage ni superlatif "
    "commercial. Chaque affirmation technique doit être vérifiable. Pas "
    "d'introduction ni de conclusion de politesse."
)


def log(msg):
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a") as f:
            f.write(line + "\n")
    except OSError:
        pass


def charger_inventaire():
    if not INVENTAIRE.exists():
        log(f"❌ Inventaire absent : {INVENTAIRE}")
        log("   Le produire d'abord (extraction des liens gumroad des pages de vente).")
        return []
    return json.loads(INVENTAIRE.read_text(encoding="utf-8"))


def _gen(prompt, max_tokens):
    """Un appel de cascade. cache=True : une reformulation identique ne
    repasse jamais par le modèle."""
    return ai_local.generate(SYSTEME, prompt, max_tokens=max_tokens, cache=True)


def forger(produit, plan_only=False):
    """Produit le markdown complet d'une formation. Renvoie (texte, backends)."""
    titre = produit.get("titre") or produit["slug"].replace("-", " ").title()
    slug = produit["slug"]
    prix = produit.get("prix") or "non fixé"
    backends = []

    res = _gen(
        f"Formation : « {titre} » (référence {slug}, prix {prix}).\n\n"
        f"Rédige le plan détaillé en {MODULES_PAR_FORMATION} modules. Pour chaque "
        "module : un titre précis, l'objectif d'apprentissage mesurable, et les "
        "3 à 5 notions couvertes. Formate en markdown avec un titre de niveau 2 "
        "par module. Vise un praticien qui sait déjà coder.",
        MAX_TOKENS_PLAN,
    )
    plan = res["text"]
    backends.append(res["backend"])

    parties = [f"# {titre}\n", f"> Référence `{slug}` · {prix}\n", "## Plan\n", plan]

    if not plan_only:
        for i in range(1, MODULES_PAR_FORMATION + 1):
            r = _gen(
                f"Formation « {titre} ». Voici son plan :\n\n{plan}\n\n"
                f"Rédige maintenant le CONTENU COMPLET du module {i} uniquement. "
                "Inclus : les explications, au moins un exemple de code commenté "
                "et fonctionnel, les pièges concrets, et un exercice de fin de "
                "module avec son corrigé. Markdown. Ne réécris pas le plan.",
                MAX_TOKENS_MODULE,
            )
            parties.append(f"\n---\n\n## Module {i} — contenu\n\n{r['text']}")
            backends.append(r["backend"])

    return "\n".join(parties), backends


def worker(produit, total, plan_only):
    global _done
    slug = produit["slug"]
    dest = FORGE_DIR / f"{slug}.md"
    for _ in range(6):
        try:
            texte, backends = forger(produit, plan_only)
            dest.write_text(texte, encoding="utf-8")
            with _lock:
                _done += 1
                pct = 100 * _done // total
                uniq = ",".join(sorted(set(backends)))
                log(f"[{_done}/{total} {pct}%] ✅ {slug}  <{uniq}>")
            return True
        except ai_local.AIUnavailable:
            time.sleep(25)  # garde-fou thermique ou backends KO : on refroidit
        except sqlite3.OperationalError:
            time.sleep(3)  # verrou transitoire sur le cache
        except Exception as e:  # noqa: BLE001 — un produit raté ne casse pas le lot
            log(f"⚠️  {slug} : {type(e).__name__} {e}")
            time.sleep(5)
    log(f"❌ ABANDON après 6 essais : {slug}")
    return False


def statut(produits):
    FORGE_DIR.mkdir(parents=True, exist_ok=True)
    faits = [p for p in produits if (FORGE_DIR / f"{p['slug']}.md").exists()]
    print(f"forgées : {len(faits)}/{len(produits)}")
    print(f"sortie  : {FORGE_DIR}")
    etat = ai_local.backend_status()
    lisible = {
        k: v for k, v in etat.items() if "cluster" in k or k in ("ollama", "gpu_temp")
    }
    print(f"backends: {lisible}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workers", nargs="?", type=int, default=WORKERS_DEFAUT)
    ap.add_argument("--only", help="forger un seul slug")
    ap.add_argument("--limit", type=int, help="s'arrêter après N formations")
    ap.add_argument("--plan-only", action="store_true", help="plan sans les modules")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()

    produits = charger_inventaire()
    if not produits:
        sys.exit(1)
    if a.status:
        statut(produits)
        return

    FORGE_DIR.mkdir(parents=True, exist_ok=True)
    if a.only:
        produits = [p for p in produits if p["slug"] == a.only]
        if not produits:
            log(f"❌ slug inconnu : {a.only}")
            sys.exit(1)
    else:
        produits = [p for p in produits if not (FORGE_DIR / f"{p['slug']}.md").exists()]
    if a.limit:
        produits = produits[: a.limit]

    total = len(produits)
    if not total:
        log("🎉 Rien à forger — tout est déjà produit.")
        return

    # Sonder avant de router : un lot lancé sans backend vivant ne fait que
    # brûler des retries pendant des minutes.
    etat = ai_local.backend_status()
    log(f"backends : {etat}")

    log(f"=== FORGE : {total} formations · {a.workers} workers · cascade 0-token ===")
    t0 = time.time()
    from concurrent.futures import ThreadPoolExecutor, as_completed

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = [ex.submit(worker, p, total, a.plan_only) for p in produits]
        for _ in as_completed(futs):
            pass
    dt = int(time.time() - t0)
    ok = sum(1 for f in futs if f.result())
    log(f"=== FIN : {ok}/{total} en {dt // 60}m{dt % 60}s · {FORGE_DIR} ===")


if __name__ == "__main__":
    main()
