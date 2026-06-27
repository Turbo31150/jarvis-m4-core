#!/usr/bin/env python3
"""
JARVIS — Logging avancé, continuité inter-sessions.

Fonctionnalités:
  - Logger JSON rotatif par service
  - SQLite sink central (jarvis_logs.db) — requêtable via jq ou SQL
  - Décorateur @logged : trace appels + durée + exceptions
  - ContextLogger : propagation session_id entre services
  - Agrégateur multi-service avec filtre niveau/service/session
  - Import des logs texte bruts existants (cluster-health, openclaw, token_usage)
  - CLI : tail, query, sessions, import, stats

Usage rapide:
    from util_logging import get_logger, logged, LogContext
    log = get_logger("mon-service")

    @logged("mon-service")
    def ma_fonction(x): ...

    with LogContext(service="mon-service", session_id="abc123") as ctx:
        ctx.info("dans la session")

CLI:
    python3 util_logging.py tail -s cluster-health -n 50
    python3 util_logging.py query --level ERROR --since 2026-05-05T14:00
    python3 util_logging.py sessions --service mon-service
    python3 util_logging.py stats
    python3 util_logging.py import-legacy
"""

import argparse
import functools
import json
import logging
import os
import re
import sqlite3
import sys
import time
import traceback
import uuid
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from threading import local
from typing import Any, Callable

# ── Constantes ────────────────────────────────────────────────────────────────

LOG_ROOT = Path(os.environ.get("JARVIS_LOG_DIR", "/home/pamerys/jarvis/logs"))
LOG_ROOT.mkdir(parents=True, exist_ok=True)

DB_PATH = LOG_ROOT / "jarvis_logs.db"
_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%d")
_LOGGERS: dict[str, logging.Logger] = {}

# Thread-local pour propagation session_id
_ctx = local()

# ── SQLite sink ───────────────────────────────────────────────────────────────


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            ts        TEXT NOT NULL,
            level     TEXT NOT NULL,
            service   TEXT NOT NULL,
            session   TEXT,
            msg       TEXT NOT NULL,
            extra     TEXT,
            duration  REAL,
            exc       TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ts      ON logs(ts)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_service ON logs(service)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON logs(session)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_level   ON logs(level)")
    # Table checkpoints : état persisté entre redémarrages
    conn.execute("""
        CREATE TABLE IF NOT EXISTS checkpoints (
            service   TEXT NOT NULL,
            key       TEXT NOT NULL,
            value     TEXT NOT NULL,
            ts        TEXT NOT NULL,
            session   TEXT,
            PRIMARY KEY (service, key)
        )
    """)
    conn.commit()
    return conn


class _SQLiteHandler(logging.Handler):
    """Handler logging → jarvis_logs.db."""

    def __init__(self):
        super().__init__()
        self._conn = _db()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            ts = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()
            session = getattr(record, "session_id", None) or getattr(
                _ctx, "session_id", None
            )
            extra_keys = {
                k: v
                for k, v in record.__dict__.items()
                if k not in logging.LogRecord.__dict__
                and k not in ("session_id", "duration", "exc_text")
                and not k.startswith("_")
            }
            extra = (
                json.dumps(extra_keys, ensure_ascii=False, default=str)
                if extra_keys
                else None
            )
            exc = None
            if record.exc_info:
                exc = "".join(traceback.format_exception(*record.exc_info))
            self._conn.execute(
                "INSERT INTO logs (ts,level,service,session,msg,extra,duration,exc) VALUES (?,?,?,?,?,?,?,?)",
                (
                    ts,
                    record.levelname,
                    record.name,
                    session,
                    record.getMessage(),
                    extra,
                    getattr(record, "duration", None),
                    exc,
                ),
            )
            self._conn.commit()
        except Exception:
            pass  # ne jamais crasher le programme hôte sur un log


