#!/usr/bin/env bash
# jarvis-lms-qwen-warm : garantit que qwen/qwen3.5-9b est charge dans LM Studio
# au bon contexte (16384) et parallel (2), sans casser le serveur :11235 en cours.
# Idempotent : ne recharge PAS si deja au bon etat.
#
# Parsing robuste : on prefere `lms ps --json` (champs stables contextLength /
# parallel / status / identifier) plutot que le parsing positionnel de la sortie
# tabulaire (la colonne SIZE "6.55 GB" occupe 2 champs et decale $6/$7).
#
# Anti-coupure : si qwen est en train de generer (status GENERATING /
# PROCESSINGPROMPT), on NE recharge PAS ce tick pour ne pas couper une reponse
# servie sur :11235. Forcer avec FORCE_RELOAD=1 si besoin.

set -uo pipefail
export PATH="$HOME/.lmstudio/bin:$PATH"

MODEL="qwen/qwen3.5-9b"
WANT_CTX=${WANT_CTX:-32768}
WANT_PAR=${WANT_PAR:-12}  # depuis 2026-08-07 : 5 GPU visibles (CUDA 0-4, 40 Go), qwen
# sert 12 predictions paralleles en ctx 32k, valide en charge (prod-runner x8).
# Ancien reglage 16384/2 : epoque 12,3 Go partages avec GNOME — ne PAS y revenir
# sans raison, un tick l'imposerait en dechargeant qwen en pleine generation.
TTL=${TTL:-86400}
FORCE_RELOAD="${FORCE_RELOAD:-0}"

if ! command -v lms >/dev/null 2>&1; then
  echo "[qwen-warm] lms CLI introuvable" >&2
  exit 1
fi

# ------------------------------------------------------------------
# Garde de l'embedding — posee en TRAP, pas en fin de script.
#
# `lms load ... --gpu max` reserve TOUTE la VRAM disponible : LM Studio evince
# alors les autres modeles, dont nomic-embed. Mesure du 2026-08-06 : embedding
# present avant l'appel, absent 25 s apres, a chaque tick du timer (7 min).
# Consequence : le moteur d'intention (~/jarvis/bin/intent-engine.py) retombait
# en boucle sur son repli lexical et l'index vectoriel ne finissait jamais.
#
# Pourquoi un trap et pas une ligne en fin de fichier : ce script sort par
# `exit 0` des que qwen est deja au bon etat (cas NOMINAL, le plus frequent) —
# une garde placee apres le `lms load` final n'aurait jamais tourne.
# nomic pese 84 Mo : le recharger ne coute rien. EMB_KEEP=0 pour desactiver.
EMB_MODEL="${EMB_MODEL:-text-embedding-nomic-embed-text-v1.5}"
garder_embedding() {
  [[ "${EMB_KEEP:-1}" == "1" ]] || return 0
  lms ps 2>/dev/null | grep -qF "$EMB_MODEL" && return 0
  # L'API /v1/models publie le catalogue, pas ce qui est sur le disque : un
  # modèle supprimé y figure encore et « échoue au chargement » à chaque tick.
  # Constat du 2026-08-06 : aucun GGUF d'embedding n'est présent localement,
  # la vectorisation passe par Ollama (nomic-embed-text). On le dit au lieu de
  # journaliser un ECHEC qu'on rediagnostiquera pour rien.
  if ! find "$HOME/.lmstudio/models" -maxdepth 4 -iname '*nomic*' -name '*.gguf' \
       -print -quit 2>/dev/null | grep -q .; then
    echo "[qwen-warm] embedding non installé localement — Ollama assure (nomic-embed-text)"
    return 0
  fi
  echo "[qwen-warm] embedding absent -> rechargement $EMB_MODEL"
  timeout 120 lms load "$EMB_MODEL" --ttl "${EMB_TTL:-3600}" -y >/dev/null 2>&1 \
    && echo "[qwen-warm] embedding OK" \
    || echo "[qwen-warm] embedding ECHEC (non bloquant)"
}
# ------------------------------------------------------------------
# Garde des AUTRES modeles — MEME cause que la garde d'embedding ci-dessus.
#
# `--gpu max` n'evince pas que nomic : il evince TOUT ce qui est charge.
# Mesure du 2026-08-06 : un second modele (hermes-2-pro-mistral-7b) disparait
# a chaque tick du timer. Consequence sur le board multi-modeles : une
# deliberation dure 3 a 6 min, elle est donc CERTAINE d'etre percutee — les
# requetes en vol meurent en `{"error":"terminated"}` et les concurrentes en
# HTTP 500 (page HTML generique, pas une erreur JSON de LM Studio). Aucune
# deliberation a deux modeles n'aboutissait tant que cette garde n'existait pas.
# MODELES_KEEP=0 pour desactiver.
AUTRES_AVANT=""
snapshot_autres() {
  [[ "${MODELES_KEEP:-1}" == "1" ]] || return 0
  AUTRES_AVANT="$(lms ps 2>/dev/null | tr -s ' ' \
    | awk -v m="$MODEL" -v e="$EMB_MODEL" \
      '$2!="" && $2!="MODEL" && $2!=m && $2!=e {print $2}' | sort -u)"
}
garder_autres() {
  # 1) restaurer ce que CE run a evince (instantane pris au demarrage)…
  local apres mod
  apres="$(lms ps 2>/dev/null | tr -s ' ' | awk '$2!="" && $2!="MODEL"{print $2}')"
  if [[ -n "$AUTRES_AVANT" ]]; then
    while read -r mod; do
      [[ -z "$mod" ]] && continue
      grep -qxF "$mod" <<<"$apres" && continue
      echo "[qwen-warm] modele evince -> rechargement $mod"
      # --gpu 0.5 + ctx 4096 : depuis qwen 32k/12 (2026-08-07), les 1660S n'ont
    # plus ~1 Go libre chacune ; un split tensor plein fait SIGABRT llama-server
    # a 74 % du chargement. L'offload partiel est le seul chemin qui charge.
    timeout 300 lms load "$mod" --ttl "${AUTRES_TTL:-86400}" --gpu "${AUTRES_GPU:-0.5}" --context-length "${AUTRES_CTX:-4096}" -y >/dev/null 2>&1 \
        && echo "[qwen-warm] $mod OK" || echo "[qwen-warm] $mod ECHEC (non bloquant)"
    done <<<"$AUTRES_AVANT"
  fi
  # 2) …ET garantir les modeles PLANCHER. L'instantane ne protege que contre
  # une eviction PENDANT ce run : un modele tombe ENTRE deux ticks (contention
  # JIT, guard, decharge manuelle) est deja absent de l'instantane suivant et
  # personne ne le relevait — constate 2026-08-06, hermes disparu 4 fois.
  # Le tick de 2 min devient son releveur. MODELES_PLANCHER="" pour desactiver.
  for mod in ${MODELES_PLANCHER:-hermes-2-pro-mistral-7b}; do
    grep -qxF "$mod" <<<"$apres" && continue
    echo "[qwen-warm] plancher absent -> rechargement $mod"
    # --gpu 0.5 + ctx 4096 : depuis qwen 32k/12 (2026-08-07), les 1660S n'ont
    # plus ~1 Go libre chacune ; un split tensor plein fait SIGABRT llama-server
    # a 74 % du chargement. L'offload partiel est le seul chemin qui charge.
    timeout 300 lms load "$mod" --ttl "${AUTRES_TTL:-86400}" --gpu "${AUTRES_GPU:-0.5}" --context-length "${AUTRES_CTX:-4096}" -y >/dev/null 2>&1 \
      && echo "[qwen-warm] $mod OK" || echo "[qwen-warm] $mod ECHEC (non bloquant)"
  done
}
trap 'garder_embedding; garder_autres' EXIT
snapshot_autres

