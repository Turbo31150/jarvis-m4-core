#!/usr/bin/env bash
# skillmp-cascade.sh — CASCADE MASSIVE skills -> agents (0-token).
#
# Declenchee a la SORTIE DU PLAN MODE : prend le plan d'implantation SkillsMP,
# construit la todolist dynamique prechargee, affecte chaque tache a la famille
# d'agents porteuse, puis dispatche par vagues bornees.
#
# Modes :
#   dry-run   (defaut) : plan + vagues + prechargement simules. 0 ecriture, 0 dispatch.
#   validated          : ecrit la todolist en base. Ne lance aucun agent.
#   auto               : dispatch reel, borne par --quota et les garde-fous charge/GPU.
#
# Usage : skillmp-cascade.sh [--mode dry-run|validated|auto] [--famille NOM|all]
#                            [--quota N] [--vague N]
# NB : pas de `pipefail` — les pipes vers head/tail peuvent recevoir SIGPIPE.
set -u

JARVIS=/home/pamerys/jarvis
DB="$JARVIS/jarvis_master.db"
BASE=/home/pamerys/labo/bibliotheque/skillsmp
PLAN="$BASE/export/plan_implantation.json"
TODO="$BASE/export/TODO_DYNAMIQUE_SKILLSMP.json"
LOG="$JARVIS/logs/skillmp-cascade.log"

MODE=dry-run
FAMILLE=all
QUOTA=5
VAGUE=3

while [ $# -gt 0 ]; do
  case "$1" in
    --mode)    MODE="$2"; shift 2;;
    --famille) FAMILLE="$2"; shift 2;;
    --quota)   QUOTA="$2"; shift 2;;
    --vague)   VAGUE="$2"; shift 2;;
    -h|--help) sed -n '2,20p' "$0"; exit 0;;
    *) echo "option inconnue : $1" >&2; exit 2;;
  esac
done

# Resolution du CLI skillmp : PATH, puis wrapper, puis module python.
# Sans cela le dispatch tombe silencieusement en "skipped" hors session interactive.
if command -v skillmp >/dev/null 2>&1; then
  SKILLMP="skillmp"
elif [ -x "$JARVIS/bin/skillmp" ]; then
  SKILLMP="$JARVIS/bin/skillmp"
else
  SKILLMP="python3 $JARVIS/bin/skillmp.py"
fi

mkdir -p "$(dirname "$LOG")"
horodate() { date -Is; }
journal() { printf '%s\t%s\t%s\n' "$(horodate)" "$MODE" "$*" >> "$LOG"; echo "$*"; }

[ -f "$PLAN" ] || { echo "plan absent : $PLAN — lancer implantation.py d'abord" >&2; exit 1; }

echo "═══════════════════════════════════════════════════════════"
echo "  CASCADE MASSIVE SkillsMP → agents JARVIS"
echo "  mode=$MODE famille=$FAMILLE quota=$QUOTA vague=$VAGUE"
echo "═══════════════════════════════════════════════════════════"

# ── 1. GARDE-FOUS (avant tout dispatch)
CHARGE=$(cut -d' ' -f1 /proc/loadavg)
RAM_PC=$(free | awk '/Mem:/{printf "%d", $3/$2*100}')
# nvidia-smi ecrit ses erreurs sur STDOUT ("Failed to initialize NVML: ...") :
# 2>/dev/null ne les filtre pas et GPU_T recevait une chaine, si bien que
# [ "$GPU_T" -ge 95 ] echouait avec "nombre entier attendu" et le garde-fou
# thermique ne bloquait JAMAIS. On ne retient donc que des lignes numeriques.
GPU_T=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits 2>/dev/null \
        | grep -Eox '[0-9]+' | sort -rn | head -1)
if [ -z "$GPU_T" ]; then
  GPU_T=0
  GPU_SONDE_MUETTE=1
fi
journal "garde-fous charge=$CHARGE ram=${RAM_PC}% gpu_max=${GPU_T}C"
[ "${GPU_SONDE_MUETTE:-0}" = 1 ] && journal "AVERTISSEMENT sonde GPU muette (nvidia-smi HS) : garde-fou thermique INACTIF"

if [ "$MODE" = auto ]; then
  # Seuil GPU 84->95 (regle Turbo 2026-08-06) : 100 C = plafond ou le materiel
  # se bride SEUL (tour 9 ventilateurs, throttling constructeur, zero degat).
  # 84 C bloquait le dispatch en permanence sous moisson — fausse prudence.
  if [ "${CHARGE%%.*}" -ge 12 ] || [ "$RAM_PC" -ge 92 ] || [ "$GPU_T" -ge 95 ]; then
    journal "ABANDON auto : systeme sous pression (charge/ram/gpu) — repli en validated"
    MODE=validated
  fi
fi

# ── 2. PLAN : familles et volumes
journal "lecture du plan $PLAN"
python3 - "$PLAN" "$FAMILLE" <<'PY'
import json, sys, collections
plan = json.load(open(sys.argv[1]))
f = sys.argv[2]
if f != "all":
    plan = [p for p in plan if p["famille"] == f]
