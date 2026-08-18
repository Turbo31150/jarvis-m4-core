#!/usr/bin/env bash
# ============================================================================
# cahier-des-charges-hook.sh — Stop hook JARVIS
# "À chaque arrêt → on balance le cahier des charges" (demande Rémi 2026-06-24).
#
# Crache une COMMAND CARD compacte construite DYNAMIQUEMENT depuis la config
# mode-audit (audit-config.yaml + audit-combos.yaml + patterns-html.md).
# Additif : coexiste avec le Stop hook plugin parse-transcript.py (logging session).
#
# CONTRAT HOOK (sécurité) :
#   - Sort TOUJOURS en exit 0 (jamais bloquer le Stop → évite boucle).
#   - Émet du JSON {continue, suppressOutput, systemMessage} : la card est
#     affichée via systemMessage, jamais réinjectée dans le contexte Claude.
#   - Zéro dépendance (awk/grep, pas de yq). Fallbacks si fichier absent.
# ============================================================================

CFG="$HOME/jarvis/config/audit-config.yaml"
COMBOS="$HOME/jarvis/config/audit-combos.yaml"
PATTERNS="$HOME/jarvis/config/audit-patterns/patterns-html.md"
JARVIS_BIN="$HOME/jarvis/bin/jarvis"

# --- comptages dynamiques (best-effort, jamais fatal) -----------------------
n_combos=$(grep -cE '^\s*-\s*name:' "$COMBOS" 2>/dev/null || echo 0)
# patterns = lignes de tableau référençant un fichier source .html (entrées réelles)
# exclut la ligne d'en-tête ("Source URL (.html / URL)") pour un comptage exact.
n_patterns=$(grep -E '^\|' "$PATTERNS" 2>/dev/null | grep -v 'Source URL' | grep -c '\.html' 2>/dev/null || echo 0)
[ -z "$n_patterns" ] && n_patterns=0
n_subs=$(grep -cE '^\s+audit:[a-z:-]+\)' "$JARVIS_BIN" 2>/dev/null || echo 0)

# modes actifs (non commentés) dans audit-config.yaml
modes=$(awk '/^modes:/{p=1;next}/^[a-z]/{p=0}p&&/^  [a-z]/{gsub(/:.*/,"");gsub(/ /,"");printf "%s/",$0}' "$CFG" 2>/dev/null | sed 's:/$::')
[ -z "$modes" ] && modes="fast/standard"

# profils actifs
profiles=$(awk '/^profiles:/{p=1;next}/^[a-z]/{p=0}p&&/^  [a-z]/{gsub(/:.*/,"");gsub(/ /,"");printf "%s ",$0}' "$CFG" 2>/dev/null | sed 's/ $//')
[ -z "$profiles" ] && profiles="tech"

# prochaine combo suggérée
next_combo=$(grep -E '^\s*-\s*name:' "$COMBOS" 2>/dev/null | head -1 | sed 's/.*name:[[:space:]]*//' || true)
[ -z "$next_combo" ] && next_combo="combo:repo-health"

# TOUS les combos enregistrés (bibliothèque complète, dynamique — pas juste le 1er)
combos_named=$(grep -E '^\s*-\s*name:' "$COMBOS" 2>/dev/null | sed 's/.*name:[[:space:]]*//' | paste -sd '~' - | sed 's/~/ · /g')
[ -z "$combos_named" ] && combos_named="$next_combo"

# bibliothèque de patterns HTML regroupée par site source — 100% DYNAMIQUE
# (dérive les marques depuis les URLs réelles du fichier, AUCUN nom codé en dur :
#  tout nouveau site enregistré apparaît automatiquement).
patterns_sites=$(grep -oiE 'https?://[a-z0-9.-]+' "$PATTERNS" 2>/dev/null \
  | sed -E 's#https?://(www\.)?##; s#/.*##; s#\.[a-z]+$##' \
  | awk 'NF{print toupper(substr($0,1,1)) substr($0,2)}' \
  | sort | uniq -c | sort -rn | awk '{printf "%s(%s) ",$2,$1}' | sed 's/ $//')
