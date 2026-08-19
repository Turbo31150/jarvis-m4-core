[user] Tu es designer/dev front. Crée 2 PAGES DE VENTE B2B designées, autonomes, cohérentes avec la famille AlkymIA (registre premium). Fichiers locaux + notes Notion. Aucun secret. Rien publié.

FAMILLE AlkymIA : souverain/local RGPD/EU AI Act, tech mais HUMAIN, support téléphone. Persona fondateur à tisser : « Franck Delmas — fondateur AlkymIA » avec emplacement `[AVATAR-FONDATEUR]` (bloc image réservé, ne pas inventer). Preuves réelles utilisables honnêtement : Airia winner 2026 (crédibilité forte B2B), SaaS mairies 290-890 €/mois (workflow-gestion), produit vendu 750 €, portefeuille ~75 repos — [À CONFIRMER] si incertain. Ne pas gonfler (stat corpus ~18k chunks, PAS 264k).

PRODUIT 1 — **AlkymIA Sovereign** (18 000–20 000 € + audit d'entrée 1 500 €) : déploiement IA souveraine on-premise entreprise, container. Cible dirigeants/DSI/collectivités données sensibles. Registre corporate premium.
PRODUIT 2 — **AlkymIA Suite** : les apps réelles (Pousseline/Academy, PassCerfa, Transcription, TradeOracle, Phone Mouse…) livrées en container multi-plateforme. ⚠️ Honnêteté : Linux prouvé ; Windows-container + APK companions = « à finaliser » (roadmap, pas acquis). 3 formules (app seule / Suite bundle / entreprise). Prix : app 29-149 € / suite bundle / entreprise (lien Sovereign).

EXIGENCES DESIGN (chaque page = 1 fichier HTML autonome) : CSS inline, 0 CDN/police externe, 0 JS externe, thème clair+sombre (tokens), accessibilité (focus/contraste/reduced-motion), registre premium sobre (beau

[assistant] I'll create the folders and both landing pages, then the Notion notes. Let me start by writing the two HTML files in parallel.

[assistant] Terminé. Les deux pages de vente et les deux notes Notion sont créées et rattachées à l'index.

## Livrables

**Fichiers HTML autonomes**
- `/home/pamerys/jarvis/livrables/alkymia-sovereign/landing.html`
- `/home/pamerys/jarvis/livrables/alkymia-suite/landing.html`

**Notes Notion** (sous le hub, rattachées à l'index via link_to_page)
- Sovereign : https://app.notion.com/p/Landing-AlkymIA-Sovereign-3bc7800a81d681e5bfc0f7ca8de267f6
- Suite : https://app.notion.com/p/Landing-AlkymIA-Suite-3bc7800a81d681888b9bda756dcaecdc

## Parti-pris design
- **Famille cohérente, deux couleurs distinctes** : registre premium sobre commun (typo serif affirmée type Palatino, beaucoup d'air, accent or `b08d57`, pills/badges identiques). Sovereign = accent terre/brun corporate `7a5c3e` ; Suite = accent vert souverain `2f5d50`. On reconnaît la même marque, on distingue les deux produits.
- **Technique exigée respectée** : chaque page est 1 seul fichier, CSS 100 % inline, 0 CDN, 0 police externe (stack système serif/sans), le seul JS est un toggle de thème inline. Thème clair+sombre par tokens CSS (auto via `prefers-color-scheme` + mémoire `localStorage`). Accessibilité : skip-link, `:focus-visible` net, contrastes soignés, `prefers-reduced-motion` neutralise transitions/scroll.
- **Structure demandée** livrée sur les deux : hero + CTA (Sovereign « demander un audit », Suite « voir la suite / demander une démo ») · trust strip · problème (3 cartes) · solution/formules · différenciateur (souverainet