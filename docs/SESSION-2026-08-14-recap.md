# Récapitulatif session — 2026-08-14 (M4)
> À ranger dans Notion (workspace JARVIS OS). Classé par thème, avec état prouvé.

## 1. Board d'experts — RENDU FONCTIONNEL
| Élément | État | Preuve |
|---|---|---|
| `board ask` | ✅ WORKING via M6 | wrapper `~/jarvis/board/ask-m6.sh <domaine> "<q>"` (M6 :1234, `qwen/qwen3.5-9b`) |
| Corpus | 10 domaines · 48 experts · 264 612 chunks | `board.py status` |
| Vectorisation | 85 787 embeddings faits (~32 %) | dispatcher M6 `dispatch_embed_m6.py` (pausé pour libérer M6) |
| Domaine le + riche | `biblio-vivante` (106 k chunks) | recherche BM25 tant que < 60 % vectorisé |

**Piège :** `qwen2.5-coder-14b` refuse de se charger sur M6 (VRAM prise par le 9b) → HTTP 500. Seul `qwen3.5-9b` marche pour le chat. Embeddings = nomic sur M6/Rémi.

## 2. Savoir-faire Rémi avalé (lecture seule) — réseaux sociaux + systeme.io
- Playbook : `~/jarvis/docs/savoir-faire-remi-reseaux-sio.md`
- 30 blocs `remi-dva` fusionnés dans `~/labo/bibliotheque/lib/BLOCS-INDEX.tsv` (routables par `bloc.sh`)
- Méthode clé : boucle générer→valider(Telegram)→publier(API)→mesurer→régler ; screener IG ; guardian d'URLs ; forge/orfèvrerie (rsync filtré, 0 secret)
- Mécanique par réseau : IG/FB via Graph API Meta ; TikTok/multi via Mirra ; WhatsApp = draft Telegram à coller ; X = moisson fxtwitter

## 3. Vente / plateformes — verdict board + live
- **systeme.io** `franckdelmas00.systeme.io` = **404** (mort) → à réparer dans le dashboard SIO
- Sites Netlify (`jarvis-delmas` 200) : builds obsolètes, repos non reliés → checkout inactif
- Priorité board : activer un tunnel Gumroad/PayPal (encaisser vite) AVANT de réparer SIO/Netlify

## 4. Guardian d'URLs de vente — INSTALLÉ (réplique DVA)
- `~/jarvis/scripts/guardian-urls.sh` + conf `~/jarvis/config/guardian-urls.txt`
- Timer systemd user 06/12/18/22h, `enabled/active` ; premier passage : `ALERT 404 systeme.io` capté
- ⚠️ Alerte Telegram muette : **token du coffre sops révoqué (401)** → régénérer via @BotFather

## 5. Connecteur MCP JARVIS ↔ Perplexity (bidirectionnel) — EN COURS
- Serveur : `~/jarvis-mcp` (FastAPI, 17 outils), service systemd user `jarvis-mcp.service` (:8901), démarrage au boot
- Sécurité ajoutée : **garde chemin secret** (`JARVIS_MCP_PATH`) — sans le secret → 404 (les scanners Internet se cassent dessus). GET /mcp → 200 (sonde de validation).
- Contrôle chaîne : `~/jarvis/scripts/mcp-funnel-check.sh` + timer boot/6h
- **Blocage identifié** : Tailscale Funnel donne une URL stable mais **Perplexity ne l'atteint pas** (0 hit serveur, `FETCHER_HTML_STATUS_CODE_ERROR`).
- **Cloudflare quick tunnel = fonctionne** (GET 200, 17 outils) MAIS URL éphémère → **il faut un tunnel NOMMÉ permanent** (Cloudflare + domaine, ou autre). ← DÉCISION UTILISATRICE REQUISE (voir §7)

## 6. Système / hygiène
- RAM : pics à Chrome (~12 onglets freelance) — non critique, ne rien tuer
- `cloudflared` 2026.8.1 installé (`~/.local/bin`)
- Token Cloudflare dans `~/.claude/skills.env` = **vide** (pas de named tunnel possible sans login/domaine)

## 7. DÉCISIONS EN ATTENTE (utilisatrice)
1. **Tunnel permanent** : as-tu un domaine sur un compte Cloudflare ? Si oui → tunnel nommé `mcp.<domaine>` stable et définitif. Sinon → login Cloudflare interactif à faire.
2. **Token Telegram** frais (BotFather) → réactive toutes les alertes JARVIS
3. **Clé Mirra** (`~/.config/mirr/api_key`) → débloque la publication réseaux sociaux
4. **systeme.io** : corriger le sous-domaine 404 dans le dashboard
