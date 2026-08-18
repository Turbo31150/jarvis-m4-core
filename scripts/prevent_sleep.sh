#!/bin/bash
# Désactivation totale de toute mise en veille / mise en sommeil du système
echo "Désactivation du mode veille système..."
systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target 2>/dev/null || true
gsettings set org.gnome.desktop.session idle-delay 0 2>/dev/null || true
gsettings set org.gnome.desktop.screensaver lock-enabled false 2>/dev/null || true
echo "Mode production ininterrompue 24/7 activé !"
