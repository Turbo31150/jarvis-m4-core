#!/usr/bin/env python3
"""
Enveloppe I/O unique (stdlib-only) pour l'écosystème JARVIS.
Respecte les invariants E1-E5.
"""
import os
import sys
import json
import time

def emit_envelope(
    ok: bool,
    tool: str,
    verb: str,
    action: str,
    data: dict = None,
    error: dict = None,
    meta_extra: dict = None,
    schema_version: int = 1
):
    command_id = os.environ.get("JARVIS_COMMAND_ID", "")
    degraded_mode = os.environ.get("JARVIS_DEGRADED_MODE", "NORMAL")
    
    meta = {
        "degraded_mode": degraded_mode,
        "served_by": os.uname().nodename,
        "fallback_used": meta_extra.get("fallback_used", False) if meta_extra else False,
        "elapsed_ms": meta_extra.get("elapsed_ms", 0) if meta_extra else 0,
        "source_ids": meta_extra.get("source_ids", []) if meta_extra else []
    }
    if meta_extra:
        meta.update(meta_extra)

    payload = {
        "ok": ok,
        "tool": tool,
        "verb": verb,
        "action": action,
        "schema_version": schema_version,
        "command_id": command_id,
        "data": data if ok else None,
        "error": error if not ok else None,
        "meta": meta
    }
    
    print(json.dumps(payload, ensure_ascii=False))

def emit_ok(tool: str, verb: str, action: str, data: dict = None, meta_extra: dict = None):
    emit_envelope(True, tool, verb, action, data=data, meta_extra=meta_extra)
    sys.exit(0)

def emit_err(tool: str, verb: str, action: str, code: str, message: str, exit_code: int = 1, frontier: str = None, retryable: bool = False, details: dict = None, meta_extra: dict = None):
    err_obj = {
        "code": code,
        "message": message,
        "retryable": retryable,
        "frontier": frontier,
        "details": details or {}
    }
    emit_envelope(False, tool, verb, action, error=err_obj, meta_extra=meta_extra)
    sys.exit(exit_code)
