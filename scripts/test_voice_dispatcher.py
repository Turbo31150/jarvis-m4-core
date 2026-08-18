#!/usr/bin/env python3
"""
Tests du dispatcher vocal (voice_dispatcher.py).

Exécution :
    python3 -m pytest test_voice_dispatcher.py -v
    (ou, sans pytest :)   python3 test_voice_dispatcher.py

Aucun effet de bord réel : l'exécution shell / l'ouverture d'URL / le collage
sont MOCKÉS par injection de dépendances (runner / opener / paster). Les
commandes destructives ne sont donc jamais lancées.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import voice_dispatcher as vd  # noqa: E402


# ── 1. Chargement : les 432 (+ éventuels legacy) se chargent ──────────────────
def test_chargement_bibliotheque():
    lib = vd.load_library(use_cache=False)
    assert len(lib) >= 432, f"attendu >=432, obtenu {len(lib)}"
    # Toutes les entrées ont une clé normalisée non vide.
    assert all(c.get("_key") for c in lib.commands)


def test_retrocompat_legacy():
    """Les 21 commandes historiques restent matchables (présentes dans l'unifié)."""
    for phrase in ("ouvre le dashboard", "formule de politesse", "capture ecran"):
        assert vd.match(phrase) is not None, f"legacy perdue : {phrase}"


# ── 2. Matching robuste (transcription Whisper imparfaite) ────────────────────
def test_match_exact():
    c = vd.match("ouvre le dashboard")
    assert c and c["type"] == "url" and "8082" in c["action"]


def test_match_accents_et_casse():
    # accents + majuscules + ponctuation parasites
    c = vd.match("Ouvre le Dashboard !")
    assert c and "8082" in c["action"]


def test_match_mots_parasites():
    # « s'il te plaît » en trop après la clé
    c = vd.match("ouvre le dashboard s'il te plait")
    assert c and "8082" in c["action"]


def test_match_flou_transcription_approx():
    # faute de transcription légère sur un mot
    c = vd.match("ouvre le dashbord")  # 'dashbord' au lieu de 'dashboard'
    assert c is not None and "8082" in c["action"]


def test_pas_de_match_dictee_normale():
    # une vraie phrase de dictée ne doit PAS déclencher d'action
    assert vd.match("je voudrais écrire un mot aux parents demain matin") is None


# ── 3. Dispatch par type (mocké) ──────────────────────────────────────────────
def test_dispatch_url_mocke():
    opened = []
    c = {"command": "x", "type": "url", "action": "http://127.0.0.1:8082"}
    r = vd.dispatch(c, opener=opened.append)
    assert r.ok and r.executed and opened == ["http://127.0.0.1:8082"]


def test_dispatch_shell_sain_mocke():
    ran = []
    c = {"command": "temp gpu", "type": "shell", "action": "nvidia-smi"}
    r = vd.dispatch(c, runner=ran.append)
    assert r.ok and r.executed and ran == ["nvidia-smi"]


def test_dispatch_text_mocke():
    pasted = []
    c = {"command": "signature", "type": "text", "action": "Claire\nPE"}
    r = vd.dispatch(c, paster=pasted.append)
    assert r.ok and r.executed and pasted == ["Claire\nPE"]


def test_dispatch_web_url_mocke():
    opened = []
    c = {
        "command": "linkedin",
        "type": "web",
        "action": "https://www.linkedin.com/feed/",
    }
    r = vd.dispatch(c, opener=opened.append)
    assert r.ok and opened == ["https://www.linkedin.com/feed/"]


def test_dispatch_web_ancre_non_actionnable():
    opened = []
    c = {"command": "linkedin site", "type": "web", "action": "linkedin"}
    r = vd.dispatch(c, opener=opened.append)
    assert (not r.ok) and (not opened) and "ancre" in r.reason


def test_dispatch_action_non_implemente():
    c = {"command": "clone", "type": "action", "action": "clone"}
    r = vd.dispatch(c, index_path=Path("/inexistant/INDEX.json"))
    assert (not r.ok) and (not r.executed) and "non implémenté" in r.reason


# ── 4. Garde-fou sécurité : destructif bloqué, PAS exécuté ────────────────────
DESTRUCTIVE = [
    "rm -rf ~/Documents",
    "sudo rm -rf /",
    "dd if=/dev/zero of=/dev/sda",
    "mkfs.ext4 /dev/sda1",
    ":(){ :|:& };:",
    "shutdown -h now",
    "sudo apt install truc",
    "chmod -R 777 /",
    "echo x > /dev/sda",
]


def test_garde_fou_detecte_destructif():
    for c in DESTRUCTIVE:
        assert vd.is_dangerous(c), f"NON détecté comme dangereux : {c}"


def test_garde_fou_bloque_sans_executer():
    ran = []
    c = {"command": "purge", "type": "shell", "action": "sudo rm -rf ~/Documents"}
    r = vd.dispatch(c, runner=ran.append)
    assert r.blocked and (not r.executed) and ran == [], "destructif exécuté !"


def test_commandes_saines_non_bloquees():
    for safe in (
        "nvidia-smi",
        "gnome-terminal",
        "nautilus ~/Documents",
        "systemctl --user restart ollama",
        "xdg-open ~/labo/demo.mp4",
    ):
        assert not vd.is_dangerous(safe), f"faux positif : {safe}"


# ── 5. Dry-run : aucune exécution même sans mock ──────────────────────────────
def test_dry_run_n_execute_rien():
    c = {"command": "x", "type": "shell", "action": "nvidia-smi"}
    r = vd.dispatch(c, dry_run=True)
    assert r.ok and (not r.executed)


# ── 6. Pipeline haut niveau ───────────────────────────────────────────────────
def test_handle_phrase_end_to_end():
    opened = []
    r = vd.handle_phrase("ouvre le dashboard", opener=opened.append)
    assert r and r.ok and opened and "8082" in opened[0]


def test_handle_phrase_aucune_commande():
    assert vd.handle_phrase("un texte de dictée tout à fait quelconque ici") is None


def test_stats_coherentes():
    s = vd.stats()
    assert s["total"] >= 432
    assert s["by_type"].get("shell", 0) > 0
    assert 0 < s["actionable_direct"] <= s["total"]


# ── Runner autonome (sans pytest) ─────────────────────────────────────────────
if __name__ == "__main__":
    fns = [
        (n, f)
        for n, f in sorted(globals().items())
        if n.startswith("test_") and callable(f)
    ]
    passed = failed = 0
    for name, fn in fns:
        try:
            fn()
            print(f"  PASS  {name}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {name} :: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR {name} :: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed / {passed + failed} total")
    sys.exit(1 if failed else 0)
