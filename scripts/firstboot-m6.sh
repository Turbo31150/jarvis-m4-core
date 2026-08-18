#!/bin/bash
# Run-once setup pour M6 (premier login GNOME)
LOG=/home/turbo/.jarvis-m6-firstboot.log
MARKER=/home/turbo/.jarvis-m6-firstboot.done
[ -f "$MARKER" ] && exit 0
exec >>"$LOG" 2>&1
echo "[$(date)] FIRSTBOOT M6 START"

# 1. Importer keybindings voice/jarvis
if [ -f /home/turbo/.jarvis-m6-firstboot.dconf ]; then
  dconf load /org/gnome/settings-daemon/plugins/media-keys/ < /home/turbo/.jarvis-m6-firstboot.dconf
  echo "  dconf keybindings importés"
fi

# 2. Installer deps voice si absent
if ! python3 -c "import whisper" 2>/dev/null; then
  notify-send "JARVIS M6" "Installation Whisper en cours..." -i audio-input-microphone
  pip3 install --user --break-system-packages openai-whisper sounddevice pyperclip 2>&1 | tail -3
fi

# 3. Activer services voice (utilisateur)
systemctl --user daemon-reload
systemctl --user enable --now jarvis-voice 2>/dev/null || true

# 4. Démarrer widget voice au login
mkdir -p /home/pamerys/.config/autostart
cat > /home/turbo/.config/autostart/jarvis-voice-widget.desktop <<EOD
[Desktop Entry]
Type=Application
Name=JARVIS Voice Widget
Exec=/home/pamerys/jarvis/scripts/ptt-widget.sh
X-GNOME-Autostart-enabled=true
NoDisplay=false
EOD

# 5. Notify done
notify-send "JARVIS M6" "Configuration premier démarrage terminée. Alt+X = Push-to-Talk." -i audio-input-microphone
touch "$MARKER"
echo "[$(date)] FIRSTBOOT M6 DONE"

# 6. Personnalisation GNOME (thèmes M5)
for section in desktop shell terminal; do
  F="/home/turbo/.jarvis-m6-firstboot.${section}.dconf"
  if [ -f "$F" ]; then
    dconf load "/org/gnome/${section}/" < "$F" 2>/dev/null && echo "  dconf $section OK"
  fi
done

# 7. Hostname runtime
sudo hostnamectl set-hostname m6 2>/dev/null || true

# 8. Identité machine
cat > /home/turbo/.jarvis-machine.env <<EOM
JARVIS_NODE=M6
JARVIS_ROLE=portable
JARVIS_HAS_GPU=false
JARVIS_LLM_PRIMARY=http://192.168.1.85:1234
JARVIS_LLM_FALLBACK=http://192.168.1.26:1234
EOM

# 9. Fond d'écran JARVIS (si présent)
if [ -f /home/turbo/jarvis/assets/wallpaper-m6.png ]; then
  gsettings set org.gnome.desktop.background picture-uri "file:///home/turbo/jarvis/assets/wallpaper-m6.png"
fi

# 10. Notification finale
notify-send "JARVIS M6 PRÊT" "Bureau personnalisé, voice widget actif (Alt+X)" -i emblem-default
