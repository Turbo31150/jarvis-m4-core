#!/usr/bin/env bash
# perf-governor.sh — Gouverneur de performance adaptatif M4 (0-token)
#
# Mesure l'état système, l'historise en SQLite, apprend ses propres seuils
# (percentiles sur l'historique) et déclenche les outils EXISTANTS au bon
# moment. Aucune inférence : ni Ollama, ni cluster, ni API facturée.
#
# Compose, ne duplique pas :
#   - ram-relief.sh        (série biblio)     -> pression mémoire / zram
#   - jarvis-zombie-reaper (service actif)    -> zombies (SIGCHLD au parent)
#   - m4-thermal-governor  (service actif)    -> thermique
#   - gpu-guardian         (service actif)    -> VRAM
#
# Usage:
#   perf-governor.sh observe        # mesure + historise, n'agit jamais (défaut)
#   perf-governor.sh act            # mesure + agit si un seuil appris est franchi
#   perf-governor.sh seuils         # affiche les seuils appris et leur assise
#   perf-governor.sh histo [N]      # N derniers relevés
set -euo pipefail

# Locale numérique C obligatoire : en fr_FR, awk écrit "53,0" et la virgule
# décimale est alors lue par SQLite comme un séparateur de valeurs.
export LC_ALL=C LC_NUMERIC=C

DB="${PERF_GOV_DB:-/home/pamerys/jarvis/data/perf_governor.db}"
RAM_RELIEF="/home/pamerys/labo/bibliotheque/series/ram-relief.sh"
MIN_ECHANTILLONS=20        # sous ce seuil, on utilise les valeurs de repli
COOLDOWN_S=300             # pas deux actions du même type à moins de 5 min

# Repli utilisé tant que l'historique est trop mince pour être crédible.
declare -A REPLI=( [zram_pct]=90 [ram_pct]=85 [swap_pct]=75 [load1]=8 [temp]=88 [zombies]=15 )

mkdir -p "$(dirname "$DB")"

init_db() {
    sqlite3 "$DB" <<'SQL'
CREATE TABLE IF NOT EXISTS releves (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ts        INTEGER NOT NULL,
    ram_pct   REAL, zram_pct REAL, swap_pct REAL,
    load1     REAL, temp     REAL,
    zombies   INTEGER, dstate INTEGER
);
CREATE TABLE IF NOT EXISTS actions (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    ts      INTEGER NOT NULL,
    type    TEXT NOT NULL,
    motif   TEXT,
    outil   TEXT,
    resultat TEXT
);
CREATE INDEX IF NOT EXISTS idx_releves_ts ON releves(ts);
CREATE INDEX IF NOT EXISTS idx_actions_ts ON actions(ts, type);
SQL
}

# --- Mesure : pur /proc et sysfs, aucune dépendance lourde -----------------
mesurer() {
    local mem_total mem_dispo ram_pct=0
    mem_total=$(awk '/^MemTotal:/{print $2}' /proc/meminfo)
    mem_dispo=$(awk '/^MemAvailable:/{print $2}' /proc/meminfo)
    [ "$mem_total" -gt 0 ] && ram_pct=$(awk "BEGIN{printf \"%.1f\", (1-$mem_dispo/$mem_total)*100}")

    local zram_pct=0 zt zu
    if [ -e /sys/block/zram0/disksize ]; then
        zt=$(cat /sys/block/zram0/disksize 2>/dev/null || echo 0)
        zu=$(awk '{print $3}' /sys/block/zram0/mm_stat 2>/dev/null || echo 0)
        [ "${zt:-0}" -gt 0 ] && zram_pct=$(awk "BEGIN{printf \"%.1f\", $zu/$zt*100}")
    fi

    local sw_total sw_libre swap_pct=0
    sw_total=$(awk '/^SwapTotal:/{print $2}' /proc/meminfo)
    sw_libre=$(awk '/^SwapFree:/{print $2}' /proc/meminfo)
    [ "$sw_total" -gt 0 ] && swap_pct=$(awk "BEGIN{printf \"%.1f\", (1-$sw_libre/$sw_total)*100}")

    local load1; load1=$(awk '{print $1}' /proc/loadavg)

    local temp=0 raw
    for z in /sys/class/thermal/thermal_zone*/temp; do
        [ -r "$z" ] || continue
        raw=$(cat "$z" 2>/dev/null || echo 0)
        [ "$raw" -gt "${temp:-0}" ] 2>/dev/null && temp=$raw
    done
    temp=$(awk "BEGIN{printf \"%.1f\", $temp/1000}")

    local zombies dstate
    zombies=$(ps -eo stat 2>/dev/null | grep -c '^Z' || true)
    dstate=$(ps -eo stat 2>/dev/null | grep -c '^D' || true)

    echo "$ram_pct|$zram_pct|$swap_pct|$load1|$temp|${zombies:-0}|${dstate:-0}"
}

