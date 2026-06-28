#!/usr/bin/env python3
"""
MODE AUDIT / DEEP RESEARCH — moteur JARVIS OS.

Pipeline multi-vagues : init → scan-local → scan-web → multi-agents → rapport + TODO.
Profils : tech / business / souverainete / ops / full / b2b
Modes   : fast / standard / deep
Analyse IA déléguée à la cascade locale (lm-ask.sh : Ollama local → cloud).

Usage :
  jarvis-audit run --target ./workspace --topic "boutique JARVIS OS" --profile full --mode deep
  jarvis-audit scan-local --target .
  jarvis-audit multi-agents --context audit-runs/XXX/context.json --agents tech,business
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LM_ASK = os.path.expanduser("~/jarvis/scripts/lm-ask.sh")
CONFIG_PATH = ROOT / "AUDIT_CONFIG.yaml"


# ─────────────────────────── utilitaires ───────────────────────────
def c(s, color):
    cols = {
        "g": "\033[32m",
        "y": "\033[33m",
        "b": "\033[36m",
        "r": "\033[31m",
        "0": "\033[0m",
    }
    return f"{cols.get(color, '')}{s}{cols['0']}"


def log(phase, msg):
    print(f"{c('[' + phase + ']', 'b')} {msg}", flush=True)


def load_config():
    """Parseur YAML minimal (sans dépendance) suffisant pour AUDIT_CONFIG."""
    try:
        import yaml  # si dispo

        return yaml.safe_load(CONFIG_PATH.read_text())
    except Exception:
        pass
    # Fallback : config en dur (agents/prompts essentiels)
    return {
        "profiles": {
            "tech": {"agents": ["tech"]},
            "business": {"agents": ["business"]},
            "souverainete": {"agents": ["legal"]},
            "ops": {"agents": ["ops"]},
            "full": {"agents": ["tech", "business", "legal", "ops"]},
            "b2b": {"agents": ["business", "legal"]},
        },
        "modes": {
            "fast": {"waves": ["local"], "agent_max_tokens": 800, "web": False},
            "standard": {
                "waves": ["local", "web"],
                "agent_max_tokens": 1500,
                "web": True,
            },
            "deep": {
                "waves": ["local", "web", "multi", "synth"],
                "agent_max_tokens": 3000,
                "web": True,
            },
        },
        "agents": {
            "tech": "Auditeur TECHNIQUE senior. Architecture, dette technique, risques, quick-wins, 5 actions priorisées. FR, concis.",
            "business": "Auditeur BUSINESS. Offres, pricing, tunnel, positionnement. Forces/faiblesses + 5 actions croissance. FR.",
            "legal": "Auditeur SOUVERAINETÉ. RGPD, CLOUD Act, NIS2, IA Act, logs, secrets. Risques classés + remédiations. FR.",
            "ops": "Auditeur OPS/SRE. Monitoring, résilience, backups, services. Points de défaillance + 5 actions. FR.",
        },
        "scan_local": {
            "secret_patterns": [
                r"api[_-]?key",
                "secret",
                "token",
                "password",
                r"sk-[A-Za-z0-9]{20}",
            ],
            "rgpd_markers": [
                "rgpd",
                "gdpr",
                "mentions légales",
                "données personnelles",
                "privacy",
            ],
            "ignore_dirs": [
                ".git",
                "node_modules",
                ".venv",
                "__pycache__",
                ".cache",
                "dist",
                "build",
            ],
        },
    }


def ask_cascade(system, prompt, max_tokens=1500):
    """Délègue l'analyse à la cascade locale (lm-ask.sh)."""
    if not os.path.exists(LM_ASK):
        return "[cascade indisponible : lm-ask.sh absent]"
    full = f"{system}\n\n=== CONTEXTE ===\n{prompt}"
    try:
        r = subprocess.run(
            ["bash", LM_ASK, "--max", str(max_tokens), full],
            capture_output=True,
            text=True,
            timeout=180,
        )
        return r.stdout.strip() or f"[cascade vide] {r.stderr.strip()[:120]}"
    except subprocess.TimeoutExpired:
        return "[cascade timeout]"
    except Exception as e:
        return f"[cascade erreur: {e}]"


