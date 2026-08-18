#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════
#  DOMINO MEGA BUILDER — Turbo JARVIS OS
#  Génère TOUTES les séries bash manquantes, compile, valide, DB + GitHub
# ═══════════════════════════════════════════════════════════════════════
set -uo pipefail
SERIES_DIR="$HOME/labo/bibliotheque/series"
DB="$HOME/jarvis/jarvis_master.db"
LOG="/tmp/domino_mega_builder.log"
REPO_DIR="$HOME/labo"
NEW=0; SKIP=0; ERR=0

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }

# ─── Fonction: créer une série si inexistante ────────────────────────
make_serie() {
  local name="$1"
  local desc="$2"
  local body="$3"
  local f="$SERIES_DIR/${name}.sh"
  if [[ -f "$f" ]]; then SKIP=$((SKIP+1)); return; fi

  cat > "$f" <<SHEOF
#!/usr/bin/env bash
# DOMINO ${name^^} — ${desc}
# Usage: bash ${name}.sh [args]
set -uo pipefail
JARVIS="\$HOME/jarvis"; SCR="\$JARVIS/scripts"
${body}
SHEOF
  chmod +x "$f"
  bash --norc -n "$f" 2>>/tmp/domino_err.log && verdict="valide-syntaxe-ok" || verdict="syntaxe-error"
  sqlite3 "$DB" "INSERT OR REPLACE INTO domino_chains(serie,verdict,steps,ts) VALUES('${name}','${verdict}','${f}',datetime('now'));" 2>/dev/null
  log "  ✅ ${name}.sh [${verdict}]"
  NEW=$((NEW+1))
}

# ─── NOUVELLES SÉRIES LINKEDIN / MAIL / SOCIAL ──────────────────────
make_serie "linkedin-post-auto" "Publier post LinkedIn via LLM local + CDP" \
'SUJET="${1:-IA et productivité 2026}"
CONTENU=$(bash ~/jarvis/scripts/lm-ask.sh "Écris un post LinkedIn professionnel sur: $SUJET. 3 paragraphes, 250 mots max, émojis, CTA.")
echo "$CONTENU" | tee /tmp/li_post_draft.txt
echo "→ Brouillon prêt. Pour publier: linkedin-protocole.sh post \"$(cat /tmp/li_post_draft.txt)\""'

make_serie "linkedin-reply-auto" "Répondre automatiquement aux messages LinkedIn non lus" \
'bash ~/labo/bibliotheque/series/linkedin-protocole.sh inbox
python3 ~/jarvis/scripts/jarvis_linkedin_mail_autonomous_engine.py
tail -5 /tmp/linkedin_mail_loop.log'

make_serie "linkedin-content-week" "Plan de contenu LinkedIn 7 jours complet" \
'OUT="/tmp/linkedin_plan_$(date +%Y%m%d).md"
bash ~/jarvis/scripts/lm-ask.sh --big "Génère un plan de contenu LinkedIn 7 jours pour un ingénieur IA indépendant. Format: Jour | Thème | Hook | Corps | CTA. Focus: IA locale, JARVIS, productivité, freelance tech." > "$OUT"
echo "Plan 7j → $OUT"
cat "$OUT" | head -40'

make_serie "mail-triage-auto" "Trier, scorer et brouillonner des réponses mails automatiquement" \
'python3 ~/jarvis/scripts/jarvis_linkedin_mail_autonomous_engine.py
sqlite3 ~/jarvis/jarvis_master.db "SELECT email, sujet, score, statut FROM registre_envoi ORDER BY ts DESC LIMIT 10;" 2>/dev/null'

make_serie "mail-reply-send" "Envoyer les brouillons approuvés par mail" \
'sqlite3 ~/jarvis/jarvis_master.db "SELECT email, sujet, reponse FROM registre_envoi WHERE statut='"'"'brouillon-auto'"'"' ORDER BY ts DESC LIMIT 5;" 2>/dev/null | while IFS="|" read email sujet reponse; do
  echo "→ [SIMULÉ] Envoyer à $email | Sujet: $sujet"
  echo "$reponse" | head -5
done'

make_serie "mail-analyze-digest" "Analyser le digest hebdomadaire des mails entrants" \
'python3 ~/jarvis/scripts/lm-ask.sh "Analyse et résume les emails suivants en identifiant priorités, actions, opportunités:" > /tmp/mail_digest.txt
cat ~/labo/bibliotheque/prospection/digest.log | tail -50 >> /tmp/mail_digest.txt
bash ~/jarvis/scripts/lm-ask.sh --big "$(cat /tmp/mail_digest.txt)" | tee /tmp/mail_digest_result.txt'

