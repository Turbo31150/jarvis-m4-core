# JARVIS OS — Livrable de session (2026-08-14)

## 1. Résumé exécutif

La session a consolidé l'infrastructure LLM locale (routeur unifié + serveur MCP en service systemd actif/enabled), fiabilisé la supervision des ventes (Guardian URLs qui a réellement capté une alerte 404), et accéléré le Board d'experts (délibération 3 experts + synthèse en ~62 s). Côté ventes, la boutique Gumroad est saine à 89 % mais 7 produits sont morts (404) dont 2 phares représentant 548 € débloquables. Plusieurs actions restent à la main de Franck (tunnel Cloudflare permanent, tokens à régénérer, secrets à migrer au coffre). Point de vigilance : une session Gemini parallèle a piloté LinkedIn en auto-approuvé, à vérifier.

## 2. Ce qui marche maintenant (prouvé)

| Brique | État | Preuve |
|---|---|---|
| Routeur LLM unifié :18800 | systemd active + enabled | service persistant |
| Serveur MCP :8901 | systemd active + enabled | service persistant |
| Guardian URLs de vente | timer 4×/j | a capté une ALERT 404 systeme.io |
| Board d'experts accéléré | délibération 3 experts + synthèse ~62 s | via hub, endpoint `/v1/completions` ajouté |
| Vectorisation du board | relancée sur Rémi (déporté) | 0 chaleur générée sur M4 |
| Bug « serveur zombie » LM Studio | corrigé | la probe exige désormais une inférence réussie |

## 3. Ventes — état

**Boutique Gumroad : saine à 89 % (59/66 boutons encaissent).**

7 slugs morts (404) :

| Slug | Prix | Note |
|---|---|---|
| pack-complet-jarvis-os | 399 € | phare |
| jarvis-os-cluster-complet | 149 € | phare |
| agents-autonomes-mcp | 99 € | |
| llms-locaux-lm-studio-ollama | 79 € | |
| gemini-cli-masterclass | 59 € | |
| jarvis-voice-ptt | 69 € | |
| ia-healthcare | 79 € | doublon de `ia-sante` qui répond 200 |

**Geste le plus rentable :** republier `pack-complet-jarvis-os` + `jarvis-os-cluster-complet` dans le dashboard Gumroad → **548 € débloqués**.

**Autres canaux :**
- systeme.io `franckdelmas00.systeme.io` = 404 depuis plusieurs jours (à corriger côté dashboard SIO).
- Netlify `jarvis-delmas` répond 200 mais builds obsolètes.

## 4. À débloquer par l'utilisateur (actions Franck)

| Action | Détail |
|---|---|
| Tunnel Cloudflare NOMMÉ permanent | domaine sur son compte Cloudflare |
| Token Telegram révoqué (401) | régénérer via @BotFather puis coffre sops+age |
| Clé Mirra absente | `~/.config/mirr/api_key` manquante |
| Migration secrets | 6 secrets de `~/.claude/settings.json` → coffre sops+age |

## 5. ⚠️ Point de vigilance

Une session Gemini parallèle a piloté le **vrai LinkedIn** en mode auto-approuvé (possible post publié) → **à vérifier sur le profil**.

## 6. Prochaines actions les plus rentables (top 3)

1. **Republier les 2 produits Gumroad phares** (548 € débloqués).
2. **Vérifier LinkedIn** (post potentiel de la session Gemini).
3. **Régénérer le token Telegram** (réarme toutes les alertes).
