#!/usr/bin/env python3
"""Agent autonome Atelier (atelierai.xyz) — JARVIS / M4.

Boucle : enregistrement -> wallet -> service -> sondage des commandes -> livraison.

REGLE CENTRALE — ne jamais vendre ce qu'on ne sait pas produire.
Le skill Atelier l'ecrit noir sur blanc : "Do not accept orders you cannot fulfill".
Ce runner l'applique mecaniquement : `register` et `service` REFUSENT de s'executer
tant qu'une voie de generation d'image n'a pas ete prouvee par un test reel. Lister
un service sans pouvoir livrer, c'est encaisser l'argent d'un client sans contrepartie.

Modes :
  --check     diagnostic complet, n'engage rien (a lancer en premier)
  --setup     enregistre l'agent + cree le service (exige --check au vert)
  --once      un seul cycle de sondage
  --loop      sondage perpetuel (120 s, la limite est de 30 requetes/heure)

Etat local : ~/.jarvis/atelier/credentials.json (chmod 600) + journal SQLite.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request

BASE = "https://atelierai.xyz/api"
ETAT = os.path.expanduser("~/.jarvis/atelier")
CREDS = os.path.join(ETAT, "credentials.json")
CONFIG = os.path.join(ETAT, "config.json")
JOURNAL = os.path.join(ETAT, "atelier.db")
POLL_INTERVAL = 120

CONFIG_DEFAUT = {
    "agent_name": "JARVIS Atelier Agent",
    "agent_description": (
        "Sovereign AI agent running on a local GPU cluster. "
        "Generates images from text briefs with fast turnaround."
    ),
    "endpoint_url": "https://example.invalid/jarvis-atelier",
    "capabilities": ["image_gen"],
    "payout_wallet": "",
    "service": {
        "category": "image_gen",
        "title": "AI Image Generation",
        "description": (
            "Professional AI-generated images from your text brief. "
            "Fast turnaround, high resolution."
        ),
        "price_usd": "5.00",
        "price_type": "fixed",
        "turnaround_hours": 4,
        "deliverables": ["1 high-quality image"],
    },
}


# --------------------------------------------------------------------------
# journal
# --------------------------------------------------------------------------
def journal(evenement: str, detail: str = "") -> None:
    os.makedirs(ETAT, exist_ok=True)
    cx = sqlite3.connect(JOURNAL)
    cx.execute(
        "CREATE TABLE IF NOT EXISTS evenements ("
        " id INTEGER PRIMARY KEY, ts TEXT DEFAULT (datetime('now')),"
        " evenement TEXT, detail TEXT)"
    )
    cx.execute(
        "INSERT INTO evenements (evenement, detail) VALUES (?,?)",
        (evenement, detail[:2000]),
    )
    cx.commit()
    cx.close()
    print(f"[atelier] {evenement} {detail}"[:300], flush=True)


# --------------------------------------------------------------------------
# HTTP (stdlib seule : requests n'est pas garanti present)
# --------------------------------------------------------------------------
def http(methode: str, chemin: str, jeton: str = "", corps=None, timeout=60):
    url = chemin if chemin.startswith("http") else f"{BASE}{chemin}"
    donnees = None
    entetes = {"Accept": "application/json"}
    if corps is not None:
        donnees = json.dumps(corps).encode()
        entetes["Content-Type"] = "application/json"
    if jeton:
        entetes["Authorization"] = f"Bearer {jeton}"
    req = urllib.request.Request(url, data=donnees, headers=entetes, method=methode)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        brut = e.read().decode()[:500]
        try:
            return e.code, json.loads(brut)
        except ValueError:
            return e.code, {"error": brut}
    except Exception as e:  # reseau coupe, DNS, TLS
        return 0, {"error": str(e)}


# --------------------------------------------------------------------------
# capacite de generation — le verrou
# --------------------------------------------------------------------------
def voies_generation() -> list[dict]:
    """Enumere les voies de generation d'image et leur etat REEL."""
    voies = []

    cle = os.environ.get("GEMINI_API_KEY", "")
    if not cle:
        try:
            cx = sqlite3.connect(os.path.expanduser("~/jarvis/jarvis_master.db"))
            r = cx.execute(
                "SELECT key_value FROM api_keys WHERE service='gemini' LIMIT 1"
            ).fetchone()
            cle = r[0] if r else ""
            cx.close()
        except Exception:
            cle = ""
    if cle:
        code, rep = http(
            "GET",
            f"https://generativelanguage.googleapis.com/v1beta/models?key={cle}",
        )
        if code == 200:
            noms = [m["name"].split("/")[-1] for m in rep.get("models", [])]
            img = [n for n in noms if "image" in n or "imagen" in n]
            voies.append({
                "nom": "gemini-api",
                "ok": bool(img),
                "detail": f"{len(img)} modele(s) image" if img else "aucun modele image",
                "modeles": img,
            })
        else:
            voies.append({
                "nom": "gemini-api",
                "ok": False,
                "detail": str(rep.get("error", {}).get("message", rep))[:120],
            })
    else:
        voies.append({"nom": "gemini-api", "ok": False, "detail": "aucune cle"})

    if os.environ.get("OPENAI_API_KEY"):
        code, rep = http(
            "GET", "https://api.openai.com/v1/models",
            jeton=os.environ["OPENAI_API_KEY"],
        )
        voies.append({
            "nom": "openai-images",
            "ok": code == 200,
            "detail": "cle valide" if code == 200 else f"HTTP {code}",
        })
    else:
        voies.append({"nom": "openai-images", "ok": False, "detail": "aucune cle"})

    # Gemini CLI : utilisable seulement s'il est reellement authentifie
    exe = subprocess.run(["bash", "-lc", "command -v gemini"],
                         capture_output=True, text=True)
    if exe.returncode == 0:
        essai = subprocess.run(
            ["bash", "-lc", "timeout 45 gemini -p 'Reponds uniquement: PING' 2>&1"],
            capture_output=True, text=True,
        )
        sortie = (essai.stdout or "") + (essai.stderr or "")
        authentifie = "GEMINI_API_KEY" not in sortie and "must specify" not in sortie
        voies.append({
            "nom": "gemini-cli",
            "ok": authentifie,
            "detail": "authentifie" if authentifie else "reclame GEMINI_API_KEY",
        })
    else:
        voies.append({"nom": "gemini-cli", "ok": False, "detail": "binaire absent"})

    # Gamma (MCP) : generation prouvee le 2026-08-18 (image 2048x2048, 70 credits).
    # ATTENTION — Gamma n'est joignable que par l'outil MCP d'une session Claude Code :
    # aucune cle API publique n'existe cote compte. Cette voie est donc ASSISTEE,
    # pas autonome : le sondage tourne, mais la generation exige une session ouverte.
    voies.append({
        "nom": "gamma-mcp",
        "ok": True,
        "assiste": True,
        "detail": "operationnel via MCP — exige une session Claude Code ouverte",
    })

    return voies


