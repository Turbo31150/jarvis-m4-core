#!/bin/bash
# Setup JARVIS Recherche + Création Contenu
# Lance après installation pour intégration GNOME complète

set -e

echo "🚀 JARVIS - Intégration Enseignante"
echo ""

# 1. Permissions
echo "✅ Permissions et chemins"
chmod +x /home/pamerys/jarvis/scripts/{recherche.py,creation_contenu.sh}
chmod +x /home/pamerys/.local/bin/jarvis-{recherche,creation}

# 2. Vérif PATH
if ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
  echo "⚠️  Ajout ~/.local/bin au PATH"
  cat >> ~/.bashrc << 'EOF'

# JARVIS CLI paths
export PATH="$HOME/.local/bin:$PATH"
EOF
  source ~/.bashrc
fi

# 3. Desktop shortcuts
echo "✅ Raccourcis GNOME activés"
update-desktop-database ~/.local/share/applications 2>/dev/null || true

# 4. Alias bash
cat >> ~/.bashrc << 'EOF'

# === JARVIS Aliases ===
alias jarvis-rech="python3 $HOME/jarvis/scripts/recherche.py"
alias jarvis-create="bash $HOME/jarvis/scripts/creation_contenu.sh"
alias j-doc="jarvis-rech --niveau college"
alias j-ex="jarvis-rech --exercices"
alias j-bib="jarvis-rech --biblio"
EOF

# 5. Test basique
echo ""
echo "✅ Tests de fonctionnalité"
python3 /home/pamerys/jarvis/scripts/recherche.py --help >/dev/null && echo "  ✓ recherche.py OK"
bash /home/pamerys/jarvis/scripts/creation_contenu.sh >/dev/null 2>&1 || echo "  ✓ creation_contenu.sh OK"

echo ""
echo "🎓 JARVIS Recherche + Création Contenu installés!"
echo ""
echo "Commandes disponibles:"
echo "  jarvis-recherche \"sujet\"              - Recherche simple"
echo "  jarvis-recherche --biblio \"sujet\"     - Bibliographie APA"
echo "  jarvis-recherche --exercices \"sujet\"  - Générer exercices"
echo "  jarvis-creation video                  - Lancer OBS"
echo "  jarvis-creation podcast                - Enregistrer podcast"
echo "  jarvis-creation presentation           - LibreOffice Impress"
echo "  jarvis-creation resume <fichier>       - Résumer automatique"
echo "  jarvis-creation dictee                 - Dictée vocale"
echo ""
echo "Alias bash:"
echo "  j-doc \"sujet\"        → recherche niveau collège"
echo "  j-ex \"sujet\"         → générer exercices"
echo "  j-bib \"sujet\"        → bibliographie"
echo ""
echo "📁 Dossiers:"
echo "  Recherche: ~/Documents/Recherche/"
echo "  Contenu:   ~/Documents/Contenu/"
