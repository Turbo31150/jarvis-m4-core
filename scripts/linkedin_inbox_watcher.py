#!/usr/bin/env python3
"""
linkedin_inbox_watcher.py — Agent JARVIS surveillance LinkedIn inbox + réponse assistée.

Flux :
1. Scan inbox via Chrome CDP (port 9222) ou BrowserOS MCP (9239)
2. Détecte nouveaux messages non lus
3. Priorise expéditeurs (recruteurs, partenariats — Benjamin Sohler, Margot Banvillet)
4. Analyse contextuelle via LLM cluster (lm-ask.sh)
5. Génère réponse adaptée au type (factuel, opportunité, échange)
6. Mode --dry-run : affiche seulement (défaut)
7. Mode --send : envoie après validation (TBD)

Usage:
  python3 linkedin_inbox_watcher.py --dry-run
  python3 linkedin_inbox_watcher.py --send --confidence 0.85
"""

import argparse
import json
import logging
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ─── Config ─────────────────────────────────────────────────────────────
JARVIS_HOME = Path.home() / "jarvis"
REPORT_DIR = JARVIS_HOME / "reports" / "linkedin"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = JARVIS_HOME / "logs" / "linkedin_inbox.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

CDP_URL = "http://127.0.0.1:9222"
LINKEDIN_MSG_URL = "https://www.linkedin.com/messaging/"

# Profil Franck Delmas — identité
PROFILE = {
    "name": "Franck Delmas",
    "role": "Architecte IA / Agents",
    "tjm": 1150,
    "expertise": [
        "RAG",
        "CI/CD",
        "Agent Platform",
        "JARVIS OS",
        "617 handlers MCP",
        "Multi-agent orchestration",
    ],
    "language": "fr",
}

# Expéditeurs prioritaires (configurables)
PRIORITY_SENDERS = {
    "Benjamin Sohler": {"type": "opportunity", "context": "Mission technique IA"},
    "Margot Banvillet": {"type": "exchange", "context": "Partenariat / Win-Win"},
}

# Patterns de classification
PATTERNS = {
    "cv_request": [r"\b(cv|curriculum|résumé|portfolio)\b"],
    "availability": [r"\b(dispo|disponib|créneau|appel|call|tel|téléphone)\b"],
    "tjm_inquiry": [r"\b(tjm|taux|tarif|prix|jour|day rate)\b"],
    "tech_question": [r"\b(rag|llm|agent|mcp|orchestrat|architecture|infra)\b"],
    "partnership": [r"\b(partenariat|collaboration|win-win|échange|cross[- ]promo)\b"],
}

# ─── Logging ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("li-inbox")


# ─── Backends ────────────────────────────────────────────────────────────
def cdp_alive() -> bool:
    """Vérifie que Chrome CDP est joignable."""
    try:
        r = subprocess.run(
            [
                "curl",
                "-s",
                "-m",
                "2",
                "-o",
                "/dev/null",
                "-w",
                "%{http_code}",
                f"{CDP_URL}/json/version",
            ],
            capture_output=True,
            text=True,
            timeout=4,
        )
        return r.stdout.strip() == "200"
    except Exception:
        return False


