#!/usr/bin/env python3
"""
JARVIS Voice Dispatcher — module « application directe » (0-token, 100 % local)

Rôle : une phrase transcrite (Whisper, imparfaite) → la bonne commande de la
bibliothèque consolidée → exécution directe, avec garde-fou de sécurité.

Source de vérité : ~/jarvis/voice_commands_unified.json (432 actions).
Rétro-compatibilité : ~/jarvis/voice_commands.json (21 actions historiques) est
fusionné en repli (les entrées absentes de l'unifié sont ajoutées).

Format d'une entrée :
    {"command": "...", "type": "url|web|shell|action|text", "action": "...",
     "source": "..."}

Dispatch par type :
    url    → xdg-open (URL http/https ou fichier)
    web    → xdg-open si l'action est une URL, sinon logué « ancre non actionnable »
    shell  → subprocess (garde-fou : les commandes destructives sont BLOQUÉES + loguées)
    action → résolu via .actions/INDEX.json si présent, sinon logué « non implémenté »
    text   → collé au curseur (via un « paster » injecté par le widget)

Conçu pour être importé (par voice_widget.py) OU utilisé en CLI / testé isolément.
Toutes les fonctions d'exécution acceptent une injection de dépendances (runner,
opener, paster) pour permettre des tests sans effets de bord réels.
"""

from __future__ import annotations

import json
import re
import subprocess
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Callable, Optional

# ── Chemins ───────────────────────────────────────────────────────────────────
JARVIS_DIR = Path.home() / "jarvis"
UNIFIED_FILE = JARVIS_DIR / "voice_commands_unified.json"
LEGACY_FILE = JARVIS_DIR / "voice_commands.json"
ACTIONS_INDEX = JARVIS_DIR / ".actions" / "INDEX.json"
LOG_DIR = JARVIS_DIR / "voice_logs"
DISPATCH_LOG = LOG_DIR / "dispatcher.log"

# ── Garde-fou sécurité : motifs de commandes destructives (type=shell) ─────────
# Word-boundaries pour éviter les faux positifs (ex. « add », « middle »).
DANGEROUS_PATTERNS = [
    r"\brm\s+-[a-z]*[rf]",  # rm -rf, rm -fr, rm -r ...
    r"\brmdir\b",  # suppression de dossier
    r"\bdd\b\s+.*\bof=",  # dd if=... of=... (écrase un disque)
    r"\bmkfs(\.\w+)?\b",  # formatage
    r"\bmkswap\b",
    r"\bwipefs\b",
    r"\bfdisk\b|\bparted\b|\bsgdisk\b",
    r"\bsudo\b",  # élévation de privilèges → confirmation requise
    r"\bshutdown\b|\breboot\b|\bpoweroff\b|\bhalt\b",
    r"\bchmod\s+-R\b|\bchown\s+-R\b",
    r":\s*\(\s*\)\s*\{",  # fork bomb :(){ :|:& };:
    r">\s*/dev/(sd|nvme|mmcblk|disk)",  # écriture brute sur un périphérique bloc
    r"\bcrontab\s+-r\b",
    r"\buserdel\b|\bgroupdel\b|\bdeluser\b",
    r"\bkillall\b|\bpkill\s+-9\s+-1\b",
    r"\bgit\s+.*\b(reset\s+--hard|clean\s+-[a-z]*f|push\s+.*--force)",
]
_DANGER_RE = [re.compile(p, re.IGNORECASE) for p in DANGEROUS_PATTERNS]

# Seuil de similarité floue (matching approximatif) et écart max de longueur.
FUZZY_THRESHOLD = 0.82
MAX_EXTRA_WORDS = 4  # tolère les formules de politesse (« s'il te plaît » = 4 mots)