enregistrer() {
    IFS='|' read -r ram zram swap load temp zomb dst <<<"$1"
    sqlite3 "$DB" "INSERT INTO releves(ts,ram_pct,zram_pct,swap_pct,load1,temp,zombies,dstate)
                   VALUES(strftime('%s','now'),$ram,$zram,$swap,$load,$temp,$zomb,$dst);"
}

# --- Modelage : le seuil est le p90 observé, borné par le repli ------------
# Sous MIN_ECHANTILLONS relevés, l'historique ne dit rien de fiable : on garde
# le repli. Au-delà, le seuil s'ajuste à la machine telle qu'elle vit vraiment.
seuil_appris() {
    local col="$1" repli="${REPLI[$1]}" n p90
    n=$(sqlite3 "$DB" "SELECT COUNT(*) FROM releves;")
    if [ "${n:-0}" -lt "$MIN_ECHANTILLONS" ]; then
        echo "$repli|repli|$n"; return
    fi
    p90=$(sqlite3 "$DB" "SELECT $col FROM releves WHERE $col IS NOT NULL
                         ORDER BY $col LIMIT 1
                         OFFSET (SELECT CAST(COUNT(*)*0.9 AS INT) FROM releves WHERE $col IS NOT NULL);")
    [ -z "${p90:-}" ] && { echo "$repli|repli|$n"; return; }
    # Jamais sous le repli : l'adaptation peut durcir, pas relâcher la garde.
    local final; final=$(awk "BEGIN{print ($p90>$repli)?$p90:$repli}")
    echo "$final|appris|$n"
}

en_cooldown() {
    local type="$1" dernier
    dernier=$(sqlite3 "$DB" "SELECT COALESCE(MAX(ts),0) FROM actions WHERE type='$type';")
    [ $(( $(date +%s) - ${dernier:-0} )) -lt "$COOLDOWN_S" ]
}

journaliser() {
    sqlite3 "$DB" "INSERT INTO actions(ts,type,motif,outil,resultat)
                   VALUES(strftime('%s','now'),'$1','$2','$3','$4');"
}

# --- Décision et action : on délègue aux outils existants ------------------
gouverner() {
    local agir="$1" mesures="$2"
    IFS='|' read -r ram zram swap load temp zomb dst <<<"$mesures"
    local s_zram s_ram agi=0
    s_zram=$(seuil_appris zram_pct | cut -d'|' -f1)
    s_ram=$(seuil_appris ram_pct  | cut -d'|' -f1)

    # Pression mémoire : c'est zram saturé qui provoque le thrash (load élevé
    # sans CPU occupé), pas la RAM seule. On teste les deux.
    if awk "BEGIN{exit !($zram>=$s_zram || $ram>=$s_ram)}"; then
        local motif="zram=${zram}% (seuil ${s_zram}%) ram=${ram}% (seuil ${s_ram}%)"
        if [ "$agir" != "1" ]; then
            echo "  ⚠ PRESSION MEMOIRE — $motif  [observe: aucune action]"
        elif en_cooldown memoire; then
            echo "  ⏸ pression mémoire mais cooldown actif (<${COOLDOWN_S}s)"
        elif [ -x "$RAM_RELIEF" ]; then
            echo "  ▶ délégation à ram-relief.sh — $motif"
            if timeout 120 bash "$RAM_RELIEF" >/dev/null 2>&1; then
                journaliser memoire "$motif" ram-relief.sh OK;  echo "    ✓ ram-relief OK"
            else
                journaliser memoire "$motif" ram-relief.sh ECHEC; echo "    ✗ ram-relief a échoué"
            fi
            agi=1
        else
            echo "  ✗ ram-relief.sh introuvable ou non exécutable : $RAM_RELIEF"
            journaliser memoire "$motif" ram-relief.sh ABSENT
        fi
    fi

    # Zombies : le reaper tourne déjà. On ne le double qu'au-delà du seuil,
    # signe que le parent ignore SIGCHLD.
    local s_zomb; s_zomb=$(seuil_appris zombies | cut -d'|' -f1)
    if awk "BEGIN{exit !($zomb>=$s_zomb)}"; then
        if [ "$agir" != "1" ]; then
            echo "  ⚠ ZOMBIES=$zomb (seuil $s_zomb) [observe]"
        elif en_cooldown zombies; then
            echo "  ⏸ zombies mais cooldown actif"
        else
            local parents; parents=$(ps -eo stat,ppid | awk '$1 ~ /^Z/ {print $2}' | sort -u | tr '\n' ' ')
            for p in $parents; do [ "$p" -gt 1 ] 2>/dev/null && kill -CHLD "$p" 2>/dev/null || true; done
            journaliser zombies "zombies=$zomb parents=$parents" "kill -CHLD" OK
            echo "  ▶ SIGCHLD envoyé aux parents : $parents"
            agi=1
        fi
    fi

    # Thermique et VRAM ont déjà leur régulateur dédié : on constate, on n'agit pas.
    local s_temp; s_temp=$(seuil_appris temp | cut -d'|' -f1)
    awk "BEGIN{exit !($temp>=$s_temp)}" && \
        echo "  ⚠ temp=${temp}°C (seuil ${s_temp}°C) — m4-thermal-governor a la main"

    [ "$agi" = "0" ] && [ "$agir" = "1" ] && echo "  ✓ rien à faire, système dans ses clous"
    return 0
}

afficher() {
    IFS='|' read -r ram zram swap load temp zomb dst <<<"$1"
    printf "  RAM %5s%%  zram %5s%%  swap %5s%%  load %5s  temp %5s°C  zombies %s  D %s\n" \
        "$ram" "$zram" "$swap" "$load" "$temp" "$zomb" "$dst"
}

init_db
case "${1:-observe}" in
    observe|act)
        m=$(mesurer); enregistrer "$m"
        echo "── perf-governor · $(date '+%F %T') · mode ${1:-observe}"
        afficher "$m"
        gouverner "$([ "${1:-observe}" = act ] && echo 1 || echo 0)" "$m"
        ;;
    seuils)
        echo "── Seuils (p90 de l'historique, jamais sous le repli)"
        for c in zram_pct ram_pct swap_pct load1 temp zombies; do
            IFS='|' read -r v src n <<<"$(seuil_appris "$c")"
            printf "  %-9s %8s   [%s, %s relevés]\n" "$c" "$v" "$src" "$n"
        done
        echo "── 5 dernières actions"
        sqlite3 -column "$DB" "SELECT datetime(ts,'unixepoch','localtime') AS quand, type, outil, resultat
                               FROM actions ORDER BY ts DESC LIMIT 5;" 2>/dev/null || echo "  (aucune)"
        ;;
    histo)
        sqlite3 -header -column "$DB" "SELECT datetime(ts,'unixepoch','localtime') AS quand,
               ram_pct, zram_pct, swap_pct, load1, temp, zombies
               FROM releves ORDER BY ts DESC LIMIT ${2:-15};"
        ;;
    *) echo "usage: $0 {observe|act|seuils|histo [N]}"; exit 2;;
esac
