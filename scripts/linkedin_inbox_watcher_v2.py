#!/usr/bin/env python3
"""
linkedin_inbox_watcher_v2.py — Agent JARVIS LinkedIn inbox V2
Surveillance + réponse automatisée avec CDP réel + automatisations avancées.

Améliorations V2 :
- Extraction réelle DOM LinkedIn via CDP WebSocket (linkedin_cdp_client)
- Envoi réponse via injection JS (execCommand insertText + click envoi)
- Mode --send avec seuil confiance
- Heures ouvrées configurables (9h-19h Lun-Ven par défaut)
- Telegram alert pour messages prioritaires
- SQLite history (anti-doublon + apprentissage)
- Multi-LLM fallback via lm-ask.sh
- Auto-tagging recruteurs (mots-clés profil)
- Stats hebdo

Usage :
  python3 linkedin_inbox_watcher_v2.py --dry-run
  python3 linkedin_inbox_watcher_v2.py --send --confidence 0.95
  python3 linkedin_inbox_watcher_v2.py --send --continuous --interval 900
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, time as dtime
from pathlib import Path

# Import du module CDP (même dir)
sys.path.insert(0, str(Path(__file__).parent))
try:
    from linkedin_cdp_client import (
        linkedin_session,
        extract_inbox_messages,
        open_conversation,
        read_conversation_messages,
        send_reply_via_cdp,
    )

    CDP_AVAILABLE = True
except ImportError as e:
    CDP_AVAILABLE = False
    _CDP_ERR = str(e)


# ─── Config ─────────────────────────────────────────────────────────────
JARVIS_HOME = Path.home() / "jarvis"
REPORT_DIR = JARVIS_HOME / "reports" / "linkedin"
LOG_FILE = JARVIS_HOME / "logs" / "linkedin_inbox.log"
DB_FILE = JARVIS_HOME / "data" / "linkedin_history.sqlite"
for p in [REPORT_DIR, LOG_FILE.parent, DB_FILE.parent]:
    p.mkdir(parents=True, exist_ok=True)

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
    "calendar_slots": "mardi/jeudi 14h-16h",
}

PRIORITY_SENDERS = {
    "Benjamin Sohler": {"type": "opportunity"},
    "Margot Banvillet": {"type": "exchange"},
}

# Mots-clés détection recruteur dans le preview/profil
RECRUITER_KEYWORDS = [
    "talent acquisition",
    "talent recruiter",
    "tech recruiter",
    "freelance",
    "consultant",
    "hiring",
    "recrutement",
    "head hunter",
    "headhunter",
    "tjm",
    "mission",
    "régie",
    "intercontrat",
    "staffing",
]

# Heures ouvrées (envoi auto)
BUSINESS_HOURS = (dtime(9, 0), dtime(19, 0))  # 9h-19h
BUSINESS_DAYS = {0, 1, 2, 3, 4}  # Lun-Ven (0=Lun)

PATTERNS = {
    "cv_request": [r"\b(cv|curriculum|résumé|portfolio|profil)\b"],
    "availability": [r"\b(dispo|disponib|créneau|appel|call|tel|téléphone|meeting)\b"],
    "tjm_inquiry": [r"\b(tjm|taux|tarif|prix|jour|day rate|rate)\b"],
    "tech_question": [r"\b(rag|llm|agent|mcp|orchestrat|architecture|infra|ia|ai)\b"],
    "partnership": [r"\b(partenariat|collaboration|win-win|échange|cross[- ]promo)\b"],
    "spam": [r"\b(crypto|nft|forex|webinar gratuit|formation 100%)\b"],
}

# Telegram (optionnel)
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID", "")


# ─── Logging ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("li-inbox-v2")


# ─── Database (history + anti-doublon + learning) ───────────────────────
def db_init():
    conn = sqlite3.connect(DB_FILE)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            sender TEXT NOT NULL,
            preview TEXT,
            tags TEXT,
            intent TEXT,
            confidence REAL,
            draft TEXT,
            sent INTEGER DEFAULT 0,
            user_validated INTEGER DEFAULT 0,
            sender_hash TEXT,
            UNIQUE(sender, preview, ts)
        );
        CREATE TABLE IF NOT EXISTS stats (
            week TEXT PRIMARY KEY,
            messages_seen INTEGER DEFAULT 0,
            priority_seen INTEGER DEFAULT 0,
            sent_auto INTEGER DEFAULT 0,
            sent_human INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS recruiters (
            sender TEXT PRIMARY KEY,
            first_seen TEXT,
            score INTEGER DEFAULT 0,
            notes TEXT
        );
    """)
    conn.commit()
    return conn


