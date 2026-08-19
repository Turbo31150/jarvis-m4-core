[user] Tu es l'agent NOTION-DOUBLONS. Objectif : documenter le risque de DOUBLON entre les IA qui pilotent la publication réseaux sociaux de l'utilisateur, et le ranger dans Notion.

SÉCURITÉ : documentation et lecture seulement. Aucune publication, aucun envoi, aucune modification de compte. Écriture uniquement dans le Notion privé de l'utilisateur.

CONTEXTE : trois pilotes potentiels se chevauchent pour publier du contenu sur les réseaux de Franck : (1) cette session Claude, (2) une session Gemini/Antigravity parallèle qui a piloté le vrai LinkedIn en mode auto-approuvé, (3) l'outil Mirra local (crée mais ne poste pas encore, clé API manquante). Risque = double publication / incohérence de ton / post non voulu.

ÉTAPE 1 — Recense l'existant (lecture seule, 0 modification) : liste les outils/scripts de publication présents localement. Utilise Bash/Grep en lecture seule dans /home/pamerys/jarvis (ex : rechercher "publish", "post_publish", "mirra", "linkedin" dans les scripts). Ne lance AUCUN script de publication. Résume ce que tu trouves.

ÉTAPE 2 — Rédige une page Notion "🔀 Audit doublons publication" :
# 🔀 Audit doublons publication — 2026-08-14
## Pilotes en concurrence
| Pilote | État | Risque |
|---|---|---|
| Session Claude (celle-ci) | prépare le contenu, ne poste pas sans accord | faible |
| Session Gemini/Antigravity | a piloté le vrai LinkedIn en auto-approuvé | ÉLEVÉ — post possible non voulu |
| Mirra local | crée, ne poste pas (clé API manquante) | faible tant que non

[assistant] Je commence par recenser les outils de publication localement, en lecture seule.

[assistant] Je précise l'inventaire sur les outils actifs (hors archive windows_recovery) et le point de publication Mirra.

[assistant] MCP Notion déconnecté. Je bascule sur le fallback REST via notion.env (sans jamais afficher le token).

[assistant] Hub trouvé (`🧠 JARVIS OS — Hub`, id `3bc7800a-81d6-8100-8f97-c66fe6f52f84`). Je crée la sous-page.

[assistant] Page créée. Rapport final.

## NOTION-DOUBLONS — Rapport

**Étape 1 — Inventaire local (lecture seule, aucun script lancé)**

Point critique : le vrai risque de publication n'est PAS Mirra local seul, mais les publishers navigateur/CDP actifs + la session Gemini auto-approuvée.

Outils ACTIFS de publication dans `/home/pamerys/jarvis/integrations/mirr/` :
- `linkedin_publish_cdp.py`, `instagram_publish_cdp.py`, `cdp_multi_publish.py`, `browseros_publisher.py`, `browseros_mcp.py` — publication réelle via navigateur/CDP
- `autopilot/` : `multi_platform_publisher.py`, `publish_linkedin_carousels.py`, `publish_profile_post.py`, `custom_route.py`
- `mirra_local/` (cli.py, scheduler.py, llm_router.py) — génère du contenu, ne poste pas seul
- MCP `local-mirra`/`mirra` : outils `mirra_publish`, `post_publish_now`, `post_schedule`

Archive NON active (`jarvis/windows_recovery/.../jarvis-cowork/dev/`) : `linkedin_publisher.py`, `linkedin_auto_routine.py`, `social_automation_engine.py`, `auto_publisher.py`.

Clé API Mirra manquante : non trouvée en clair (cohérent avec le coffre sops+age). C'est ce qui empêche Mirra local de poster tout seul.

**Étape 2/3 — Page Notion créée**

MCP Notion était DÉCONNECTÉ → fallback REST via `notion.env` (token jamais affiché). Sous-page créée sous le hub `🧠 JARVIS OS — Hub` :

URL : https://app.notion.com/p/Audit-doublons-publication-2026-08-14-3bc7800a81d6811c945ac390f7ed2c58

Contenu : tableau des 3 pilotes en concurrence (Claude=faible, Gemini/Antig