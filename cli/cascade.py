#!/usr/bin/env python3
"""
cascade.py — Cascade Domino Engine
Lazy-load, single-pass, SQL-driven tool orchestration.
"""

import json
import re
import sqlite3
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = "/home/pamerys/jarvis/jarvis_master.db"

# Tokens trop génériques à ignorer lors du matching
STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "jarvis",
    "cli",
    "script",
    "agent",
    "ai",
    "llm",
    "model",
    "tool",
    "run",
    "use",
}


class CascadeEngine:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        # Rien d'autre chargé au __init__ — lazy total

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ── Tokenization ──────────────────────────────────────────────────────────

    def _tokenize(self, text: str) -> list[str]:
        tokens = re.split(r"[\s\-_./,;:!?]+", text.lower())
        return [t for t in tokens if len(t) > 1 and t not in STOP_WORDS]

    # ── Core: SQL lookup ──────────────────────────────────────────────────────

    def resolve(self, query: str) -> list[dict]:
        """
        SQL lookup: query → outils correspondants, triés par priorité.
        Aucun outil n'est chargé ou exécuté.
        """
        tokens = self._tokenize(query)
        if not tokens:
            return []

        conn = self._conn()
        try:
            # Build a LIKE clause per token against keywords JSON
            conditions = " OR ".join("keywords LIKE ?" for _ in tokens)
            params = [f"%{t}%" for t in tokens]
            sql = f"""
                SELECT *, (
                  {" + ".join("(CASE WHEN keywords LIKE ? THEN 1 ELSE 0 END)" for _ in tokens)}
                ) AS match_score
                FROM tool_map
                WHERE loaded = 0 AND ({conditions})
                ORDER BY match_score DESC, priority DESC, usage_count DESC
                LIMIT 20
            """
            # params: once for scoring, once for filter
            rows = conn.execute(sql, params + params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ── Plan generation ───────────────────────────────────────────────────────

    def plan(self, query: str) -> list[dict]:
        """
        Génère le plan domino complet sans rien exécuter.
        Retourne liste ordonnée : [{step, tool, loader, triggers_next, match_score}]
        """
        resolved = self.resolve(query)
        if not resolved:
            return []

        # Build domino chain: BFS expansion via triggers
        visited = set()
        plan_steps = []
        queue = [(r, 0) for r in resolved[:5]]  # top-5 entry points

        conn = self._conn()
        try:
            step = 0
            while queue:
                tool, depth = queue.pop(0)
                name = tool["name"]
                if name in visited or depth > 4:
                    continue
                visited.add(name)

                plan_steps.append(
                    {
                        "step": step,
                        "depth": depth,
                        "tool": name,
                        "category": tool["category"],
                        "loader": tool["loader"],
                        "priority": tool["priority"],
                        "match_score": tool.get("match_score", 0),
                        "triggers_next": json.loads(tool.get("triggers") or "[]"),
                    }
                )
                step += 1

                # Expand triggers into next queue entries
                raw_triggers = json.loads(tool.get("triggers") or "[]")
                for tname in raw_triggers:
                    if tname in visited:
                        continue
                    row = conn.execute(
                        "SELECT * FROM tool_map WHERE name=?", (tname,)
                    ).fetchone()
                    if row:
                        queue.append((dict(row), depth + 1))
        finally:
            conn.close()

        return plan_steps

    # ── Execution ─────────────────────────────────────────────────────────────

    def execute(
        self, plan_steps: list[dict], dry_run: bool = False, query: str = ""
    ) -> dict:
        """
        Exécute le plan en cascade, lazy-load outil par outil.
        dry_run=True → affiche le plan sans exécuter.
        """
        if not plan_steps:
            return {"status": "empty", "steps": 0, "results": []}

        self._print_plan(plan_steps, dry_run)

        if dry_run:
            return {"status": "dry_run", "steps": len(plan_steps), "results": []}

        results = []
        conn = self._conn()

        try:
            for step in plan_steps:
                tool_name = step["tool"]
                loader = step["loader"]
                category = step["category"]

                print(f"\n[step {step['step']}] {tool_name}")
                print(f"  category : {category}")
                print(f"  loader   : {loader}")

                t_start = time.time()
                output, error = self._invoke(loader, query, category)
                latency_ms = int((time.time() - t_start) * 1000)

                status = "ok" if not error else "error"
                results.append(
                    {
                        "step": step["step"],
                        "tool": tool_name,
                        "status": status,
                        "latency_ms": latency_ms,
                        "output": output[:500] if output else "",
                        "error": error[:200] if error else "",
                    }
                )

                print(f"  status   : {status}  latency={latency_ms}ms")
                if output:
                    preview = output[:200].replace("\n", " ")
                    print(f"  output   : {preview}")
                if error:
                    print(f"  error    : {error[:100]}")

                # Update stats in DB
                conn.execute(
                    """UPDATE tool_map SET
                         usage_count = usage_count + 1,
                         last_used = ?
                       WHERE name = ?""",
                    (datetime.now(timezone.utc).isoformat(), tool_name),
                )

                # Log into pipeline_log
                conn.execute(
                    """INSERT INTO pipeline_log
                         (step, machine, model, latency_ms, quality_score)
                       VALUES (?,?,?,?,?)""",
                    (
                        f"cascade:{tool_name}",
                        self._node_from_loader(loader),
                        tool_name,
                        latency_ms,
                        1.0 if status == "ok" else 0.0,
                    ),
                )
                conn.commit()

        finally:
            conn.close()

        ok = sum(1 for r in results if r["status"] == "ok")
        print(f"\n[cascade] Done: {ok}/{len(results)} steps OK")
        return {
            "status": "done",
            "steps": len(results),
            "ok": ok,
            "results": results,
        }

    # ── Single-pass shortcut ──────────────────────────────────────────────────

    def avalanche(self, query: str, dry_run: bool = False) -> dict:
        """resolve → plan → execute en une commande."""
        print(f"[cascade] Query: {query!r}")
        steps = self.plan(query)
        if not steps:
            print("[cascade] No matching tools found.")
            return {"status": "no_match", "query": query}
        return self.execute(steps, dry_run=dry_run, query=query)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _print_plan(self, steps: list[dict], dry_run: bool):
        mode = "[DRY RUN]" if dry_run else "[PLAN]"
        print(f"\n{mode} {len(steps)} step(s) in cascade:")
        print(f"  {'#':>3}  {'D':>2}  {'PRI':>3}  {'SCORE':>5}  {'CATEGORY':10}  TOOL")
        print("  " + "-" * 72)
        for s in steps:
            triggers = s["triggers_next"]
            t_str = f" → {triggers}" if triggers else ""
            print(
                f"  {s['step']:>3}  {s['depth']:>2}  {s['priority']:>3}"
                f"  {s.get('match_score', 0):>5}  {s['category']:10}  {s['tool']}{t_str}"
            )
        print()

    def _invoke(self, loader: str, query: str, category: str) -> tuple[str, str]:
        """Lazy-load: invoke the tool loader. Returns (stdout, stderr)."""
        # MCP / skill → symbolic, no actual subprocess
        if category in ("skill", "mcp") or loader.startswith("claude-code-skill:"):
            return f"[{category}] {loader} — symbolic invocation (no subprocess)", ""

        # model via lm-ask.sh
        if "lm-ask.sh" in loader or "ollama run" in loader:
            script = "/home/pamerys/jarvis/scripts/lm-ask.sh"
            if not Path(script).exists():
                return "", f"lm-ask.sh not found at {script}"
            try:
                cmd = ["bash", script, query[:200]]
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                return r.stdout.strip(), r.stderr.strip()
            except subprocess.TimeoutExpired:
                return "", "timeout"
            except Exception as e:
                return "", str(e)

        # docker exec agent
        if loader.startswith("docker exec"):
            parts = loader.split()
            container = parts[2] if len(parts) > 2 else ""
            try:
                r = subprocess.run(
                    [
                        "docker",
                        "exec",
                        container,
                        "echo",
                        f"jarvis-cascade:{query[:100]}",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if r.returncode == 0:
                    return r.stdout.strip(), ""
                return "", r.stderr.strip()
            except Exception as e:
                return "", str(e)

        # cli script
        if category == "cli":
            parts = loader.split()
            try:
                r = subprocess.run(
                    parts[:2] + ["--help"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                return r.stdout.strip()[:200] or "(no help)", r.stderr.strip()[:100]
            except Exception as e:
                return "", str(e)

        # generic fallback
        return f"[{category}] loader={loader} — no executor defined", ""

    def _node_from_loader(self, loader: str) -> str:
        if "192.168.1.85" in loader or "M1" in loader:
            return "M1"
        if "192.168.1.26" in loader or "M2" in loader:
            return "M2"
        if "ollama" in loader or "OL1" in loader:
            return "OL1"
        if "docker" in loader:
            return "docker"
        return "local"


# ── CLI standalone ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(prog="cascade", description="Cascade Domino Engine")
    p.add_argument("action", choices=["resolve", "plan", "execute", "avalanche"])
    p.add_argument("query", nargs="+", help="Query text")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--db", default=DB_PATH)
    args = p.parse_args()

    engine = CascadeEngine(args.db)
    q = " ".join(args.query)

    if args.action == "resolve":
        hits = engine.resolve(q)
        for h in hits:
            print(
                f"  [{h['category']:8}] {h['name']:40} score={h.get('match_score', 0)}"
            )

    elif args.action == "plan":
        steps = engine.plan(q)
        engine._print_plan(steps, dry_run=True)

    elif args.action in ("execute", "avalanche"):
        engine.avalanche(q, dry_run=args.dry_run)
