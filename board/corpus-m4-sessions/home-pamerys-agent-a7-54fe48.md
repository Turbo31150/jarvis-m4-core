[user] Tu es product manager. Cadre l'offre « AlkymIA — Suite d'applications multi-plateforme (container) » à partir des apps réelles du GitHub de Franck + le modèle de distribution container. Écris dans Notion. AUCUN fichier local. Aucun secret. Rien publié. N'invente pas d'app : base-toi sur l'existant réel.

SOURCES (Notion, lecture seule via GET children / search) :
- « 🐙 Extraction — Repos GitHub Turbo31150 » (165 repos, dont ~77 produits finis, 61 archives à EXCLURE) — id 3bc7800a81d6812f8d02caab87c7c621.
- « 📦 Extraction — Tous les livrables & applications » (44 livrables, 12 apps/SaaS) — id 3bc7800a81d6814389c9c360e2326567.
Sélectionne UNIQUEMENT les vraies applications vendables (Pousseline/AlkymIA Academy, PassCerfa, transcription-ia, tradeoracle, prof-ia, phone-mouse, etc.), EXCLUS les archives/backups/PII (dossier-creanciers, BASE-SQL3, configs privées).

CADRE PRODUIT — page Notion « 📦 AlkymIA Suite — apps multi-plateforme (container) » sous le hub « 🧠 JARVIS OS — Hub » (id 3bc7800a-81d6-8100-8f97-c66fe6f52f84) :
1. Callout : « JARVIS OS = socle technique interne ; distribué sous marque AlkymIA. Toutes les apps réelles, livrées en container portable. »
2. **Argument de distribution CONTAINER / MULTI-PLATEFORME** (le cœur) : AlkymIA livré en container (Docker/OCI) → tourne sur Linux, **Windows via container (Docker Desktop/WSL2)**, serveur ; + **app Android** (companion / accès mobile) ; local-first, souverain, RGPD. Explique en clair le bénéfice client (installe partout

[assistant] I'll fetch the key tables: Applications & SaaS from livrables, and Produits finis from repos.

[assistant] Page created. Now the bookmark append to the master index (at the very end, to avoid write conflicts).

[assistant] Terminé. Cadre produit AlkymIA Suite créé dans Notion, basé uniquement sur les apps réelles extraites (aucune inventée, archives/PII exclues).

## Rapport final

**URL page** : https://app.notion.com/p/AlkymIA-Suite-apps-multi-plateforme-container-3bc7800a81d681348229c3e08e6e93b2 (sous le hub JARVIS OS)

**Apps réelles retenues : 11** (extraites de la table « Applications & SaaS » + « Produits finis ») : Pousseline/AlkymIA Academy, Espace Prof/Prof-IA, PassCerfa, Transcription-IA (Phanesis), Mirra-Local, Planning App, TradeOracle/Trading-AI, Phone Mouse Pro, Transcription-portable, app.atsd.info, AlkymIA-OS/JARVIS OS (Sovereign). Écartés : archives/backups, briques verticales privées non finies (repliées en note dans la formule entreprise).

**État container / Windows / Android (prouvé vs à finaliser)** :
- **Prouvé** : local-first souverain sur Linux (socle de prod actuel) ; multi-plateforme natif seulement pour **Phone Mouse Pro** (app Android + serveur Windows) et **Transcription-portable** (app Android) ; Pousseline/Prof-IA accessibles en PWA Android.
- **À finaliser** (marqué honnêtement dans un callout ⚠️ et par ligne du catalogue) : images container/OCI publiées, run Windows-container (Docker Desktop/WSL2), APK Android companion des autres apps. Aucune preuve de packaging container distribué → étiqueté « à finaliser », pas prétendu comme fait.

**Contenu** : callout de cadrage, section argument container/multi-plateforme (bénéfice client + état honnête), catalogue tabl