c = collections.Counter(p["famille"] for p in plan)
print(f"  skills au plan : {len(plan)}")
for fam, n in c.most_common():
    print(f"    {fam:12s} {n:3d}")
PY

# ── 3. TODOLIST DYNAMIQUE + PRECHARGEMENT
if [ -f "$TODO" ]; then
  N_TODO=$(python3 -c "import json;print(len(json.load(open('$TODO'))['taches']))")
  N_PRE=$(python3 -c "
import json
t=json.load(open('$TODO'))['taches']
print(sum(1 for x in t if x.get('prechargement')))")
  journal "todolist : $N_TODO taches, $N_PRE avec contexte precharge"
else
  journal "todolist absente — relancer implantation.py"
fi

# ── 4. ECRITURE EN BASE (validated + auto)
if [ "$MODE" != dry-run ]; then
  python3 - "$TODO" "$DB" "$FAMILLE" <<'PY'
import json, sqlite3, sys
todo, db, famille = sys.argv[1], sys.argv[2], sys.argv[3]
taches = json.load(open(todo))["taches"]
if famille != "all":
    taches = [t for t in taches if t["famille"] == famille]
cx = sqlite3.connect(db); cx.execute("PRAGMA busy_timeout=15000")
cx.execute("""CREATE TABLE IF NOT EXISTS skillmp_cascade_taches (
  id INTEGER PRIMARY KEY AUTOINCREMENT, titre TEXT UNIQUE, famille TEXT,
  agents TEXT, skill TEXT, commande TEXT, prechargement TEXT,
  statut TEXT DEFAULT 'pending', cree_le TEXT DEFAULT (datetime('now')))""")
n = 0
for t in taches:
    try:
        cx.execute("""INSERT OR IGNORE INTO skillmp_cascade_taches
          (titre,famille,agents,skill,commande,prechargement)
          VALUES (?,?,?,?,?,?)""",
          (t["titre"], t["famille"], ",".join(t["agents_cibles"]), t["skill"],
           t["commande"], json.dumps(t.get("prechargement", []), ensure_ascii=False)))
        n += cx.total_changes and 1 or 0
    except sqlite3.Error as e:
        print("  ERR", e)
cx.commit()
total = cx.execute("SELECT COUNT(*) FROM skillmp_cascade_taches WHERE statut='pending'").fetchone()[0]
cx.close()
print(f"  taches en file : {total} (pending)")
PY
  journal "todolist persistee en base (skillmp_cascade_taches)"
fi

# ── 5. DISPATCH PAR VAGUES (auto uniquement)
# Garde-fou anti-injection SQL : FAMILLE et QUOTA sont interpolés dans sqlite3
# ci-dessous (pas de bind ? possible dans le heredoc). --famille n'a pas de
# choices côté CLI, donc `--famille "x'; DROP TABLE..."` passerait. On refuse
# tout ce qui n'est pas un nom de famille pur ou un entier.
# regex ANCRÉE (^…$) : un glob case `[a-z]*` laisserait passer `xa'; DROP`
# car `*` y est un joker. Ici seules des minuscules pures, ou "all".
[[ "$FAMILLE" =~ ^[a-z]+$ ]] || { echo "famille invalide: $FAMILLE" >&2; exit 2; }
[[ "$QUOTA" =~ ^[0-9]+$ ]] || { echo "quota invalide: $QUOTA" >&2; exit 2; }
[[ "$VAGUE" =~ ^[0-9]+$ ]] || { echo "vague invalide: $VAGUE" >&2; exit 2; }

if [ "$MODE" = auto ]; then
  journal "dispatch : $VAGUE vagues x $QUOTA taches"
  for v in $(seq 1 "$VAGUE"); do
    echo "── vague $v/$VAGUE ──"
    mapfile -t LOT < <(sqlite3 "$DB" \
      "SELECT id||'|'||skill||'|'||famille FROM skillmp_cascade_taches
       WHERE statut='pending' $([ "$FAMILLE" != all ] && echo "AND famille='$FAMILLE'")
       ORDER BY id LIMIT $QUOTA;")
    [ "${#LOT[@]}" -eq 0 ] && { journal "file vide — cascade terminee"; break; }
    for entree in "${LOT[@]}"; do
      ID=${entree%%|*}; RESTE=${entree#*|}; SKILL=${RESTE%%|*}; FAM=${RESTE##*|}
      if $SKILLMP install "$SKILL" --cible both >/dev/null 2>&1; then
        ETAT=done
      else
        ETAT=failed
      fi
      sqlite3 "$DB" "UPDATE skillmp_cascade_taches SET statut='$ETAT' WHERE id=$ID;"
      journal "  [$FAM] $SKILL -> $ETAT"
    done
    # respiration entre vagues : laisse retomber la charge
    sleep 3
  done
fi

# ── 6. RAPPORT
echo
echo "── RAPPORT ─────────────────────────────────────────────────"
if [ "$MODE" != dry-run ]; then
  sqlite3 -column -header "$DB" \
    "SELECT famille, statut, COUNT(*) AS n FROM skillmp_cascade_taches
     GROUP BY famille, statut ORDER BY n DESC LIMIT 20;"
fi
journal "cascade terminee (mode=$MODE)"
echo "  journal : $LOG"
