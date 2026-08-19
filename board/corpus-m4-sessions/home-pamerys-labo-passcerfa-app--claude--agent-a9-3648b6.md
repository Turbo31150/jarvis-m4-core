[user] Contexte : on prépare la mise en conformité d'applications à la réforme française de la facturation électronique 2026/2027. Il faut un CAHIER DES CHARGES des normes, à jour (nous sommes en juillet 2026).

Tâche (recherche web sur sources officielles : impots.gouv.fr, service-public.fr, FNFE-MPE, AFNOR, legifrance ; cite les URLs) :
1. Calendrier exact et à jour de l'obligation (réception obligatoire, émission par taille d'entreprise, e-reporting). Précise les dates 2026 et 2027.
2. Rôles PPF (Portail Public de Facturation) vs PDP vs OD, après la réforme (le PPF a changé de périmètre en 2024-2025 — vérifie l'état actuel).
3. Formats normés obligatoires : Factur-X (profils), CII, UBL, socle EN 16931 ; version Factur-X en vigueur.
4. Mentions obligatoires (CGI art. 289, nouvelles mentions : n° SIREN client, type d'opération, option paiement TVA, adresse de livraison).
5. e-reporting (transactions B2C et international) : quoi transmettre.
6. Norme AFNOR XP Z12-012 : ce qu'elle couvre.

Écris un cahier des charges structuré dans /home/pamerys/.claude/jobs/161b6ed8/tmp/veille-02-normes-cdc.md (sections + checklist de conformité). Factuel, daté, sourcé. Retourne un résumé de 8 lignes max : les 5 points de conformité les plus critiques + toute date qui aurait changé récemment.

[assistant] I'll research the French e-invoicing reform and produce the specification document. Let me start by loading the web tools and setting up.

[assistant] I'll research the official sources. Let me run parallel searches on the key topics.

[assistant] Let me research formats, mandatory mentions, e-reporting details, and the AFNOR norm.

[assistant] I have enough authoritative material. Let me verify the exact Factur-X version and mandatory lifecycle statuses from FNFE-MPE.

[assistant] Cahier des charges écrit dans `/home/pamerys/.claude/jobs/161b6ed8/tmp/veille-02-normes-cdc.md` (6 sections sourcées + checklist de conformité).

Résumé (points de conformité les plus critiques + dates récentes) :

1. **Réception obligatoire pour TOUTES les entreprises au 1er sept. 2026** ; émission + e-reporting au **1er sept. 2026 pour GE/ETI** et **1er sept. 2027 pour PME/TPE/micro**. Calendrier confirmé, aucun report.
2. **Le PPF n'émet/reçoit plus (abandon acté le 15 oct. 2024)** : il ne fait qu'annuaire + concentrateur. Toute app doit être PA immatriculée ou raccordée à une PA — plus d'option gratuite.
3. **Renommage 2025** : PDP → **Plateforme Agréée (PA)** ; OD → **Solution Compatible (SC)**. Seules les PA transmettent à l'administration.
4. **Formats socle EN 16931** : Factur-X (hybride), UBL, CII ; profil minimum **EN 16931** (pas MINIMUM/BASIC WL). Version Factur-X la plus récente : **1.09 / ZUGFeRD 2.5, publiée le 10 juin 2026**.
5. **4 nouvelles mentions** à câbler : SIREN client, adresse de livraison si différente, type d'opération (biens/services/mixte), option paiement TVA sur débits.
6. **e-reporting** = B2C + B2B international + données de paiement (services), fréquence selon régime TVA. **Statuts cycle de vie obligatoires (CDAR, AFNOR XP Z12-012)** : Déposée, Rejetée, Refusée, Encaissée.

Dates ayant changé récemment : Factur-X **1.09** sortie le **10 juin 2026** (nouveauté) ; norme **XP Z12-012 mise à jour mai 2025** ; annuaire ouvert **sept. 2025**.