"""Benchmark & PREUVE de parallélisme.

Le verdict DUAL_PARALLEL ne dépend pas d'une intention mais d'une mesure :
chevauchement temporel réel des deux fenêtres d'exécution (overlap) et
entrelacement des tokens. Séquentiel → FAILED, et on dit pourquoi.
"""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor

from .journal import Journal
from .providers import UNAVAILABLE, Timeouts, build_provider

PROMPT = (
    "Explique en trois phrases ce qu'est un système d'orchestration "
    "multi-agents. Sois concret."
)


def _run_one(prov, model, slot, prompt, timeline, lock, max_tokens):
    """Exécute et horodate chaque étape en temps monotone partagé."""
    t_start = time.perf_counter()
    with lock:
        timeline.append((t_start, slot, "START"))
    first = None
    n = 0
    res = None
    for ev in prov.stream(
        model,
        [{"role": "user", "content": prompt}],
        worker=slot,
        max_tokens=max_tokens,
        temperature=0.2,
    ):
        if ev["event"] == "FIRST_TOKEN":
            first = time.perf_counter()
            with lock:
                timeline.append((first, slot, "FIRST_TOKEN"))
        elif ev["event"] == "TOKEN":
            n += 1
            if n % 10 == 0:
                with lock:
                    timeline.append((time.perf_counter(), slot, f"TOKEN[{n}]"))
        elif ev["event"] == "RESULT":
            res = ev["result"]
    t_end = time.perf_counter()
    with lock:
        timeline.append((t_end, slot, "END"))
    return {
        "worker": slot,
        "provider": prov.name,
        "model": model,
        "status": res.status if res else "http_error",
        "t_start": t_start,
        "t_first": first,
        "t_end": t_end,
        "duration_s": round(t_end - t_start, 3),
        "ttft_s": round(first - t_start, 3) if first else None,
        "chunks": n,
        "metrics": res.metrics if res else {},
        "error": res.error if res else "pas de résultat",
        "chars": len(res.content) if res else 0,
    }


def _providers(cfg):
    t = Timeouts(**cfg.get("timeouts", {}))
    out = {}
    for slot, spec in cfg.get("workers", {}).items():
        p = cfg["providers"][spec["provider"]]
        out[slot] = (
            build_provider(p["kind"], p["base_url"], t),
            spec["model"],
            spec["provider"],
        )
    return out


def solo(cfg, max_tokens=160, prompt=PROMPT) -> list[dict]:
    """Mesure A puis B séparément (référence pour l'efficacité parallèle)."""
    res = []
    lock = threading.Lock()
    for slot, (prov, model, alias) in _providers(cfg).items():
        tl = []
        r = _run_one(prov, model, slot, prompt, tl, lock, max_tokens)
        r["provider_alias"] = alias
        res.append(r)
    return res


def dual(cfg, max_tokens=160, prompt=PROMPT, job_id="bench-dual") -> dict:
    """Lance A et B SIMULTANÉMENT et prouve (ou réfute) la concurrence."""
    provs = _providers(cfg)
    if len(provs) < 2:
        return {
            "verdict": "DUAL_PARALLEL = BLOCKED",
            "reason": f"{len(provs)} worker(s) disponible(s), 2 requis",
            "runs": [],
            "timeline": [],
        }

    journal = Journal(job_id)
    timeline, lock = [], threading.Lock()
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=len(provs)) as ex:
        futs = {
            slot: ex.submit(_run_one, p, m, slot, prompt, timeline, lock, max_tokens)
            for slot, (p, m, _a) in provs.items()
        }
        runs = [f.result() for f in futs.values()]
    wall = time.perf_counter() - t0

    a, b = runs[0], runs[1]
    overlap = max(0.0, min(a["t_end"], b["t_end"]) - max(a["t_start"], b["t_start"]))
    sum_solo = a["duration_s"] + b["duration_s"]
    longest = max(a["duration_s"], b["duration_s"])
    # Efficacité : 1.0 = parfaitement parallèle, 0 = strictement séquentiel
    efficiency = (
        round((sum_solo - wall) / max(sum_solo - longest, 1e-9), 3)
        if sum_solo > longest
        else 0.0
    )
    efficiency = max(0.0, min(1.0, efficiency))

    # Entrelacement : les deux workers émettent-ils des tokens en alternance ?
    seq = [s for _t, s, e in sorted(timeline) if e.startswith(("TOKEN", "FIRST_TOKEN"))]
    switches = sum(1 for i in range(1, len(seq)) if seq[i] != seq[i - 1])
    both_ok = a["status"] == "success" and b["status"] == "success"

    if not both_ok:
        verdict, reason = (
            "DUAL_PARALLEL = FAILED",
            f"worker en échec: A={a['status']} B={b['status']}",
        )
    elif overlap > 0.15 and switches >= 2:
        verdict, reason = (
            "DUAL_PARALLEL = PASS",
            f"chevauchement {overlap:.2f}s et {switches} alternances de tokens",
        )
    elif overlap > 0.15:
        verdict, reason = (
            "DUAL_PARALLEL = PARTIAL",
            f"fenêtres chevauchées ({overlap:.2f}s) mais tokens non entrelacés",
        )
    else:
        verdict, reason = (
            "DUAL_PARALLEL = FAILED",
            f"exécution sérialisée (chevauchement {overlap:.3f}s)",
        )

    journal.emit(
        "DIAGNOSTIC",
        component="benchmark",
        verdict=verdict,
        reason=reason,
        overlap_s=round(overlap, 3),
        efficiency=efficiency,
        wall_s=round(wall, 3),
    )

    return {
        "verdict": verdict,
        "reason": reason,
        "wall_s": round(wall, 3),
        "sum_solo_s": round(sum_solo, 3),
        "overlap_s": round(overlap, 3),
        "parallel_efficiency": efficiency,
        "token_switches": switches,
        "runs": runs,
        "timeline": [(round(t - t0, 4), s, e) for t, s, e in sorted(timeline)],
        "journal": str(journal.path),
    }


def render_timeline(res: dict, limit: int = 24) -> str:
    lines = ["PREUVE DE PARALLÉLISME (t=0 au lancement, secondes)", "-" * 52]
    for t, slot, ev in res["timeline"][:limit]:
        lines.append(f"  {t:8.4f}  {slot:9s} {ev}")
    if len(res["timeline"]) > limit:
        lines.append(f"  … {len(res['timeline']) - limit} événements supplémentaires")
    lines += [
        "-" * 52,
        f"  wall={res['wall_s']}s  somme_solo={res['sum_solo_s']}s  "
        f"overlap={res['overlap_s']}s  efficacité={res['parallel_efficiency']}",
        f"  {res['verdict']} — {res['reason']}",
    ]
    return "\n".join(lines)


def render_runs(runs: list[dict]) -> str:
    head = f"{'WORKER':10s} {'MODEL':32s} {'STATUS':10s} {'TTFT':>8s} {'DUR':>8s} {'TOK/S':>8s} {'CHARS':>7s}"
    lines = [head, "-" * len(head)]
    for r in runs:
        tps = r["metrics"].get("tokens_per_second", UNAVAILABLE)
        tps = f"{tps:.1f}" if isinstance(tps, (int, float)) else "n/a"
        ttft = f"{r['ttft_s']:.2f}s" if r["ttft_s"] else "n/a"
        lines.append(
            f"{r['worker']:10s} {r['model'][:32]:32s} {r['status']:10s} "
            f"{ttft:>8s} {r['duration_s']:>7.2f}s {tps:>8s} {r['chars']:>7d}"
        )
    return "\n".join(lines)
