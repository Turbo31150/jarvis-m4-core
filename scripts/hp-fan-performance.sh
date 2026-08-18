#!/bin/bash
# ==============================================================================
# Script de Performance & Régulation Thermique Active (HP Laptop M3)
# Force le mode performance CPU et ajuste les ventilateurs en continu :
# - Charge légère : Mode auto / vitesse basse
# - Charge moyenne (travail) : Ventilateur à 80%
# - Charge lourde / Pic massif (temp > 72°C ou CPU > 75%) : Ventilateur à 100%
# ==============================================================================

set -euo pipefail

# ── GARDE-FOU AJOUTE LE 2026-08-18 ────────────────────────────────────────────
# Ce script cible un chassis HP (M3). Il a ete lance par erreur sur M4, qui est un
# ASUS, et y a fait des degats durables :
#   - il force le gouverneur 'performance' sur tous les coeurs ;
#   - il prend le controle manuel des ventilateurs via "${PWM_CONTROL}_enable",
#     alors que PWM_CONTROL vaut ici 'pwm1_enable' alui-meme : le pilote ASUS
#     n'expose AUCUN fichier 'pwm1'/'pwm2', seulement les '_enable'. Le script
#     ecrivait donc 255/204/100 dans un fichier de MODE, et visait un
#     'pwm1_enable_enable' inexistant.
# Resultat constate : ventilateurs a 0 RPM, 95-97 °C sous charge, 23 528 bridages
# thermiques. Sur ASUS le seul levier reel est /sys/firmware/acpi/platform_profile
# ('balanced' => 0 RPM, 'performance' => ~3100 RPM) — voir le service
# m4-ventilateurs-max.service.
case "$(cat /sys/devices/virtual/dmi/id/sys_vendor 2>/dev/null)" in
  *HP*|*Hewlett*) : ;;
  *) echo "⛔ chassis non-HP ($(cat /sys/devices/virtual/dmi/id/sys_vendor 2>/dev/null))." >&2
     echo "   Sur ASUS, utiliser platform_profile / m4-ventilateurs-max.service." >&2
     exit 1 ;;
esac

echo "=== Initialisation du mode Performance HP (M3) ==="

# 1. Forcer le CPU en mode Performance maximale
echo "Configuration des cœurs CPU en mode Performance..."
if command -v cpupower &>/dev/null; then
    sudo cpupower frequency-set -g performance
else
    for gov in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
        if [ -f "$gov" ]; then
            echo "performance" | sudo tee "$gov" >/dev/null
        fi
    done
fi

# 2. Recherche des interfaces de contrôle de ventilateur (pwm)
PWM_CONTROL=$(find /sys/class/hwmon/hwmon*/ -name "pwm*" 2>/dev/null | head -n 1)

if [ -z "${PWM_CONTROL}" ] || [ ! -f "${PWM_CONTROL}_enable" ]; then
    echo "L'interface PWM directe du kernel est absente ou verrouillée par le BIOS HP."
    echo "Pour bypasser le contrôle EC d'entreprise HP lors de pics massifs, installez NBFC :"
    echo "  1. Installez nbfc-linux"
    echo "  2. nbfc config -a \"[Votre modèle HP]\""
    echo "  3. Créez une règle ou lancez : nbfc set -s 100 lors des charges."
    exit 0
fi

echo "Interface PWM détectée : ${PWM_CONTROL}"

# Désactiver le contrôle automatique du BIOS sur cette interface PWM (mode manuel = 1)
echo 1 | sudo tee "${PWM_CONTROL}_enable" >/dev/null

# Fonction pour obtenir la température maximale actuelle du CPU (en °C)
get_cpu_temp() {
    local temp_raw=0
    for temp_file in /sys/class/thermal/thermal_zone*/temp /sys/class/hwmon/hwmon*/temp*_input; do
        if [ -f "$temp_file" ]; then
            local val
            val=$(cat "$temp_file")
            if [ "$val" -gt "$temp_raw" ]; then
                temp_raw="$val"
            fi
        fi
    done
    echo $((temp_raw / 1000))
}

# Fonction pour obtenir l'utilisation CPU globale (pourcentage)
get_cpu_usage() {
    # Lit /proc/stat sur un intervalle de 1 seconde
    local cpu_stat_1
    cpu_stat_1=$(grep 'cpu ' /proc/stat)
    sleep 1
    local cpu_stat_2
    cpu_stat_2=$(grep 'cpu ' /proc/stat)

    local prev_idle prev_total idle total diff_idle diff_total usage
    prev_idle=$(echo "$cpu_stat_1" | awk '{print $5+$6}')
    prev_total=$(echo "$cpu_stat_1" | awk '{print $2+$3+$4+$5+$6+$7+$8}')
    idle=$(echo "$cpu_stat_2" | awk '{print $5+$6}')
    total=$(echo "$cpu_stat_2" | awk '{print $2+$3+$4+$5+$6+$7+$8}')

    diff_idle=$((idle - prev_idle))
    diff_total=$((total - prev_total))
    
    if [ "$diff_total" -eq 0 ]; then
        echo 0
    else
        usage=$((100 * (diff_total - diff_idle) / diff_total))
        echo "$usage"
    fi
}

echo "Démarrage de la boucle de surveillance active (Ctrl+C pour stopper)..."
while true; do
    TEMP=$(get_cpu_temp)
    CPU=$(get_cpu_usage)
    
    # 100% de vitesse (valeur PWM 255) lors de pics massifs :
    # Si la température dépasse 72°C OU si l'utilisation CPU dépasse 75%
    if [ "$TEMP" -gt 72 ] || [ "$CPU" -gt 75 ]; then
        echo "⚠️  [Pic Massif Détecté] Temp: ${TEMP}°C, CPU: ${CPU}%. Forçage ventilateur à 100%."
        echo 255 | sudo tee "${PWM_CONTROL}" >/dev/null
    
    # 80% de vitesse (valeur PWM 204) en charge de travail moyenne :
    # Si la température dépasse 55°C OU si l'utilisation CPU dépasse 20%
    elif [ "$TEMP" -gt 55 ] || [ "$CPU" -gt 20 ]; then
        echo "⚡ [Charge de Travail] Temp: ${TEMP}°C, CPU: ${CPU}%. Régulation ventilateur à 80%."
        echo 204 | sudo tee "${PWM_CONTROL}" >/dev/null
    
    # Mode silencieux standard (valeur PWM 100, soit ~39%) si le système est calme
    else
        echo "💤 [Mode Calme] Temp: ${TEMP}°C, CPU: ${CPU}%. Ventilateur ralenti à 39%."
        echo 100 | sudo tee "${PWM_CONTROL}" >/dev/null
    fi
    
    sleep 3
done
