#!/usr/bin/env python3
"""board-serveur — la table ronde consultable depuis n'importe quel poste.

Le board vivait derriere un CLI local et des outils MCP : pour le consulter il
fallait etre sur M4, dans une session. Ce serveur l'expose en HTTP sur le reseau
local — une page web lisible sur telephone ou tablette, et une API JSON pour les
agents.

    GET  /                     interface web (autonome, sans dependance externe)
    GET  /api/etat             compteurs globaux
    GET  /api/boards           boards + domaines + groupes + taches ouvertes
    GET  /api/board/<nom>      detail d'un board
    GET  /api/groupes          groupes et leurs membres
    GET  /api/assistants       super-assistants
    GET  /api/taches?statut=   file de travail
    GET  /api/recherche?q=     recherche FTS5 dans le corpus (260 000 blocs)
    GET  /api/seances          tables rondes tracees
    POST /api/tache            cree une tache   {board,titre,detail,priorite,groupe}
    POST /api/tache/statut     change un statut {id,statut}
    POST /api/seance           ouvre une seance {board,question,mode}

Lecture par defaut ; l'ecriture (POST) n'est ouverte qu'avec --ecriture.
Par prudence le serveur n'ecoute que sur le LAN : --hote 0.0.0.0 est un choix
explicite, jamais le defaut.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

DB = os.path.expanduser("~/jarvis/databases/board.db")
ECRITURE = False

PAGE = """<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Table Ronde JARVIS</title><style>
:root{--fd:#0f1115;--ct:#171a21;--bd:#262b36;--tx:#e6e9ef;--dx:#9aa4b8;--ac:#5b9dff;--ok:#3fb950;--wn:#d29922}
*{box-sizing:border-box}body{margin:0;font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:var(--fd);color:var(--tx)}
header{padding:18px 20px;border-bottom:1px solid var(--bd);position:sticky;top:0;background:var(--fd);z-index:5}
h1{margin:0;font-size:18px;letter-spacing:.2px}
.sub{color:var(--dx);font-size:13px;margin-top:4px}
main{padding:16px 20px;max-width:1100px;margin:0 auto}
.grid{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(250px,1fr))}
.c{background:var(--ct);border:1px solid var(--bd);border-radius:10px;padding:14px}
.c h3{margin:0 0 8px;font-size:15px}
.k{color:var(--dx);font-size:12px;text-transform:uppercase;letter-spacing:.5px}
.n{font-size:26px;font-weight:600}
.tag{display:inline-block;background:#1f2430;border:1px solid var(--bd);border-radius:20px;padding:2px 9px;font-size:12px;margin:2px 3px 2px 0;color:var(--dx)}
nav{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0}
button{background:var(--ct);color:var(--tx);border:1px solid var(--bd);border-radius:8px;padding:8px 13px;cursor:pointer;font-size:14px}
button.on{border-color:var(--ac);color:var(--ac)}
input{background:var(--ct);color:var(--tx);border:1px solid var(--bd);border-radius:8px;padding:9px 12px;width:100%;font-size:15px}
table{width:100%;border-collapse:collapse;font-size:14px}
td,th{padding:7px 9px;border-bottom:1px solid var(--bd);text-align:left;vertical-align:top}
th{color:var(--dx);font-weight:500;font-size:12px;text-transform:uppercase}
.p1{color:#f85149}.p2{color:var(--wn)}.p3{color:var(--dx)}
.ok{color:var(--ok)}
.ex{color:var(--dx);font-size:13px;white-space:pre-wrap}
@media(max-width:600px){main{padding:12px}.n{font-size:22px}}
</style></head><body>
<header><h1>Table Ronde JARVIS</h1><div class="sub" id="sub">chargement…</div></header>
<main>
<nav>
 <button class="on" onclick="vue('etat',this)">Vue d'ensemble</button>
 <button onclick="vue('boards',this)">Boards</button>
 <button onclick="vue('groupes',this)">Groupes</button>
 <button onclick="vue('assistants',this)">Assistants</button>
 <button onclick="vue('taches',this)">Tâches</button>
 <button onclick="vue('recherche',this)">Corpus</button>
</nav>
<div id="z"></div></main>
<script>
const $=(s)=>document.querySelector(s);
async function j(u){const r=await fetch(u);return r.json()}
function esc(s){return String(s??'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
async function vue(v,b){
 document.querySelectorAll('nav button').forEach(x=>x.classList.remove('on'));
 if(b)b.classList.add('on');
 const z=$('#z');z.innerHTML='<p class="k">chargement…</p>';
 if(v==='etat'){const d=await j('/api/etat');
  z.innerHTML='<div class="grid">'+Object.entries(d).map(([k,n])=>
   `<div class="c"><div class="k">${esc(k)}</div><div class="n">${n}</div></div>`).join('')+'</div>';}
 if(v==='boards'){const d=await j('/api/boards');
  z.innerHTML='<div class="grid">'+d.map(b=>`<div class="c"><h3>${esc(b.nom)}</h3>
   <div class="k">${esc(b.visibilite)} · ${b.domaines.length} domaines · ${b.groupes} groupes · ${b.taches_ouvertes} tâches</div>
   <div style="margin-top:8px">${b.domaines.map(x=>`<span class="tag">${esc(x)}</span>`).join('')}</div>
   <div class="ex" style="margin-top:8px">${esc(b.description||'')}</div></div>`).join('')+'</div>';}
 if(v==='groupes'){const d=await j('/api/groupes');
  z.innerHTML='<div class="grid">'+d.map(g=>`<div class="c"><h3>${esc(g.nom)}</h3>
   <div class="k">${esc(g.board)} · ${g.experts} experts · ${g.assistants} assistants</div>
   <div class="ex" style="margin-top:6px">${esc(g.objectif||'')}</div></div>`).join('')+'</div>';}
 if(v==='assistants'){const d=await j('/api/assistants');
  z.innerHTML='<table><tr><th>rang</th><th>nom</th><th>board</th><th>rôle</th><th>backend</th></tr>'+
   d.map(a=>`<tr><td>${a.rang}</td><td><b>${esc(a.nom)}</b></td><td>${esc(a.board||'—')}</td>
   <td>${esc(a.role)}</td><td class="ex">${esc(a.backend||'')} ${esc(a.model||'')}</td></tr>`).join('')+'</table>';}
 if(v==='taches'){const d=await j('/api/taches');
  z.innerHTML=d.length?('<table><tr><th>P</th><th>statut</th><th>board</th><th>titre</th></tr>'+
   d.map(t=>`<tr><td class="p${t.priorite}">P${t.priorite}</td><td>${esc(t.statut)}</td>
   <td>${esc(t.board)}</td><td>${esc(t.titre)}</td></tr>`).join('')+'</table>'):'<p class="k">aucune tâche</p>';}
 if(v==='recherche'){z.innerHTML=`<input id="q" placeholder="rechercher dans les 260 000 blocs du corpus…"><div id="r" style="margin-top:14px"></div>`;
  $('#q').addEventListener('keydown',async e=>{if(e.key!=='Enter')return;
   $('#r').innerHTML='<p class="k">recherche…</p>';
   const d=await j('/api/recherche?q='+encodeURIComponent(e.target.value));
   $('#r').innerHTML=d.length?d.map(x=>`<div class="c" style="margin-bottom:8px">
    <div class="k">${esc(x.domain_id)}</div><div class="ex">${esc(x.extrait)}</div></div>`).join(''):'<p class="k">aucun résultat</p>';});
  $('#q').focus();}
}
(async()=>{const d=await j('/api/etat');
 $('#sub').textContent=`${d.boards} boards · ${d.groupes} groupes · ${d.assistants} assistants · ${d.chunks} blocs indexés`;
 vue('etat');})();
</script></body></html>"""


def cx() -> sqlite3.Connection:
    c = sqlite3.connect(f"file:{DB}?mode=ro" if not ECRITURE else DB, uri=not ECRITURE, timeout=30)
    c.row_factory = sqlite3.Row
    return c


def etat() -> dict:
    c = cx()
    d = {}
    for t in ("boards", "groupes", "assistants", "taches", "seances",
              "domains", "experts", "sources", "chunks"):
        try:
            d[t] = c.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        except sqlite3.OperationalError:
            d[t] = 0
    return d


def boards() -> list:
    c = cx()
    out = []
    for b in c.execute("SELECT * FROM boards ORDER BY nom"):
        out.append({
            "id": b["id"], "nom": b["nom"], "description": b["description"],
            "visibilite": b["visibilite"],
            "domaines": [r[0] for r in c.execute(
                "SELECT domain_id FROM board_domaines WHERE board_id=?", (b["id"],))],
            "groupes": c.execute("SELECT count(*) FROM groupes WHERE board_id=?",
                                 (b["id"],)).fetchone()[0],
            "taches_ouvertes": c.execute(
                "SELECT count(*) FROM taches WHERE board_id=? AND statut!='fait'",
                (b["id"],)).fetchone()[0],
        })
    return out


def groupes() -> list:
    c = cx()
    return [dict(
        id=g["id"], nom=g["nom"], objectif=g["objectif"], board=g["bnom"],
        experts=c.execute("SELECT count(*) FROM groupe_membres WHERE groupe_id=? AND membre_type='expert'",
                          (g["id"],)).fetchone()[0],
        assistants=c.execute("SELECT count(*) FROM groupe_membres WHERE groupe_id=? AND membre_type='assistant'",
                             (g["id"],)).fetchone()[0],
    ) for g in c.execute(
        "SELECT g.*, b.nom bnom FROM groupes g JOIN boards b ON b.id=g.board_id ORDER BY b.nom,g.nom")]


def assistants() -> list:
    c = cx()
    return [dict(nom=a["nom"], role=a["role"], rang=a["rang"], board=a["bnom"],
                 model=a["model"], backend=a["backend"], consigne=a["consigne"])
            for a in c.execute("SELECT a.*, b.nom bnom FROM assistants a "
                               "LEFT JOIN boards b ON b.id=a.board_id ORDER BY a.rang,a.nom")]


def taches(statut: str = "") -> list:
    c = cx()
    q = ("SELECT t.*, b.nom bnom, g.nom gnom FROM taches t JOIN boards b ON b.id=t.board_id "
         "LEFT JOIN groupes g ON g.id=t.groupe_id")
    p = []
    if statut:
        q += " WHERE t.statut=?"; p.append(statut)
    q += " ORDER BY t.priorite, t.cree_le"
    return [dict(id=t["id"], titre=t["titre"], detail=t["detail"], statut=t["statut"],
                 priorite=t["priorite"], board=t["bnom"], groupe=t["gnom"])
            for t in c.execute(q, p)]


def seances() -> list:
    c = cx()
    return [dict(id=s["id"], question=s["question"], mode=s["mode"], statut=s["statut"],
                 board=s["bnom"], cree_le=s["cree_le"])
            for s in c.execute("SELECT s.*, b.nom bnom FROM seances s "
                               "JOIN boards b ON b.id=s.board_id ORDER BY s.cree_le DESC LIMIT 50")]


def recherche(q: str, limite: int = 25) -> list:
    if not q.strip():
        return []
    c = cx()
    try:
        lignes = c.execute(
            "SELECT c.domain_id, snippet(chunks_fts,0,'[',']','…',24) extrait "
            "FROM chunks_fts f JOIN chunks c ON c.rowid=f.rowid "
            "WHERE chunks_fts MATCH ? LIMIT ?", (q, limite)).fetchall()
    except sqlite3.OperationalError:
        motif = f"%{q}%"
        lignes = c.execute(
            "SELECT domain_id, substr(text,1,300) extrait FROM chunks "
            "WHERE text LIKE ? LIMIT ?", (motif, limite)).fetchall()
    return [dict(domain_id=r["domain_id"], extrait=r["extrait"]) for r in lignes]


class H(BaseHTTPRequestHandler):
    def _envoi(self, code, corps, ctype="application/json; charset=utf-8"):
        donnees = corps if isinstance(corps, bytes) else json.dumps(
            corps, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(donnees)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(donnees)

    def log_message(self, *a):
        pass

    def do_GET(self):
        u = urlparse(self.path)
        p, qs = u.path, parse_qs(u.query)
        try:
            if p == "/":
                return self._envoi(200, PAGE.encode(), "text/html; charset=utf-8")
            if p == "/api/etat":
                return self._envoi(200, etat())
            if p == "/api/boards":
                return self._envoi(200, boards())
            if p.startswith("/api/board/"):
                nom = p.split("/")[-1]
                r = [b for b in boards() if b["nom"] == nom or b["id"] == nom]
                return self._envoi(200 if r else 404, r[0] if r else {"error": "inconnu"})
            if p == "/api/groupes":
                return self._envoi(200, groupes())
            if p == "/api/assistants":
                return self._envoi(200, assistants())
            if p == "/api/taches":
                return self._envoi(200, taches(qs.get("statut", [""])[0]))
            if p == "/api/seances":
                return self._envoi(200, seances())
            if p == "/api/recherche":
                return self._envoi(200, recherche(qs.get("q", [""])[0]))
            return self._envoi(404, {"error": "route inconnue"})
        except Exception as e:
            return self._envoi(500, {"error": str(e)})

    def do_POST(self):
        if not ECRITURE:
            return self._envoi(403, {"error": "serveur en lecture seule (relancer avec --ecriture)"})
        n = int(self.headers.get("Content-Length", 0))
        try:
            corps = json.loads(self.rfile.read(n) or "{}")
        except ValueError:
            return self._envoi(400, {"error": "JSON invalide"})
        c = sqlite3.connect(DB, timeout=30)
        c.row_factory = sqlite3.Row
        try:
            if self.path == "/api/tache":
                b = c.execute("SELECT id FROM boards WHERE nom=? OR id=?",
                              (corps.get("board"), corps.get("board"))).fetchone()
                if not b:
                    return self._envoi(400, {"error": "board inconnu"})
                g = None
                if corps.get("groupe"):
                    r = c.execute("SELECT id FROM groupes WHERE nom=? OR id=?",
                                  (corps["groupe"], corps["groupe"])).fetchone()
                    g = r["id"] if r else None
                tid = f"tch_{uuid.uuid4().hex[:12]}"
                c.execute("INSERT INTO taches (id,board_id,groupe_id,titre,detail,priorite)"
                          " VALUES (?,?,?,?,?,?)",
                          (tid, b["id"], g, corps.get("titre", ""), corps.get("detail", ""),
                           int(corps.get("priorite", 2))))
                c.commit()
                return self._envoi(201, {"id": tid})
            if self.path == "/api/tache/statut":
                c.execute("UPDATE taches SET statut=?, maj_le=datetime('now') WHERE id=?",
                          (corps.get("statut"), corps.get("id")))
                c.commit()
                return self._envoi(200, {"ok": True})
            if self.path == "/api/seance":
                b = c.execute("SELECT id FROM boards WHERE nom=? OR id=?",
                              (corps.get("board"), corps.get("board"))).fetchone()
                if not b:
                    return self._envoi(400, {"error": "board inconnu"})
                sid = f"sea_{uuid.uuid4().hex[:12]}"
                c.execute("INSERT INTO seances (id,board_id,question,mode) VALUES (?,?,?,?)",
                          (sid, b["id"], corps.get("question", ""),
                           corps.get("mode", "consensus")))
                c.commit()
                return self._envoi(201, {"id": sid})
            return self._envoi(404, {"error": "route inconnue"})
        except Exception as e:
            return self._envoi(500, {"error": str(e)})
        finally:
            c.close()


def main() -> int:
    global ECRITURE
    p = argparse.ArgumentParser(prog="board-serveur")
    p.add_argument("--port", type=int, default=8790)
    p.add_argument("--hote", default="127.0.0.1",
                   help="127.0.0.1 (defaut) ou 0.0.0.0 pour exposer au LAN")
    p.add_argument("--ecriture", action="store_true", help="autorise les POST")
    a = p.parse_args()
    ECRITURE = a.ecriture
    srv = ThreadingHTTPServer((a.hote, a.port), H)
    print(f"board-serveur sur http://{a.hote}:{a.port}  "
          f"({'lecture+ecriture' if ECRITURE else 'lecture seule'})", flush=True)
    srv.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
