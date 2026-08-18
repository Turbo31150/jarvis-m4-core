#!/usr/bin/env python3
"""
events.py — journal opérationnel append-only JSONL de l'écosystème JARVIS.

Loi A2, côté ÉPHÉMÈRE/TECHNIQUE : ce journal reçoit les logs d'exécution, les
bascules de backend, les décisions de policy. Il ne reçoit **jamais** de fait
métier durable — ça, c'est `jarvis-mem` (PERSISTANT). La frontière est nette :
si ça a de la valeur dans six mois, ça va dans mem, pas ici.

HONNÊTETÉ SUR LA GARANTIE : ce journal n'est **pas** tamper-evident. Le flock +
O_APPEND + write unique protègent de l'entrelacement concurrent et de la
troncature accidentelle. Ils ne protègent de rien face à un attaquant qui a les
droits d'écriture sur le fichier — root, ou l'utilisateur propriétaire, peut
réécrire l'historique sans laisser de trace. Pour de l'inviolabilité il faudrait
un chaînage de hash + une ancre externe ; ce n'est pas fait, ne le prétends pas.

API : emit(event_type, **fields) -> event_id · query(...) -> list[dict]
Stdlib-only.
"""

import os
import json
import time
import uuid
import fcntl
from pathlib import Path

SCHEMA_VERSION = 1
MAX_DETAIL_BYTES = 4096

ROOT = Path(os.environ.get("JARVIS_ROOT", Path(__file__).resolve().parents[2]))
JOURNAL = Path(os.environ.get("JARVIS_EVENTS_FILE", ROOT / "ops" / "events.jsonl"))


def _truncate(value):
    """Borne la taille d'un champ libre. Une trace tronquée vaut mieux qu'un journal noyé."""
    if not isinstance(value, str):
        try:
            value = json.dumps(value, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            value = str(value)
    encoded = value.encode("utf-8", errors="replace")
    if len(encoded) <= MAX_DETAIL_BYTES:
        return value
    return encoded[:MAX_DETAIL_BYTES].decode("utf-8", errors="ignore") + "…[tronqué]"


def emit(event_type, **fields):
    """Écrit un événement. Retourne son event_id.

    Ne lève jamais : un journal cassé ne doit pas faire tomber la brique qu'il
    observe. En cas d'échec d'écriture, retourne l'event_id quand même.
    """
    event = {
        "event_id": str(uuid.uuid4()),
        "schema_version": SCHEMA_VERSION,
        "ts": time.time(),
        "ts_iso": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "type": event_type,
        "command_id": os.environ.get("JARVIS_COMMAND_ID", ""),
        "pid": os.getpid(),
        "host": os.uname().nodename,
    }
    for key, val in fields.items():
        event[key] = _truncate(val)

    # un seul write() par événement : pas d'entrelacement possible entre process
    line = json.dumps(event, ensure_ascii=False, default=str) + "\n"
    try:
        JOURNAL.parent.mkdir(parents=True, exist_ok=True)
        # O_NOFOLLOW : refuse d'écrire si le journal a été remplacé par un lien
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW
        fd = os.open(JOURNAL, flags, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            os.write(fd, line.encode("utf-8"))
        finally:
            os.close(fd)
    except OSError:
        pass
    return event["event_id"]


def query(event_type=None, command_id=None, since=None, limit=100):
    """Relit le journal, du plus récent au plus ancien, avec filtres optionnels."""
    if not JOURNAL.is_file():
        return []
    out = []
    try:
        with open(JOURNAL, "r", encoding="utf-8", errors="replace") as handle:
            lines = handle.readlines()
    except OSError:
        return []
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except ValueError:
            continue  # ligne corrompue : on saute, on ne casse pas la lecture
        if event_type and event.get("type") != event_type:
            continue
        if command_id and event.get("command_id") != command_id:
            continue
        if since and event.get("ts", 0) < since:
            continue
        out.append(event)
        if len(out) >= limit:
            break
    return out
