"""jarvis doctor — diagnostic global. Chaque erreur porte CAUSE / IMPACT / ACTION.

Règle : un composant n'est [OK] que si un test réel l'a démontré.
Sinon [WARN], [ERROR] ou [UNKNOWN]. Jamais [OK] par défaut.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

from . import config as cfgmod
from .providers import Timeouts, build_provider

OK, WARN, ERR, UNK = "OK", "WARN", "ERROR", "UNKNOWN"


def _check(name, level, detail, cause=None, impact=None, action=None):
    return {
        "name": name,
        "level": level,
        "detail": detail,
        "cause": cause,
        "impact": impact,
        "action": action,
    }


def _cmd(*args, timeout=8):
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()
    except FileNotFoundError:
        return 127, "not found"
    except subprocess.TimeoutExpired:
        return 124, "timeout"


def run(probe_inference: bool = True) -> list[dict]:
    out: list[dict] = []
    cfg = cfgmod.load()

    # --- outils système ---------------------------------------------------
    for tool, args in (
        ("git", ("--version",)),
        ("python3", ("--version",)),
        ("node", ("--version",)),
        ("tmux", ("-V",)),
        ("claude", ("--version",)),
        ("openclaw", ("--version",)),
    ):
        if not shutil.which(tool):
            out.append(
                _check(
                    tool,
                    WARN,
                    "absent du PATH",
                    cause=f"{tool} non installé ou hors PATH",
                    impact="fonctionnalités dépendantes indisponibles",
                    action=f"installer {tool} ou ajuster le PATH",
                )
            )
            continue
        rc, o = _cmd(tool, *args)
        out.append(
            _check(tool, OK if rc == 0 else WARN, o.splitlines()[0][:70] if o else "?")
        )

    # --- ressources -------------------------------------------------------
    try:
        mem = Path("/proc/meminfo").read_text().splitlines()
        kv = {l.split(":")[0]: int(l.split()[1]) for l in mem if ":" in l}
        avail_gb = kv.get("MemAvailable", 0) / 1024 / 1024
        lvl = OK if avail_gb > 3 else (WARN if avail_gb > 1.2 else ERR)
        out.append(
            _check(
                "RAM",
                lvl,
                f"{avail_gb:.1f} Gi disponibles",
                cause="mémoire sur-engagée" if lvl != OK else None,
                impact="chargement de modèle refusé / freeze" if lvl != OK else None,
                action="libérer la RAM (série ram-relief)" if lvl != OK else None,
            )
        )
    except Exception as e:  # noqa: BLE001
        out.append(_check("RAM", UNK, str(e)))

    rc, o = _cmd(
        "nvidia-smi",
        "--query-gpu=name,memory.total,memory.used",
        "--format=csv,noheader",
    )
    if rc == 0 and o:
        for line in o.splitlines():
            parts = [p.strip() for p in line.split(",")]
            try:
                tot = int(parts[1].split()[0])
                used = int(parts[2].split()[0])
                free = tot - used
                lvl = OK if free > 2000 else WARN
                out.append(
                    _check(
                        f"GPU {parts[0]}",
                        lvl,
                        f"{used}/{tot} MiB utilisés, {free} MiB libres",
                        cause="VRAM saturée" if lvl != OK else None,
                        impact="second modèle local non chargeable"
                        if lvl != OK
                        else None,
                        action="DUAL via 2 backends distincts" if lvl != OK else None,
                    )
                )
            except (IndexError, ValueError):
                out.append(_check("GPU", UNK, line))
    else:
        out.append(_check("GPU", UNK, "nvidia-smi indisponible"))

    du = shutil.disk_usage("/")
    pct = du.used / du.total * 100
    out.append(
        _check(
            "Disque /",
            OK if pct < 90 else WARN,
            f"{pct:.0f}% utilisé",
            cause="disque presque plein" if pct >= 90 else None,
            impact="échec d'écriture logs/checkpoints" if pct >= 90 else None,
            action="nettoyage caches" if pct >= 90 else None,
        )
    )

    # --- providers --------------------------------------------------------
    discovered = cfgmod.discover()
    if not discovered["providers"]:
        out.append(
            _check(
                "Providers",
                ERR,
                "aucun backend d'inférence joignable",
                cause="LM Studio et Ollama injoignables",
                impact="aucun worker ne peut travailler",
                action="démarrer LM Studio (serveur) ou `ollama serve`",
            )
        )
    for alias, p in discovered["providers"].items():
        out.append(
            _check(
                f"Provider {alias}",
                OK,
                f"{p['base_url']} — {len(p['models'])} modèle(s)",
            )
        )

    # --- workers + preuve d'inférence ------------------------------------
    workers = discovered.get("workers", {})
    if len(workers) < 2:
        out.append(
            _check(
                "DUAL",
                WARN,
                f"{len(workers)} worker(s) configurable(s)",
                cause="un seul backend joignable",
                impact="mode parallel dégradé en single",
                action="démarrer un second backend (Ollama ou LM Studio distant)",
            )
        )
    t = Timeouts(**cfg.get("timeouts", {}))
    for slot, spec in workers.items():
        pcfg = discovered["providers"][spec["provider"]]
        label = f"{slot} ({spec['provider']}/{spec['model']})"
        if not probe_inference:
            out.append(_check(label, UNK, "inférence non testée (--fast)"))
            continue
        prov = build_provider(pcfg["kind"], pcfg["base_url"], t)
        t0 = time.perf_counter()
        res = prov.chat(
            spec["model"],
            [{"role": "user", "content": "Réponds: OK"}],
            max_tokens=8,
            temperature=0,
        )
        dt = (time.perf_counter() - t0) * 1000
        if res.ok:
            out.append(
                _check(
                    label,
                    OK,
                    f"inférence réelle {dt:.0f} ms, ttft={res.metrics.get('ttft_ms')} ms",
                )
            )
        else:
            out.append(
                _check(
                    label,
                    ERR,
                    f"{res.status}: {res.error}",
                    cause="modèle listé mais inférence en échec (modèle fantôme)",
                    impact="worker inutilisable malgré /v1/models",
                    action="recharger le modèle dans le backend",
                )
            )

    # --- MCP --------------------------------------------------------------
    mcp_path = Path.home() / ".claude.json"
    if mcp_path.exists():
        try:
            servers = json.loads(mcp_path.read_text()).get("mcpServers", {})
            out.append(
                _check(
                    "MCP (config projet/global)",
                    OK if servers else WARN,
                    f"{len(servers)} serveur(s) déclaré(s): {', '.join(sorted(servers)) or '—'}",
                    cause="aucun MCP déclaré dans ~/.claude.json"
                    if not servers
                    else None,
                    impact="les MCP viennent des plugins, non versionnés ici"
                    if not servers
                    else None,
                    action="déclarer les MCP nécessaires dans .mcp.json du dépôt"
                    if not servers
                    else None,
                )
            )
        except json.JSONDecodeError as e:
            out.append(_check("MCP", ERR, f"~/.claude.json illisible: {e}"))
    else:
        out.append(_check("MCP", UNK, "~/.claude.json absent"))

    # --- OpenClaw gateway -------------------------------------------------
    import http.client

    try:
        c = http.client.HTTPConnection("127.0.0.1", 18789, timeout=3)
        c.request("GET", "/health")
        r = c.getresponse()
        body = r.read().decode()[:80]
        out.append(
            _check(
                "OpenClaw gateway",
                OK if r.status == 200 else WARN,
                f":18789 → {r.status} {body}",
            )
        )
        c.close()
    except Exception as e:  # noqa: BLE001
        out.append(
            _check(
                "OpenClaw gateway",
                WARN,
                f"injoignable: {type(e).__name__}",
                cause="gateway arrêté",
                impact="worker OpenClaw indisponible",
                action="`openclaw gateway` ou script jarvis-dual.sh",
            )
        )

    # --- persistance ------------------------------------------------------
    for label, d in (("Logs", cfgmod.LOG_DIR), ("Checkpoints", cfgmod.JOB_DIR)):
        d.mkdir(parents=True, exist_ok=True)
        writable = os.access(d, os.W_OK)
        out.append(
            _check(
                label,
                OK if writable else ERR,
                str(d),
                cause=None if writable else "répertoire non inscriptible",
                impact=None if writable else "aucune reprise possible",
                action=None if writable else f"chmod u+w {d}",
            )
        )
    return out


def render(checks: list[dict]) -> str:
    icon = {OK: "[OK]   ", WARN: "[WARN] ", ERR: "[ERROR]", UNK: "[UNK]  "}
    lines = ["JARVIS DOCTOR", "=" * 62]
    for c in checks:
        lines.append(f"{icon[c['level']]} {c['name']:32s} {c['detail']}")
        if c["level"] in (WARN, ERR) and c.get("cause"):
            lines.append(f"         CAUSE : {c['cause']}")
            lines.append(f"         IMPACT: {c['impact']}")
            lines.append(f"         ACTION: {c['action']}")
    n = {lv: sum(1 for c in checks if c["level"] == lv) for lv in (OK, WARN, ERR, UNK)}
    lines += ["=" * 62, f"OK={n[OK]}  WARN={n[WARN]}  ERROR={n[ERR]}  UNKNOWN={n[UNK]}"]
    return "\n".join(lines)


def exit_code(checks: list[dict]) -> int:
    return 1 if any(c["level"] == ERR for c in checks) else 0