# ------------------------------------------------------------------
# Attente readiness du daemon LM Studio (API locale 127.0.0.1:1234), en
# LECTURE SEULE : ne lance jamais l'app, ne tue jamais rien. Objectif :
# distinguer un simple warmup (Xvfb+Electron cold-boot ~60-90s apres un
# restart de lms-headless.service) d'une vraie panne, sans faire echouer
# le service a chaque tick de 10 min pendant le warmup.
# Avant ce fix : "lms load" echouait immediatement (rc=1, "daemon is not
# running") -> systemd marquait le service FAILED toutes les 10 min meme
# quand LM Studio etait juste en train de demarrer. Desormais : on attend
# jusqu'a WAIT_MAX secondes, et si le daemon reste injoignable, on SKIPPE
# proprement (exit 0, pas un echec) -> le timer reessaiera au tick suivant.
# ------------------------------------------------------------------
WAIT_MAX=${WAIT_MAX:-60}
WAIT_STEP=2
waited=0
while ! curl -fsS -o /dev/null --max-time 3 "http://127.0.0.1:1234/v1/models" 2>/dev/null; do
  if [[ "$waited" -ge "$WAIT_MAX" ]]; then
    echo "[qwen-warm] daemon LM Studio (127.0.0.1:1234) injoignable apres ${WAIT_MAX}s -> skip ce tick (pas un echec, retry au prochain tick timer)" >&2
    exit 0
  fi
  sleep "$WAIT_STEP"
  waited=$((waited + WAIT_STEP))
done
[[ "$waited" -gt 0 ]] && echo "[qwen-warm] daemon pret apres ${waited}s d'attente (warmup)"

# ------------------------------------------------------------------
# Detection de l etat via JSON si dispo, sinon fallback grep robuste.
# Renseigne : ctx, par, status (minuscule normalise), present (0/1).
# ------------------------------------------------------------------
HAS_JSON=0
if lms ps --help 2>&1 | grep -q -- '--json'; then
  HAS_JSON=1
fi

ctx=""; par=""; status=""; present=0

