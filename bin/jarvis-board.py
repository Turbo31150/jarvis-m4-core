#!/usr/bin/env python3
"""jarvis-board — Centre de Commande JARVIS (port 8890).

Logique capturee sur le board de rem-linux (:3200 « JARVIS OpenClaw — Centre de
Commande ») puis adaptee a l'ecosysteme de M1 : memes primitives (sonde /health
par service, cartes KPI, grille de containers cliquables, journal, soumission de
tache, rafraichissement 30 s), mais branchees sur les briques reelles d'ici —
hub :18800, LMS :1234, ollama :11434, planning :8899, tampon M6, bibliotheque
vivante, agent_index (319 agents / 20 familles).

Deux ajouts par rapport a l'original : les agents portent un avatar deterministe
(pas d'asset externe, le board reste monofichier) et l'etat de sante est calcule
cote serveur, pas dans le navigateur.

Stdlib seule. Lecture SQLite en mode ro (jamais de verrou a chaud).
"""

from __future__ import annotations

import json
import os
import socket
import sqlite3
import subprocess
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = int(os.environ.get("BOARD_PORT", "8890"))
HOME = Path("/home/pamerys")
MASTER_DB = HOME / "jarvis/jarvis_master.db"
LOGS_DB = HOME / "jarvis/logs/jarvis_logs.db"
BLOCS_INDEX = HOME / "labo/bibliotheque/lib/BLOCS-INDEX.tsv"
TAMPON_PY = HOME / "jarvis/scripts/m6_tampon.py"

# (cle, libelle, icone, url de sonde, hote logique)
SERVICES = [
    ("hub", "Hub LLM", "\U0001f9e0", "http://127.0.0.1:18800/v1/models", "M1"),
    ("dash", "Dashboard", "\U0001f4ca", "http://127.0.0.1:18801/", "M1"),
    ("ccr", "CCR proxy", "\U0001f501", "http://127.0.0.1:18802/", "M1"),
    ("sqlbridge", "SQL Bridge", "\U0001f5c4", "http://127.0.0.1:18803/", "M1"),
    ("lms", "LM Studio", "\U0001f39b", "http://127.0.0.1:1234/v1/models", "M1"),
    ("ollama", "Ollama", "\U0001f999", "http://127.0.0.1:11434/api/tags", "OL1"),
    ("planning", "Planning", "\U0001f4c5", "http://127.0.0.1:8899/data", "M1"),
    ("browseros", "BrowserOS MCP", "\U0001f310", "http://127.0.0.1:9201/health", "M1"),
    ("n8n", "n8n", "⚙", "http://127.0.0.1:9742/healthz", "M1"),
    ("whisper", "WhisperFlow", "\U0001f399", "http://127.0.0.1:9743/health", "M1"),
]

# Un avatar = un emoji + une teinte, derives de la famille. Deterministe : la
# meme famille rend toujours le meme visuel, d'un rafraichissement a l'autre.
FAMILY_AVATAR = {
    "jarvis": ("\U0001f9e0", "#10b981"),
    "chef": ("\U0001f451", "#f59e0b"),
    "cowork": ("\U0001f91d", "#3b82f6"),
    "ops": ("\U0001f527", "#8b5cf6"),
    "run": ("▶", "#06b6d4"),
    "dev": ("\U0001f4bb", "#ec4899"),
    "business": ("\U0001f4bc", "#eab308"),
    "monitoring": ("\U0001f4c8", "#14b8a6"),
    "comms": ("\U0001f4e1", "#f97316"),
    "omega": ("Ω", "#a855f7"),
    "data": ("\U0001f5c3", "#0ea5e9"),
    "ai": ("✨", "#22c55e"),
    "automation": ("\U0001f916", "#6366f1"),
    "pilotage": ("\U0001f9ed", "#f43f5e"),
    "openclaw": ("\U0001f43e", "#84cc16"),
    "misc": ("\U0001f4e6", "#94a3b8"),
    "trading": ("\U0001f4b9", "#ef4444"),
    "web-api": ("\U0001f517", "#38bdf8"),
    "systeme": ("\U0001f5a5", "#a3a3a3"),
    "rust-go": ("\U0001f980", "#fb923c"),
}
AVATAR_FALLBACK = ("\U0001f7e2", "#64748b")