def list_cdp_tabs() -> list[dict]:
    """Liste les onglets Chrome ouverts via CDP."""
    try:
        r = subprocess.run(
            ["curl", "-s", "-m", "3", f"{CDP_URL}/json/list"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return json.loads(r.stdout) if r.stdout else []
    except Exception as e:
        log.warning(f"CDP /json/list failed: {e}")
        return []


def find_linkedin_tab(tabs: list[dict]) -> dict | None:
    """Cherche l'onglet LinkedIn messaging dans les tabs CDP."""
    for t in tabs:
        url = t.get("url", "")
        if "linkedin.com" in url:
            return t
    return None


# ─── Classification & analyse ────────────────────────────────────────────
def classify_message(text: str) -> dict:
    """Classe un message en catégories sans LLM (regex)."""
    text_low = text.lower()
    tags = []
    for tag, patterns in PATTERNS.items():
        for p in patterns:
            if re.search(p, text_low):
                tags.append(tag)
                break
    return {"tags": tags, "length": len(text)}


def ask_llm(prompt: str, model_type: str = "fast", max_tokens: int = 600) -> str:
    """Délègue au cluster via lm-ask.sh."""
    script = Path.home() / "jarvis" / "scripts" / "lm-ask.sh"
    if not script.exists():
        log.warning("lm-ask.sh introuvable — réponse stub")
        return ""
    try:
        r = subprocess.run(
            [
                "bash",
                str(script),
                f"--{model_type}" if model_type != "fast" else "",
                "--max",
                str(max_tokens),
                prompt,
            ],
            capture_output=True,
            text=True,
            timeout=90,
        )
        return r.stdout.strip()
    except Exception as e:
        log.error(f"LLM call failed: {e}")
        return ""


# ─── Génération réponse ──────────────────────────────────────────────────
SYSTEM_PROMPT = (
    f"Tu es {PROFILE['name']}, {PROFILE['role']} freelance (TJM {PROFILE['tjm']}€/j). "
    f"Tu maîtrises: {', '.join(PROFILE['expertise'])}. "
    "Tu réponds aux messages LinkedIn de manière professionnelle, directe, en français. "
    "Mentionne la spécificité technique JARVIS OS uniquement si pertinent. "
    "Ne promets jamais d'engagement complexe sans validation préalable. "
    "Maximum 4 phrases, ton chaleureux mais expert."
)


def craft_reply(sender: str, message: str, classification: dict) -> dict:
    """Génère une réponse adaptée au contexte."""
    sender_meta = PRIORITY_SENDERS.get(sender, {"type": "generic", "context": ""})
    intent = sender_meta["type"]
    tags = classification["tags"]

    # Templates de base (avant LLM)
    if intent == "opportunity":
        seed = (
            f"Bonjour {sender.split()[0]}, merci pour votre message. "
            f"Le besoin correspond à mon expertise ({', '.join(PROFILE['expertise'][:3])}). "
            f"Je propose un créneau d'appel : mardi ou jeudi 14h-16h. "
            "Mon TJM cadre architecte IA est de 1150€/j."
        )
    elif intent == "exchange":
        seed = (
            f"Bonjour {sender.split()[0]}, votre proposition est notée. "
            "Je préfère valider la valeur mutuelle avant engagement — "
            "pouvez-vous préciser le périmètre, la cible et les bénéfices attendus pour chaque partie ?"
        )
    elif "cv_request" in tags:
        seed = (
            f"Bonjour, voici mon profil : architecte IA/Agents, "
            f"expertise {', '.join(PROFILE['expertise'][:3])}. "
            "Je vous envoie le CV en PJ dès réception de votre adresse mail."
        )
    elif "availability" in tags:
        seed = (
            "Bonjour, mes créneaux d'échange : mardi/jeudi 14h-16h cette semaine. "
            "Indiquez-moi votre préférence + numéro et je vous appelle."
        )
    elif "tjm_inquiry" in tags:
        seed = (
            f"Bonjour, mon TJM est de {PROFILE['tjm']}€/j pour des missions "
            "architecte IA/Agents (RAG, MCP, orchestration multi-agents). "
            "Adaptable selon durée + complexité."
        )
    else:
        # Demande LLM pour analyse contextuelle
        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"Message de {sender} sur LinkedIn:\n---\n{message[:1500]}\n---\n"
            f"Tags détectés: {', '.join(tags) or 'aucun'}\n"
            "Rédige UNIQUEMENT la réponse à envoyer (pas de préambule, pas de signature)."
        )
        seed = (
            ask_llm(prompt, model_type="fast", max_tokens=400)
            or f"Bonjour {sender.split()[0]}, merci pour votre message. Pouvez-vous préciser votre demande pour que je puisse vous répondre au mieux ?"
        )

    return {
        "intent": intent,
        "tags": tags,
        "draft": seed,
        "confidence": 0.95 if intent != "generic" else 0.65,
    }


# ─── Pipeline principal ──────────────────────────────────────────────────
def scan_inbox(dry_run: bool = True, confidence_threshold: float = 0.85) -> dict:
    """Scan principal LinkedIn inbox."""
    started = time.time()
    report = {
        "timestamp": datetime.now().isoformat(),
        "mode": "dry-run" if dry_run else f"send (threshold {confidence_threshold})",
        "messages_found": 0,
        "messages_priority": 0,
        "replies_drafted": [],
        "errors": [],
    }

    manual_input = Path("/tmp/linkedin_messages.json")
    has_mock = manual_input.exists()

    if not cdp_alive():
        report["errors"].append(
            f"Chrome CDP {CDP_URL} unreachable — lance BrowserOS/Chrome avec "
            "--remote-debugging-port=9222"
        )
        if not has_mock:
            return report
        log.info("CDP down mais input mock présent → continue en mode offline")
    else:
        tabs = list_cdp_tabs()
        li_tab = find_linkedin_tab(tabs)
        if not li_tab:
            report["errors"].append(
                f"Aucun onglet LinkedIn ouvert. Ouvre {LINKEDIN_MSG_URL}"
            )
            if not has_mock:
                return report
        else:
            log.info(
                f"LinkedIn tab found: {li_tab.get('title', '?')} → {li_tab.get('url')}"
            )
            report["linkedin_tab"] = li_tab.get("url")

    # NOTE: l'extraction des messages LinkedIn nécessite injection JS via CDP.
    # Cette V1 expose le squelette ; l'extraction réelle utilisera CDP Runtime.evaluate
    # ou BrowserOS MCP (port 9239) avec ses outils get_page_text / find / read_page.
    #
    # TODO V2:
    #  - via CDP Runtime.evaluate: scraper la liste des conversations (.msg-conversations-container__convo-item)
    #  - extraire pour chaque thread: sender, last_msg, unread_count
    #  - filter unread_count > 0
    #
    # Pour V1 : on lit un fichier d'input manuel /tmp/linkedin_messages.json si présent

    manual_input = Path("/tmp/linkedin_messages.json")
    if manual_input.exists():
        msgs = json.loads(manual_input.read_text())
        log.info(f"Loaded {len(msgs)} messages from manual input")
        for m in msgs:
            sender = m.get("sender", "Inconnu")
            text = m.get("text", "")
            report["messages_found"] += 1
            classification = classify_message(text)
            is_priority = (
                sender in PRIORITY_SENDERS or "tech_question" in classification["tags"]
            )
            if is_priority:
                report["messages_priority"] += 1
            reply = craft_reply(sender, text, classification)
            entry = {
                "sender": sender,
                "preview": text[:120],
                "classification": classification,
                "reply": reply,
                "would_send": (not dry_run)
                and reply["confidence"] >= confidence_threshold,
            }
            report["replies_drafted"].append(entry)
            log.info(f"  → {sender} [{reply['intent']}] conf={reply['confidence']:.2f}")
    else:
        report["errors"].append(
            "Pas d'input messages — créer /tmp/linkedin_messages.json "
            '(format: [{"sender":"...","text":"..."}]) '
            "OU implémenter CDP extraction (V2)"
        )

    report["duration_s"] = round(time.time() - started, 2)
    return report


def save_report(report: dict):
    """Sauvegarde rapport dans ~/jarvis/reports/linkedin/."""
    fname = f"inbox-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    fpath = REPORT_DIR / fname
    fpath.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    log.info(f"Report saved: {fpath}")
    return fpath


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Lecture seule, génère drafts (défaut)",
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help="Active l'envoi auto si confiance >= threshold",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.85,
        help="Seuil confiance pour envoi auto (défaut 0.85)",
    )
    parser.add_argument(
        "--once", action="store_true", default=True, help="Une seule passe (défaut)"
    )
    args = parser.parse_args()

    dry = not args.send
    log.info(
        f"Starting LinkedIn inbox watcher (mode={'send' if not dry else 'dry-run'})"
    )

    report = scan_inbox(dry_run=dry, confidence_threshold=args.confidence)
    save_report(report)

    # Affichage humain
    print("\n" + "═" * 60)
    print(f"  LinkedIn Inbox Watcher — {report['timestamp']}")
    print("═" * 60)
    print(f"  Messages trouvés : {report['messages_found']}")
    print(f"  Prioritaires     : {report['messages_priority']}")
    print(f"  Drafts rédigés   : {len(report['replies_drafted'])}")
    if report.get("errors"):
        print("  Erreurs :")
        for e in report["errors"]:
            print(f"    - {e}")
    for r in report["replies_drafted"]:
        s = r["sender"]
        print(
            f"\n  → {s} [{r['reply']['intent']}] conf={r['reply']['confidence']:.2f}"
            f" {'[ENVOYÉ]' if r['would_send'] else '[DRAFT]'}"
        )
        print(f"    Preview: {r['preview']}")
        print(f"    Draft  : {r['reply']['draft'][:200]}")
    print("═" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
