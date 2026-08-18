#!/bin/bash
# simul-boot.sh — JARVIS M1, 2026-08-06
#
# Simule la chaine de demarrage BIOS -> GNOME sans redemarrer, en verifiant chaque
# maillon separement, puis en superposant les verdicts avec une ponderation par
# criticite. Objectif : savoir AVANT de redemarrer si la machine repartira seule,
# et sur quel maillon elle trebucherait.
#
# Ponderation : chaque maillon vaut un poids selon ce que couterait sa rupture.
#   10 = la machine ne demarre pas du tout (UEFI, ESP, racine)
#    7 = la machine demarre mais s'arrete avant l'interface
#    4 = l'interface arrive mais degradee
#    2 = confort
# Le score final est la somme des poids valides / somme des poids totaux.
#
# LECTURE SEULE — ce script ne modifie rien, ne monte rien, ne redemarre rien.

set -uo pipefail
DISQUE_PRINCIPAL="24375P800775"   # SN du disque qui doit porter le demarrage
total=0; acquis=0
declare -a ECHECS=()

verdict() {  # verdict <poids> <libelle> <0=ok|1=ko> [detail]
    local poids="$1" libelle="$2" ok="$3" detail="${4:-}"
    total=$((total + poids))
    if [ "$ok" -eq 0 ]; then
        acquis=$((acquis + poids))
        printf "  \033[32m✓\033[0m [%2d] %-46s %s\n" "$poids" "$libelle" "$detail"
    else
        ECHECS+=("[$poids] $libelle — $detail")
        printf "  \033[31m✗\033[0m [%2d] %-46s %s\n" "$poids" "$libelle" "$detail"
    fi
}

echo "═══════════════════════════════════════════════════════════════════"
echo "  SIMULATION DE DEMARRAGE — BIOS -> GNOME     $(date '+%F %H:%M:%S')"
echo "═══════════════════════════════════════════════════════════════════"

# ── ETAGE 1 : firmware UEFI ────────────────────────────────────────────────
echo; echo "── Etage 1 : firmware UEFI ──"

premier=$(sudo efibootmgr 2>/dev/null | awk -F': ' '/^BootOrder/{split($2,a,","); print a[1]}')
entree=$(sudo efibootmgr -v 2>/dev/null | grep -E "^Boot${premier}")
partuuid_esp=$(findmnt -n -o SOURCE /boot/efi 2>/dev/null | xargs -r lsblk -no PARTUUID 2>/dev/null)

[ -n "$premier" ] && verdict 10 "un ordre de demarrage est defini" 0 "premier = Boot$premier" \
                  || verdict 10 "un ordre de demarrage est defini" 1 "BootOrder vide"

if echo "$entree" | grep -qi "$partuuid_esp"; then
    verdict 10 "la 1re entree vise l'ESP du disque montee" 0 "$(echo "$entree" | sed 's/\t.*//')"
else
    verdict 10 "la 1re entree vise l'ESP du disque montee" 1 "vise un AUTRE disque -> selection manuelle"
fi

echo "$entree" | grep -q '^Boot[0-9A-F]*\*' \
    && verdict 7 "cette entree est active (marquee *)" 0 "" \
    || verdict 7 "cette entree est active (marquee *)" 1 "entree inactive, ignoree par l'UEFI"

# ── ETAGE 2 : le bon disque ────────────────────────────────────────────────
echo; echo "── Etage 2 : le disque principal ──"

disque_racine=$(findmnt -n -o SOURCE / | sed 's/[0-9]*$//')
sn_racine=$(lsblk -dn -o SERIAL "$disque_racine" 2>/dev/null | tr -d ' ')

[ "$sn_racine" = "$DISQUE_PRINCIPAL" ] \
    && verdict 10 "la racine est sur le disque attendu" 0 "SN $sn_racine" \
    || verdict 10 "la racine est sur le disque attendu" 1 "SN $sn_racine, attendu $DISQUE_PRINCIPAL"

# sudo obligatoire : /boot/efi/EFI/ubuntu est en drwx------ root. Un test « [ -e ] »
# lance par turbo recoit « permission refusee » et conclut a tort que le fichier
# manque — faux negatif constate le 2026-08-06 sur cette meme simulation.
for f in shimx64.efi grubx64.efi; do
    if sudo test -e "/boot/efi/EFI/ubuntu/$f"; then
        verdict 10 "l'ESP contient $f" 0 "$(sudo stat -c '%s octets' "/boot/efi/EFI/ubuntu/$f")"
    else
        verdict 10 "l'ESP contient $f" 1 "ABSENT — demarrage impossible"
    fi
done

# ── ETAGE 3 : GRUB ─────────────────────────────────────────────────────────
echo; echo "── Etage 3 : GRUB ──"

uuid_reel=$(findmnt -n -o UUID /)
uuid_grub=$(sudo grep -m1 -oE 'root=UUID=[a-f0-9-]+' /boot/grub/grub.cfg 2>/dev/null | cut -d= -f3)

[ -n "$uuid_grub" ] && [ "$uuid_grub" = "$uuid_reel" ] \
    && verdict 10 "grub.cfg vise la racine reelle" 0 "$uuid_reel" \
    || verdict 10 "grub.cfg vise la racine reelle" 1 "grub=$uuid_grub reel=$uuid_reel"

noyau=$(sudo grep -m1 -oE '/boot/vmlinuz-[0-9.]+-[0-9]+-generic' /boot/grub/grub.cfg 2>/dev/null)
[ -n "$noyau" ] && [ -e "$noyau" ] \
    && verdict 10 "le noyau par defaut existe" 0 "$(basename "$noyau")" \
    || verdict 10 "le noyau par defaut existe" 1 "$noyau introuvable"

