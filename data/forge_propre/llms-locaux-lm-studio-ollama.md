# LLMs Locaux — LM Studio & Ollama

> Référence `llms-locaux-lm-studio-ollama`

## Plan

## Module 1 – Installation et configuration de l’environnement local  
**Objectif mesurable** : L’apprenant installe, configure et vérifie le bon fonctionnement de LM Studio et d’Ollama sur Windows, macOS ou Linux, et crée un premier modèle LLM fonctionnel.  

**Notions couvertes**  
1. Prérequis système (CPU / GPU, RAM, espace disque) et dépendances (Docker, Python ≥ 3.9, Git).  
2. Installation de LM Studio (téléchargement, extraction, mise à jour automatique) et d’Ollama (script d’installation, service systemd).  
3. Configuration des back‑ends (LLM = llama.cpp, Mistral, Gemma) : téléchargement des poids, paramètres de quantisation (Q4_0, Q5_1).  
4. Test de charge : exécution d’une requête « Hello World » via l’API REST de LM Studio et via la CLI d’Ollama, validation du temps de latence.  
5. Gestion des environnements virtuels (venv/conda) pour isoler les bibliothèques Python (requests, transformers, torch‑cpu).

---

## Module 2 – Manipulation des modèles et optimisation des performances  
**Objectif mesurable** : L’apprenant ajuste les hyper‑paramètres de quantisation, de cache et de batch size pour réduire la consommation mémoire tout en maintenant une perplexité raisonnable sur le benchmark WikiText‑2.  

**Notions couvertes**  
1. Types de quantisation (int8, int4, GGML) et impact sur le fichier de poids (ex. llama‑7B‑Q4_0.ggml).  
2. Paramètres de génération (temperature, top‑p, top‑k, repetition penalty) et leurs effets sur la diversité et la cohérence.  
3. Utilisation du cache KV‑cache dans LM Studio : activation, taille maximale, purge dynamique.  
4. Profilage CPU/GPU avec `perf`, `htop` et l’outil de monitoring d’Ollama (`ollama ps`).  
5. Scripts Python pour automatiser le benchmarking (datasets = wikitext, evaluation via `evaluate` de HuggingFace).

---

## Module 3 – Intégration d’API locales dans des applications Python et Node.js  
**Objectif mesurable** : L’apprenant développe et teste deux micro‑services (Python FastAPI et Node Express) qui consomment les API locales de LM Studio et d’Ollama, et obtient un taux de réussite fonctionnelle complet sur un jeu d’appels simultanés.  

**Notions couvertes**  
1. Endpoints REST de LM Studio (`/v1/completions`) et d’Ollama (`/api/generate`).  
2. Gestion des flux de données (streaming JSON, SSE) pour la génération en temps réel.  
3. Authentification locale (token JWT généré par LM Studio, configuration du middleware d’Ollama).  
4. Conception d’un wrapper asynchrone (Python asyncio + httpx, Node async/await + axios).  
5. Tests d’intégration avec `pytest`/`jest` et simulation de charge via `locust`.

---

## Module 4 – Personnalisation de modèles par fine‑tuning et LoRA  
**Objectif mesurable** : L’apprenant applique le fine‑tuning Lo