# ── Formatters ────────────────────────────────────────────────────────────────


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        session = getattr(record, "session_id", None) or getattr(
            _ctx, "session_id", None
        )
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "lvl": record.levelname,
            "svc": record.name,
            "msg": record.getMessage(),
        }
        if session:
            payload["session"] = session
        dur = getattr(record, "duration", None)
        if dur is not None:
            payload["duration"] = round(dur, 4)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


_COLORS = {
    "DEBUG": "\033[90m",
    "INFO": "\033[36m",
    "WARNING": "\033[33m",
    "ERROR": "\033[31m",
    "CRITICAL": "\033[1;31m",
}
_RESET = "\033[0m"


class _HumanFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.fromtimestamp(record.created, tz=timezone.utc).strftime(
            "%H:%M:%S"
        )
        session = getattr(record, "session_id", None) or getattr(
            _ctx, "session_id", None
        )
        sid = f"[{session[:8]}]" if session else ""
        _dur = getattr(record, "duration", None)
        dur = f" ({_dur:.2f}s)" if _dur is not None else ""
        color = _COLORS.get(record.levelname, "")
        return f"{color}[{ts}]{sid}[{record.name}][{record.levelname}]{_RESET} {record.getMessage()}{dur}"


# ── Logger factory ────────────────────────────────────────────────────────────


