#!/usr/bin/env python3
"""Bibliothèque de code SQL — patterns/recettes réutilisables du système Pousseline.
Objectif : SQL AVANT compute. Chercher un pattern validé ici avant de re-générer.
Rejouable, idempotent (UPSERT sur nom)."""
import sqlite3, os
DB = os.path.join(os.path.dirname(__file__), "code_library.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS patterns(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nom TEXT UNIQUE NOT NULL,
  categorie TEXT, langage TEXT,
  triggers TEXT,            -- mots-clés déclencheurs (recherche)
  description TEXT,
  quand_utiliser TEXT,
  code TEXT,                -- squelette réutilisable
  source TEXT,              -- fichier/skill d'origine
  created_at TEXT DEFAULT (datetime('now','localtime'))
);
CREATE VIRTUAL TABLE IF NOT EXISTS patterns_fts USING fts5(nom, triggers, description, content='patterns', content_rowid='id');
"""

PATTERNS = [
 ("cablage-onglet-front-back","frontend","python+js",
  "onglet, orphelin, câbler, section, navigate, loadX, front, backend",
  "Brancher un module backend Flask orphelin à un nouvel onglet du front.",
  "Quand un module a des routes /api prêtes mais aucune UI (onglet mort/absent).",
  "1) <div id='section-X' class='.card'>  2) 'X' dans const SECTIONS[]  3) hook `if(id==='X') loadX();` dans navigate()  4) async function loadX(){ const d=await pJson('/api/...'); ... }  5) tester routes+console(0 err)+screenshot",
  "index.html / skill espace-prof-app"),
 ("dispatch-masse-0token","backend","python",
  "dispatch, masse, remplir, banque, parallèle, vagues, 0-token, threadpool",
  "Générer N items en parallèle via cascade IA déportée (0 token, 0 chaleur).",
  "Remplir une table en volume (fiches, exercices). PAS pour 1 item.",
  "from concurrent.futures import ThreadPoolExecutor\ncells=manquants()  # SQL: cible - deja_en_DB\ndef worker(c):\n  for _ in range(6):\n    try: return gen_cell(c)  # ai_local.generate + INSERT ON CONFLICT\n    except AIUnavailable: time.sleep(25)  # surchauffe/rate-limit\nThreadPoolExecutor(max_workers=6)  # 6-10 max, PAS 10000. Le cloud rate-limite vers ~250-500.",
  "webapp/scripts/dispatch_banque.py / skill dispatch-generation-masse"),
 ("snapshot-avant-test-prod","test","bash",
  "test, endpoint, POST, prod, données réelles, snapshot, restore",
  "Protéger les vraies données avant un POST/DELETE de test.",
  "AVANT tout test qui écrit sur ecole.db (budget, élèves, notes).",
  "GET .../api/xxx  # noter valeurs\nsqlite3 ecole.db \".backup 'backups/pretest.db'\"\n# ...test POST...\nGET .../api/xxx  # diff, restaurer si modif non voulue",
  "skill snapshot-avant-test-prod (incident budget 800->300)"),
 ("extraction-soutien-locale","frontend","js",
  "version courte, soutien, raccourcir, hors-ligne, 0 IA, plan b",
  "Extraire le niveau Soutien d'une fiche sans IA (repli instantané).",
  "Exercice trop long en classe → montrer juste la partie Soutien.",
  "function extraitSoutien(txt){const i=txt.search(/soutien/i);if(i<0)return null;const a=txt.slice(i);const j=a.search(/standard|approfondiss/i);return j>0?a.slice(0,j):a;}",
  "index.html Plan B"),
 ("remplissage-sql-api","backend","python",
  "remplir, rubriques, données, dominos, sql, groupes, ateliers, insert",
  "Peupler des tables vides via les routes API (respecte la logique métier).",
  "Rubrique vide (groupes, ateliers, sorties). Tables à 0 = 0 risque d'écrasement.",
  "import urllib.request,json\ndef post(p,b): return json.load(urllib.request.urlopen(urllib.request.Request(BASE+p,data=json.dumps(b).encode(),headers={'Content-Type':'application/json'},method='POST')))\nfor item in donnees_types: post('/api/groupes', item)",
  "session remplissage groupes/ateliers/sorties/réunions"),
 ("recueil-html-imprimable","docs","python",
  "recueil, pdf, imprimable, supports, documents, md2html, ctrl+p",
  "Compiler des fiches en recueil HTML imprimable (Ctrl+P→PDF), 0 dépendance.",
  "Rubrique Documents à alimenter quand aucune lib PDF n'est installée.",
  "def md2html(s): s=html.escape(s); s=re.sub(r'^## (.*)$',r'<h3>\\1</h3>',s,flags=re.M); return s\n# grouper par matiere, écrire <html><style>@media print{...}</style>...",
  "webapp/static/recueils/"),
 ("garde-fou-checkpoint-rgpd","ops","bash",
  "checkpoint, push, git, rgpd, secret, pii, sauvegarde",
  "Bloquer tout secret/PII/base avant un commit/push (dernière ligne de défense).",
  "Avant chaque push d'une app contenant des données élèves.",
  "git diff --cached --name-only | grep -iE '\\.db$|\\.env$|token|secret|\\.pem$|\\.key$|certs/' && echo FUITE && exit 1",
  "skill checkpoint-securise-app"),
 ("cascade-ai-ordre","backend","python",
  "cascade, ai_local, backend, ollama, cloud, gemini, fallback, generate",
  "Ordre de la cascade IA 0-token déporté-d'abord, avec garde-fou thermique.",
  "Toute génération : lire cache SQL avant d'inférer.",
  "# ai_local.generate(): cache SQL -> M1/M2 LM Studio -> Ollama cloud gpt-oss:120b (clé API directe) -> Gemini -> Ollama local CPU (bloqué si GPU>=82C). Cloud rate-limite vers ~500 req.",
  "webapp/ai_local.py"),
 ("cells-2026-generator","backend","python",
  "programme, maternelle, 2026, domaines, cellules, aplatir, notions",
  "Aplatir un dict programme (niveau→domaine→période→notions) en cellules générables.",
  "Alimenter le dispatch de masse depuis un programme officiel structuré.",
  "def cells_2026(niv):\n  out=[]\n  for dom,pers in PROG[niv].items():\n    for pk,notions in pers.items():\n      for n in notions: out.append({'niveau':niv,'matiere':dom,'periode':int(pk[1]),'notion':n})\n  return out",
  "webapp/programme_maternelle_2026.py"),
 ("audit-cablage-front-back","ops","bash",
  "audit, câblage, orphelins, onglets morts, register, sections",
  "Diff modules backend enregistrés vs onglets/loaders front → orphelins.",
  "Avant refactor front ou périodiquement (dérive front/back).",
  "grep -n 'register' server.py   # modules montés\ngrep -n \"data-section=\" index.html  # onglets\ngrep -n \"fetch('/api\\|pJson('/api\" index.html  # routes consommées\n# orphelin = route jamais fetch ; onglet mort = data-section sans loadX",
  "skill audit-cablage-front-back"),
]

def main():
    c=sqlite3.connect(DB); c.executescript(SCHEMA)
    for p in PATTERNS:
        c.execute("""INSERT INTO patterns(nom,categorie,langage,triggers,description,quand_utiliser,code,source)
                     VALUES(?,?,?,?,?,?,?,?)
                     ON CONFLICT(nom) DO UPDATE SET categorie=excluded.categorie,langage=excluded.langage,
                       triggers=excluded.triggers,description=excluded.description,quand_utiliser=excluded.quand_utiliser,
                       code=excluded.code,source=excluded.source""", p)
    c.execute("INSERT INTO patterns_fts(patterns_fts) VALUES('rebuild')")
    c.commit()
    n=c.execute("SELECT COUNT(*) FROM patterns").fetchone()[0]
    print(f"✅ {n} patterns dans {DB}")
    c.close()

if __name__=="__main__": main()
