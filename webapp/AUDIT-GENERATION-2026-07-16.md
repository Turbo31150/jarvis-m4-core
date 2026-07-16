# Audit génération & comparatif ancienne app — 2026-07-16 (23h)

## A. Diagnostic « l'app ne génère rien » — VRAI/FAUX
L'app **génère bien** (test live : `ollama-cloud`, 2,9 s, exercice CE2 produit). MAIS elle ne tient qu'à **un seul fil** :

| Backend | État | Détail |
|---|---|---|
| Cluster **M1** (10.42.0.1:1234) | ❌ DOWN | le backend que tu veux (« OAM1 ») est injoignable |
| Cluster M2 (192.168.1.26) | ❌ down | |
| Ollama **local** CPU | ⚠️ BRIDÉ | `local_bride=True`, GPU 82-83 °C ≥ seuil 82 |
| Ollama **cloud** | ✅ seul actif | kimi/gpt-oss, déporté, 0 token |
| Gemini / ZAI | ❌ | pas de clé |

→ **Si le net ou la clé cloud tombe : plus AUCUN backend → HTTP 503 → « ça ne génère rien ».**

## B. Checkpoints PROBLÉMATIQUES relevés
| # | Problème | Gravité | Piste |
|---|---|---|---|
| CP-1 | **M1 down** (câble direct 10.42.0.1 + LAN .85) | 🔴 | rebrancher/rallumer M1, ou accepter cloud-first |
| CP-2 | **Thermique 82-89 °C** bloque le local + GPU `HOT` | 🔴 | traquer charge locale (LM Studio ? systemd-USER), governor 82 °C |
| CP-3 | **Mono-dépendance ollama-cloud** (SPOF) | 🟠 | ajouter clé Gemini en repli |
| CP-4 | **Pas de repli hors-IA** (503 si cascade KO) — l'ancienne sortait toujours un résultat via templates | 🔴 | **réintégrer un moteur templates local** (delta #7) |
| CP-5 | Note du budget classe **vidée** par un test | 🟢 | à réécrire manuellement |
| CP-6 | 3 orphelins front restants (biblio dédoublon, systeme_io, banque UI) | 🟢 | boucle en cours |
| CP-7 | GPU 89 °C `HOT` persistant, non lié au dispatch | 🟠 | diag prochaine session |

## C. Ce que l'ANCIENNE version (disque Windows `/mnt/windows/Users/clair/`) faisait de PLUS
Delta priorisé (fonctions produit absentes aujourd'hui) :

| # | Manquant | Source ancienne | Faisabilité |
|---|---|---|---|
| 1 | **5 styles de formulation** (standard/encourageant/formel/bienveillant/objectif) — l'actuelle a un ton codé en dur | `generateur_commentaires_v3.py` (`StyleFormulation`) | Facile |
| 2 | **Appréciation structurée en 3 blocs** (à améliorer / points forts / conseils) | `generer_appreciation_structuree` | Facile-moyen |
| 3 | **Génération par LOT / classe entière** + parallélisme | `generer_bulletins_lot`, `LMStudioManager.generate_parallel` | Moyen |
| 4 | **Export Word (.docx) + Excel (.xlsx) + HTML** (actuelle = PDF + Markdown only) | `export_bulletins.py` | Moyen |
| 5 | **Lecture vocale (TTS) du bulletin** (actuelle = dictée en entrée seulement) | `module_vocal.SyntheseVocale` | Moyen |
| 6 | **Accord genre F/M automatique** garanti hors-IA | `_accorder`, `_pronom` | Facile |
| 7 | **Fallback 100 % local sans IA** (templates matière×niveau) → jamais de 503 | `generateur_commentaires_scolaires.py` | Gros mais = robustesse |

**Backends** : l'ancienne = LM Studio 2 serveurs LAN en génération **parallèle** + **repli templates local**. L'actuelle = cascade cache→M1/M2→Ollama local→cloud→Gemini (techniquement supérieure : 0-token, cache, anti-surchauffe) MAIS **sans repli hors-IA**.

## D. Plan de réintégration (ordre conseillé)
1. **CP-4 + delta #7** : moteur templates local de repli (fin des 503) — priorité robustesse.
2. Delta #1 + #2 + #6 : styles + structuré 3 blocs + accord genre (rapides, fort impact perçu).
3. Delta #3 : génération par lot classe entière.
4. Delta #4 + #5 : exports Word/Excel + TTS bulletin.
5. CP-1/CP-2/CP-7 : rallumer M1 + gouverneur thermique.

Sources : `/mnt/windows/Users/clair/{interface_generateur_v3,generateur_commentaires_v3,generateur_commentaires_scolaires,lmstudio_integration,module_vocal,export_bulletins}.py`.
Base ancienne : `/mnt/windows/Users/clair/BACKUP_2026-06-14/ecole_20260614_194012.db`.
