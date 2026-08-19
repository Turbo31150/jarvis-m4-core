[user] Audit comparatif d'une app enseignante. Lecture seule, ne modifie rien.

CONTEXTE : l'utilisatrice (professeure des écoles) dit que son ANCIENNE version d'outils (sur le disque Windows) générait des exercices, corrigeait, et proposait BEAUCOUP PLUS d'actions et de meilleure qualité que l'app actuelle « Pousseline ». Je veux savoir ce que l'ancienne faisait de plus, pour le relever.

ANCIENNE VERSION (disque Windows monté en lecture seule) — lis ces fichiers :
- /mnt/windows/Users/clair/interface_generateur_v3.py
- /mnt/windows/Users/clair/generateur_commentaires_scolaires.py
- /mnt/windows/Users/clair/generateur_commentaires_v3.py
- /mnt/windows/Users/clair/interface_generateur_commentaires.py
- /mnt/windows/Users/clair/symbiose_dashboard.py
- /mnt/windows/Users/clair/notion_dashboard.py
(si un fichier est absent/illisible, ignore-le. Liste aussi le contenu de /mnt/windows/Users/clair/ pour repérer d'autres scripts prof/générateurs/correcteurs pertinents et lis les 2-3 plus gros.)

APP ACTUELLE — pour comparer, survole ces fichiers dans /home/pamerys/jarvis/webapp/ :
- prof_routes.py (cœur : exos, corrections, séances, bulletins)
- outils_classe.py, banque_annuelle.py, adaptatif.py, ai_local.py

Rends un rapport markdown COMPACT et factuel :
1. **Fonctionnalités de l'ANCIENNE version** : liste par script — quoi (génère quoi ? corrige quoi ? quelles actions ?), quel backend/LLM utilisé (OpenAI ? Ollama ? local ?), entrées/sorties. Cite les noms de fonctions.
2. **Fonctionnalit

[assistant] Je lis la fonction IA clé de l'ancienne interface et les fichiers de l'app actuelle.

[assistant] Je vérifie quelques équivalents précis dans l'app actuelle (styles, export Word/Excel, TTS, lot classe).

[assistant] Analyse terminée. Voici le rapport.

---

# Audit comparatif — ANCIENNE (disque Windows) vs Pousseline (webapp actuelle)

## 1. Fonctionnalités de l'ANCIENNE version (par script)

| Script | Rôle / actions | Fonctions clés | Backend / LLM | Entrées → Sorties |
|---|---|---|---|---|
| **interface_generateur_v3.py** (98 Ko, GUI Tkinter, la plus riche) | Génère bulletins/appréciations, mode classe (lot), base SQL, exports multi-format, TTS, chat d'aide, backups | `generer_commentaires`, `_generer_avec_lmstudio`, `_parser_appreciation_lmstudio`, `generer_bulletins_lot`, `exporter('pdf/word/excel/html')`, `exporter_classe`, `lire_bulletin_vocal`, `envoyer_message_chat`, `demander_aide_bulletin`, `sauvegarder/charger_classe`, `sauvegarder_eleve_db`, `backup_to_github/gist/n8n` | **LM Studio** 2 serveurs LAN (192.168.1.26 & .85:1234) en génération **parallèle**, sinon **fallback template 100% local (0 IA)** | élève+matières+niveau+**style** → bulletin structuré, PDF/DOCX/XLSX/HTML, lecture vocale |
| **generateur_commentaires_v3.py** | Moteur templates v3 : appréciation **structurée en 3 blocs** (points à améliorer / points forts / conseils bienveillants) + **5 styles de formulation** | `StyleFormulation` (standard, encourageant, formel, bienveillant, objectif), `GenerateurAppreciation.generer_appreciation_structuree`, `_analyser_resultats`, `generer_commentaire`, `generer_bulletin_complet`, `_accorder`, `_pronom` | **Local pur** (templates + connecteurs, aucune IA) | infos élève + 