def already_processed(conn, sender: str, preview: str) -> bool:
    cur = conn.execute(
        "SELECT 1 FROM messages WHERE sender=? AND substr(preview,1,80)=substr(?,1,80) LIMIT 1",
        (sender, preview),
    )
    return cur.fetchone() is not None


def record_message(conn, msg: dict):
    conn.execute(
        """INSERT OR IGNORE INTO messages
           (ts, sender, preview, tags, intent, confidence, draft, sent)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            datetime.now().isoformat(),
            msg["sender"],
            msg["preview"][:500],
            ",".join(msg["tags"]),
            msg["intent"],
            msg["confidence"],
            msg["draft"][:1500],
            1 if msg.get("sent") else 0,
        ),
    )
    conn.commit()


def bump_recruiter_score(conn, sender: str, delta: int = 1, note: str = ""):
    conn.execute(
        """INSERT INTO recruiters (sender, first_seen, score, notes)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(sender) DO UPDATE SET score = score + excluded.score,
                                              notes = CASE WHEN excluded.notes='' THEN notes ELSE excluded.notes END""",
        (sender, datetime.now().isoformat(), delta, note),
    )
    conn.commit()


# ─── Classification ──────────────────────────────────────────────────────
def classify(text: str, sender: str = "") -> dict:
    combined = f"{sender} {text}".lower()
    tags = []
    for tag, patterns in PATTERNS.items():
        for p in patterns:
            if re.search(p, combined):
                tags.append(tag)
                break
    is_recruiter = any(k in combined for k in RECRUITER_KEYWORDS)
    if is_recruiter:
        tags.append("recruiter")
    return {"tags": tags, "is_recruiter": is_recruiter}


# ─── LLM ────────────────────────────────────────────────────────────────
def ask_llm(prompt: str, model_type: str = "fast", max_tokens: int = 600) -> str:
    script = Path.home() / "jarvis" / "scripts" / "lm-ask.sh"
    if not script.exists():
        return ""
    flag = "" if model_type == "fast" else f"--{model_type}"
    try:
        cmd = ["bash", str(script)]
        if flag:
            cmd.append(flag)
        cmd += ["--max", str(max_tokens), prompt]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        return r.stdout.strip()
    except Exception as e:
        log.error(f"LLM failed: {e}")
        return ""


SYSTEM_PROMPT = (
    f"Tu es {PROFILE['name']}, {PROFILE['role']} freelance (TJM {PROFILE['tjm']}€/j). "
    f"Expertise: {', '.join(PROFILE['expertise'])}. "
    "Réponse LinkedIn professionnelle, française, max 4 phrases. "
    "Ne promets jamais d'engagement complexe sans accord."
)


# ─── Génération réponse ──────────────────────────────────────────────────
def craft_reply(sender: str, message: str, classification: dict) -> dict:
    sender_meta = PRIORITY_SENDERS.get(sender)
    tags = classification["tags"]

    if "spam" in tags:
        return {"intent": "spam", "draft": "", "confidence": 0.0, "skip": True}

    intent = sender_meta["type"] if sender_meta else "generic"
    if classification["is_recruiter"] and intent == "generic":
        intent = "recruiter"

    first = sender.split()[0] if sender else ""

    if intent == "opportunity":
        draft = (
            f"Bonjour {first}, merci pour votre message. "
            f"Le besoin colle à mon expertise ({', '.join(PROFILE['expertise'][:3])}). "
            f"Créneau d'appel : {PROFILE['calendar_slots']}. "
            f"Mon TJM cadre architecte IA est de {PROFILE['tjm']}€/j."
        )
        conf = 0.96
    elif intent == "exchange":
        draft = (
            f"Bonjour {first}, votre proposition est notée. "
            "Avant tout engagement, pouvez-vous préciser le périmètre, "
            "la cible et les bénéfices attendus pour chaque partie ?"
        )
        conf = 0.94
    elif intent == "recruiter":
        draft = (
            f"Bonjour {first}, merci pour votre message. "
            f"Mon profil : architecte IA/Agents — {', '.join(PROFILE['expertise'][:3])}. "
            f"TJM {PROFILE['tjm']}€/j. Dispo pour échange : {PROFILE['calendar_slots']}."
        )
        conf = 0.90
    elif "cv_request" in tags:
        draft = (
            f"Bonjour {first}, voici mon profil : architecte IA/Agents, "
            f"expertise {', '.join(PROFILE['expertise'][:3])}. "
            "Je vous envoie le CV en PJ dès réception de votre adresse email."
        )
        conf = 0.92
    elif "availability" in tags:
        draft = (
            f"Bonjour {first}, mes créneaux d'échange : {PROFILE['calendar_slots']}. "
            "Indiquez-moi votre préférence et votre numéro, je vous appelle."
        )
        conf = 0.90
    elif "tjm_inquiry" in tags:
        draft = (
            f"Bonjour {first}, mon TJM est de {PROFILE['tjm']}€/j pour des missions "
            "architecte IA/Agents (RAG, MCP, orchestration multi-agents). "
            "Adaptable selon durée et complexité."
        )
        conf = 0.90
    else:
        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"Message LinkedIn reçu de {sender} :\n---\n{message[:1500]}\n---\n"
            f"Tags : {', '.join(tags) or 'aucun'}\n"
            "Rédige UNIQUEMENT la réponse (pas de préambule, pas de signature)."
        )
        draft = ask_llm(prompt, "fast", 400) or (
            f"Bonjour {first}, merci pour votre message. "
            "Pouvez-vous préciser votre demande pour que je puisse vous répondre au mieux ?"
        )
        conf = 0.65

    return {"intent": intent, "draft": draft, "confidence": conf}


# ─── Heures ouvrées ──────────────────────────────────────────────────────
def in_business_hours() -> bool:
    now = datetime.now()
    if now.weekday() not in BUSINESS_DAYS:
        return False
    t = now.time()
    return BUSINESS_HOURS[0] <= t <= BUSINESS_HOURS[1]


# ─── Telegram ────────────────────────────────────────────────────────────
def tg_notify(text: str):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        return
    try:
        import urllib.parse
        import urllib.request

        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
        data = urllib.parse.urlencode(
            {"chat_id": TG_CHAT_ID, "text": text[:4000], "parse_mode": "HTML"}
        ).encode()
        urllib.request.urlopen(url, data=data, timeout=5)
    except Exception as e:
        log.warning(f"TG notify failed: {e}")


# ─── Pipeline ────────────────────────────────────────────────────────────
def process_inbox(send: bool, confidence_threshold: float) -> dict:
    started = time.time()
    conn = db_init()
    report = {
        "timestamp": datetime.now().isoformat(),
        "mode": "SEND" if send else "DRY-RUN",
        "business_hours": in_business_hours(),
        "messages_seen": 0,
        "priority_seen": 0,
        "skipped_known": 0,
        "drafts": [],
        "sent": [],
        "errors": [],
    }

    if not CDP_AVAILABLE:
        report["errors"].append(f"CDP module missing: {_CDP_ERR}")
        return _finalize(report, started)

    try:
        with linkedin_session() as sess:
            inbox = extract_inbox_messages(sess)
            if not inbox:
                report["errors"].append(
                    "Aucune conversation extraite — pas loggé LinkedIn dans Chrome ?"
                )
                # Fallback mock si présent
                mock = Path("/tmp/linkedin_messages.json")
                if mock.exists():
                    log.info("Fallback sur mock /tmp/linkedin_messages.json")
                    inbox = [
                        {
                            "sender": m["sender"],
                            "preview": m["text"],
                            "unread": True,
                            "idx": i,
                        }
                        for i, m in enumerate(json.loads(mock.read_text()))
                    ]

            for conv in inbox:
                if not conv["unread"]:
                    continue
                report["messages_seen"] += 1
                sender = conv["sender"]
                preview = conv["preview"]

                if already_processed(conn, sender, preview):
                    report["skipped_known"] += 1
                    continue

                classification = classify(preview, sender)
                if classification["is_recruiter"]:
                    bump_recruiter_score(conn, sender)
                is_priority = (
                    sender in PRIORITY_SENDERS
                    or "tech_question" in classification["tags"]
                    or classification["is_recruiter"]
                )
                if is_priority:
                    report["priority_seen"] += 1

                reply = craft_reply(sender, preview, classification)
                if reply.get("skip"):
                    log.info(f"  ⏭️  {sender} → spam, skip")
                    continue

                entry = {
                    "sender": sender,
                    "preview": preview[:200],
                    "tags": classification["tags"],
                    "intent": reply["intent"],
                    "confidence": reply["confidence"],
                    "draft": reply["draft"],
                    "priority": is_priority,
                }

                # Envoi auto ?
                may_send = (
                    send
                    and reply["confidence"] >= confidence_threshold
                    and in_business_hours()
                )
                if may_send:
                    # Open conversation + send via CDP
                    if conv.get("idx") is not None and open_conversation(
                        sess, conv["idx"]
                    ):
                        time.sleep(1.5)
                        res = send_reply_via_cdp(sess, reply["draft"])
                        entry["sent"] = res.get("ok", False)
                        entry["send_err"] = res.get("err")
                        if entry["sent"]:
                            report["sent"].append(sender)
                            tg_notify(
                                f"📨 <b>LinkedIn auto-reply</b>\n"
                                f"→ {sender}\nIntent: {reply['intent']} "
                                f"({reply['confidence']:.2f})\n\n{reply['draft'][:300]}"
                            )
                    else:
                        entry["send_err"] = "could not open conversation"

                entry["msg"] = {**entry, "sent": entry.get("sent", False)}
                record_message(conn, entry["msg"])
                report["drafts"].append(entry)

                # Telegram alert pour priorités même en dry-run
                if is_priority and not entry.get("sent"):
                    tg_notify(
                        f"⚠️ <b>LinkedIn priorité</b>\n→ {sender}\n"
                        f"Intent: {reply['intent']}\n\nDraft: {reply['draft'][:300]}"
                    )

    except Exception as e:
        log.exception("CDP session error")
        report["errors"].append(f"Exception: {e}")

    return _finalize(report, started)


def _finalize(report: dict, started: float) -> dict:
    report["duration_s"] = round(time.time() - started, 2)
    fname = f"inbox-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    fpath = REPORT_DIR / fname
    fpath.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    log.info(f"Report saved: {fpath}")
    return report


# ─── CLI ─────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--send", action="store_true", help="Active l'envoi auto (sinon dry-run)"
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.90,
        help="Seuil confiance envoi auto (défaut 0.90)",
    )
    parser.add_argument(
        "--continuous", action="store_true", help="Mode boucle (sinon une seule passe)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=900,
        help="Interval boucle en secondes (défaut 900 = 15 min)",
    )
    parser.add_argument(
        "--ignore-hours",
        action="store_true",
        help="Ignore les heures ouvrées (override)",
    )
    args = parser.parse_args()

    if args.ignore_hours:
        global BUSINESS_HOURS, BUSINESS_DAYS
        BUSINESS_HOURS = (dtime(0, 0), dtime(23, 59))
        BUSINESS_DAYS = set(range(7))

    log.info(
        f"Start V2 send={args.send} conf={args.confidence} "
        f"continuous={args.continuous} interval={args.interval}s"
    )

    while True:
        report = process_inbox(args.send, args.confidence)
        print("═" * 60)
        print(f"  LinkedIn Watcher V2 — {report['timestamp']}")
        print(f"  Mode: {report['mode']} | BusinessHours: {report['business_hours']}")
        print(
            f"  Seen: {report['messages_seen']} | Priority: {report['priority_seen']} | Skipped: {report['skipped_known']}"
        )
        print(f"  Drafts: {len(report['drafts'])} | Sent: {len(report['sent'])}")
        if report["errors"]:
            for e in report["errors"]:
                print(f"  ⚠ {e}")
        for d in report["drafts"][:10]:
            mark = "★" if d["priority"] else " "
            sent = "✅" if d.get("sent") else "📝"
            print(
                f"  {mark} {sent} {d['sender']} [{d['intent']} {d['confidence']:.2f}]"
            )
        print("═" * 60)
        if not args.continuous:
            break
        time.sleep(args.interval)
    return 0


if __name__ == "__main__":
    sys.exit(main())
