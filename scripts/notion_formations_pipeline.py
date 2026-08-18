#!/usr/bin/env python3
"""Génère les 72 formations rédigées (Ollama cloud, 0 token facturé) et les livre dans Notion.

Idempotent et reprenable : l'état vit dans data/formations_contenu.db.
  1. init-db   : crée la table de contenu + la base Notion (une seule fois)
  2. generate  : rédige les formations manquantes (fan-out parallèle, backend déporté)
  3. push      : crée/complète les pages Notion des formations rédigées

Usage : notion_formations_pipeline.py {init-db|generate|push|status} [--limit N] [--workers N]
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HOME = Path.home()
SRC_DB = HOME / "jarvis-commercial-2026/data/commercial.db"
WORK_DB = HOME / "jarvis/data/formations_contenu.db"
NOTION_ENV = HOME / ".config/jarvis/notion.env"
HUB_PAGE_ID = "3bc7800a-81d6-8100-8f97-c66fe6f52f84"  # 🧠 JARVIS OS — Hub

# Backend de rédaction. Deux voies éprouvées :
#   m6    — LM Studio sur M6 (qwen3.5-9b, 16k ctx) : souverain, aucun quota.
#   cloud — Ollama cloud gpt-oss:120b : meilleure prose, mais plafonné (HTTP 429
#           constaté sur 50 formations d'affilée le 14/08).
BACKEND = os.environ.get("FORMATIONS_BACKEND", "m6")
M6_COMPLETIONS = "http://10.42.0.230:1234/v1/completions"
# IDENTIFIANT de l'instance chargée, pas le nom du modèle : demander
# « qwen/qwen3.5-9b » pousse LM Studio à charger une SECONDE instance, ce que
# les 12 Go de la RTX 2060 ne permettent pas — d'où un HTTP 400 après plusieurs
# minutes d'attente. Charger avec `--identifier qwen3.5` et l'appeler ainsi.
M6_MODEL = os.environ.get("M6_MODEL", "qwen3.5")
OLLAMA = "http://127.0.0.1:11434/api/chat"
MODEL = "gpt-oss:120b-cloud"  # déporté : 0 token facturé, 0 chauffe M4
NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


# ─────────────────────────── socle ───────────────────────────


def notion_token() -> str:
    for line in NOTION_ENV.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        if key.strip() in ("NOTION_TOKEN", "NOTION_API_KEY"):
            return val.strip().strip("'\"")
    sys.exit(f"Aucun token dans {NOTION_ENV}")


def notion(method: str, path: str, payload: dict | None = None) -> dict:
    req = urllib.request.Request(
        f"{NOTION_API}{path}",
        method=method,
        data=json.dumps(payload).encode() if payload else None,
        headers={
            "Authorization": f"Bearer {notion_token()}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        },
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode()[:400]
            if exc.code in (429, 502, 503) and attempt < 3:
                time.sleep(2**attempt)
                continue
            raise RuntimeError(f"Notion {exc.code} sur {path} : {body}") from exc
    raise RuntimeError(f"Notion injoignable sur {path}")


def work_db() -> sqlite3.Connection:
    WORK_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(WORK_DB, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def formations() -> list[dict]:
    conn = sqlite3.connect(f"file:{SRC_DB}?mode=ro&immutable=1", uri=True)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT slug, titre, prix, categorie FROM formations ORDER BY prix DESC, categorie"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─────────────────────────── rédaction ───────────────────────────

PROMPT = """Tu es un formateur expert francophone. Rédige une formation COMPLÈTE et LIVRABLE.

Titre : {titre}
Catégorie : {categorie}
Prix de vente : {prix} €

Contraintes de rédaction :
- Français impeccable, accents obligatoires, ton direct et concret.
- Sortie en Markdown pur. Titres avec ##, sous-titres avec ###.
- Structure imposée :
  ## Présentation  (à qui s'adresse la formation, prérequis, ce qu'on saura faire à la fin)
  ## Objectifs pédagogiques  (6 à 8 objectifs mesurables, en liste)
  ## Module 1 … jusqu'à ## Module 6  — chaque module contient :
     ### Leçon (contenu RÉDIGÉ, 400 à 600 mots, avec exemples concrets et commandes/code réels)
     ### Exercice pratique  (énoncé précis)
     ### Corrigé  (solution complète et commentée)
  ## Ressources  (outils, liens, lectures)
  ## Évaluation finale  (10 questions + corrigés)
- Aucune phrase creuse, aucun remplissage marketing. Du contenu que l'acheteur peut appliquer immédiatement.
- Longueur cible : 4000 à 6000 mots.