def probe(url: str, timeout: float = 2.5) -> dict:
    """Sonde un endpoint. Sonder avant de router : un port ouvert ne suffit pas,
    on veut un code HTTP. Toute erreur est capturee — une sonde ne doit jamais
    faire tomber le board."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "jarvis-board"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"up": True, "code": r.status}
    except urllib.error.HTTPError as e:
        # Un 404/401 prouve qu'un serveur repond : le service est vivant.
        return {"up": True, "code": e.code}
    except Exception as e:
        return {"up": False, "code": 0, "err": type(e).__name__}


def ro_query(db: Path, sql: str, default=None):
    if not db.exists():
        return default
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=5)
        con.row_factory = sqlite3.Row
        try:
            return [dict(r) for r in con.execute(sql).fetchall()]
        finally:
            con.close()
    except Exception:
        return default


def read_agents() -> dict:
    rows = (
        ro_query(
            MASTER_DB,
            "SELECT family, COUNT(*) n FROM agent_index "
            "GROUP BY family ORDER BY n DESC",
        )
        or []
    )
    fams = []
    for r in rows:
        fam = (r.get("family") or "misc").strip()
        emoji, color = FAMILY_AVATAR.get(fam, AVATAR_FALLBACK)
        fams.append({"family": fam, "n": r["n"], "emoji": emoji, "color": color})
    return {"total": sum(f["n"] for f in fams), "familles": fams}


def read_biblio() -> dict:
    n = 0
    try:
        with BLOCS_INDEX.open("rb") as fh:
            n = max(0, sum(1 for _ in fh) - 1)  # l'entete n'est pas un bloc
    except Exception:
        pass
    return {"blocs": n, "index": str(BLOCS_INDEX)}


def read_tampon() -> dict:
    try:
        out = subprocess.run(
            ["python3", str(TAMPON_PY), "status"],
            capture_output=True,
            text=True,
            timeout=20,
        )
        return json.loads(out.stdout)
    except Exception as e:
        return {"ok": False, "err": type(e).__name__}


def read_failed_services() -> list:
    failed = []
    for scope in (["systemctl"], ["systemctl", "--user"]):
        try:
            out = subprocess.run(
                scope + ["list-units", "--state=failed", "--no-legend", "--no-pager"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            for line in out.stdout.splitlines():
                parts = line.replace("●", "").split()
                if parts:
                    failed.append(parts[0])
        except Exception:
            pass
    return failed


def read_plan() -> dict:
    rows = ro_query(MASTER_DB, "SELECT COUNT(*) n FROM plan") or [{"n": 0}]
    return {"entrees": rows[0].get("n", 0)}


def health_verdict(services: list, failed: list) -> dict:
    """TODO(turbo) — regle de sante globale du board.

    Les donnees brutes sont la : `services` (chaque entree a un booleen `up` et
    une cle `key`) et `failed` (noms des unites systemd en echec). Il reste a
    decider ce que le bandeau affiche.

    C'est un arbitrage metier, pas une evidence technique : tous les services ne
    pesent pas pareil. Le hub :18800 en panne coupe toute la cascade 0-token,
    alors qu'un BrowserOS MCP mort (panne connue, CDP jamais ouvert) ne bloque
    rien d'essentiel. Un seuil purement quantitatif ("3 services down = rouge")
    ferait donc clignoter le board en rouge pour une brique optionnelle, et le
    laisserait vert quand la brique vitale tombe.

    Retourner : {"level": "OK"|"DEGRADE"|"CRITIQUE", "why": "<une phrase>"}

    Regle issue d'un consensus MAO (M1 qwen3.5-9b poids 1.8 + hub gemma-4-12b
    poids 1.4 ; OL1 muet). Les deux propositions ont ete CORRIGEES sur un point
    chacune : M1 mettait DEGRADE des que BrowserOS tombe — badge orange a
    perpetuite puisque sa panne est permanente ; le hub renvoyait OK dans ce
    meme cas, ce qui court-circuitait toutes les conditions suivantes.
    """
    # Une panne permanente connue n'est pas un signal : c'est du bruit. On
    # l'ecarte du calcul plutot que de la laisser saturer le badge.
    IGNORES = {"browseros"}
    VITAUX = {"hub"}

    juges = [s for s in services if s["key"] not in IGNORES]
    morts = [s for s in juges if not s["up"]]
    morts_vitaux = [s for s in morts if s["key"] in VITAUX]

    if morts_vitaux:
        noms = ", ".join(s["nom"] for s in morts_vitaux)
        return {
            "level": "CRITIQUE",
            "why": f"brique vitale morte : {noms} — la cascade 0-token est coupee",
        }

    # Sous le tiers, on parle d'un service isole ; au-dela, c'est un motif.
    if morts and len(morts) * 3 >= len(juges):
        return {
            "level": "DEGRADE",
            "why": f"{len(morts)}/{len(juges)} backends muets : "
            + ", ".join(s["nom"] for s in morts),
        }
    if morts:
        return {
            "level": "DEGRADE",
            "why": "backend(s) muet(s) : " + ", ".join(s["nom"] for s in morts),
        }

    # Une unite systemd en echec ne suffit pas a declarer CRITIQUE : un montage
    # de sauvegarde casse n'interrompt aucune production.
    if failed:
        return {
            "level": "DEGRADE",
            "why": f"{len(failed)} unite(s) systemd en echec : " + ", ".join(failed),
        }
    return {
        "level": "OK",
        "why": f"{len(juges)} backends repondent, aucune unite en echec",
    }


def build_state() -> dict:
    with ThreadPoolExecutor(max_workers=len(SERVICES)) as pool:
        probes = list(pool.map(lambda s: probe(s[3]), SERVICES))
    services = [
        {"key": k, "nom": nom, "icone": ico, "url": url, "hote": hote, **p}
        for (k, nom, ico, url, hote), p in zip(SERVICES, probes)
    ]
    failed = read_failed_services()
    try:
        sante = health_verdict(services, failed)
    except NotImplementedError as e:
        sante = {"level": "?", "why": str(e)}
    return {
        "services": services,
        "failed": failed,
        "sante": sante,
        "agents": read_agents(),
        "biblio": read_biblio(),
        "tampon": read_tampon(),
        "plan": read_plan(),
        "hote": socket.gethostname(),
    }


HTML = r"""<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>JARVIS — Centre de Commande</title><style>
:root{--bg:#0a0e17;--card:#111827;--border:#1f2937;--accent:#10b981;--accent2:#3b82f6;--text:#e5e7eb;--muted:#9ca3af;--danger:#ef4444;--warn:#f59e0b}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh}
.header{background:linear-gradient(135deg,#064e3b,#0a0e17);padding:20px 32px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px}
.header h1{font-size:22px;font-weight:700}.header h1 span{color:var(--accent)}
.dot{width:10px;height:10px;border-radius:50%;display:inline-block}
.dot.g{background:var(--accent);box-shadow:0 0 8px var(--accent)}.dot.r{background:var(--danger)}.dot.y{background:var(--warn)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;padding:20px 32px}
.card{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px}
.card h3{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}
.card .v{font-size:32px;font-weight:700;color:var(--accent)}.card .s{font-size:12px;color:var(--muted);margin-top:4px}
.section{padding:0 32px 20px}.section h2{font-size:16px;margin-bottom:12px;padding-bottom:6px;border-bottom:1px solid var(--border)}
.containers{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px}
.cc{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px;text-align:center;cursor:pointer;transition:.2s}
.cc:hover{border-color:var(--accent);transform:translateY(-2px)}
.cc .ico{font-size:26px}.cc .nm{font-weight:600;font-size:13px;margin:6px 0 2px}.cc .pt{color:var(--accent);font-family:monospace;font-size:11px}.cc .st{font-size:11px;margin-top:4px}
.agents-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:8px}
.ac{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px 12px;font-size:13px;display:flex;align-items:center;gap:10px}
.av{width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:17px;flex:0 0 34px}
.ac .n{margin-left:auto;font-weight:700;color:var(--accent)}
.log{background:#000;border-radius:8px;padding:12px;font-family:monospace;font-size:11px;max-height:240px;overflow-y:auto;line-height:1.6}
.log .ts{color:var(--muted)}.log .ok{color:var(--accent)}.log .err{color:var(--danger)}.log .info{color:var(--accent2)}
.badge{padding:3px 10px;border-radius:20px;font-size:12px;font-weight:600}
</style></head><body>
<div class="header">
 <h1><span>JARVIS</span> — Centre de Commande</h1>
 <div style="display:flex;gap:14px;align-items:center">
  <span id="sante" class="badge">—</span>
  <span id="st"><span class="dot y"></span> Chargement…</span>
  <span id="clock" style="font-family:monospace;color:var(--muted)"></span>
 </div>
</div>
<div class="grid">
 <div class="card"><h3>Agents</h3><div class="v" id="n-ag">—</div><div class="s" id="n-fam">— familles</div></div>
 <div class="card"><h3>Bibliotheque</h3><div class="v" id="n-bl">—</div><div class="s">blocs vivants</div></div>
 <div class="card"><h3>Backends</h3><div class="v" id="n-sv">—</div><div class="s" id="n-svs">— sondes</div></div>
 <div class="card"><h3>Tampon M6</h3><div class="v" id="n-tp">—</div><div class="s" id="n-tps">file</div></div>
 <div class="card"><h3>Plan</h3><div class="v" id="n-pl">—</div><div class="s">entrees</div></div>
 <div class="card"><h3>Services failed</h3><div class="v" id="n-fl">—</div><div class="s" id="n-fls">systemd</div></div>
</div>
<div class="section"><h2>Backends — sonde reelle</h2><div class="containers" id="svc"></div></div>
<div class="section"><h2>Agents par famille (avatars)</h2><div class="agents-grid" id="ags"></div></div>
<div class="section"><h2>Projections multiples — simulation pondérée parallèle (0 token)</h2>
 <div style="display:flex;gap:10px;margin-bottom:12px">
  <input id="q" placeholder="Intention à projeter (ex: sauvegarde sql postgres cluster)…"
   style="flex:1;padding:10px 14px;border-radius:8px;border:1px solid var(--border);background:var(--card);color:var(--text);font-size:13px">
  <button onclick="simuler()" style="padding:10px 20px;border-radius:8px;border:none;background:var(--accent);color:#000;font-weight:600;cursor:pointer">Projeter</button>
 </div>
 <div id="sim-proj" class="grid" style="padding:0;margin-bottom:12px"></div>
 <div id="sim-sup"></div>
 <div id="sim-chr" style="margin-top:12px"></div>
</div>
<div class="section"><h2>Journal</h2><div class="log" id="log"></div></div>
<script>
function log(m,c){const e=document.getElementById("log"),t=new Date().toLocaleTimeString("fr-FR");
 e.innerHTML=`<div><span class="ts">[${t}]</span> <span class="${c||'info'}">${m}</span></div>`+e.innerHTML}
async function refresh(){
 try{
  const d=await (await fetch("/api/state",{cache:"no-store"})).json();
  const up=d.services.filter(s=>s.up).length;
  document.getElementById("n-ag").textContent=d.agents.total;
  document.getElementById("n-fam").textContent=d.agents.familles.length+" familles";
  document.getElementById("n-bl").textContent=d.biblio.blocs.toLocaleString("fr-FR");
  document.getElementById("n-sv").textContent=up+"/"+d.services.length;
  document.getElementById("n-svs").textContent="sondes HTTP";
  const f=(d.tampon&&d.tampon.file)||{};
  document.getElementById("n-tp").textContent=(f.pending||0)+(f.running||0);
  document.getElementById("n-tps").textContent="en file · "+(f.done||0)+" done";
  document.getElementById("n-pl").textContent=d.plan.entrees;
  document.getElementById("n-fl").textContent=d.failed.length;
  document.getElementById("n-fls").textContent=d.failed.join(", ")||"aucun";
  const sa=document.getElementById("sante"),lv=(d.sante&&d.sante.level)||"?";
  sa.textContent=lv; sa.title=(d.sante&&d.sante.why)||"";
  sa.style.background=lv=="OK"?"rgba(16,185,129,.15)":lv=="DEGRADE"?"rgba(245,158,11,.15)":lv=="CRITIQUE"?"rgba(239,68,68,.15)":"rgba(148,163,184,.15)";
  sa.style.color=lv=="OK"?"#10b981":lv=="DEGRADE"?"#f59e0b":lv=="CRITIQUE"?"#ef4444":"#94a3b8";
  document.getElementById("svc").innerHTML=d.services.map(s=>{
   const c=s.up?"#10b981":"#ef4444";
   return `<div class="cc" onclick="window.open('${s.url}','_blank')"><div class="ico">${s.icone}</div>
   <div class="nm">${s.nom}</div><div class="pt">${(s.url.match(/:(\d+)/)||[,''])[1]} · ${s.hote}</div>
   <div class="st" style="color:${c}">${s.up?"OK "+s.code:"offline"}</div></div>`}).join("");
  document.getElementById("ags").innerHTML=d.agents.familles.map(a=>
   `<div class="ac"><div class="av" style="background:${a.color}22;color:${a.color};border:1px solid ${a.color}55">${a.emoji}</div>
   <span>${a.family}</span><span class="n">${a.n}</span></div>`).join("");
  document.getElementById("st").innerHTML='<span class="dot g"></span> Live';
  log(`refresh — ${up}/${d.services.length} backends, ${d.failed.length} failed`,"ok");
 }catch(e){document.getElementById("st").innerHTML='<span class="dot r"></span> Off';log(e.message,"err")}
}
async function simuler(){
 const q=document.getElementById("q").value.trim(); if(!q){log("intention requise","err");return}
 document.getElementById("sim-sup").innerHTML='<div class="ts">simulation en cours…</div>';
 log("projection : "+q,"info");
 try{
  const d=await (await fetch("/api/simul?q="+encodeURIComponent(q))).json();
  if(d.erreur){document.getElementById("sim-sup").innerHTML=`<div class="log err">${d.erreur}</div>`;return}
  document.getElementById("sim-proj").innerHTML=d.projections.map(p=>
   `<div class="card"><h3>${p.lentille}</h3><div class="v">${p.score}</div>
    <div class="s">${p.blocs} blocs · poids ${p.poids}</div></div>`).join("");
  document.getElementById("sim-sup").innerHTML=
   `<div class="log" style="max-height:230px">`+d.consensus.map(c=>
   `<div><b style="color:var(--accent)">${c.votes}×</b> ${c.danger} ${c.nom}
    <span class="ts">[${c.lentilles.join(",")}]</span> <span class="info">${c.phase}</span></div>`).join("")+`</div>`;
  document.getElementById("sim-chr").innerHTML=d.chronologie.map(ph=>
   `<div style="margin-bottom:8px"><b>${ph.rang}. ${ph.phase}</b> <span class="ts">(${ph.actions.length})</span>
    <div class="log" style="max-height:150px">`+ph.actions.map(a=>
    `<div>${a.danger} <b>${a.nom}</b> <span class="ts">${a.cmd}</span></div>`).join("")+`</div></div>`).join("");
  log(`${d.blocs_routes} blocs routés · ${d.retenu} au consensus`,"ok");
 }catch(e){log(e.message,"err")}
}
document.addEventListener("keydown",e=>{if(e.key=="Enter"&&document.activeElement.id=="q")simuler()});
setInterval(()=>{document.getElementById("clock").textContent=new Date().toLocaleTimeString("fr-FR")},1000);
refresh();setInterval(refresh,30000);
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/api/simul"):
            from urllib.parse import parse_qs, urlparse

            q = (parse_qs(urlparse(self.path).query).get("q") or [""])[0].strip()
            if not q:
                self._send(
                    400,
                    b'{"erreur":"parametre q requis"}',
                    "application/json; charset=utf-8",
                )
                return
            try:
                # Le moteur tourne en sous-processus : une simulation qui part
                # en vrille ne doit pas emporter le board avec elle.
                out = subprocess.run(
                    ["python3", str(HOME / "jarvis/bin/jarvis-simul.py"), q, "--json"],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                body = out.stdout.encode() or b'{"erreur":"simulation vide"}'
            except Exception as e:
                body = json.dumps({"erreur": type(e).__name__}).encode()
            self._send(200, body, "application/json; charset=utf-8")
        elif self.path.startswith("/api/state"):
            body = json.dumps(build_state(), ensure_ascii=False).encode()
            self._send(200, body, "application/json; charset=utf-8")
        elif self.path in ("/", "/index.html"):
            self._send(200, HTML.encode(), "text/html; charset=utf-8")
        else:
            self._send(404, b"not found", "text/plain")

    def log_message(self, *a):  # pas de bruit sur stderr
        pass


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"jarvis-board -> http://127.0.0.1:{PORT}", flush=True)
    srv.serve_forever()
