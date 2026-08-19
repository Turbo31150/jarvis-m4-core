#!/usr/bin/env bash
# cascade-massive.sh — convertit une todolist PRECHARGEE en file de cascade.
#
# Ce fichier manquait : le skill `run-cascade-plan` en fait son point d entree
# (`~/jarvis/bin/cascade-massive.sh --from-plan ...`) mais il n existait pas sur disque.
# Toute la chaine plan -> file etait donc rompue, en silence.
#
# DEUX NATURES, DEUX FILES — corrige le 19/08 apres echec mesure.
# `skillmp_cascade_taches` a UNE seule semantique : installer un slug du catalogue
# SkillsMP. Son dispatcher (skillmp-cascade.sh:168) IGNORE la colonne `commande` et
# lance toujours `skillmp install <skill> --cible both`. Y verser une tache d ACTION
# ("Skill: /run-biblio-filler") echoue donc forcement : le skill existe deja en local
# et n est pas un slug du catalogue. Mesure : 2 taches versees, 2 failed.
# Les taches d action vont desormais dans `file_actions`, avec leur commande respectee.
#
# GARDE-FOU CENTRAL — chemins reels uniquement.
# Verifie le 19/08 : les 898 blocs de `prechargement` deja en base pointent vers
# /home/turbo/... (le home de M6). AUCUN n existe sur M4 : 898/898 absents. Le
# "contexte precharge" affiche par la cascade etait donc entierement fictif ici.
# Ce script n ecrit que des chemins verifies par [ -e ]. Un chemin absent est
# ECARTE et COMPTE, jamais recopie tel quel.
#
#   --from-plan            source = table `plan` de jarvis_master.db (defaut)
#   --from-plan <fichier>  source = fichier JSON/markdown de plan mode
#   --source <nom>         filtre sur plan.source (ex: moisson, domino)
#   --limit N              borne le nombre de taches converties
#   --confiance <niveau>   ne garde que forte | bonne | indicative (defaut: toutes)
#   --dry-run              n ecrit rien (defaut)
#   --apply                ecrit dans skillmp_cascade_taches

set -uo pipefail
DB="${JARVIS_DB:-$HOME/jarvis/jarvis_master.db}"
LOG="$HOME/jarvis/logs/cascade-massive.log"
SRC_TABLE="plan"; FICHIER=""; FILTRE_SOURCE=""; LIMIT=0; CONF=""; APPLY=0

while [ $# -gt 0 ]; do
  case "$1" in
    --from-plan) shift; if [ $# -gt 0 ] && [ -e "${1:-}" ]; then FICHIER="$1"; shift; fi ;;
    --source)    FILTRE_SOURCE="${2:-}"; shift 2 ;;
    --limit)     LIMIT="${2:-0}"; shift 2 ;;
    --confiance) CONF="${2:-}"; shift 2 ;;
    --apply)     APPLY=1; shift ;;
    --dry-run)   APPLY=0; shift ;;
    *) echo "option inconnue ignoree: $1" >&2; shift ;;
  esac
done

log(){ echo "[$(date +%H:%M:%S)] $*"; echo "[$(date '+%F %T')] $*" >>"$LOG" 2>/dev/null || true; }

log "═══ cascade-massive — from-plan${FICHIER:+ ($FICHIER)} apply=$APPLY ═══"

[ -f "$DB" ] || { echo "base introuvable: $DB" >&2; exit 2; }
sqlite3 "$DB" "CREATE TABLE IF NOT EXISTS skillmp_cascade_taches (
  id INTEGER PRIMARY KEY AUTOINCREMENT, titre TEXT, famille TEXT, agents TEXT,
  skill TEXT, commande TEXT, prechargement TEXT, statut TEXT, cree_le TEXT,
  UNIQUE(titre));
CREATE TABLE IF NOT EXISTS file_actions (
  id INTEGER PRIMARY KEY AUTOINCREMENT, titre TEXT UNIQUE, famille TEXT, agents TEXT,
  skill TEXT, commande TEXT, prechargement TEXT, confiance TEXT,
  statut TEXT DEFAULT 'pending', cree_le TEXT DEFAULT (datetime('now')));" >/dev/null

DB="$DB" FICHIER="$FICHIER" FILTRE="$FILTRE_SOURCE" LIMIT="$LIMIT" CONF="$CONF" APPLY="$APPLY" \
python3 <<'PYEOF'
import json, os, sqlite3, sys

DB     = os.environ["DB"]
FICH   = os.environ.get("FICHIER") or ""
FILTRE = os.environ.get("FILTRE") or ""
LIMIT  = int(os.environ.get("LIMIT") or 0)
CONF   = os.environ.get("CONF") or ""
APPLY  = os.environ.get("APPLY") == "1"

FAMILLES = {"ai","automation","business","chef","comms","cowork","data","dev","misc",
            "monitoring","omega","openclaw","ops","run","trading"}

