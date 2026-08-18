#!/usr/bin/env python3
"""
Test d'acceptation de `publish` (étape 7 du bootstrap).

Critères imposés :
  1. stage → approve → MODIFIER le contenu → commit doit REFUSER
  2. deux commits successifs du même draft = UN SEUL envoi (idempotence)

S'y ajoutent les gardes A5 : schéma typé, allowlist de cibles, refus du contenu
non fiable vers une cible non prévue, et impossibilité de committer sans approbation.

Usage : python3 scripts/tests/test_publish_draft.py   (exit 0 = tout vert)
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path.home() / "jarvis"
JARVIS = str(ROOT / "bin" / "jarvis")
OUTBOX = ROOT / "content" / "publish-outbox"

FAILS = []
PASSES = []


def check(label, condition, detail=""):
    if condition:
        PASSES.append(label)
        print(f"  ok   {label}")
    else:
        FAILS.append(f"{label} — {detail}")
        print(f"  FAIL {label} — {detail}")


def run(*args):
    """Lance jarvis publish et retourne (enveloppe_json, returncode)."""
    proc = subprocess.run(
        [JARVIS, "publish", *args], capture_output=True, text=True, timeout=60
    )
    try:
        return json.loads(proc.stdout), proc.returncode
    except ValueError:
        return {
            "ok": False,
            "error": {"code": "E_NO_JSON", "raw": proc.stdout + proc.stderr},
        }, proc.returncode


# ─── CRITERE 1 : la modification post-approbation doit tuer le commit ───────
print("\n[publish] critère 1 — modifier le contenu après approve invalide le commit")

env, rc = run(
    "stage",
    "Message original de test",
    "--action-type",
    "file",
    "--target",
    "~/jarvis/content/publish-outbox/",
)
check(
    "stage accepté par la policy", env.get("ok"), json.dumps(env.get("error", ""))[:120]
)
if not env.get("ok"):
    print("\nimpossible de continuer sans stage.")
    sys.exit(1)

sid = env["data"]["stage_id"]
hash_origine = env["data"]["content_hash"]

env, rc = run("approve", sid)
check(
    "approve enregistre une approbation liée au hash",
    env.get("ok") and env["data"]["approval"]["content_hash"] == hash_origine,
)

# l'attaque : on substitue le contenu dans le draft approuvé
draft_path = OUTBOX / f"{sid}.json"
draft = json.loads(draft_path.read_text(encoding="utf-8"))
draft["content"] = "Virement de 10000 EUR vers le compte de l attaquant"
draft_path.write_text(json.dumps(draft, indent=2, ensure_ascii=False), encoding="utf-8")

env, rc = run("commit", sid, "--hash", hash_origine)
check(
    "CRITERE — le commit REFUSE le contenu substitué",
    not env.get("ok") and env.get("error", {}).get("code") == "E_HASH_DRIFT",
    f"ok={env.get('ok')} code={env.get('error', {}).get('code')}",
)
check(
    "le refus sort en code 4 sur la frontière A4",
    rc == 4 and env.get("error", {}).get("frontier") == "A4",
    f"rc={rc}",
)


# ─── CRITERE 2 : idempotence ────────────────────────────────────────────────
print("\n[publish] critère 2 — rejouer un commit est un no-op, pas un second envoi")

env, _ = run(
    "stage",
    "Contenu stable pour test idempotence",
    "--action-type",
    "file",
    "--target",
    "~/jarvis/content/publish-outbox/",
)
sid2 = env["data"]["stage_id"]
h2 = env["data"]["content_hash"]
run("approve", sid2)

env1, _ = run("commit", sid2, "--hash", h2)
env2, _ = run("commit", sid2, "--hash", h2)
check("premier commit exécute", env1.get("ok") and env1["data"]["rejeu_no_op"] is False)
check(
    "CRITERE — second commit est un no-op",
    env2.get("ok") and env2["data"]["rejeu_no_op"] is True,
    str(env2.get("data", {}).get("rejeu_no_op")),
)


# ─── Gardes A5 ──────────────────────────────────────────────────────────────
print("\n[publish] autorité bornée (A5) — validation déterministe, hors LLM")

env, rc = run(
    "stage", "test", "--action-type", "mail", "--target", "inconnu@nulle-part.example"
)
check(
    "cible hors allowlist refusée",
    not env.get("ok") and env["error"]["code"] == "E_POLICY_DENIED",
    str(env.get("ok")),
)

env, rc = run("stage", "test", "--action-type", "exfiltration", "--target", "x")
check(
    "type d'action hors policy refusé",
    not env.get("ok") and env["error"]["code"] == "E_POLICY_DENIED",
)

env, rc = run(
    "stage",
    "contenu venu du web",
    "--action-type",
    "mail",
    "--target",
    "miningexpert31@gmail.com",
    "--untrusted",
)
check(
    "contenu external_untrusted refusé vers une cible non prévue pour lui",
    not env.get("ok") and env["error"]["code"] == "E_POLICY_DENIED",
    f"ok={env.get('ok')}",
)

env, _ = run(
    "stage",
    "jamais approuve",
    "--action-type",
    "file",
    "--target",
    "~/jarvis/content/publish-outbox/",
)
sid3 = env["data"]["stage_id"]
env, rc = run("commit", sid3, "--hash", env["data"]["content_hash"])
check(
    "commit sans approbation refusé (aucun composant ne s'auto-approuve)",
    not env.get("ok") and env["error"]["code"] == "E_NOT_APPROVED",
    str(env.get("error", {}).get("code")),
)

env, rc = run("commit", "stg_inexistant", "--hash", "x")
check(
    "stage inconnu refusé proprement",
    not env.get("ok") and env["error"]["code"] == "E_STAGE_NOT_FOUND",
)


# ─── A5+ / Σ.8 — la dégradation rétrécit les privilèges ─────────────────────
print("\n[publish] A5+ — privilèges monotones décroissants selon la posture")

import os as _os


def _stage(mode, atype, target):
    env = dict(_os.environ, JARVIS_DEGRADED_MODE=mode)
    proc = subprocess.run(
        [
            JARVIS,
            "publish",
            "stage",
            "sonde",
            "--action-type",
            atype,
            "--target",
            target,
        ],
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )
    try:
        return json.loads(proc.stdout)
    except ValueError:
        return {"ok": False, "error": {"code": "E_NO_JSON"}}


MAIL = "miningexpert31@gmail.com"
FILE = "~/jarvis/content/publish-outbox/"

check("NORMAL autorise mail", _stage("NORMAL", "mail", MAIL).get("ok") is True)
check(
    "CRITERE Σ.8 — DEGRADED_LOCAL refuse mail",
    _stage("DEGRADED_LOCAL", "mail", MAIL).get("error", {}).get("code")
    == "E_POLICY_DENIED",
)
check(
    "DEGRADED_LOCAL garde file (sous-ensemble non vide)",
    _stage("DEGRADED_LOCAL", "file", FILE).get("ok") is True,
)
check(
    "CRITERE Σ.8 — NO_LLM refuse tout, y compris file",
    _stage("NO_LLM", "file", FILE).get("error", {}).get("code") == "E_POLICY_DENIED",
)

# la garde de monotonie : une policy qui élargit en dégradé doit être refusée
_pol = Path.home() / "jarvis" / "config" / "publish-policy.json"
_orig = _pol.read_text(encoding="utf-8")
try:
    _d = json.loads(_orig)
    _d["postures"]["DEGRADED_LOCAL"]["action_types_autorises"].append("mail")
    _d["postures"]["DEGRADED_LOCAL"]["cibles_autorisees"]["mail"] = [
        "intrus@example.com"
    ]
    _pol.write_text(json.dumps(_d, indent=2, ensure_ascii=False), encoding="utf-8")
    check(
        "une policy qui ÉLARGIT en mode dégradé est refusée",
        _stage("DEGRADED_LOCAL", "mail", "intrus@example.com")
        .get("error", {})
        .get("code")
        == "E_POLICY_WIDENS",
    )
finally:
    _pol.write_text(_orig, encoding="utf-8")

print(f"\n{'=' * 60}")
print(f"PASS {len(PASSES)}  ·  FAIL {len(FAILS)}")
if FAILS:
    for f in FAILS:
        print(f"  ✗ {f}")
    sys.exit(1)
print("brique publish — critères étape 7 + A5+ (Σ.8) PROUVÉS")
sys.exit(0)