# ─── NOUVELLES SÉRIES DEEP RESEARCH ─────────────────────────────────
make_serie "deep-research-auto" "Lancer une deep research LLM sur un sujet" \
'SUJET="${1:-Intelligence Artificielle et automatisation 2026}"
OUT="/tmp/research_$(date +%Y%m%d_%H%M).md"
log() { echo "[$(date +%H:%M:%S)] $*"; }
log "Deep Research: $SUJET"
bash ~/jarvis/scripts/lm-ask.sh --reason "Fais une deep research exhaustive sur: $SUJET. Include: état de lart, acteurs clés, tendances, opportunités, risques, sources." > "$OUT"
log "→ Résultat: $OUT ($(wc -l < "$OUT") lignes)"
cat "$OUT" | head -60'

make_serie "research-vectorize" "Deep research + vectorisation Nomic embeddings" \
'SUJET="${1:-LLM local 2026}"
bash ~/labo/bibliotheque/series/deep-research-auto.sh "$SUJET"
python3 ~/jarvis/cli/biblio-vectorize.py --input /tmp/research_*.md 2>/dev/null || true
echo "✅ Recherche vectorisée dans la Bibliothèque Vivante"'

make_serie "planning-deep-preload" "Précharger le planning JARVIS avec deep research dynamique" \
'jarvis-planning-cli deep-research "${1:-planning stratégique IA 2026}"
jarvis-planning-cli preload
jarvis-planning-cli status'

# ─── NOUVELLES SÉRIES BIBLIO / KNOWLEDGE ────────────────────────────
make_serie "biblio-expand-turbo" "Expansion turbo bibliothèque + 1000 sujets nouveaux" \
'python3 ~/jarvis/scripts/biblio_massive_expansion.py 2>/dev/null
python3 ~/jarvis/cli/biblio_filler.py --once --batch 10 2>/dev/null
sqlite3 ~/jarvis/jarvis_master.db "SELECT count(*) as total FROM biblio_knowledge;" 2>/dev/null | xargs echo "Fiches:"'

make_serie "biblio-topic-inject" "Injecter manuellement des topics dans la bibliothèque" \
'TOPIC="${1:-Agents IA autonomes 2026}"
sqlite3 ~/jarvis/jarvis_master.db "INSERT OR IGNORE INTO biblio_topics(categorie,sujet,statut) VALUES('"'"'custom'"'"','"'"'$TOPIC'"'"','"'"'pending'"'"');" 2>/dev/null
echo "✅ Topic injecté: $TOPIC"
sqlite3 ~/jarvis/jarvis_master.db "SELECT count(*) FROM biblio_topics WHERE statut='"'"'pending'"'"';" 2>/dev/null | xargs echo "Topics pending:"'

# ─── NOUVELLES SÉRIES INFRA / SYSTÈME ────────────────────────────────
make_serie "cluster-health-full" "Bilan complet de santé du cluster M1/M2/OL1" \
'log() { echo "[$(date +%H:%M:%S)] $*"; }
log "=== CLUSTER HEALTH FULL ==="
log "M1 (192.168.0.10:1234):"
curl -s -m5 http://192.168.0.10:1234/v1/models 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print([m['"'"'id'"'"'] for m in d.get('"'"'data'"'"',[])])" 2>/dev/null || echo "  ⚠️ M1 DOWN"
log "M2 (127.0.0.1:18800):"
curl -s -m5 http://127.0.0.1:18800/v1/models 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print([m['"'"'id'"'"'] for m in d.get('"'"'data'"'"',[])])" 2>/dev/null || echo "  ⚠️ M2 DOWN"
log "OL1 (127.0.0.1:11434):"
curl -s -m5 http://127.0.0.1:11434/api/tags 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print([m['"'"'name'"'"'] for m in d.get('"'"'models'"'"',[])])" 2>/dev/null || echo "  ⚠️ OL1 DOWN"
log "Bridges:"
ss -tlnp 2>/dev/null | grep -E "9742|18800|9761|8420" | awk '"'"'{print "  ✅ Port",$4}'"'"' | head -10'

make_serie "services-restart-all" "Redémarrer tous les services JARVIS critiques" \
'log() { echo "[$(date +%H:%M:%S)] $*"; }
for svc in jarvis-biblio-infinite jarvis-task-auto task-autogen; do
  systemctl --user restart "$svc" 2>/dev/null && log "✅ $svc restarted" || log "⚠️ $svc non trouvé"
done
systemctl --user status jarvis-biblio-infinite --no-pager -l | tail -5'

make_serie "gpu-watch-live" "Monitoring GPU temps + VRAM en temps réel" \
'watch -n 2 '"'"'nvidia-smi --query-gpu=name,temperature.gpu,memory.used,memory.free,utilization.gpu --format=csv,noheader,nounits 2>/dev/null | awk -F, "{printf \"GPU: %s | Temp: %s°C | VRAM: %sMiB/%sMiB | Util: %s%%\n\",\$1,\$2,\$3,\$4,\$5}"'"'"''