if [[ "$HAS_JSON" == "1" ]] && command -v python3 >/dev/null 2>&1; then
  # Parse le JSON : premiere entree dont identifier == MODEL exact.
  read -r ctx par status < <(
    lms ps --json 2>/dev/null | MODEL="$MODEL" python3 -c '
import sys, os, json
m = os.environ["MODEL"]
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
for e in data if isinstance(data, list) else []:
    if e.get("identifier") == m or e.get("modelKey") == m:
        ctx = e.get("contextLength", "")
        par = e.get("parallel", "")
        st  = str(e.get("status", "")).strip().lower()
        print(ctx, par, st)
        break
' )
  [[ -n "${ctx:-}" ]] && present=1
else
  # Fallback : extraction par motif robuste sur la sortie tabulaire.
  # Ligne identifier == MODEL exact ; on isole CONTEXT (entier), PARALLEL (entier)
  # et STATUS via motifs, sans dependre de la position exacte des colonnes.
  line="$(lms ps 2>/dev/null | grep -E "^${MODEL}[[:space:]]" | head -n1)"
  if [[ -n "$line" ]]; then
    present=1
    status="$(printf '%s' "$line" | grep -oiE '(GENERATING|PROCESSINGPROMPT|PROCESSING|IDLE|LOADING)' | head -n1 | tr '[:upper:]' '[:lower:]')"
    # CONTEXT et PARALLEL : les 2 derniers grands entiers avant DEVICE/TTL.
    # On collapse et on cible : ctx = contexte (>=256), par = parallel (petit).
    nums="$(printf '%s' "$line" | grep -oE '[0-9]+')"
    ctx="$(printf '%s\n' "$nums" | awk '$1>=256{print; exit}')"
    par="$(printf '%s\n' "$nums" | awk -v c="$ctx" '$1==c{f=1;next} f&&$1<=64{print;exit}')"
  fi
fi

# Normalisation status
status="$(printf '%s' "${status:-}" | tr '[:upper:]' '[:lower:]')"

if [[ "$present" == "1" ]]; then
  echo "[qwen-warm] etat detecte : ctx=${ctx:-?} parallel=${par:-?} status=${status:-?}"
  if [[ "$ctx" == "$WANT_CTX" && "$par" == "$WANT_PAR" ]]; then
    echo "[qwen-warm] deja au bon etat (ctx $WANT_CTX / parallel $WANT_PAR) -> rien a faire"
    exit 0
  fi
  # Anti-coupure : ne pas recharger si generation en cours (sauf FORCE_RELOAD).
  case "$status" in
    generating|processingprompt|processing)
      if [[ "$FORCE_RELOAD" != "1" ]]; then
        echo "[qwen-warm] /!\\ qwen en cours de generation (status=$status) -> reload REPORTE (utiliser FORCE_RELOAD=1 pour forcer)" >&2
        exit 0
      fi
      echo "[qwen-warm] status=$status mais FORCE_RELOAD=1 -> reload force"
      ;;
  esac
  echo "[qwen-warm] etat incorrect -> rechargement"
else
  echo "[qwen-warm] qwen non charge -> chargement"
fi

# Decharge d abord toute instance existante du modele pour eviter les doublons
# d identifier (qwen:2, qwen:3...), puis recharge une instance unique propre.
# Detection d identifier unifiee : on liste les identifiers dont modelKey/path == MODEL.
if [[ "$HAS_JSON" == "1" ]] && command -v python3 >/dev/null 2>&1; then
  ids="$(lms ps --json 2>/dev/null | MODEL="$MODEL" python3 -c '
import sys, os, json
m = os.environ["MODEL"]
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
for e in data if isinstance(data, list) else []:
    if e.get("modelKey") == m or e.get("path") == m or e.get("identifier","").split(":")[0] == m:
        print(e.get("identifier",""))
')"
else
  ids="$(lms ps 2>/dev/null | tr -s ' ' | awk -v m="$MODEL" '$2==m || $1==m || $1 ~ "^"m":" {print $1}')"
fi
for id in $ids; do
  [[ -z "$id" ]] && continue
  echo "[qwen-warm] unload instance existante: $id"
  lms unload "$id" >/dev/null 2>&1 || true
done
# PLUS de --gpu max : il reservait TOUTE la VRAM pour qwen, evincait les
# autres modeles ET empechait la garde plancher de recharger hermes juste
# apres (echec constate 2026-08-06 : « plancher absent -> ECHEC »). Le
# placement automatique laisse ~4 Go libres — qwen (5,6 Go) et hermes
# (4,1 Go) coexistent, c'est l'ordre multi-modele de Turbo.
lms load "$MODEL" -c "$WANT_CTX" --parallel "$WANT_PAR" --ttl "$TTL" -y
rc=$?
echo "[qwen-warm] lms load rc=$rc"
echo "=== etat final ==="
lms ps 2>/dev/null | awk -v m="$MODEL" -v e="$EMB_MODEL" 'NR==1 || $0 ~ m || $0 ~ e'
exit $rc
