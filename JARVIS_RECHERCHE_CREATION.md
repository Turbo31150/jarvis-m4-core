# JARVIS Recherche & Création Contenu

Système pédagogique d'IA pour enseignants. Intégration locale Ubuntu 24.04 avec backend M2 (qwen3.5-9b).

## 📋 Composants

| Fichier | Rôle | Exécutable |
|---------|------|-----------|
| `recherche.py` | Agent de recherche pédagogique | ✅ Python3 |
| `creation_contenu.sh` | Outil multimédia (vidéo/podcast/présentation) | ✅ Bash |
| `jarvis-integration.sh` | Setup GNOME + aliases | ✅ Bash |
| `.local/bin/jarvis-{recherche,creation}` | Wrappers CLI | ✅ Bash |
| `.local/share/applications/*.desktop` | Raccourcis GNOME | ✅ Desktop |

## 🚀 Installation

```bash
bash ~/jarvis/scripts/jarvis-integration.sh
source ~/.bashrc
```

## 📖 Recherche Pédagogique

### Recherche simple
```bash
jarvis-recherche "photosynthèse"
jarvis-recherche "théorème de Thalès" --niveau college
```

**Niveaux:** primaire, college, lycee, universite

**Format retourné:**
- Définition courte
- Concept développé
- Exemples concrets (2-3)
- Liens avec autres sujets
- Astuce mnémotechnique

### Bibliographie APA
```bash
jarvis-recherche --biblio "révolution française"
```
Génère 5-8 sources formatées APA 7e édition (livres, articles, sites fiables).

### Exercices générés
```bash
jarvis-recherche --exercices "sujet" --nb 8
jarvis-recherche --exercices "sujet" --nb 5 --niveau college
```

**Par exercice:**
- Énoncé clair et précis
- Réponse avec explication pédagogique
- Compétence testée

## 🎬 Création de Contenu

### Vidéo (OBS Studio)
```bash
jarvis-creation video
```
Lance OBS Studio. Format recommandé: MP4 720p pour cours en ligne.

### Podcast (Audio WAV)
```bash
jarvis-creation podcast
```
Enregistrement stéréo 44.1 kHz. Appuyer CTRL+C pour terminer.
Fichier: `~/Documents/Contenu/Podcasts/YYYYMMDD_HHMMSS_podcast.wav`

### Présentation (LibreOffice Impress)
```bash
jarvis-creation presentation
```
Utilise le template si disponible, sinon crée nouvelle présentation.

### Résumé automatique
```bash
jarvis-creation resume mon_cours.txt
```
Résume IA (backend M2 local) en 5 points clés, format markdown.
Sauvegarde: `~/Documents/Contenu/Resumes/YYYYMMDD_HHMMSS_resume.md`

### Dictée vocale → Texte
```bash
jarvis-creation dictee
```
Enregistre et transcrit via Whisper (nécessite: `pip install openai-whisper`)

## 🔌 Architecture Technique

### Backend IA
- **M2 Node:** 192.168.1.26:1234
- **Modèle:** qwen/qwen3.5-9b
- **Framework:** LM Studio API
- **Endpoint:** `/v1/chat/completions`

### Stockage
```
~/Documents/
├── Recherche/
│   └── YYYY-MM-DD_hhmss_sujet_[recherche|biblio|exercices].md
└── Contenu/
    ├── Videos/
    ├── Podcasts/
    ├── Presentations/
    └── Resumes/
```

## 🎯 Alias Rapides

Ajouter au `~/.bashrc` :
```bash
alias j-doc="jarvis-recherche --niveau college"
alias j-ex="jarvis-recherche --exercices"
alias j-bib="jarvis-recherche --biblio"
```

Utilisation:
```bash
j-doc "sujet"              # Recherche collège
j-ex "sujet"               # Exercices lycée
j-bib "sujet"              # Biblio APA
```

## 🔧 Troubleshooting

### Erreur 500 de M2
```
[ERREUR API M2] 500 Server Error
```
→ Vérifier: `curl http://192.168.1.26:1234/api/tags`

### OBS non trouvé
```
obs non installé
```
→ `sudo apt install obs-studio`

### arecord/whisper manquants
```
arecord: command not found
```
→ `sudo apt install alsa-utils && pip install openai-whisper`

### Wrappers CLI non trouvés
```bash
command not found: jarvis-recherche
```
→ Vérifier: `echo $PATH | grep .local/bin`
→ Si absent, exécuter: `bash ~/jarvis/scripts/jarvis-integration.sh`

## 📚 Exemples d'Usage

```bash
# Recherche lycée simple
jarvis-recherche "mitochondrie"

# Exercices niveau collège (8 exercices)
jarvis-recherche --exercices "circuits électriques" --nb 8 --niveau college

# Bibliographie sur la Renaissance
jarvis-recherche --biblio "Renaissance italienne"

# Créer vidéo pédagogique
jarvis-creation video
# → OBS ouvre

# Résumer un cours
echo "# Mon cours sur l'ADN..." > /tmp/mon_cours.txt
jarvis-creation resume /tmp/mon_cours.txt

# Enregistrer un podcast
jarvis-creation podcast
# CTRL+C pour terminer
# Fichier sauvé: ~/Documents/Contenu/Podcasts/...
```

## 📝 Notes

- Tous les résultats sauvegardés automatiquement (sauf `--no-save`)
- Format markdown pour faciliter intégration dans d'autres outils
- Timestamps UTC dans noms de fichiers
- Backend IA confidentiel (aucun cloud externe)

## 👤 Auteur

JARVIS Assistant pour Pamerys (Enseignante, Ubuntu 24.04)
Créé: 2026-05-23