def get_logger(
    service: str,
    level: int = logging.DEBUG,
    json_file: bool = True,
    console: bool = True,
    sqlite_sink: bool = True,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 7,
) -> logging.Logger:
    """
    Retourne (ou crée) un logger persisté pour `service`.
    Sorties : fichier JSONL rotatif + SQLite central + console colorée.
    """
    if service in _LOGGERS:
        return _LOGGERS[service]

    logger = logging.getLogger(f"jarvis.{service}")
    logger.setLevel(level)
    logger.propagate = False

    if json_file:
        svc_dir = LOG_ROOT / service
        svc_dir.mkdir(parents=True, exist_ok=True)
        fh = RotatingFileHandler(
            svc_dir / f"{_DATE}.jsonl",
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        fh.setFormatter(_JsonFormatter())
        fh.setLevel(logging.DEBUG)
        logger.addHandler(fh)

    if sqlite_sink:
        logger.addHandler(_SQLiteHandler())

    if console:
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(_HumanFormatter())
        sh.setLevel(level)
        logger.addHandler(sh)

    _LOGGERS[service] = logger
    return logger


# ── Session markers ───────────────────────────────────────────────────────────


def log_session_start(
    service: str, session_id: str | None = None, meta: dict | None = None
) -> str:
    """Marque SESSION_START. Retourne le session_id (généré si absent)."""
    sid = session_id or str(uuid.uuid4())[:8]
    log = get_logger(service, console=False)
    r = logging.LogRecord(
        name=f"jarvis.{service}",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=json.dumps({"event": "SESSION_START", "session": sid, **(meta or {})}),
        args=(),
        exc_info=None,
    )
    r.session_id = sid
    log.handle(r)
    return sid


def log_session_end(
    service: str, session_id: str | None = None, meta: dict | None = None
) -> None:
    log = get_logger(service, console=False)
    r = logging.LogRecord(
        name=f"jarvis.{service}",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=json.dumps({"event": "SESSION_END", **(meta or {})}),
        args=(),
        exc_info=None,
    )
    if session_id:
        r.session_id = session_id
    log.handle(r)


# ── ContextLogger ─────────────────────────────────────────────────────────────


class LogContext:
    """
    Context manager — propage session_id à tous les loggers dans le bloc.

    with LogContext("mon-service", session_id="abc") as ctx:
        ctx.info("message tracé avec le session_id")
    """

    def __init__(
        self, service: str, session_id: str | None = None, meta: dict | None = None
    ):
        self.service = service
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.meta = meta or {}
        self._log = get_logger(service)

    def _emit(self, level: int, msg: str, **extra) -> None:
        r = self._log.makeRecord(self._log.name, level, "", 0, msg, (), None)
        r.session_id = self.session_id
        for k, v in extra.items():
            setattr(r, k, v)
        self._log.handle(r)

    def debug(self, msg: str, **kw) -> None:
        self._emit(logging.DEBUG, msg, **kw)

    def info(self, msg: str, **kw) -> None:
        self._emit(logging.INFO, msg, **kw)

    def warning(self, msg: str, **kw) -> None:
        self._emit(logging.WARNING, msg, **kw)

    def error(self, msg: str, **kw) -> None:
        self._emit(logging.ERROR, msg, **kw)

    def __enter__(self) -> "LogContext":
        _ctx.session_id = self.session_id
        log_session_start(self.service, self.session_id, self.meta)
        return self

    def __exit__(self, exc_type, exc_val, _exc_tb) -> bool:
        if exc_type:
            self.error(f"Exception: {exc_val}", exc=traceback.format_exc())
        log_session_end(self.service, self.session_id)
        _ctx.session_id = None
        return False


# ── Décorateur @logged ────────────────────────────────────────────────────────


def logged(service: str, level: int = logging.DEBUG):
    """
    Décorateur : trace appel + durée + valeur retour + exceptions.

    @logged("trading")
    def analyse_signal(symbol: str) -> dict: ...
    """

    def decorator(fn: Callable) -> Callable:
        log = get_logger(service, console=False)

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            fname = fn.__qualname__
            session = getattr(_ctx, "session_id", None)
            start = time.perf_counter()
            r_start = logging.LogRecord(
                name=f"jarvis.{service}",
                level=level,
                pathname="",
                lineno=0,
                msg=f"CALL {fname}",
                args=(),
                exc_info=None,
            )
            if session:
                r_start.session_id = session
            log.handle(r_start)
            try:
                result = fn(*args, **kwargs)
                dur = time.perf_counter() - start
                r_ok = logging.LogRecord(
                    name=f"jarvis.{service}",
                    level=level,
                    pathname="",
                    lineno=0,
                    msg=f"RETURN {fname}",
                    args=(),
                    exc_info=None,
                )
                r_ok.duration = dur
                if session:
                    r_ok.session_id = session
                log.handle(r_ok)
                return result
            except Exception as exc:
                dur = time.perf_counter() - start
                r_err = logging.LogRecord(
                    name=f"jarvis.{service}",
                    level=logging.ERROR,
                    pathname="",
                    lineno=0,
                    msg=f"ERROR {fname}: {exc}",
                    args=(),
                    exc_info=sys.exc_info(),
                )
                r_err.duration = dur
                if session:
                    r_err.session_id = session
                log.handle(r_err)
                raise

        return wrapper

    return decorator


# ── Requêtes SQLite ───────────────────────────────────────────────────────────


def query_logs(
    service: str | None = None,
    level: str | None = None,
    session: str | None = None,
    since: str | None = None,
    until: str | None = None,
    search: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """Requête SQL sur jarvis_logs.db."""
    conn = _db()
    clauses, params = [], []
    if service:
        clauses.append("service LIKE ?")
        params.append(f"%{service}%")
    if level:
        clauses.append("level = ?")
        params.append(level.upper())
    if session:
        clauses.append("session LIKE ?")
        params.append(f"%{session}%")
    if since:
        clauses.append("ts >= ?")
        params.append(since)
    if until:
        clauses.append("ts <= ?")
        params.append(until)
    if search:
        clauses.append("msg LIKE ?")
        params.append(f"%{search}%")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = conn.execute(
        f"SELECT ts,level,service,session,msg,duration,exc FROM logs {where} ORDER BY ts DESC LIMIT ?",
        params + [limit],
    ).fetchall()
    return [
        {
            "ts": r[0],
            "level": r[1],
            "service": r[2],
            "session": r[3],
            "msg": r[4],
            "duration": r[5],
            "exc": r[6],
        }
        for r in reversed(rows)
    ]


def get_sessions(service: str | None = None) -> list[dict]:
    """Liste les sessions (SESSION_START/END) avec leur durée."""
    conn = _db()
    where = "WHERE service LIKE ? AND " if service else "WHERE "
    params = [f"%{service}%"] if service else []
    rows = conn.execute(
        f"SELECT session, MIN(ts), MAX(ts), COUNT(*) FROM logs "
        f"{where}session IS NOT NULL GROUP BY session ORDER BY MIN(ts) DESC LIMIT 50",
        params,
    ).fetchall()
    return [
        {"session": r[0], "start": r[1], "last": r[2], "entries": r[3]} for r in rows
    ]


def stats() -> dict:
    """Statistiques globales du DB de logs."""
    conn = _db()
    total = conn.execute("SELECT COUNT(*) FROM logs").fetchone()[0]
    by_level = dict(
        conn.execute("SELECT level, COUNT(*) FROM logs GROUP BY level").fetchall()
    )
    by_service = dict(
        conn.execute(
            "SELECT service, COUNT(*) FROM logs GROUP BY service ORDER BY COUNT(*) DESC LIMIT 10"
        ).fetchall()
    )
    errors_24h = conn.execute(
        "SELECT COUNT(*) FROM logs WHERE level IN ('ERROR','CRITICAL') AND ts >= datetime('now','-1 day')"
    ).fetchone()[0]
    return {
        "total": total,
        "by_level": by_level,
        "top_services": by_service,
        "errors_24h": errors_24h,
    }


# ── Checkpoints (état persisté inter-redémarrages) ───────────────────────────


def checkpoint(service: str, key: str, value: Any, session: str | None = None) -> None:
    """
    Sauvegarde une valeur d'état pour `service`.
    Écrase silencieusement la valeur précédente (UPSERT).

    checkpoint("scraper", "last_page", 42)
    checkpoint("cluster-health", "last_status", {"M1": "UP", "M2": "DOWN"})
    """
    conn = _db()
    sid = session or getattr(_ctx, "session_id", None)
    ts = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT OR REPLACE INTO checkpoints (service,key,value,ts,session) VALUES (?,?,?,?,?)",
        (service, key, json.dumps(value, ensure_ascii=False, default=str), ts, sid),
    )
    conn.commit()


def get_checkpoint(service: str, key: str, default: Any = None) -> Any:
    """
    Récupère la valeur du checkpoint, ou `default` si absent.

    last_page = get_checkpoint("scraper", "last_page", 0)
    """
    conn = _db()
    row = conn.execute(
        "SELECT value FROM checkpoints WHERE service=? AND key=?", (service, key)
    ).fetchone()
    if row is None:
        return default
    try:
        return json.loads(row[0])
    except json.JSONDecodeError:
        return row[0]


def get_all_checkpoints(service: str) -> dict[str, Any]:
    """Retourne tous les checkpoints d'un service sous forme de dict."""
    conn = _db()
    rows = conn.execute(
        "SELECT key, value, ts FROM checkpoints WHERE service=? ORDER BY key",
        (service,),
    ).fetchall()
    return {r[0]: {"value": json.loads(r[1]), "ts": r[2]} for r in rows}


def clear_checkpoint(service: str, key: str | None = None) -> None:
    """Supprime un checkpoint précis ou tous les checkpoints du service."""
    conn = _db()
    if key:
        conn.execute(
            "DELETE FROM checkpoints WHERE service=? AND key=?", (service, key)
        )
    else:
        conn.execute("DELETE FROM checkpoints WHERE service=?", (service,))
    conn.commit()


# ── Resume : contexte de reprise au démarrage ─────────────────────────────────


def resume(service: str, last_n_errors: int = 5) -> dict:
    """
    Retourne un snapshot de continuité pour un service qui redémarre :
      - dernière session (id, début, fin, nb entrées)
      - erreurs récentes (last_n_errors)
      - tous les checkpoints enregistrés

    Usage typique en début de script :
        ctx = resume("scraper")
        last_page = ctx["checkpoints"].get("last_page", {}).get("value", 0)
        print(ctx["summary"])
    """
    conn = _db()

    # Dernière session
    row = conn.execute(
        "SELECT session, MIN(ts), MAX(ts), COUNT(*) FROM logs "
        "WHERE service LIKE ? AND session IS NOT NULL "
        "GROUP BY session ORDER BY MIN(ts) DESC LIMIT 1",
        (f"%{service}%",),
    ).fetchone()
    last_session = (
        {"id": row[0], "start": row[1], "end": row[2], "entries": row[3]}
        if row
        else None
    )

    # Dernières erreurs
    err_rows = conn.execute(
        "SELECT ts, level, msg FROM logs WHERE service LIKE ? AND level IN ('ERROR','CRITICAL') "
        "ORDER BY ts DESC LIMIT ?",
        (f"%{service}%", last_n_errors),
    ).fetchall()
    errors = [{"ts": r[0], "level": r[1], "msg": r[2]} for r in reversed(err_rows)]

    # Checkpoints
    chk = get_all_checkpoints(service)

    # Résumé lisible
    lines = [f"=== RESUME [{service}] ==="]
    if last_session:
        lines.append(
            f"Dernière session : {last_session['id']} "
            f"({last_session['start'][:19]} → {last_session['end'][:19]}, "
            f"{last_session['entries']} entrées)"
        )
    else:
        lines.append("Aucune session précédente.")
    if chk:
        lines.append(f"Checkpoints ({len(chk)}) :")
        for k, v in chk.items():
            lines.append(f"  {k} = {v['value']}  (sauvé {v['ts'][:19]})")
    if errors:
        lines.append(f"Dernières erreurs ({len(errors)}) :")
        for e in errors:
            lines.append(f"  [{e['ts'][:19]}][{e['level']}] {e['msg'][:120]}")

    return {
        "last_session": last_session,
        "errors": errors,
        "checkpoints": chk,
        "summary": "\n".join(lines),
    }


# ── Follow : tail -f live sur JSONL ──────────────────────────────────────────


def follow(service: str, poll_interval: float = 0.5):
    """
    Générateur qui yield les nouvelles entrées JSONL d'un service en temps réel.
    Arrêt propre sur KeyboardInterrupt.

    for entry in follow("cluster-health"):
        print(entry["msg"])
    """
    svc_dir = LOG_ROOT / service
    svc_dir.mkdir(parents=True, exist_ok=True)
    log_path = svc_dir / f"{_DATE}.jsonl"
    pos = log_path.stat().st_size if log_path.exists() else 0
    try:
        while True:
            # Recalcule le fichier courant (rotation de minuit)
            cur_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            cur_path = svc_dir / f"{cur_date}.jsonl"
            if cur_path != log_path:
                log_path = cur_path
                pos = 0
            if log_path.exists():
                with log_path.open(encoding="utf-8") as fh:
                    fh.seek(pos)
                    for line in fh:
                        line = line.strip()
                        if line:
                            try:
                                yield json.loads(line)
                            except json.JSONDecodeError:
                                yield {"raw": line}
                    pos = fh.tell()
            time.sleep(poll_interval)
    except (KeyboardInterrupt, GeneratorExit):
        return


# ── Import logs legacy (texte brut → DB) ─────────────────────────────────────

_CLUSTER_RE = re.compile(r"\[(?P<ts>\d{2}:\d{2}:\d{2})\] (?P<msg>.+)")
_TOKEN_RE = re.compile(r"(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - (?P<msg>.+)")


def import_legacy_logs(date_prefix: str = "2026-05-05") -> int:
    """
    Importe les logs texte bruts existants dans jarvis_logs.db.
    Retourne le nombre de lignes importées.
    """
    conn = _db()
    imported = 0

    # cluster-health.log
    ch = LOG_ROOT / "cluster-health.log"
    if ch.exists():
        for line in ch.read_text().splitlines():
            m = _CLUSTER_RE.match(line.strip())
            if m:
                ts = f"{date_prefix}T{m.group('ts')}+00:00"
                conn.execute(
                    "INSERT OR IGNORE INTO logs (ts,level,service,msg) VALUES (?,?,?,?)",
                    (ts, "INFO", "jarvis.cluster-health", m.group("msg")),
                )
                imported += 1

    # token_usage.log
    tu = LOG_ROOT / "token_usage.log"
    if tu.exists():
        for line in tu.read_text().splitlines():
            m = _TOKEN_RE.match(line.strip())
            if m:
                ts = m.group("ts").replace(" ", "T") + "+00:00"
                conn.execute(
                    "INSERT OR IGNORE INTO logs (ts,level,service,msg) VALUES (?,?,?,?)",
                    (ts, "INFO", "jarvis.token-usage", m.group("msg")),
                )
                imported += 1

    conn.commit()
    return imported


# ── Helpers affichage CLI ─────────────────────────────────────────────────────


def _print_entry(e: dict) -> None:
    ts = (e.get("ts") or "?")[:19]
    lvl = e.get("level") or e.get("lvl") or "---"
    svc = e.get("service") or e.get("svc") or ""
    sid = f"[{e['session'][:8]}]" if e.get("session") else ""
    dur = f" ({e['duration']:.2f}s)" if e.get("duration") else ""
    msg = e.get("msg", e.get("raw", ""))
    c = _COLORS.get(lvl, "\033[90m")
    print(f"{c}[{ts}]{sid}[{svc}][{lvl}]{_RESET} {msg}{dur}")


def list_services() -> list[str]:
    conn = _db()
    rows = conn.execute("SELECT DISTINCT service FROM logs ORDER BY service").fetchall()
    db_svcs = [r[0] for r in rows]
    fs_svcs = [d.name for d in sorted(LOG_ROOT.iterdir()) if d.is_dir()]
    return sorted(set(db_svcs + fs_svcs))


# ── CLI ───────────────────────────────────────────────────────────────────────


def _cli() -> None:
    parser = argparse.ArgumentParser(description="JARVIS log util avancé")
    sub = parser.add_subparsers(dest="cmd")

    # tail
    t = sub.add_parser("tail", help="Dernières entrées d'un service (JSONL)")
    t.add_argument("--service", "-s", required=True)
    t.add_argument("--lines", "-n", type=int, default=50)
    t.add_argument("--since", help="Filtre ISO (ex: 2026-05-05T14:00)")

    # query — SQLite
    q = sub.add_parser("query", help="Requête SQL sur tous les services")
    q.add_argument("--service", "-s")
    q.add_argument("--level", "-l", help="DEBUG|INFO|WARNING|ERROR|CRITICAL")
    q.add_argument("--session", help="Filtrer par session_id (partiel)")
    q.add_argument("--since", help="ISO timestamp")
    q.add_argument("--until", help="ISO timestamp")
    q.add_argument("--search", help="Texte dans msg")
    q.add_argument("--limit", "-n", type=int, default=100)

    # sessions
    ses = sub.add_parser("sessions", help="Lister les sessions")
    ses.add_argument("--service", "-s")

    # stats
    sub.add_parser("stats", help="Statistiques globales")

    # ls
    sub.add_parser("ls", help="Lister les services loggués")

    # import-legacy
    imp = sub.add_parser("import-legacy", help="Importer logs texte bruts → DB")
    imp.add_argument("--date", default=_DATE)

    # resume — snapshot de reprise
    res = sub.add_parser("resume", help="Snapshot de continuité au démarrage")
    res.add_argument("--service", "-s", required=True)

    # follow — tail -f live
    fw = sub.add_parser("follow", help="Tail -f live (Ctrl+C pour quitter)")
    fw.add_argument("--service", "-s", required=True)

    # checkpoint get/set/ls/clear
    ck = sub.add_parser("checkpoint", help="Gérer les checkpoints d'état")
    ck_sub = ck.add_subparsers(dest="ck_cmd")
    ck_set = ck_sub.add_parser("set")
    ck_set.add_argument("service")
    ck_set.add_argument("key")
    ck_set.add_argument("value")
    ck_get = ck_sub.add_parser("get")
    ck_get.add_argument("service")
    ck_get.add_argument("key")
    ck_ls = ck_sub.add_parser("ls")
    ck_ls.add_argument("service")
    ck_del = ck_sub.add_parser("del")
    ck_del.add_argument("service")
    ck_del.add_argument("key", nargs="?", default=None)

    args = parser.parse_args()

    if args.cmd == "ls":
        for svc in list_services():
            print(svc)

    elif args.cmd == "tail":
        svc_dir = LOG_ROOT / args.service
        if not svc_dir.exists():
            print(f"[Aucun log pour '{args.service}']")
            return
        entries: list[dict] = []
        for f in sorted(svc_dir.glob("*.jsonl")):
            for line in f.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if args.since and obj.get("ts", "") < args.since:
                        continue
                    entries.append(obj)
                except json.JSONDecodeError:
                    entries.append({"raw": line})
        for e in entries[-args.lines :]:
            _print_entry(e)

    elif args.cmd == "query":
        entries = query_logs(
            service=args.service,
            level=args.level,
            session=args.session,
            since=args.since,
            until=args.until,
            search=args.search,
            limit=args.limit,
        )
        if not entries:
            print("[Aucun résultat]")
        for e in entries:
            _print_entry(e)

    elif args.cmd == "sessions":
        sessions = get_sessions(args.service)
        if not sessions:
            print("[Aucune session]")
            return
        print(f"{'SESSION':10} {'DÉBUT':20} {'FIN':20} {'ENTRÉES':>8}")
        print("-" * 65)
        for s in sessions:
            print(
                f"{s['session']:10} {s['start'][:19]:20} {s['last'][:19]:20} {s['entries']:>8}"
            )

    elif args.cmd == "stats":
        s = stats()
        print(f"Total entrées : {s['total']}")
        print(f"Erreurs 24h   : {s['errors_24h']}")
        print("\nPar niveau :")
        for lvl, n in sorted(s["by_level"].items()):
            c = _COLORS.get(lvl, "")
            print(f"  {c}{lvl:10}{_RESET} {n}")
        print("\nTop services :")
        for svc, n in s["top_services"].items():
            print(f"  {svc:40} {n}")

    elif args.cmd == "import-legacy":
        n = import_legacy_logs(args.date)
        print(f"{n} lignes importées → {DB_PATH}")

    elif args.cmd == "resume":
        ctx = resume(args.service)
        print(ctx["summary"])

    elif args.cmd == "follow":
        print(f"[Suivi live : {args.service}] Ctrl+C pour quitter\n")
        for entry in follow(args.service):
            _print_entry(entry)

    elif args.cmd == "checkpoint":
        if args.ck_cmd == "set":
            try:
                val = json.loads(args.value)
            except json.JSONDecodeError:
                val = args.value
            checkpoint(args.service, args.key, val)
            print(f"✓ {args.service}:{args.key} = {val}")
        elif args.ck_cmd == "get":
            val = get_checkpoint(args.service, args.key)
            print(
                json.dumps(val, ensure_ascii=False, indent=2)
                if isinstance(val, (dict, list))
                else val
            )
        elif args.ck_cmd == "ls":
            chk = get_all_checkpoints(args.service)
            if not chk:
                print("[Aucun checkpoint]")
            else:
                print(f"{'CLÉ':30} {'VALEUR':40} SAUVÉ")
                print("-" * 85)
                for k, v in chk.items():
                    print(f"{k:30} {str(v['value'])[:40]:40} {v['ts'][:19]}")
        elif args.ck_cmd == "del":
            clear_checkpoint(args.service, args.key)
            print(f"✓ supprimé {args.service}:{args.key or '(tous)'}")
        else:
            ck.print_help()

    else:
        parser.print_help()


if __name__ == "__main__":
    _cli()
