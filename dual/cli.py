"""CLI `jarvis-dual` — une commande = une responsabilité = un code retour."""

from __future__ import annotations

import argparse
import json
import sys

from . import benchmark as bench
from . import board as board_mod
from . import checkpoint as cp
from . import config as cfgmod
from . import doctor as doc
from . import watchdog as wd
from .dispatcher import DualDispatcher, aggregate


def _cfg(args):
    cfg = cfgmod.discover() if getattr(args, "discover", True) else cfgmod.load()
    if not cfg.get("workers"):
        print(
            "BLOCKED: aucun worker disponible. Lance `jarvis-dual doctor`.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return cfg


def cmd_doctor(args):
    checks = doc.run(probe_inference=not args.fast)
    print(
        json.dumps(checks, indent=2, ensure_ascii=False)
        if args.json
        else doc.render(checks)
    )
    return doc.exit_code(checks)


def cmd_discover(args):
    cfg = cfgmod.discover(verbose=True)
    if args.save:
        p = cfgmod.save(cfg)
        print(f"config écrite: {p}")
    print(
        json.dumps(
            {
                "providers": {
                    k: {"base_url": v["base_url"], "models": len(v["models"])}
                    for k, v in cfg["providers"].items()
                },
                "workers": cfg["workers"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if cfg["workers"] else 2


def cmd_models(args):
    cfg = cfgmod.discover()
    for alias, p in cfg["providers"].items():
        print(f"\n{alias}  ({p['base_url']})")
        for m in p["models"]:
            print(f"  - {m}")
    return 0


def cmd_workers(args):
    cfg = _cfg(args)
    d = DualDispatcher(cfg)
    for slot, w in d.workers.items():
        h = w.health()
        print(
            f"{slot:9s} {w.provider.name:10s} {w.model:34s} "
            f"{'HEALTHY' if h['healthy'] else 'UNHEALTHY'}  {h['server']['detail']}"
        )
    return 0


def cmd_run(args):
    cfg = _cfg(args)
    d = DualDispatcher(cfg, job_id=args.job)
    out = d.run(
        args.prompt,
        mode=args.mode,
        system=args.system,
        resume=args.resume,
        max_tokens=args.max_tokens,
    )
    if args.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0 if out["status"] == "SUCCESS" else 1
    agg = aggregate(out["results"], strategy=args.aggregate)
    print(f"\n=== JOB {out['job_id']} [{out['mode']}] {out['status']} ===")
    for r in out["results"]:
        m = r.get("metrics", {})
        print(
            f"  {r.get('task', '?'):16s} {r['worker']:9s} {r['status']:10s} "
            f"ttft={m.get('ttft_ms')}ms dur={m.get('duration_ms')}ms"
        )
    print(f"\n--- agrégation ({agg['strategy']}) ---\n{agg.get('content', '')[:2000]}")
    print(f"\njournal    : {out['journal']}\ncheckpoint : {out['checkpoint']}")
    return 0 if out["status"] == "SUCCESS" else 1


def cmd_test(args):
    """`dual test` — détecte A et B, lance une tâche courte sur les deux."""
    cfg = _cfg(args)
    if len(cfg["workers"]) < 2:
        print("DUAL TEST = BLOCKED — un seul worker disponible", file=sys.stderr)
        return 2
    res = bench.dual(cfg, max_tokens=args.max_tokens, job_id=cp.new_job_id("dualtest"))
    print(bench.render_runs(res["runs"]))
    print()
    print(bench.render_timeline(res))
    return 0 if res["verdict"].endswith("PASS") else 1


def cmd_benchmark(args):
    cfg = _cfg(args)
    print("— SOLO —")
    solo = bench.solo(cfg, max_tokens=args.max_tokens)
    print(bench.render_runs(solo))
    print("\n— DUAL (A+B simultanés) —")
    res = bench.dual(cfg, max_tokens=args.max_tokens, job_id=cp.new_job_id("bench"))
    print(bench.render_runs(res["runs"]))
    print()
    print(bench.render_timeline(res))
    if args.json:
        print(
            json.dumps(
                {"solo": solo, "dual": res}, indent=2, ensure_ascii=False, default=str
            )
        )
    return 0 if res["verdict"].endswith("PASS") else 1


def cmd_jobs(args):
    jobs = cp.list_jobs()
    if not jobs:
        print("aucun job")
        return 0
    print(f"{'JOB_ID':40s} {'STATUS':12s} {'MODE':10s} {'ÉTAPES':8s}")
    for j in jobs[: args.limit]:
        print(f"{j['job_id']:40s} {j['status']:12s} {j['mode']:10s} {j['progress']:8s}")
    return 0


def cmd_replay(args):
    print(board_mod.replay(args.job_id))
    return 0


def cmd_board(args):
    if args.watch:
        board_mod.watch(interval=args.interval)
    else:
        print(board_mod.render(probe=not args.fast))
    return 0


def cmd_watchdog(args):
    rep = wd.sweep(max_age_s=args.max_age, act=args.act)
    print(wd.render(rep))
    return 0


def cmd_recover(args):
    store = cp.JobStore(args.job_id)
    if not store.load():
        print(f"job inconnu: {args.job_id}", file=sys.stderr)
        return 2
    if not store.resumable():
        print(f"{args.job_id}: rien à reprendre (toutes les tâches en SUCCESS)")
        return 0
    cfg = _cfg(args)
    d = DualDispatcher(cfg, job_id=args.job_id)
    out = d.run(
        "",
        mode=store.load().get("mode", "single"),
        resume=True,
        max_tokens=args.max_tokens,
    )
    print(f"REPRISE {args.job_id} → {out['status']}")
    for r in out["results"]:
        print(f"  {r.get('task')} {r['status']} ({r['worker']})")
    return 0 if out["status"] == "SUCCESS" else 1


def build_parser():
    p = argparse.ArgumentParser(
        prog="jarvis-dual", description="JARVIS DUAL ORCHESTRATOR"
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("doctor", help="diagnostic global")
    d.add_argument("--fast", action="store_true", help="sans test d'inférence réel")
    d.add_argument("--json", action="store_true")
    d.set_defaults(func=cmd_doctor)

    d = sub.add_parser("discover", help="sonde les backends et propose A/B")
    d.add_argument("--save", action="store_true", help="écrire dual/config.json")
    d.set_defaults(func=cmd_discover)

    sub.add_parser("models", help="liste les modèles réellement exposés").set_defaults(
        func=cmd_models
    )
    sub.add_parser("workers", help="santé des workers").set_defaults(func=cmd_workers)

    d = sub.add_parser("run", help="exécute une demande")
    d.add_argument("prompt")
    d.add_argument(
        "-m",
        "--mode",
        default="single",
        choices=("single", "parallel", "cascade", "review", "fallback", "pipeline"),
    )
    d.add_argument(
        "-a",
        "--aggregate",
        default="first",
        choices=("first", "best", "merge", "consensus"),
    )
    d.add_argument("-s", "--system")
    d.add_argument("--job")
    d.add_argument("--resume", action="store_true")
    d.add_argument("--max-tokens", type=int, default=400)
    d.add_argument("--json", action="store_true")
    d.set_defaults(func=cmd_run)

    d = sub.add_parser("test", help="test DUAL réel (preuve de concurrence)")
    d.add_argument("--max-tokens", type=int, default=120)
    d.set_defaults(func=cmd_test)

    d = sub.add_parser("benchmark", help="solo A, solo B, puis A+B")
    d.add_argument("--max-tokens", type=int, default=160)
    d.add_argument("--json", action="store_true")
    d.set_defaults(func=cmd_benchmark)

    d = sub.add_parser("jobs", help="liste les jobs")
    d.add_argument("--limit", type=int, default=20)
    d.set_defaults(func=cmd_jobs)

    d = sub.add_parser("replay", help="chronologie exacte d'un job")
    d.add_argument("job_id")
    d.set_defaults(func=cmd_replay)

    d = sub.add_parser("board", help="tableau de bord")
    d.add_argument("--watch", action="store_true")
    d.add_argument("--interval", type=float, default=2.0)
    d.add_argument("--fast", action="store_true")
    d.set_defaults(func=cmd_board)

    d = sub.add_parser("watchdog", help="détecte les jobs figés")
    d.add_argument("--max-age", type=float, default=600.0)
    d.add_argument("--act", action="store_true", help="marquer RECOVERABLE")
    d.set_defaults(func=cmd_watchdog)

    d = sub.add_parser("recover", help="reprend un job interrompu")
    d.add_argument("job_id")
    d.add_argument("--max-tokens", type=int, default=400)
    d.set_defaults(func=cmd_recover)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