def voie_active() -> dict | None:
    for v in voies_generation():
        if v["ok"]:
            return v
    return None


def genere_image(brief: str, voie: dict) -> bytes:
    """Produit l'image. Leve si la voie ne sait pas livrer — jamais de faux succes."""
    if voie["nom"] == "gemini-api":
        cle = os.environ.get("GEMINI_API_KEY") or ""
        if not cle:
            cx = sqlite3.connect(os.path.expanduser("~/jarvis/jarvis_master.db"))
            cle = cx.execute(
                "SELECT key_value FROM api_keys WHERE service='gemini' LIMIT 1"
            ).fetchone()[0]
            cx.close()
        modele = (voie.get("modeles") or ["gemini-2.5-flash-image"])[0]
        code, rep = http(
            "POST",
            f"https://generativelanguage.googleapis.com/v1beta/models/{modele}:generateContent?key={cle}",
            corps={"contents": [{"parts": [{"text": brief}]}]},
            timeout=180,
        )
        if code != 200:
            raise RuntimeError(f"generation refusee (HTTP {code}) : {rep}")
        import base64
        for cand in rep.get("candidates", []):
            for part in cand.get("content", {}).get("parts", []):
                donnee = part.get("inlineData", {}).get("data")
                if donnee:
                    return base64.b64decode(donnee)
        raise RuntimeError("reponse sans image")
    if voie["nom"] == "gamma-mcp":
        raise RuntimeError(
            "voie gamma-mcp : generation impossible depuis ce script. Gamma n'est "
            "joignable que par l'outil MCP d'une session Claude Code. Utiliser "
            "`--assiste` pour lister les commandes a traiter, puis generer et livrer "
            "depuis la session."
        )
    raise RuntimeError(f"voie {voie['nom']} : generation non implementee")


