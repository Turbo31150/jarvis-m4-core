[user] Lis attentivement /home/pamerys/labo/CLAUDE_TASK_INBOX.md et traite immédiatement la directive PRIORITÉ 1:
1. Analyse le dossier FMS Toulouse (RQTH) et génère la lettre de motivation et l'argumentaire technique adapté.
2. Sauvegarde le dossier complet dans /home/pamerys/labo/output/CANDIDATURE_FMS_TOULOUSE_RQTH.md.
3. Mets à jour le statut dans Notion / CLAUDE_TASK_INBOX.md. Mode 100% autonome.

[assistant] Le fichier inbox est régénéré automatiquement toutes les 15 min — mes statuts y ont été écrasés. Je consigne donc dans `REPORT.md`, qui est persistant.

[assistant] Directive 1 livrée. J'interprète votre « 2 » comme la directive n°2 de l'inbox et j'enchaîne.

[assistant] Deux de ces fichiers sont lisibles par tout le système. Je restreins les permissions — action réversible, sans suppression.

[assistant] **Directive 1 — FMS Toulouse (RQTH) : livrée.**

`output/CANDIDATURE_FMS_TOULOUSE_RQTH.md` contient l'analyse d'adéquation, la lettre de motivation (version poste ciblé + variante spontanée), l'argumentaire technique d'entretien et le calendrier J+1→J+25 en dates absolues. Statut consigné sur la page Notion source.

Deux choses que j'ai tranchées :
- **Tech Lead SAP ABAP/UI5 écarté** — aucune expérience SAP au dossier. Cibler Support N1-N2 et Développeur BI, avec l'Academy FMS en porte d'entrée.
- **Le dépôt n'a pas été effectué**, volontairement : la lettre affirme le statut de bénéficiaire RQTH alors que votre propre plan place encore l'appel à Cap emploi 31 en J+1. Déclarer un statut non détenu à une Entreprise Adaptée serait une faute. Une formulation de repli est fournie au §6 du dossier.

**Directive 2 — clôture session 14/08 : partielle.** Les chiffres de la page Notion ne tenaient pas à la vérification :

| Point | Réalité |
|---|---|
| « 3 exports de mots de passe » | **5 fichiers**, 1 941 identifiants — 2 lisibles par tout le système → `chmod 600` appliqué |
| « /storage à 97 %, 64 Go » | `/storage` est un répertoire vide ; le disque réel est à **71 %**, 53 copies pour 30 Go |
| LM Studio M4/M6 muet | Confirmé, M6 ne répond même plus au ping — action physique requise |

Je n'ai rien supprimé. Il reste deux décisions qui vous appartiennent : le sort des 5 exports d'identifiants (coffre `sops+age` ou suppression après rotation des accès OVH/Orange/Bouygues), et la rem

[user] Actualise la liste des prospects B2B dans /home/pamerys/Bureau/VENTE/ et synchronise avec Notion.

[assistant] Je consolide les sources faisant autorité, en écartant la table empoisonnée du 14/08.

[assistant] Les 15 envois du 14/08 sont authentiques (destinataires réels, SMTP 250, Message-ID). J'intègre ce statut.

[assistant] Un écart : 16 contactés pour 15 envois réels. Je traque la collision d'appariement.

[assistant] C'est un doublon de graphie dans la source (« In Extenso Finance » / « … Occitanie »). Je fusionne les variantes.

[assistant] Le vivier contient des variantes d'entreprises déjà contactées (IRDI, Sogeclair, Pierre Fabre, Barreau/Ordre des Avocats). Je corrige avant publication — recontacter serait une faute.

[assistant] Fait. Deux livrables dans `~/Bureau/VENTE/` : `PROSPECTS_B2B.csv` (fichier de travail) et `PROSPECTS_B2B.md` (vue lisible), plus le bloc de mise à jour sur la page Notion « Prospection Toulouse ».

**Un point sur la demande :** `~/Bureau/VENTE/` ne contenait aucune liste de prospects — il n'y avait rien à actualiser sur place. J'ai donc reconstitué la liste depuis les sources faisant autorité (`contacts_verifies_stricts` et `envois_reels`) et l'ai déposée là.

**Résultat :** 141 lignes brutes → **26 entreprises** · 15 contactées · 11 au vivier · 0 réponse.

Trois choses que la consolidation a fait apparaître :

- **Les 15 envois du 14/08 sont authentiques** — destinataire réel, acquittement SMTP 250, Message-ID en base. Il ne faut pas les confondre avec les faux envois d'avant 21h ; ce sont deux lots distincts.
- **4 doublons de graphie auraient provoqué un double contact** d'entreprises déjà démarchées : IRDI Capital / IRDI Capital Investissement, Sogeclair / Sogeclair Aerospace, Pierre Fabre / Laboratoires Pierre Fabre, et Barreau de Toulouse / Ordre des Avocats Toulouse. Fusionnés.
- **`contacts_verifies` reste un piège** : cette table non suffixée contient les 62 adresses inventées de l'incident du 14/08. Une requête naïve y puise des adresses fausses en croyant lire des contacts vérifiés. Le renommage n'a été fait que sur la copie `_BRUT_A_REVALIDER`.

Conformément à votre choix, Notion reçoit le pilotage (statuts, échéances, garde-fous) et non les adresses — le CSV loca