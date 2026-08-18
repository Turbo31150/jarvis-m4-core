#!/usr/bin/env python3
"""guard_frontiers.py — rend les frontières EXÉCUTABLES et bloquantes (étape 8, plan v2).

Vérifie statiquement que le code respecte les 4 lois de frontières :
tout LLM -> agent (A1) · toute mémoire durable -> mem (A2) ·
tout web -> web (A3) · tout effet de bord -> publish (A4).

Principe : le manifeste config/frontiers.json déclare, par loi, les motifs
qui ne doivent apparaître QUE dans la brique propriétaire. Toute occurrence
ailleurs est une fuite de frontière.

Analyse par AST quand c'est un appel Python (pas par grep) : le mot
`urlopen` apparaît dans le docstring de webguard.py qui explique justement
pourquoi on ne s'en sert pas — un grep produirait un faux positif.

Sortie : JSON sur stdout + exit 0 (vert) / 1 (violation) — ratchet CI.
Stdlib uniquement.
"""

import ast
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BIN = os.path.join(ROOT, "bin")
FRONTIERS = os.path.join(ROOT, "config", "frontiers.json")
DAG = os.path.join(ROOT, "config", "dag.json")
PROC = os.path.join(ROOT, "scripts", "lib", "proc.py")


# Les 7 briques officielles (whitelist du launcher bin/jarvis). Les ~33 autres
# bin/jarvis-* sont des outils annexes NON routés par le launcher : les inclure
# noierait le guard sous des violations hors périmètre.
BRICKS = ("mail", "media", "board", "web", "publish", "agent", "mem", "deepsearch")


def _brick_of(path):
    """bin/jarvis-web -> 'web' ; None si ce n'est pas une des 7 briques."""
    name = os.path.basename(path)
    if not name.startswith("jarvis-"):
        return None
    brick = name[len("jarvis-") :]
    return brick if brick in BRICKS else None


def _calls_and_strings(path):
    """Retourne (appels qualifiés, littéraux str) d'un fichier Python, via AST."""
    try:
        tree = ast.parse(open(path, encoding="utf-8", errors="replace").read())
    except (SyntaxError, OSError):
        return set(), set()
    calls, strings = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            parts, cur = [], node.func
            while isinstance(cur, ast.Attribute):
                parts.append(cur.attr)
                cur = cur.value
            if isinstance(cur, ast.Name):
                parts.append(cur.id)
            if parts:
                calls.add(".".join(reversed(parts)))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            strings.add(node.value)
    return calls, strings


def check_frontiers(frontiers):
    """Une occurrence d'un motif hors de sa brique propriétaire = violation."""
    violations = []
    bricks = [
        os.path.join(BIN, f)
        for f in os.listdir(BIN)
        if f.startswith("jarvis-") and os.path.isfile(os.path.join(BIN, f))
    ]
    for path in bricks:
        brick = _brick_of(path)
        if brick is None:
            continue  # outil annexe, hors périmètre des 7 briques
        calls, strings = _calls_and_strings(path)
        if not calls and not strings:
            continue  # non-Python (shell) : hors périmètre de ce guard
        for law, spec in frontiers["lois"].items():
            owner = spec.get("brique")
            if not owner or brick == owner:
                continue
            if brick in spec.get("exempt_briques", []):
                continue
            # Un appel réseau vers le LOOPBACK n'est ni de l'ingestion web
            # (A3) ni un appel LLM externe : c'est de la supervision locale.
            # Ne le compter comme violation que si le fichier manipule au
            # moins une URL NON-loopback — sinon on aveuglerait le guard par
            # une exemption de brique, qui masquerait l'ingestion réelle.
            has_external_url = any(
                s.startswith(("http://", "https://"))
                and "127.0.0.1" not in s
                and "localhost" not in s
                for s in strings
            )
            # LIMITE ASSUMÉE de l'analyse statique : on voit les appels et les
            # littéraux, pas quel argument va à quel appel. Un fichier qui
            # acquiert l'externe via le gate (webguard.fetch) tout en gardant
            # urlopen pour des probes loopback est CONFORME — le signaler
            # serait un faux positif qui pousserait à exempter la brique,
            # donc à éteindre le capteur. Si le gate est utilisé, on fait
            # confiance au gate ; c'est lui qui porte la garantie SSRF.
            uses_gate = any(c.startswith("webguard.") for c in calls)
            for pat in spec.get("interdit_hors_brique", []):
                hit = pat in calls or any(pat in s for s in strings)
                if hit and law in ("A1", "A3") and (not has_external_url or uses_gate):
                    continue  # probes loopback, ou acquisition externe gatée
                if hit:
                    violations.append(
                        {
                            "loi": law,
                            "enonce": spec["enonce"],
                            "brique_fautive": brick,
                            "brique_proprietaire": owner,
                            "motif": pat,
                        }
                    )
    return violations


def check_dag_sync():
    """dag.json doit refléter proc.py:ADJ — sinon le manifeste ment."""
    if not os.path.exists(DAG):
        return [{"erreur": "config/dag.json absent"}]
    import importlib.util

    spec = importlib.util.spec_from_file_location("proc", PROC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    declared = json.load(open(DAG, encoding="utf-8"))["adjacence"]
    if declared != mod.ADJ:
        return [
            {
                "erreur": "dag.json désynchronisé de proc.py:ADJ",
                "indice": "régénérer config/dag.json",
            }
        ]
    return []


def main():
    if not os.path.exists(FRONTIERS):
        print(json.dumps({"ok": False, "erreur": "config/frontiers.json absent"}))
        return 1
    frontiers = json.load(open(FRONTIERS, encoding="utf-8"))
    violations = check_frontiers(frontiers) + check_dag_sync()
    ok = not violations
    print(
        json.dumps(
            {
                "ok": ok,
                "lois_verifiees": sorted(frontiers["lois"].keys()),
                "violations": violations,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
