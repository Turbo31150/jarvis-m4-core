#!/usr/bin/env python3
"""
Registre des erreurs canoniques JARVIS (errors.py).
Mappe les codes fine -> exit_code, retryable, et frontière M1.
"""
from enum import Enum

class ErrorCode(Enum):
    E_PROMPT_EMPTY = ("E_PROMPT_EMPTY", 2, False, None)
    E_LLM_UNAVAILABLE = ("E_LLM_UNAVAILABLE", 1, True, "A1")
    E_SSRF_BLOCKED = ("E_SSRF_BLOCKED", 5, False, "A3")
    E_SCHEMA_INVALID = ("E_SCHEMA_INVALID", 2, False, "A4")
    E_POLICY_MISSING = ("E_POLICY_MISSING", 4, False, "A5")
    E_ALLOWLIST_DENIED = ("E_ALLOWLIST_DENIED", 4, False, "A0")
    E_HASH_DRIFT = ("E_HASH_DRIFT", 4, False, "A4")
    E_TRACE_REQUIRED = ("E_TRACE_REQUIRED", 1, False, "A4")
    E_NO_VOICE = ("E_NO_VOICE", 3, True, None)
    E_TIMEOUT = ("E_TIMEOUT", 124, True, None)

    def __init__(self, code_str, exit_code, retryable, frontier):
        self.code_str = code_str
        self.exit_code = exit_code
        self.retryable = retryable
        self.frontier = frontier

def get_error_info(code_name: str):
    try:
        err = ErrorCode[code_name]
        return err.code_str, err.exit_code, err.retryable, err.frontier
    except KeyError:
        return code_name, 1, False, None