# ── Normalisation ─────────────────────────────────────────────────────────────
def normalize(text: str) -> str:
    """minuscules + accents supprimés (NFKD) + ponctuation → espaces + espaces réduits.

    Reprend la logique de commander.py (unicodedata) — plus complète que la table
    manuelle historique (gère œ, æ, ü, toutes les combinaisons)."""
    if not text:
        return ""
    text = text.lower().strip()
    nfkd = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in nfkd if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


# ── Modèle ────────────────────────────────────────────────────────────────────
@dataclass
class DispatchResult:
    """Résultat d'un dispatch — sérialisable, testable, sans effet de bord implicite."""

    ok: bool
    label: str  # libellé court pour l'affichage widget (⚡ ...)
    type: str = ""
    action: str = ""
    executed: bool = False  # l'action a-t-elle réellement été lancée ?
    blocked: bool = False  # bloquée par le garde-fou sécurité ?
    reason: str = ""  # explication (erreur, blocage, non implémenté)


@dataclass
class CommandLibrary:
    """Bibliothèque de commandes chargée + index normalisé pour le matching."""

    commands: list[dict] = field(default_factory=list)

    def __post_init__(self):
        for c in self.commands:
            c.setdefault("_key", normalize(c.get("command", "")))

    def __len__(self) -> int:
        return len(self.commands)


# ── Chargement (unifié + repli legacy, cache sur mtime) ────────────────────────
_cache: dict = {"sig": None, "lib": None}