Écris la formation maintenant, sans préambule ni commentaire sur ta démarche."""


def rediger_m6(f: dict) -> str:
    """Rédige sur LM Studio M6, sans reasoning-runaway.

    qwen3.5 ignore « /no_think » sur /chat/completions : il raisonne jusqu'à
    épuiser max_tokens et rend un `content` VIDE. Le seul remède éprouvé (déjà
    retenu dans board.py) passe par /v1/completions avec un prompt ChatML brut
    où le bloc <think></think> est DÉJÀ FERMÉ dans le tour de l'assistant — le
    modèle n'a plus d'endroit où raisonner et écrit directement sa réponse.
    """
    prompt = (
        "<|im_start|>system\nTu es un formateur expert francophone. Tu écris en "
        "français impeccable, accents obligatoires.<|im_end|>\n"
        f"<|im_start|>user\n{PROMPT.format(**f)}<|im_end|>\n"
        "<|im_start|>assistant\n<think></think>\n"
    )
    payload = {
        "model": M6_MODEL,
        "prompt": prompt,
        "max_tokens": 8000,
        "temperature": 0.6,
        "stop": ["<|im_end|>", "<|im_start|>"],
    }
    req = urllib.request.Request(
        M6_COMPLETIONS,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=1800) as resp:
        data = json.load(resp)
    contenu = data["choices"][0]["text"].strip()
    if len(contenu) < 1500:
        raise RuntimeError(f"contenu trop court ({len(contenu)} car.)")
    return contenu


def rediger(f: dict) -> str:
    if BACKEND == "m6":
        return rediger_m6(f)
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": PROMPT.format(**f)}],
        "stream": False,
        "think": False,
        "options": {"temperature": 0.6, "num_ctx": 16384},
    }
    req = urllib.request.Request(
        OLLAMA,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=900) as resp:
        data = json.load(resp)
    contenu = data.get("message", {}).get("content", "").strip()
    if len(contenu) < 1500:
        raise RuntimeError(f"contenu trop court ({len(contenu)} car.)")
    return contenu


# ─────────────────────────── Markdown → blocs Notion ───────────────────────────


def rich(texte: str) -> list[dict]:
    """Notion plafonne un rich_text à 2000 caractères."""
    return [
        {"type": "text", "text": {"content": texte[i : i + 1900]}}
        for i in range(0, max(len(texte), 1), 1900)
    ]


def md_vers_blocs(md: str) -> list[dict]:
    blocs: list[dict] = []
    dans_code, tampon_code = False, []

    for ligne in md.splitlines():
        if ligne.startswith("```"):
            if dans_code:
                blocs.append(
                    {
                        "object": "block",
                        "type": "code",
                        "code": {
                            "rich_text": rich("\n".join(tampon_code)[:1900]),
                            "language": "plain text",
                        },
                    }
                )
                tampon_code, dans_code = [], False
            else:
                dans_code = True
            continue
        if dans_code:
            tampon_code.append(ligne)
            continue

        nu = ligne.strip()
        if not nu:
            continue
        if nu.startswith("### "):
            blocs.append(
                {
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {"rich_text": rich(nu[4:])},
                }
            )
        elif nu.startswith("## "):
            blocs.append(
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": rich(nu[3:])},
                }
            )
        elif nu.startswith("# "):
            blocs.append(
                {
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {"rich_text": rich(nu[2:])},
                }
            )
        elif nu.startswith(("- ", "* ")):
            blocs.append(
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": rich(nu[2:])},
                }
            )
        else:
            blocs.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": rich(nu)},
                }
            )
    return blocs


# ─────────────────────────── étapes ───────────────────────────


def cmd_init_db() -> None:
    conn = work_db()
    conn.execute("""CREATE TABLE IF NOT EXISTS contenu (
        slug TEXT PRIMARY KEY, titre TEXT, prix INTEGER, categorie TEXT,
        markdown TEXT, mots INTEGER, notion_page_id TEXT,
        genere_le TEXT, pousse_le TEXT, erreur TEXT)""")
    conn.execute("CREATE TABLE IF NOT EXISTS meta (cle TEXT PRIMARY KEY, valeur TEXT)")
    for f in formations():
        conn.execute(
            "INSERT OR IGNORE INTO contenu(slug,titre,prix,categorie) VALUES(?,?,?,?)",
            (f["slug"], f["titre"], f["prix"], f["categorie"]),
        )
    conn.commit()

    existante = conn.execute(
        "SELECT valeur FROM meta WHERE cle='database_id'"
    ).fetchone()
    if existante:
        print(f"Base Notion déjà créée : {existante[0]}")
    else:
        cats = sorted({f["categorie"] for f in formations()})
        db = notion(
            "POST",
            "/databases",
            {
                "parent": {"type": "page_id", "page_id": HUB_PAGE_ID},
                "title": [
                    {
                        "type": "text",
                        "text": {"content": "🎓 Formations 2026 — catalogue livrable"},
                    }
                ],
                "properties": {
                    "Titre": {"title": {}},
                    "Catégorie": {"select": {"options": [{"name": c} for c in cats]}},
                    "Prix (€)": {"number": {"format": "euro"}},
                    "Statut": {
                        "select": {
                            "options": [
                                {"name": "Rédigée", "color": "green"},
                                {"name": "À rédiger", "color": "gray"},
                            ]
                        }
                    },
                    "Mots": {"number": {}},
                    "Slug": {"rich_text": {}},
                },
            },
        )
        conn.execute("INSERT INTO meta VALUES('database_id',?)", (db["id"],))
        conn.commit()
        print(f"Base Notion créée : {db['id']}")
    conn.close()


def cmd_generate(limit: int, workers: int) -> None:
    conn = work_db()
    restantes = conn.execute(
        "SELECT slug,titre,prix,categorie FROM contenu WHERE markdown IS NULL ORDER BY prix DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    if not restantes:
        print("Rien à rédiger.")
        return
    print(
        f"Rédaction de {len(restantes)} formations ({workers} en parallèle, {MODEL})…",
        flush=True,
    )

    def travail(row):
        f = {"slug": row[0], "titre": row[1], "prix": row[2], "categorie": row[3]}
        return f, rediger(f)

    fait = rate = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futurs = {pool.submit(travail, r): r for r in restantes}
        for fut in as_completed(futurs):
            slug = futurs[fut][0]
            c = work_db()
            try:
                f, md = fut.result()
                c.execute(
                    "UPDATE contenu SET markdown=?,mots=?,genere_le=datetime('now'),erreur=NULL "
                    "WHERE slug=?",
                    (md, len(md.split()), slug),
                )
                fait += 1
                print(f"  ✅ {slug} — {len(md.split())} mots", flush=True)
            except Exception as exc:  # noqa: BLE001 — on trace et on continue le lot
                c.execute(
                    "UPDATE contenu SET erreur=? WHERE slug=?", (str(exc)[:300], slug)
                )
                rate += 1
                print(f"  ❌ {slug} — {exc}", flush=True)
            c.commit()
            c.close()
    print(f"Rédigées : {fait} · échecs : {rate}")


def cmd_push(limit: int) -> None:
    conn = work_db()
    db_id = conn.execute("SELECT valeur FROM meta WHERE cle='database_id'").fetchone()
    if not db_id:
        sys.exit("Base Notion absente — lance d'abord init-db.")
    db_id = db_id[0]
    lot = conn.execute(
        "SELECT slug,titre,prix,categorie,markdown,mots FROM contenu "
        "WHERE markdown IS NOT NULL AND notion_page_id IS NULL ORDER BY prix DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    if not lot:
        print("Rien à pousser.")
        return

    for slug, titre, prix, cat, md, mots in lot:
        blocs = md_vers_blocs(md)
        page = notion(
            "POST",
            "/pages",
            {
                "parent": {"database_id": db_id},
                "properties": {
                    "Titre": {"title": [{"text": {"content": titre[:200]}}]},
                    "Catégorie": {"select": {"name": cat}},
                    "Prix (€)": {"number": prix},
                    "Statut": {"select": {"name": "Rédigée"}},
                    "Mots": {"number": mots},
                    "Slug": {"rich_text": [{"text": {"content": slug[:200]}}]},
                },
                "children": blocs[:100],
            },
        )
        for i in range(100, len(blocs), 100):  # Notion : 100 blocs par appel
            notion(
                "PATCH",
                f"/blocks/{page['id']}/children",
                {"children": blocs[i : i + 100]},
            )
        c = work_db()
        c.execute(
            "UPDATE contenu SET notion_page_id=?,pousse_le=datetime('now') WHERE slug=?",
            (page["id"], slug),
        )
        c.commit()
        c.close()
        print(f"  📤 {slug} → {len(blocs)} blocs", flush=True)


def cmd_status() -> None:
    conn = work_db()
    total, redigees, poussees, erreurs, mots = conn.execute(
        "SELECT count(*), count(markdown), count(notion_page_id), count(erreur), "
        "coalesce(sum(mots),0) FROM contenu"
    ).fetchone()
    print(f"Formations   : {total}")
    print(f"Rédigées     : {redigees}  ({mots} mots au total)")
    print(f"Dans Notion  : {poussees}")
    print(f"En erreur    : {erreurs}")
    for slug, err in conn.execute(
        "SELECT slug,erreur FROM contenu WHERE erreur IS NOT NULL LIMIT 5"
    ):
        print(f"   ❌ {slug} — {err[:120]}")
    conn.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("etape", choices=["init-db", "generate", "push", "status"])
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    {
        "init-db": lambda: cmd_init_db(),
        "generate": lambda: cmd_generate(args.limit, args.workers),
        "push": lambda: cmd_push(args.limit),
        "status": lambda: cmd_status(),
    }[args.etape]()


if __name__ == "__main__":
    main()