def run_dir(target, topic):
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = re.sub(r"[^a-z0-9]+", "-", (topic or "audit").lower())[:30].strip("-")
    d = Path.cwd() / "audit-runs" / f"{ts}_{slug}"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ─────────────────────────── Phase 0 : init ───────────────────────────
def phase_init(target, topic, client, profile, mode, cfg, url=""):
    log("INIT", f"profil={profile} mode={mode} target={target}")
    prof = cfg["profiles"].get(profile, cfg["profiles"]["full"])
    md = cfg["modes"].get(mode, cfg["modes"]["standard"])
    ctx = {
        "topic": topic,
        "client": client,
        "url": url,
        "profile": profile,
        "mode": mode,
        "target": str(Path(target).resolve()),
        "agents": prof["agents"],
        "waves": md["waves"],
        "max_tokens": md["agent_max_tokens"],
        "web": md.get("web", False),
        "started": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    log("INIT", f"vagues={ctx['waves']} agents={ctx['agents']}")
    return ctx


# ─────────────────────────── Phase 1 : scan local ───────────────────────────
def phase_scan_local(ctx, cfg):
    target = Path(ctx["target"])
    sl = cfg["scan_local"]
    ignore = set(sl["ignore_dirs"])
    log("WAVE1", f"scan local de {target}")
    langs, files, total_size, key_files = {}, 0, 0, []
    secret_hits, rgpd_hits = [], 0
    sec_re = re.compile("|".join(sl["secret_patterns"]), re.I)
    rgpd_re = re.compile("|".join(sl["rgpd_markers"]), re.I)
    EXT = {
        ".py": "Python",
        ".js": "JS",
        ".ts": "TS",
        ".sh": "Shell",
        ".md": "Markdown",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".json": "JSON",
        ".html": "HTML",
        ".css": "CSS",
        ".go": "Go",
        ".rs": "Rust",
        ".java": "Java",
        ".sql": "SQL",
        ".tsx": "React",
    }
    KEY = {
        "dockerfile",
        "docker-compose.yml",
        "package.json",
        "requirements.txt",
        "readme.md",
        ".env",
        "makefile",
        "pyproject.toml",
        "cargo.toml",
    }
    for dp, dns, fns in os.walk(target):
        dns[:] = [d for d in dns if d not in ignore and not d.startswith(".")]
        for fn in fns:
            files += 1
            p = Path(dp) / fn
            ext = p.suffix.lower()
            if ext in EXT:
                langs[EXT[ext]] = langs.get(EXT[ext], 0) + 1
            if fn.lower() in KEY:
                key_files.append(str(p.relative_to(target)))
            try:
                total_size += p.stat().st_size
            except OSError:
                pass
            # scan secrets/rgpd sur fichiers texte légers
            if (
                ext
                in (
                    ".py",
                    ".js",
                    ".ts",
                    ".sh",
                    ".env",
                    ".yaml",
                    ".yml",
                    ".json",
                    ".md",
                    ".html",
                )
                and files < 5000
            ):
                try:
                    txt = p.read_text(errors="ignore")[:50000]
                    for m in sec_re.finditer(txt):
                        ln = txt[: m.start()].count("\n") + 1
                        # heuristique : valeur assignée après le mot-clé
                        seg = txt[m.start() : m.start() + 80]
                        if re.search(r"[=:]\s*['\"][^'\"]{12,}", seg):
                            secret_hits.append(f"{p.relative_to(target)}:{ln}")
                    if rgpd_re.search(txt):
                        rgpd_hits += 1
                except Exception:
                    pass
    # git
    git = {}
    if (target / ".git").exists():

        def g(args):
            try:
                return subprocess.run(
                    ["git", "-C", str(target)] + args,
                    capture_output=True,
                    text=True,
                    timeout=10,
                ).stdout.strip()
            except Exception:
                return ""

        git = {
            "branch": g(["branch", "--show-current"]),
            "commits": g(["rev-list", "--count", "HEAD"]),
            "last": g(["log", "-1", "--format=%cd %s", "--date=short"]),
            "contributors": g(["shortlog", "-sn", "--all"]).count("\n") + 1
            if g(["shortlog", "-sn", "--all"])
            else 0,
        }
    result = {
        "files": files,
        "size_mb": round(total_size / 1e6, 1),
        "languages": dict(sorted(langs.items(), key=lambda x: -x[1])),
        "key_files": key_files[:20],
        "git": git,
        "secrets_suspects": secret_hits[:15],
        "rgpd_markers_files": rgpd_hits,
    }
    log(
        "WAVE1",
        f"{files} fichiers, {result['size_mb']} Mo, langs={list(result['languages'])[:4]}, "
        f"{len(secret_hits)} secrets suspects, {rgpd_hits} fichiers RGPD",
    )
    return result


# ─────────────────────────── Phase 2 : scan web ───────────────────────────
def _curl(url, max_bytes=400000):
    """Fetch HTTP autonome via curl (suit redirections, UA navigateur)."""
    try:
        r = subprocess.run(
            [
                "curl",
                "-fsSL",
                "--max-time",
                "20",
                "-A",
                "Mozilla/5.0 (JARVIS-Audit)",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=25,
        )
        return r.stdout[:max_bytes] if r.returncode == 0 else ""
    except Exception:
        return ""


def fetch_site(url):
    """Extrait titre, headings, sections clés (offres/pricing/légal) + sitemap."""
    if not url:
        return {}
    if not re.match(r"^https?://", url):
        url = "https://" + url
    html = _curl(url)
    if not html:
        return {"url": url, "error": "injoignable"}
    txt = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S | re.I)

    def grab(tag):
        return [
            re.sub(r"<[^>]+>", "", m).strip()[:120]
            for m in re.findall(rf"<{tag}[^>]*>(.*?)</{tag}>", txt, re.S | re.I)
            if re.sub(r"<[^>]+>", "", m).strip()
        ]

    title = (grab("title") or [""])[0]
    plain = re.sub(r"<[^>]+>", " ", txt)
    plain = re.sub(r"\s+", " ", plain).lower()
    SECT = {
        "offres": ["offre", "service", "solution", "produit"],
        "pricing": ["tarif", "prix", "pricing", "abonnement", "€", "forfait"],
        "legal": ["mentions légales", "rgpd", "cgv", "confidentialité", "privacy"],
        "contact": ["contact", "rendez-vous", "demander un devis", "réserver"],
    }
    sections = {k: any(w in plain for w in ws) for k, ws in SECT.items()}
    # sitemap
    sm = _curl(url.rstrip("/") + "/sitemap.xml", 200000)
    sm_urls = re.findall(r"<loc>(.*?)</loc>", sm)[:25]
    return {
        "url": url,
        "title": title,
        "h1": grab("h1")[:8],
        "h2": grab("h2")[:12],
        "sections_detected": sections,
        "sitemap_urls": sm_urls,
        "bytes": len(html),
    }


def phase_scan_web(ctx):
    log("WAVE2", "collecte externe (site + GitHub)")
    out = {"github": {}, "site": {}, "note": ""}
    client = ctx.get("client") or ""
    url = ctx.get("url") or ""
    # Site client (curl autonome)
    if url:
        out["site"] = fetch_site(url)
        if out["site"].get("error"):
            log("WAVE2", c(f"site {url}: {out['site']['error']}", "y"))
        else:
            det = [k for k, v in out["site"].get("sections_detected", {}).items() if v]
            log(
                "WAVE2",
                f"site ✓ '{out['site'].get('title', '')[:50]}' "
                f"sections={det} sitemap={len(out['site'].get('sitemap_urls', []))}",
            )
    # GitHub via gh (si dispo et client = user github)
    if client:
        try:
            r = subprocess.run(
                [
                    "gh",
                    "api",
                    f"users/{client}/repos?per_page=10",
                    "--jq",
                    '.[] | .name + " — " + (.description // "")',
                ],
                capture_output=True,
                text=True,
                timeout=20,
            )
            if r.returncode == 0:
                out["github"]["repos"] = [l for l in r.stdout.strip().split("\n") if l][
                    :10
                ]
        except Exception:
            pass
    out["note"] = (
        "LinkedIn nécessite un connecteur authentifié (à brancher : MCP LinkedIn). "
        "Web search large : passer par la cascade/WebSearch en amont."
    )
    log("WAVE2", f"github repos: {len(out['github'].get('repos', []))}")
    return out


# ─────────────────────────── Phase 3 : multi-agents ───────────────────────────
def phase_multi_agents(ctx, cfg, scan_local, scan_web):
    reports = {}
    base_ctx = json.dumps(
        {"topic": ctx["topic"], "scan_local": scan_local, "scan_web": scan_web},
        ensure_ascii=False,
        indent=1,
    )[:6000]
    for agent in ctx["agents"]:
        sysmsg = cfg["agents"].get(agent, f"Auditeur {agent}.")
        log("WAVE3", f"agent {agent} en analyse (cascade)…")
        reports[agent] = ask_cascade(sysmsg, base_ctx, ctx["max_tokens"])
        log("WAVE3", f"agent {agent} ✓ ({len(reports[agent])} car.)")
    return reports


# ─────────────────────────── Phase 4 : synthèse + TODO ───────────────────────────
def phase_synth(ctx, reports, outdir):
    log("SYNTH", "génération rapport + TODO")
    joined = "\n\n".join(f"### Agent {a}\n{r}" for a, r in reports.items())
    todo = ask_cascade(
        "Tu es chef de projet. À partir des rapports d'audit, produis UNE TODO exécutable "
        "priorisée (format: - [ ] [P1/P2/P3] action — pourquoi). 15 items max. FR.",
        joined,
        2000,
    )
    return joined, todo


def write_reports(ctx, scan_local, scan_web, reports, joined, todo, outdir):
    (outdir / "context.json").write_text(json.dumps(ctx, ensure_ascii=False, indent=2))
    (outdir / "audit_scan_local.json").write_text(
        json.dumps(scan_local, ensure_ascii=False, indent=2)
    )
    if scan_web:
        (outdir / "audit_scan_web.json").write_text(
            json.dumps(scan_web, ensure_ascii=False, indent=2)
        )
    rpt = [
        f"# Rapport d'audit — {ctx.get('topic') or ctx['target']}",
        f"> Profil **{ctx['profile']}** · Mode **{ctx['mode']}** · {ctx['started']}\n",
        "## 1. Scan local (Wave 1)",
        f"- Fichiers : {scan_local['files']} ({scan_local['size_mb']} Mo)",
        f"- Langages : {scan_local['languages']}",
        f"- Fichiers clés : {', '.join(scan_local['key_files']) or '—'}",
        f"- Git : {scan_local['git'] or '—'}",
        f"- ⚠️ Secrets suspects : {len(scan_local['secrets_suspects'])} — {scan_local['secrets_suspects'][:5]}",
        f"- Marqueurs RGPD : {scan_local['rgpd_markers_files']} fichiers\n",
    ]
    if scan_web:
        rpt += ["## 2. Collecte externe (Wave 2)"]
        site = scan_web.get("site") or {}
        if site and not site.get("error"):
            det = [k for k, v in site.get("sections_detected", {}).items() if v]
            rpt += [
                f"- Site : [{site.get('title', '')}]({site.get('url', '')})",
                f"- Accroche (h1) : {' / '.join(site.get('h1', [])) or '—'}",
                f"- Sections détectées : {', '.join(det) or '—'}",
                f"- Pages sitemap : {len(site.get('sitemap_urls', []))}",
            ]
        elif site.get("error"):
            rpt += [f"- Site : {site.get('url', '')} — {site['error']}"]
        rpt += [
            f"- GitHub repos : {scan_web['github'].get('repos', [])}",
            f"- Note : {scan_web['note']}\n",
        ]
    if reports:
        rpt += ["## 3. Analyse multi-agents (Wave 3)", joined, ""]
    if todo:
        rpt += ["## 4. Plan d'action (TODO exécutable)", todo, ""]
        (outdir / "TODO.md").write_text("# TODO Audit\n\n" + todo)
    (outdir / "RAPPORT.md").write_text("\n".join(rpt))
    return outdir / "RAPPORT.md"


# ─────────────────────────── orchestration ───────────────────────────
def cmd_run(a):
    cfg = load_config()
    ctx = phase_init(
        a.target, a.topic, a.client, a.profile, a.mode, cfg, getattr(a, "url", "")
    )
    outdir = run_dir(a.target, a.topic)
    ctx["outdir"] = str(outdir)
    scan_local = phase_scan_local(ctx, cfg)
    scan_web = phase_scan_web(ctx) if (ctx["web"] and "web" in ctx["waves"]) else {}
    reports = (
        phase_multi_agents(ctx, cfg, scan_local, scan_web)
        if "multi" in ctx["waves"] or a.mode != "fast"
        else {}
    )
    joined, todo = ("", "")
    if reports and ("synth" in ctx["waves"] or a.mode == "deep"):
        joined, todo = phase_synth(ctx, reports, outdir)
    elif reports:
        joined = "\n\n".join(f"### Agent {k}\n{v}" for k, v in reports.items())
    path = write_reports(ctx, scan_local, scan_web, reports, joined, todo, outdir)
    print()
    log("DONE", c(f"Rapport → {path}", "g"))
    print(f"\n{c('Dossier run:', 'y')} {outdir}")
    return 0


def cmd_scan_local(a):
    cfg = load_config()
    ctx = phase_init(a.target, None, None, "tech", "fast", cfg)
    r = phase_scan_local(ctx, cfg)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0


def cmd_scan_web(a):
    cfg = load_config()
    ctx = phase_init(".", a.topic, a.client, "business", "standard", cfg, a.url)
    r = phase_scan_web(ctx)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0


def main():
    p = argparse.ArgumentParser(
        prog="jarvis-audit", description="MODE AUDIT / DEEP RESEARCH"
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("run", help="pipeline complet")
    pr.add_argument("--target", default=".")
    pr.add_argument("--topic", default="")
    pr.add_argument("--client", default="")
    pr.add_argument(
        "--profile",
        default="full",
        choices=["tech", "business", "souverainete", "ops", "full", "b2b"],
    )
    pr.add_argument("--mode", default="standard", choices=["fast", "standard", "deep"])
    pr.add_argument("--url", default="", help="site client à fetcher (Wave 2)")
    pr.set_defaults(func=cmd_run)
    ps = sub.add_parser("scan-local", help="Wave 1 seule")
    ps.add_argument("--target", default=".")
    ps.set_defaults(func=cmd_scan_local)
    pw = sub.add_parser("scan-web", help="Wave 2 seule (site + GitHub)")
    pw.add_argument("--url", default="", help="site à fetcher")
    pw.add_argument("--client", default="", help="user GitHub")
    pw.add_argument("--topic", default="")
    pw.set_defaults(func=cmd_scan_web)
    a = p.parse_args()
    sys.exit(a.func(a))


if __name__ == "__main__":
    main()