initrd="${noyau/vmlinuz/initrd.img}"
[ -e "$initrd" ] \
    && verdict 10 "l'initramfs correspondant existe" 0 "$(du -h "$initrd" 2>/dev/null | cut -f1)" \
    || verdict 10 "l'initramfs correspondant existe" 1 "ABSENT"

grep -q 'GRUB_TIMEOUT_STYLE=hidden' /etc/default/grub 2>/dev/null \
    && verdict 2 "le menu GRUB est masque (demarrage direct)" 0 "" \
    || verdict 2 "le menu GRUB est masque (demarrage direct)" 1 "menu affiche"

grep -q 'GRUB_RECORDFAIL_TIMEOUT' /etc/default/grub 2>/dev/null \
    && verdict 7 "pas de menu bloquant apres arret brutal" 0 "recordfail borne" \
    || verdict 7 "pas de menu bloquant apres arret brutal" 1 "30 s d'attente au prochain demarrage rate"

# ── ETAGE 4 : noyau et materiel ────────────────────────────────────────────
echo; echo "── Etage 4 : noyau et materiel ──"

sudo grep -q 'iommu=pt' /boot/grub/grub.cfg 2>/dev/null \
    && verdict 7 "iommu=pt arme (anti IO_PAGE_FAULT)" 0 "" \
    || verdict 7 "iommu=pt arme (anti IO_PAGE_FAULT)" 1 "le demarrage peut avorter sur un GPU"

fbdev=$(sudo cat /sys/module/nvidia_drm/parameters/fbdev 2>/dev/null)
grep -qs 'fbdev=0' /etc/modprobe.d/*.conf \
    && verdict 4 "nvidia_drm fbdev=0 (anti course VT)" 0 "actif au prochain demarrage (courant: $fbdev)" \
    || verdict 4 "nvidia_drm fbdev=0 (anti course VT)" 1 "X peut rater son 1er essai"

# ── ETAGE 5 : montages ─────────────────────────────────────────────────────
echo; echo "── Etage 5 : montages fstab ──"

manquants=0; details=""
while read -r src tgt _; do
    case "$src" in
        UUID=*) id="${src#UUID=}"
                blkid -U "$id" >/dev/null 2>&1 || blkid | grep -q "\"$id\"" || { manquants=$((manquants+1)); details="$details $tgt"; } ;;
        /dev/*) [ -e "$src" ] || { manquants=$((manquants+1)); details="$details $tgt"; } ;;
    esac
done < <(grep -E '^(UUID=|/dev/)' /etc/fstab | awk '{print $1, $2}')

[ "$manquants" -eq 0 ] \
    && verdict 7 "toutes les entrees fstab resolvent" 0 "" \
    || verdict 7 "toutes les entrees fstab resolvent" 1 "manquant:$details"

grep -qE 'nofail' /etc/fstab \
    && verdict 7 "les montages secondaires sont en nofail" 0 "un disque absent ne bloque pas" \
    || verdict 7 "les montages secondaires sont en nofail" 1 "un disque absent bloquerait 90 s"

# ── ETAGE 6 : session graphique ────────────────────────────────────────────
echo; echo "── Etage 6 : GNOME ──"

[ "$(systemctl is-enabled gdm.service 2>/dev/null)" = "enabled" ] \
    && verdict 10 "gdm demarre automatiquement" 0 "" \
    || verdict 10 "gdm demarre automatiquement" 1 "pas d'interface graphique au demarrage"

grep -q '^AutomaticLoginEnable=True' /etc/gdm3/custom.conf 2>/dev/null \
    && verdict 4 "connexion automatique active" 0 "utilisateur $(grep -m1 '^AutomaticLogin=' /etc/gdm3/custom.conf 2>/dev/null | cut -d= -f2)" \
    || verdict 4 "connexion automatique active" 1 "mot de passe demande"

[ "$(systemctl get-default 2>/dev/null)" = "graphical.target" ] \
    && verdict 10 "la cible par defaut est graphique" 0 "" \
    || verdict 10 "la cible par defaut est graphique" 1 "$(systemctl get-default 2>/dev/null)"

# ── ETAGE 7 : ce qui bloque ici et maintenant ──────────────────────────────
echo; echo "── Etage 7 : verrous du moment ──"

pgrep e2fsck >/dev/null \
    && verdict 10 "aucun fsck en cours" 1 "e2fsck actif depuis $(ps -o etime= -p "$(pgrep e2fsck | head -1)" | tr -d ' ') — NE PAS REDEMARRER" \
    || verdict 10 "aucun fsck en cours" 0 ""

nb_failed=$(systemctl --failed --no-pager --plain 2>/dev/null | grep -c '\.service')
[ "$nb_failed" -eq 0 ] \
    && verdict 4 "aucun service systeme en echec" 0 "" \
    || verdict 4 "aucun service systeme en echec" 1 "$nb_failed en echec"

# ── SYNTHESE PONDEREE ──────────────────────────────────────────────────────
echo
echo "═══════════════════════════════════════════════════════════════════"
score=$(awk -v a="$acquis" -v t="$total" 'BEGIN{printf "%.1f", (t>0 ? a*100/t : 0)}')
printf "  SCORE PONDERE : %s / %s  =  %s%%\n" "$acquis" "$total" "$score"

if [ ${#ECHECS[@]} -eq 0 ]; then
    echo "  VERDICT : la machine doit repartir seule du BIOS jusqu'a GNOME."
else
    echo "  MAILLONS EN DEFAUT (du plus critique au moins critique) :"
    printf '%s\n' "${ECHECS[@]}" | sort -rn -t'[' -k2 | sed 's/^/    /'
fi
echo "═══════════════════════════════════════════════════════════════════"
exit 0
