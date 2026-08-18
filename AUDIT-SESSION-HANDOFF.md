# AUDIT & REGISTRE DE HANDOFF — session M4 (2026-06-29)

> À lire par un autre terminal / station d'entreprise pour reprendre le travail.
> Tout est factuel et traçable. Aucune clé vivante ici (les clés systeme.io ont été révoquées).

## 1. Ce qui a été créé/modifié — app Pousseline (webapp :7777)

Repo : **jarvis-m4-core** (GitHub Turbo31150) · branche active : **`sites-2026-refonte`** · dossier `/home/pamerys/jarvis/webapp/`.

| Fichier | Rôle | Commit |
|---|---|---|
| `banque_annuelle.py` | Banque annuelle : fiches d'exercices différenciées toutes matières PS→CM2, génération progressive 0-token + garde thermique 86°C, PDF compilé. Routes `/api/banque/{plan,generer,batch,pdf,cellule}` + GET liste | 5e394c5 |
| `systeme_io.py` | Intégration **optionnelle** systeme.io (OFF par défaut) : toggle + clé API locale (kv) + proxy générique `/api/systeme/{config,ping,proxy}` | 1d4ae4d, 218da40, cf97723 |
| `prof.html` | Refonte UX : **6 rubriques** (Accueil/Préparer/Suivre/Classe/Automatiser/Outils) + 18 onglets ; onglets Année, Vie de classe, Outils, Pilotage, systeme.io ; bouton PDF partout | 5e394c5 + |
| `pousseline_nuit.sh` | Prépa nocturne (timer `pousseline-nuit.timer` 05:00) : mails dus + cahier-journal J+1 + 3 fiches banque/nuit, garde thermique | acd9714, 19aff0a |
| `ai_local.py` | Fix perf : `backend_status()` sondes parallèles + pas de re-sonde d'hôte injoignable → dashboard 8 s→1,5 s | 5aa2739 |
| `automations.py` | Sécu : `require_token` par route sur `/api/automations/*` (défense en profondeur) | a44fc26 |
| `server.py` | Enregistrement modules `banque_annuelle` + `systeme_io` | 5e394c5, 1d4ae4d |

Commits session (récents) : cf97723, 218da40, 1d4ae4d, 19aff0a, 5e394c5, a44fc26, acd9714, 5aa2739 — **tous poussés sur origin/sites-2026-refonte**.

## 2. Skill créée

- **`~/.claude/skills/banque-annuelle/`** : SKILL.md (description optimisée — recall 0%→fonctionnel via run_loop) + `references/api-banque.md` + `scripts/remplir-annee.sh`. Validée par skill-reviewer (PASS).

## 3. Bibliothèque unifiée (registre des outils)

- **`jarvis_master.db` → `tool_map` : 705 outils** (skill, agent, cli, command, cmd-template 253, model, mcp, cowork-agent 34, pattern, script). Intégration idempotente (`INSERT OR IGNORE`).
- **`labo/JARVIS-INC/registry.json`** : 111 entrées (19 skills + 59 agents + 33 commands).
- **Dashboard** : `/home/pamerys/jarvis/bibliotheque-dashboard.html` (vue lecture seule, 705 outils filtrables/cherchables, 0-token).
- 14 agents OMEGA intégrés ; 34 patterns cowork (etoile.db) intégrés.
- ⚠️ Les 329 `cowork_script_mapping` d'etoile.db sont **TOUS `status=missing`** (placeholders, 0 script réel) → **NON intégrés** (pas de fabrication).

## 4. Clés / credentials — STATUT

| Clé | Statut | Action |
|---|---|---|
| systeme.io **API publique** (« jarvis ») | ❌ **RÉVOQUÉE** par l'utilisateur | purgée d'`ecole.db` ; module désactivé |
| systeme.io **MCP** (« pamerys ») | ❌ **RÉVOQUÉE** | serveur MCP retiré de `~/.claude.json` |

→ Intégration systeme.io **prête à réactiver** dès nouvelles clés (coller clé API dans l'onglet 🚀 ; `claude mcp add` pour le MCP). **Stocker les clés dans le coffre age**, jamais en clair/git.

## 5. Infra / thermique — décisions appliquées

Boucles d'inférence locale **STOPPÉES + DISABLED** (root cause surchauffe GPU 86°C + RAM 92%, conforme mémoire `m4-dispatch-flux-ondemand` / `m4-surchauffe-overclocking`) :
- `jarvis-cowork-loop.service` — disabled
- `jarvis-cowork-dispatcher.service` — disabled
- `jarvis-domino.service` — disabled
- **NE PAS réactiver sur M4 seul** (provoque RAM 92% + GPU 86°C via réinférence qwen2.5:7b 5 Go).

## 6. État système au handoff

- GPU **73°C**, 0% util · RAM **10 Gi utilisé / 5,3 Gi dispo** · 0 modèle Ollama chargé · 0 service en échec.
- Webapp `jarvis-webapp.service` : active (port 7777).
- Timers actifs : `pousseline-nuit.timer` (05:00). 

## 7. Pour reprendre (autre terminal)

1. `cd /home/pamerys/jarvis && git checkout sites-2026-refonte && git pull`
2. Webapp : `http://127.0.0.1:7777/prof` (Espace Prof) — 6 rubriques.
3. Bibliothèque : ouvrir `bibliotheque-dashboard.html` (ou requêter `jarvis_master.db`).
4. NE PAS relancer cowork-loop/dispatcher/domino sur M4 seul.
5. systeme.io : recréer les clés côté plateforme, puis réactiver via l'onglet + `claude mcp add`.
6. Cluster M1/M2/M5 : DOWN (WoL bloqué par subnet — émettre depuis un nœud du LAN 192.168.1.x). Les ~86 « skills cowork » sont des placeholders (non implémentés).