def famille_de(pre, titre):
    """Famille deduite de l agent precharge, sinon du vocabulaire du titre."""
    ag = (pre.get("agent") or "")
    if ag.startswith("squad-"):
        f = ag.split("-")[1]
        if f in FAMILLES: return f
    t = titre.lower()
    for mot, fam in (("linkedin","comms"),("mail","comms"),("telegram","comms"),
                     ("trading","trading"),("gpu","monitoring"),("monitor","monitoring"),
                     ("audit","ops"),("service","ops"),("docker","ops"),("backup","ops"),
                     ("biblio","data"),("sql","data"),("embed","data"),("index","data"),
                     ("llm","ai"),("model","ai"),("prompt","ai"),("rag","ai"),
                     ("n8n","automation"),("workflow","automation"),("cron","automation"),
                     ("openclaw","openclaw"),("cowork","cowork"),("omega","omega"),
                     ("test","dev"),("code","dev"),("script","dev"),("api","dev")):
        if mot in t: return fam
    return "misc"

def blocs_reels(pre):
    """Ne conserve QUE les chemins existant sur CETTE machine. Compte les rejets."""
    gardes, rejets = [], 0
    for cle in ("cli",):
        p = pre.get(cle)
        if not p: continue
        if os.path.exists(p): gardes.append({"nom": os.path.basename(p), "source": cle, "bloc": p})
        else: rejets += 1
    return gardes, rejets

con = sqlite3.connect(DB, timeout=60)
con.row_factory = sqlite3.Row

if FICH:
    txt = open(FICH, encoding="utf-8").read()
    try:
        d = json.loads(txt)
        items = d if isinstance(d, list) else d.get("tasks") or d.get("taches") or []
        rows = [{"titre": (it.get("titre") or it.get("title") or str(it))[:400],
                 "preloaded": json.dumps(it.get("preloaded") or {}), "source": "fichier"}
                for it in items]
    except json.JSONDecodeError:
        # markdown : on prend les puces et les cases a cocher
        rows = [{"titre": l.strip().lstrip("-*[ ]xX").strip()[:400],
                 "preloaded": "{}", "source": "fichier"}
                for l in txt.splitlines()
                if l.strip().startswith(("- ", "* ", "- [")) and len(l.strip()) > 6]
else:
    q = "SELECT titre, preloaded, source FROM plan WHERE 1=1"
    p = []
    if FILTRE: q += " AND source = ?"; p.append(FILTRE)
    if CONF:   q += " AND preloaded LIKE ?"; p.append(f'%"confiance": "{CONF}"%')
    if LIMIT:  q += f" LIMIT {LIMIT}"
    rows = [dict(r) for r in con.execute(q, p)]

if LIMIT and len(rows) > LIMIT:
    rows = rows[:LIMIT]

print(f"  taches candidates : {len(rows)}")
if not rows:
    print("  rien a convertir."); sys.exit(0)

lignes, sans_skill, rejets_tot = [], 0, 0
for r in rows:
    try: pre = json.loads(r["preloaded"] or "{}")
    except Exception: pre = {}
    skill = (pre.get("skill") or "").lstrip("/") or None
    if not skill: sans_skill += 1
    fam = famille_de(pre, r["titre"] or "")
    blocs, rej = blocs_reels(pre); rejets_tot += rej
    cmd = pre.get("command") or ""
    lignes.append((r["titre"], fam, f"squad-{fam}-integrateur", skill, cmd,
                   json.dumps(blocs, ensure_ascii=False), pre.get("confiance") or "", "pending"))

from collections import Counter
print(f"  sans skill apparie : {sans_skill}  |  chemins ecartes (inexistants) : {rejets_tot}")
print(f"  familles : {dict(Counter(l[1] for l in lignes).most_common())}")

if not APPLY:
    print("\n  DRY-RUN — 3 exemples :")
    for l in lignes[:3]:
        print(f"    [{l[1]}] {l[0][:58]}\n        skill={l[3]}  cmd={l[4][:60]}  conf={l[6]}")
    print("\n  relancer avec --apply pour ecrire.")
    sys.exit(0)

avant = con.execute("SELECT COUNT(*) FROM file_actions").fetchone()[0]
# UNIQUE(titre) sur la table : on met a jour plutot que d echouer. Le statut d une
# tache DEJA traitee (done/failed) n est PAS remis a pending — sinon chaque conversion
# rejouerait tout le travail deja fait.
con.executemany("""INSERT INTO file_actions
    (titre,famille,agents,skill,commande,prechargement,confiance,statut,cree_le)
    VALUES (?,?,?,?,?,?,?,?,datetime('now'))
    ON CONFLICT(titre) DO UPDATE SET
      famille=excluded.famille, agents=excluded.agents, skill=excluded.skill,
      commande=excluded.commande, prechargement=excluded.prechargement,
      confiance=excluded.confiance,
      statut=CASE WHEN file_actions.statut IN ('done','failed')
                  THEN file_actions.statut ELSE excluded.statut END""", lignes)
con.commit()
apres = con.execute("SELECT COUNT(*) FROM file_actions").fetchone()[0]
pend  = con.execute("SELECT COUNT(*) FROM file_actions WHERE statut='pending'").fetchone()[0]
print(f"\n  file_actions : {avant} -> {apres} (+{apres-avant})   pending={pend}")
con.close()
PYEOF

log "═══ fin ═══"
