[user] Contexte : réforme française de la facturation électronique 2026/2027. On prépare une app qui laisse le client choisir sa Plateforme de Dématérialisation (PDP) certifiée. On veut un inventaire technique EXPLOITABLE des API.

Tâche (recherche web + sources officielles, cite les URLs) :
1. Récupère la liste des principales PDP immatriculées par la DGFiP (impots.gouv.fr publie la liste). Donne au moins les 15 plus connues (Pennylane, Qonto, Docaposte/SERES, Cegid, Sage, Sellsy, Esker, Generix, Yooz, Libeo, Tiime, etc.).
2. Pour chacune, quand c'est public : URL de la doc API, modèle d'authentification (OAuth2 client_credentials ? clé API ?), endpoint d'envoi de facture, formats supportés (Factur-X/CII, UBL), présence de webhooks de statut.
3. Indique lesquelles ont un programme partenaire/affiliation/revendeur public (URL).

Écris le résultat dans le fichier /home/pamerys/.claude/jobs/161b6ed8/tmp/veille-01-pdp-apis.md sous forme de tableau markdown + notes de sources. Sois factuel, ne pas inventer d'endpoints : si non trouvé, écris "non public". Retourne un résumé de 8 lignes max avec les 3 PDP les plus « API-friendly + affiliation ».

[assistant] API Error: Connection closed mid-response. The response above may be incomplete.

[assistant] Fichier écrit : `/home/pamerys/.claude/jobs/161b6ed8/tmp/veille-01-pdp-apis.md`

Résumé (source DGFiP : 137 plateformes agréées, ex-PDP, juillet 2026 — liste officielle sur impots.gouv.fr) :

1. **Pennylane** — la plus « API-friendly » : doc développeur publique complète (pennylane.readme.io), endpoint e-invoice clair `POST /api/external/v2/e-invoices/imports`, OAuth2 en prod, Factur-X/UBL/CII, webhooks + Marketplace/partenaires éditeurs.
2. **Qonto** — OAuth2 Bearer, sandbox + Developer portal, webhooks temps réel, endpoints e-invoicing documentés, et **programme d'affiliation public net** (qonto.com/en/affiliate + referral 300€/100€).
3. **Sellsy** — API V2 OAuth2 + webhooks, PA intégrée, et **programme partenaire public riche** (Ambassadeur/Accrédité/Marketplace/marque blanche : go.sellsy.com/sellsy-partner-program).

Points de vigilance : Docaposte/SERES, Esker, Yooz, Generix, Tiime exposent formats (Factur-X/UBL/CII) mais leur doc développeur et endpoints précis sont **non publics** (accès partenaire) — colonnes marquées « non public », aucun endpoint inventé. Constante réglementaire : toutes les PA doivent supporter Factur-X + UBL + CII (EN 16931), auth OAuth2/mTLS, certif ISO 27001.