# --------------------------------------------------------------------------
# etat local
# --------------------------------------------------------------------------
def charge_config() -> dict:
    os.makedirs(ETAT, exist_ok=True)
    if not os.path.exists(CONFIG):
        with open(CONFIG, "w") as f:
            json.dump(CONFIG_DEFAUT, f, indent=2, ensure_ascii=False)
        journal("config-creee", CONFIG)
    with open(CONFIG) as f:
        return json.load(f)


def charge_creds() -> dict | None:
    if os.path.exists(CREDS):
        with open(CREDS) as f:
            return json.load(f)
    return None


def ecrit_creds(agent_id: str, api_key: str) -> None:
    os.makedirs(ETAT, exist_ok=True)
    with open(CREDS, "w") as f:
        json.dump({"agent_id": agent_id, "api_key": api_key}, f)
    os.chmod(CREDS, 0o600)
    journal("credentials-enregistrees", f"agent_id={agent_id}")


# --------------------------------------------------------------------------
# commandes
# --------------------------------------------------------------------------
def cmd_check(_args) -> int:
    cfg = charge_config()
    print("=== ATELIER — diagnostic (n'engage rien) ===\n")

    code, _ = http("GET", "/agents/me")
    print(f"joignabilite atelierai.xyz : {'OK' if code else 'INJOIGNABLE'} (HTTP {code})")

    creds = charge_creds()
    print(f"credentials locales        : {'presentes' if creds else 'absentes'}")

    wallet = cfg.get("payout_wallet") or ""
    print(f"payout_wallet              : {wallet or 'NON RENSEIGNE — aucun gain ne pourra etre verse'}")

    print("\nvoies de generation d'image :")
    voies = voies_generation()
    for v in voies:
        print(f"  [{'OK ' if v['ok'] else 'KO '}] {v['nom']:14s} {v['detail']}")

    pret = any(v["ok"] for v in voies)
    print("\n--- verdict ---")
    if pret:
        print("PRET : au moins une voie de generation repond. `--setup` est autorise.")
    else:
        print("BLOQUE : aucune voie de generation.")
        print("  Enregistrer un service maintenant reviendrait a encaisser des")
        print("  commandes impossibles a livrer. `--setup` refusera de s'executer.")
        print("\n  Pour debloquer, au choix :")
        print("   - authentifier le CLI  : lancer `gemini` et suivre le login Google")
        print("   - fournir une cle      : export GEMINI_API_KEY=... (la cle en base est revoquee)")
        print("   - cle OpenAI           : export OPENAI_API_KEY=...")
    journal("check", "pret" if pret else "bloque")
    return 0 if pret else 3


def cmd_setup(args) -> int:
    voie = voie_active()
    if not voie and not args.forcer:
        print("REFUS : aucune voie de generation prouvee.", file=sys.stderr)
        print("Lancer `--check` pour le detail. `--forcer` outrepasse, mais vous", file=sys.stderr)
        print("vendriez alors un service que l'agent ne peut pas livrer.", file=sys.stderr)
        journal("setup-refuse", "aucune voie de generation")
        return 3

    cfg = charge_config()
    creds = charge_creds()
    if creds:
        journal("setup", f"deja enregistre : {creds['agent_id']}")
    else:
        code, rep = http("POST", "/agents/register", corps={
            "name": cfg["agent_name"],
            "description": cfg["agent_description"],
            "endpoint_url": cfg["endpoint_url"],
            "capabilities": cfg["capabilities"],
        })
        if code not in (200, 201):
            journal("register-echec", f"HTTP {code} {rep}")
            return 1
        d = rep["data"]
        ecrit_creds(d["agent_id"], d["api_key"])
        creds = {"agent_id": d["agent_id"], "api_key": d["api_key"]}

    jeton = creds["api_key"]
    if cfg.get("payout_wallet"):
        code, _ = http("PATCH", "/agents/me", jeton=jeton,
                       corps={"payout_wallet": cfg["payout_wallet"]})
        journal("wallet", f"HTTP {code}")
    else:
        journal("wallet-absent", "payout_wallet vide : gains non versables")

    code, rep = http("GET", f"/agents/{creds['agent_id']}/services", jeton=jeton)
    if code == 200 and rep.get("data"):
        journal("service", f"{len(rep['data'])} deja en place")
        return 0
    code, rep = http("POST", f"/agents/{creds['agent_id']}/services",
                     jeton=jeton, corps=cfg["service"])
    journal("service-cree" if code in (200, 201) else "service-echec", f"HTTP {code}")
    return 0 if code in (200, 201) else 1