def _read_json(path: Path) -> list[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def load_library(
    unified: Path = UNIFIED_FILE, legacy: Path = LEGACY_FILE, use_cache: bool = True
) -> CommandLibrary:
    """Charge l'unifié (432) puis complète avec le legacy (21) pour les entrées
    dont la clé normalisée est absente. Cache invalidé sur mtime des deux fichiers."""
    sig = tuple(
        (p, p.stat().st_mtime if p.exists() else None) for p in (unified, legacy)
    )
    if use_cache and _cache["sig"] == sig and _cache["lib"] is not None:
        return _cache["lib"]

    entries = _read_json(unified)
    seen = {normalize(c.get("command", "")) for c in entries}
    # Rétro-compatibilité : n'ajouter du legacy que ce qui manque.
    for c in _read_json(legacy):
        k = normalize(c.get("command", ""))
        if k and k not in seen:
            entries.append(c)
            seen.add(k)

    entries = [c for c in entries if normalize(c.get("command", ""))]
    lib = CommandLibrary(entries)
    if use_cache:
        _cache["sig"], _cache["lib"] = sig, lib
    return lib


# ── Matching robuste (exact → préfixe toléré → flou) ──────────────────────────
def match(text: str, lib: Optional[CommandLibrary] = None) -> Optional[dict]:
    """Retourne la commande correspondant le mieux à la phrase transcrite, ou None.

    Stratégie (du plus sûr au plus permissif) :
      1. Égalité normalisée exacte.
      2. La phrase = clé + jusqu'à MAX_EXTRA_WORDS mots en plus (préfixe OU suffixe).
      3. Similarité floue (difflib) ≥ FUZZY_THRESHOLD sur les phrases assez longues.
    Le flou n'est autorisé que pour les clés ≥ 2 mots (évite qu'un mot isolé mal
    transcrit ne déclenche une action au milieu d'une vraie dictée)."""
    lib = lib or load_library()
    key = normalize(text)
    if not key:
        return None
    words = key.split()

    best_fuzzy: tuple[float, Optional[dict]] = (0.0, None)

    for c in lib.commands:
        ck = c.get("_key") or normalize(c.get("command", ""))
        if not ck:
            continue
        if key == ck:
            return c
        ckw = ck.split()
        # Préfixe/suffixe toléré : la dictée contient la clé + quelques mots parasites.
        extra = len(words) - len(ckw)
        if 0 < extra <= MAX_EXTRA_WORDS:
            if words[: len(ckw)] == ckw or words[-len(ckw) :] == ckw:
                return c
        # Flou : seulement pour clés multi-mots (sécurité anti-faux-déclenchement).
        if len(ckw) >= 2:
            ratio = SequenceMatcher(None, key, ck).ratio()
            if ratio > best_fuzzy[0]:
                best_fuzzy = (ratio, c)

    if best_fuzzy[0] >= FUZZY_THRESHOLD:
        return best_fuzzy[1]
    return None


# ── Sécurité ──────────────────────────────────────────────────────────────────
def is_dangerous(command: str) -> bool:
    """True si la commande shell contient un motif destructif connu."""
    if not command:
        return False
    return any(rx.search(command) for rx in _DANGER_RE)


def _log(line: str) -> None:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(DISPATCH_LOG, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat(timespec='seconds')} {line}\n")
    except Exception:
        pass


# ── Résolution des actions (type=action) ──────────────────────────────────────
def _resolve_action(action_id: str, index_path: Path = ACTIONS_INDEX) -> Optional[list]:
    """Retourne la liste des handlers déclarés pour un id dans .actions/INDEX.json,
    ou None si l'index/l'entrée n'existe pas."""
    if not index_path.exists():
        return None
    try:
        idx = json.loads(index_path.read_text(encoding="utf-8")).get("index", {})
        return idx.get(action_id)
    except Exception:
        return None


# ── Dispatch ──────────────────────────────────────────────────────────────────
def dispatch(
    cmd: dict,
    *,
    dry_run: bool = False,
    runner: Optional[Callable[[str], None]] = None,
    opener: Optional[Callable[[str], None]] = None,
    paster: Optional[Callable[[str], None]] = None,
    index_path: Path = ACTIONS_INDEX,
) -> DispatchResult:
    """Exécute une commande selon son type. Dépendances injectables pour les tests.

    - runner(cmd_str)  : lance une commande shell (défaut : subprocess, détaché)
    - opener(url_str)  : ouvre une URL/fichier   (défaut : xdg-open)
    - paster(text_str) : colle du texte au curseur (défaut : no-op ; le widget fournit)
    En dry_run, aucun effet réel : on renvoie l'intention (executed=False)."""
    typ = (cmd.get("type") or "shell").lower()
    action = str(cmd.get("action", "") or "")  # certaines metadata web sont non-str
    label = (cmd.get("command") or action)[:40]

    def _default_runner(c: str) -> None:
        subprocess.Popen(
            c, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

    def _default_opener(u: str) -> None:
        subprocess.Popen(
            ["xdg-open", u], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

    runner = runner or _default_runner
    opener = opener or _default_opener

    # ── url ────────────────────────────────────────────────────────────────
    if typ == "url":
        if dry_run:
            return DispatchResult(True, f"⚡ {label}", typ, action)
        try:
            opener(action)
            return DispatchResult(True, f"⚡ {label}", typ, action, executed=True)
        except Exception as e:
            _log(f"[url ERR] {action} :: {e}")
            return DispatchResult(False, f"[err {label}]", typ, action, reason=str(e))

    # ── web ────────────────────────────────────────────────────────────────
    if typ == "web":
        if re.match(r"^https?://", action):
            if dry_run:
                return DispatchResult(True, f"⚡ {label}", typ, action)
            try:
                opener(action)
                return DispatchResult(True, f"⚡ {label}", typ, action, executed=True)
            except Exception as e:
                _log(f"[web ERR] {action} :: {e}")
                return DispatchResult(
                    False, f"[err {label}]", typ, action, reason=str(e)
                )
        # Ancre / sélecteur non-URL : non actionnable en ouverture directe.
        _log(f"[web SKIP] ancre non actionnable : {cmd.get('command')} → {action}")
        return DispatchResult(
            False,
            f"↷ {label} (ancre)",
            typ,
            action,
            reason="ancre web non actionnable (pas une URL)",
        )

    # ── shell (avec garde-fou) ──────────────────────────────────────────────
    if typ == "shell":
        if is_dangerous(action):
            _log(f"[shell BLOCKED] {cmd.get('command')} :: {action}")
            return DispatchResult(
                False,
                f"⛔ bloqué : {label}",
                typ,
                action,
                blocked=True,
                reason="commande destructive bloquée par le garde-fou",
            )
        if dry_run:
            return DispatchResult(True, f"⚡ {label}", typ, action)
        try:
            runner(action)
            return DispatchResult(True, f"⚡ {label}", typ, action, executed=True)
        except Exception as e:
            _log(f"[shell ERR] {action} :: {e}")
            return DispatchResult(False, f"[err {label}]", typ, action, reason=str(e))

    # ── text ────────────────────────────────────────────────────────────────
    if typ == "text":
        if dry_run or paster is None:
            reason = "" if paster else "aucun paster fourni"
            return DispatchResult(
                bool(paster) and not dry_run, f"⚡ {label}", typ, action, reason=reason
            )
        try:
            paster(action)
            return DispatchResult(True, f"⚡ {label}", typ, action, executed=True)
        except Exception as e:
            _log(f"[text ERR] :: {e}")
            return DispatchResult(False, f"[err {label}]", typ, action, reason=str(e))

    # ── action (résolution via INDEX.json) ──────────────────────────────────
    if typ == "action":
        handlers = _resolve_action(action, index_path)
        if handlers:
            # Un moteur d'exécution d'actions n'existe pas encore côté widget : on
            # loggue la résolution mais on n'invente pas d'exécution silencieuse.
            _log(f"[action RESOLVED-NOEXEC] {action} → {handlers}")
            return DispatchResult(
                False,
                f"↷ {label} (action connue)",
                typ,
                action,
                reason=f"action résolue ({handlers}) mais moteur non branché",
            )
        _log(f"[action UNIMPL] {action}")
        return DispatchResult(
            False,
            f"↷ {label} (non impl.)",
            typ,
            action,
            reason="type=action non implémenté (pas d'INDEX.json actif)",
        )

    # ── type inconnu ────────────────────────────────────────────────────────
    _log(f"[type INCONNU] {typ} :: {cmd.get('command')}")
    return DispatchResult(
        False, f"↷ {label} (?)", typ, action, reason=f"type inconnu : {typ}"
    )


# ── API haut niveau ───────────────────────────────────────────────────────────
def handle_phrase(text: str, **kw) -> Optional[DispatchResult]:
    """Phrase transcrite → matching → dispatch. None si aucune commande ne matche
    (le widget écrit alors le texte normalement). kw = options passées à dispatch()."""
    cmd = match(text)
    if cmd is None:
        return None
    return dispatch(cmd, **kw)


def stats() -> dict:
    """Compteurs pour diagnostic (nb total + par type + actionnables)."""
    lib = load_library()
    by_type: dict[str, int] = {}
    actionable = 0
    for c in lib.commands:
        t = (c.get("type") or "shell").lower()
        by_type[t] = by_type.get(t, 0) + 1
        if t in ("url", "text"):
            actionable += 1
        elif t == "shell" and not is_dangerous(c.get("action", "")):
            actionable += 1
        elif t == "web" and re.match(r"^https?://", str(c.get("action", "") or "")):
            actionable += 1
    return {"total": len(lib), "by_type": by_type, "actionable_direct": actionable}


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        phrase = " ".join(sys.argv[1:])
        c = match(phrase)
        if c is None:
            print(f"(aucune commande) : {phrase!r}")
        else:
            r = dispatch(c, dry_run=True)
            print(f"MATCH : {c.get('command')!r} [{r.type}] → {r.action}")
            print(f"  {'OK' if r.ok else 'NON-EXEC'} · {r.reason or r.label}")
    else:
        s = stats()
        print(json.dumps(s, ensure_ascii=False, indent=2))
