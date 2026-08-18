#!/usr/bin/env bash
# Régénère ~/Bureau/JARVIS_RACCOURCIS_ET_WIDGETS.txt à partir de l'état système courant
set -euo pipefail
OUT="$HOME/Bureau/JARVIS_RACCOURCIS_ET_WIDGETS.txt"

python3 << 'PY' > "$OUT"
import subprocess, glob, os
def gset(path, key):
    r = subprocess.run(["gsettings","get",
        f"org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{path}", key],
        capture_output=True, text=True)
    return r.stdout.strip().strip("'")

print("╔══════════════════════════════════════════════════════════════════╗")
print("║          JARVIS — RACCOURCIS CLAVIER & WIDGETS — M1              ║")
print(f"║          Généré : {subprocess.check_output(['date','+%Y-%m-%d %H:%M']).decode().strip():<46} ║")
print("╚══════════════════════════════════════════════════════════════════╝\n")

print("━━━ RACCOURCIS CLAVIER GNOME (custom) ━━━\n")
print(f"{'Raccourci':<22}{'Nom':<32}Commande")
print("-"*100)
cks_raw = subprocess.check_output(["gsettings","get",
    "org.gnome.settings-daemon.plugins.media-keys","custom-keybindings"]).decode()
cks = [c.strip().strip("'") for c in cks_raw.strip("[]\n").split(",") if c.strip()]
for p in cks:
    n = gset(p, "name")
    b = gset(p, "binding").replace("<","[").replace(">","]+").rstrip("+")
    c = gset(p, "command")
    print(f"{b:<22}{n:<32}{c}")

print("\n\n━━━ RACCOURCIS GNOME NATIFS UTILES ━━━\n")
for k,d in [("Super","Vue d'ensemble Activités"),("Super+A","Toutes les applications"),
    ("Super+S","Recherche"),("Super+D","Afficher le bureau"),("Super+L","Verrouiller la session"),
    ("Super+H","Réduire la fenêtre"),("Super+Up","Agrandir la fenêtre"),
    ("Super+Left/Right","Snap fenêtre moitié écran"),("Super+PgUp/PgDn","Workspace prev/next"),
    ("Alt+Tab","Changer de fenêtre"),("Alt+F2","Lancer une commande"),
    ("Alt+F4","Fermer la fenêtre"),("Ctrl+Alt+T","Terminal"),
    ("PrtSc","Capture écran"),("Shift+PrtSc","Capture zone")]:
    print(f"{k:<22}{d}")

print("\n\n━━━ WIDGETS / SYSTRAY / AUTOSTART JARVIS ━━━\n")
print(f"{'Nom':<38}{'Statut':<10}Exec")
print("-"*100)
for f in sorted(glob.glob(os.path.expanduser("~/.config/autostart/*.desktop"))):
    name = os.path.basename(f)
    if not any(k in name.lower() for k in ["jarvis","whisper","ptt","voice","lmstudio","triple"]):
        continue
    exec_line = ""; enabled = "?"
    with open(f, errors="ignore") as fh:
        for ln in fh:
            if ln.startswith("Exec="): exec_line = ln[5:].strip()
            if "X-GNOME-Autostart-enabled" in ln:
                enabled = "ON" if "true" in ln.lower() else "OFF"
    print(f"{name:<38}{enabled:<10}{exec_line[:80]}")

print("\n\n━━━ SERVICES VOCAUX SYSTEMD (user) ━━━\n")
r = subprocess.run(["systemctl","--user","list-unit-files","--no-pager"], capture_output=True, text=True)
for ln in r.stdout.splitlines():
    if any(k in ln.lower() for k in ["jarvis-voice","jarvis-whisper","jarvis-vocal","jarvis-ptt"]):
        print(ln)

print("\n\n━━━ SCRIPTS VOIX/PTT DISPONIBLES ━━━\n")
for s in sorted(f for f in os.listdir("/home/pamerys/jarvis/scripts")
                if any(k in f.lower() for k in ["ptt","voice","whisper","vocal","hud","tts","stt"])):
    full = f"/home/pamerys/jarvis/scripts/{s}"
    print(f"  {s:<40} ({os.path.getsize(full)}o)")

print("\n\n━━━ MODES PTT (Alt+X) ━━━\n")
print("  Mode 'dictée'    → Whisper STT → Qwen nettoie → texte tapé au curseur (xdotool)")
print("  Mode 'assistant' → Whisper STT → Qwen répond → Piper TTS dans le casque")
mode_path = os.path.expanduser('~/.config/jarvis/ptt-mode')
mode = open(mode_path).read().strip() if os.path.exists(mode_path) else "(non défini)"
print(f"\n  Mode actif : {mode}")
print(f"  Bascule    : Alt+Shift+X  ou  clic-droit sur l'icône micro du systray")

print("\n\n━━━ CLUSTER LLM (référence) ━━━")
print("""
  M1  192.168.0.10:1234   LMStudio  — leader (qwen3.5-35b, claude-distill...)
  M2  127.0.0.1:18800   LMStudio  — reasoning
  M3  127.0.0.1:18800 Ollama    — actuellement DOWN
  M4  127.0.0.1:18800   LMStudio  — Windows integration
  M5  192.168.42.241      Ollama    — relay CPU (interface vocale)
  OL1 127.0.0.1:11434     Ollama    — local M1
""")

print("━━━ COMMANDES UTILES ━━━\n")
print("  claudelm                                # Claude Code branché LMStudio (gratuit)")
print("  bash ~/jarvis/scripts/lm-ask.sh         # 1-shot LLM local")
print("  bash ~/jarvis/scripts/gemini-ask.sh     # Gemini 2.5 Pro (Google One)")
print("  ~/jarvis/scripts/ptt-toggle.sh          # PTT direct")
print("  ~/jarvis/scripts/ptt-widget.sh          # Relancer systray PTT")
print("  ~/jarvis/scripts/regen-cheatsheet.sh    # Régénérer cette fiche")
PY

echo "✓ Fiche régénérée : $OUT ($(wc -c < "$OUT") octets)"