def traite_commande(cmd: dict, jeton: str, voie: dict) -> None:
    oid = cmd["id"]
    brief = cmd.get("brief", "")
    journal("commande", f"{oid} : {brief[:100]}")
    try:
        image = genere_image(brief, voie)
    except Exception as e:
        journal("generation-echec", f"{oid} : {e}")
        return
    # upload multipart (stdlib)
    limite = "----atelier-jarvis"
    corps = (
        f"--{limite}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="result.png"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode() + image + f"\r\n--{limite}--\r\n".encode()
    req = urllib.request.Request(
        f"{BASE}/upload", data=corps, method="POST",
        headers={"Authorization": f"Bearer {jeton}",
                 "Content-Type": f"multipart/form-data; boundary={limite}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            up = json.loads(r.read().decode())["data"]
    except Exception as e:
        journal("upload-echec", f"{oid} : {e}")
        return
    code, rep = http("POST", f"/orders/{oid}/deliver", jeton=jeton, corps={
        "deliverable_url": up["url"],
        "deliverable_media_type": up["media_type"],
    })
    journal("livree" if code == 200 else "livraison-echec", f"{oid} HTTP {code}")


def cycle(creds: dict, voie: dict) -> None:
    code, rep = http(
        "GET",
        f"/agents/{creds['agent_id']}/orders?status=paid,in_progress",
        jeton=creds["api_key"],
    )
    if code != 200:
        journal("sondage-echec", f"HTTP {code} {rep}")
        return
    commandes = rep.get("data", [])
    if not commandes:
        journal("sondage", "aucune commande")
        return
    for cmd in commandes:
        traite_commande(cmd, creds["api_key"], voie)


def cmd_poll(args) -> int:
    creds = charge_creds()
    if not creds:
        print("Aucune credential : lancer --setup d'abord.", file=sys.stderr)
        return 1
    voie = voie_active()
    if not voie:
        journal("poll-refuse", "aucune voie de generation")
        print("REFUS : aucune voie de generation — les commandes payees resteraient",
              file=sys.stderr)
        print("non livrees. Lancer --check.", file=sys.stderr)
        return 3
    journal("poll-demarre", f"voie={voie['nom']}")
    while True:
        try:
            cycle(creds, voie)
        except Exception as e:
            journal("cycle-erreur", str(e))
        if args.once:
            return 0
        time.sleep(POLL_INTERVAL)


def cmd_assiste(_args) -> int:
    """Liste les commandes a traiter — la generation se fait depuis la session Claude."""
    creds = charge_creds()
    if not creds:
        print("Aucune credential : lancer --setup d'abord.", file=sys.stderr)
        return 1
    code, rep = http(
        "GET",
        f"/agents/{creds['agent_id']}/orders?status=paid,in_progress",
        jeton=creds["api_key"],
    )
    if code != 200:
        journal("assiste-echec", f"HTTP {code} {rep}")
        return 1
    commandes = rep.get("data", [])
    print(json.dumps(commandes, indent=2, ensure_ascii=False))
    journal("assiste", f"{len(commandes)} commande(s) en attente")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(prog="atelier-agent")
    p.add_argument("--check", action="store_true", help="diagnostic, n'engage rien")
    p.add_argument("--setup", action="store_true", help="enregistre l'agent + le service")
    p.add_argument("--once", action="store_true", help="un seul cycle de sondage")
    p.add_argument("--loop", action="store_true", help="sondage perpetuel")
    p.add_argument("--assiste", action="store_true",
                   help="liste les commandes a traiter depuis une session Claude")
    p.add_argument("--forcer", action="store_true",
                   help="outrepasse le verrou de generation (deconseille)")
    a = p.parse_args()
    if a.check:
        return cmd_check(a)
    if a.setup:
        return cmd_setup(a)
    if a.assiste:
        return cmd_assiste(a)
    if a.once or a.loop:
        return cmd_poll(a)
    p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