# + patterns internes (fichiers locaux .html sans URL, ex. captures DVA/wbs)
n_internal=$(grep -E '^\|' "$PATTERNS" 2>/dev/null | grep -v 'Source URL' | grep -v 'http' | grep -c '\.html' 2>/dev/null || echo 0)
[ -z "$n_internal" ] && n_internal=0
[ "$n_internal" -gt 0 ] 2>/dev/null && patterns_sites="${patterns_sites} interne(${n_internal})"
[ -z "$patterns_sites" ] && patterns_sites="(voir fichier)"

# TOUS les combos DÉCOMPOSÉS (chaque combo éclaté en sa série complète, prêt à coller —
# pas juste le 1er). "série enregistrée ET décomposée pour exécution immédiate" (Rémi 2026-06-29).
# awk pur, zéro dépendance ; tout combo ajouté au yaml apparaît automatiquement.
combos_decomposed=$(awk '
  /^[[:space:]]*-[[:space:]]*name:/ { if(nm!=""){emit()} nm=$0; sub(/.*name:[[:space:]]*/,"",nm); inc=0; cmds=""; next }
  /^[[:space:]]*commands:/ { inc=1; next }
  inc && /^[[:space:]]*-[[:space:]]+jarvis /{
    c=$0; sub(/^[[:space:]]*-[[:space:]]+/,"",c); sub(/[[:space:]]*#.*/,"",c);
    gsub(/[[:space:]]+/," ",c); sub(/[[:space:]]+$/,"",c);
    cmds=(cmds==""?c:cmds" \342\206\222 "c); next }
  inc && /^[[:space:]]*[a-zA-Z]/ { inc=0 }
  END { if(nm!=""){emit()} }
  function emit(){ printf "   \342\206\263 %s : %s\n", nm, cmds }
' "$COMBOS" 2>/dev/null)
[ -z "$combos_decomposed" ] && combos_decomposed="   ↳ ${combos_named}"

# total "actions" chargées = subcommands CLI + combos (série décomposée)
n_actions=$(( n_subs + n_combos ))

# acid-test mesurable move ③ : verdicts critic-gate des 7 derniers jours.
# 1 seule requête, best-effort (timeout 3s + fallback), JAMAIS fatal pour le Stop.
# Flag "Nodding" si des passages ont eu lieu mais 0 rejet (VETO/WARN) → évaluateur en carton.
# 2026-08-04 — routage tour. Depuis la migration du 03/08 le `docker exec` local
# echouait a CHAQUE fin de tour ; le `2>/dev/null` + fallback affichait sagement
# "critic_reports indispo (best-effort)" comme si la table etait vide, alors que
# c'est la connexion qui etait morte. ControlMaster : ce hook tourne a chaque
# Stop, le multiplexage ramene la poignee de main ssh de ~1,4 s a ~0,35 s.
CDC_JOURNAL=/home/rempc/jarvis/logs/cahier-des-charges-hook.log
mkdir -p "$(dirname "$CDC_JOURNAL")" 2>/dev/null
acid_err=$(timeout 12 ssh -o BatchMode=yes -o ConnectTimeout=5 \
  -o ControlMaster=auto -o ControlPath=/home/rempc/.ssh/cm-%r@%h:%p -o ControlPersist=600 \
  root@100.124.69.1 \
  "docker exec -i jarvis-postgres psql -U jarvis_agent -d jarvis_main -tA" 2>&1 >/tmp/.cdc-acid.$$ <<'ACIDSQL'
SELECT count(*)||' verdicts 7j ('||coalesce(sum((verdict='VETO')::int),0)||' VETO · '||coalesce(sum((verdict='WARN')::int),0)||' WARN)'||CASE WHEN count(*)>0 AND coalesce(sum((verdict IN ('VETO','WARN'))::int),0)=0 THEN ' ⚠ 0 rejet = évaluateur en carton (Nodding)' ELSE '' END FROM critic_reports WHERE created_at > now()-interval '7 days';
ACIDSQL
)
acid_rc=$?
acid=$(tr -d '\n' </tmp/.cdc-acid.$$ 2>/dev/null); rm -f /tmp/.cdc-acid.$$
if [ "$acid_rc" -ne 0 ] || [ -z "$acid" ]; then
  # Ne plus confondre "table vide" et "base injoignable" : on le dit, et on le trace.
  echo "$(date -Iseconds) ECHEC lecture critic_reports rc=${acid_rc} err=${acid_err//$'\n'/ }" >>"$CDC_JOURNAL" 2>/dev/null
  acid="critic_reports INJOIGNABLE (tour ssh rc=${acid_rc}) — voir $CDC_JOURNAL"
fi

# --- construction de la card (compacte, balises de sortie) ------------------
# Balises de sortie : ⟦OLAB-MODE:CASCADE-MAX⟧ … ⟦/OLAB⟧ délimitent la card
# (marqueur "charge maximale / cascade maximale" demandé par Rémi).
read -r -d '' CARD <<CARD || true
⟦OLAB-MODE:CASCADE-MAX⟧ 📋 CAHIER DES CHARGES — LOOP ENGINEERING · AUDIT · PLAN · DEEP-RESEARCH | ${n_actions} actions · ${n_combos} combos · ${n_patterns} patterns HTML · profils:${profiles} · modes:${modes}
▶ La boucle (5 moves, coupe-en 1 = tourne dans le vide) : ① Discovery → ② Handoff → ③ Verify → ④ Persist → ⑤ Schedule · l'output d'aujourd'hui = l'input de demain
▶ Plan mode : /superpowers:writing-plans · EnterPlanMode (archi AVANT code)
▶ ① Discovery (charge max) : jarvis audit:run --target <T> --topic "<S>" --profile tech --mode standard · /deep-research "<Q>" · /jarvis:deep-audit → JUGE actionnable-now vs bruit (le loop CHOISIT, pas toi — sinon Blind Loop)
▶ ② Handoff : 1 tâche = 1 worktree isolé — combo:loop-triage (~/jarvis/bin/loop-triage.sh, cap parallèle, jamais de merge) ou EnterWorktree · todolist CLI : TaskCreate → TaskUpdate(in_progress) → … → completed · combos décomposés (${n_combos}, prêts à coller, remplace <T>) · next: ${next_combo} :
${combos_decomposed}
   liste: jarvis audit:combos · Card: jarvis audit:card --target <T>
▶ ③ Verify — la porte qui dit NON (ASSUME BROKEN, juge le comportement pas l'intention, modèle différent) : critic-gate · gemini challenge · board · /goal (modèle frais juge la condition) ≠ /loop (intervalle, AUCUN jugement d'arrêt) · acid-test : ${acid}
▶ ④ Persist (état sur disque ≠ contexte flushé, LOI#2 conteneurs) : combo gagnant → memory_timeline → promo dans ${COMBOS} (bloc -name/quand/valeur/commands)
▶ ⑤ Schedule : CronCreate · ScheduleWakeup · 3 caps AVANT le 1er run (timeout / budget / retries — Paperclip circuit-breaker) · porte humaine (jamais auto-merge / irréversible sans go Rémi)
▶ Biblio patterns HTML (${n_patterns}) : ${patterns_sites} · ${PATTERNS}
▶ Garde anti-maladie : Blind(le loop choisit) · Tangled(worktree/tâche) · Nodding(porte NON) · Amnesiac(disque) · Manual(trigger) — 4 dettes silencieuses : vérification · comprehension-rot · cognitive-surrender · token-blowout
▶ Triggers : "mode audit" · "deep research" · "plan" · "scan" · "cascade" · "todolist" · "cahier des charges" · "loop"
▶ Cascade max : OpenClaw :3200 (cheap-first) → board → Gemini API (best-effort, fallback 3-voix si 429) → ChatGPT gpt-5 → merge Claude · liaison mémoire au départ
⟦/OLAB⟧
CARD

# --- émission JSON hook (display-only, jamais bloquant) ----------------------
python3 - "$CARD" <<'PY' 2>/dev/null || printf '{"continue":true,"suppressOutput":true}\n'
import json, sys
msg = sys.argv[1] if len(sys.argv) > 1 else ""
print(json.dumps({"continue": True, "suppressOutput": True, "systemMessage": msg}))
PY
exit 0