make_serie "docker-audit-all" "Audit complet tous les containers Docker JARVIS" \
'docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null
echo "---"
docker ps -a --format "{{.Names}}\t{{.Status}}" 2>/dev/null | grep -v "Up" | head -20'

make_serie "systemd-status-all" "Statut de tous les services systemd --user JARVIS" \
'systemctl --user list-units --type=service --state=active --no-pager | grep -E "jarvis|biblio|lumen|openclaw|task" | head -30
echo "---"
systemctl --user list-units --type=service --state=failed --no-pager | head -20'

# ─── NOUVELLES SÉRIES PROSPECTION / CRM ─────────────────────────────
make_serie "prospect-linkedin-full" "Pipeline complet prospection LinkedIn: scan + draft + envoi" \
'log() { echo "[$(date +%H:%M:%S)] $*"; }
log "1. Scan inbox LinkedIn"
bash ~/labo/bibliotheque/series/linkedin-protocole.sh inbox
log "2. Génération drafts"
python3 ~/jarvis/scripts/jarvis_linkedin_mail_autonomous_engine.py
log "3. Post automatique LinkedIn"
bash ~/labo/bibliotheque/series/linkedin-post-auto.sh "IA autonome et productivité ingénieur 2026"
log "✅ Pipeline prospection LinkedIn terminé"'

make_serie "crm-full-cycle" "Cycle CRM complet: mails + LinkedIn + enrichissement" \
'bash ~/labo/bibliotheque/series/mail-triage-auto.sh
bash ~/labo/bibliotheque/series/linkedin-reply-auto.sh
bash ~/labo/bibliotheque/series/crm-enrich.sh 2>/dev/null || true
sqlite3 ~/jarvis/jarvis_master.db "SELECT count(*) FROM registre_envoi;" 2>/dev/null | xargs echo "Contacts CRM:"'

make_serie "content-linkedin-week-publish" "Générer ET publier 7 posts LinkedIn en une passe" \
'for i in $(seq 1 7); do
  THEMES=("IA locale vs Cloud" "Automatisation JARVIS OS" "Productivité ingénieur IA" "LLM on-premise" "Freelance tech 2026" "Agent autonome JARVIS" "Deep Research IA")
  THEME="${THEMES[$((i-1))]}"
  bash ~/labo/bibliotheque/series/linkedin-post-auto.sh "$THEME"
  echo "--- Post $i/$i généré ---"
  sleep 5
done'

# ─── NOUVELLES SÉRIES GIT / DEPLOY ──────────────────────────────────
make_serie "git-sync-all" "Synchroniser tous les repos JARVIS sur GitHub" \
'log() { echo "[$(date +%H:%M:%S)] $*"; }
REPOS=(~/labo ~/jarvis ~/Workspaces/jarvis-linux ~/deep-research/repos/jarvis-profile)
for REPO in "${REPOS[@]}"; do
  [[ -d "$REPO/.git" ]] || continue
  log "Syncing $REPO..."
  cd "$REPO"
  git add -A && git commit -m "auto-sync: $(date +%Y%m%d_%H%M)" --quiet && git push --quiet 2>/dev/null && log "✅ $REPO pushed" || log "  ⤷ rien de nouveau / pas de remote"
done'

make_serie "domino-compile-all" "Recompiler et valider toutes les séries domino" \
'SERIES_DIR="$HOME/labo/bibliotheque/series"
DB="$HOME/jarvis/jarvis_master.db"
OK=0; ERR=0
for f in "$SERIES_DIR"/*.sh; do
  name=$(basename "$f" .sh)
  bash --norc -n "$f" 2>/dev/null && verdict="valide-syntaxe-ok" || verdict="syntaxe-error"
  sqlite3 "$DB" "INSERT OR REPLACE INTO domino_chains(serie,verdict,steps,ts) VALUES('"'"'$name'"'"','"'"'$verdict'"'"','"'"'$f'"'"',datetime('"'"'now'"'"'));" 2>/dev/null
  [[ "$verdict" == "valide-syntaxe-ok" ]] && OK=$((OK+1)) || ERR=$((ERR+1))
done
echo "✅ Compilés: $OK valides / $ERR erreurs"'

# ─── RÉSUMÉ FINAL ────────────────────────────────────────────────────
log ""
log "═══════════════════════════════════════════"
log "  DOMINO MEGA BUILDER TERMINÉ"
log "  Nouvelles séries: $NEW | Existantes: $SKIP | Erreurs: $ERR"
TOTAL=$(ls "$SERIES_DIR"/*.sh 2>/dev/null | wc -l)
log "  TOTAL SÉRIES: $TOTAL"
log "═══════════════════════════════════════════"
