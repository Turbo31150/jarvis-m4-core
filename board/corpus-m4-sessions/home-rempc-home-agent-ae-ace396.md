[user] REGLES ABSOLUES (JARVIS / Remi) — leur violation invalide ton travail :
- ANTI-FABRICATION : n'affirme JAMAIS le resultat d'une commande que tu n'as pas executee. Si tu ne trouves pas, ecris "NON TROUVE".
- POSTGRES-AVANT-DISQUE : la verite est dans jarvis_main (docker exec jarvis-postgres psql -U jarvis -d jarvis_main -tA -c "..."), puis dans les pieces sur disque. Jamais dans une supposition.
- N'ENVOIE RIEN : aucun mail, aucun push, aucune action irreversible. Aucune exception.
- Ne touche PAS a MEMORY.md ni a ~/.claude.json ni aux settings.
- Gros fichiers : jamais Read sur >1 Mo, passe par python3/grep avec sorties bornees.
- Ecris en francais.
CONTEXTE DOSSIER : SARL Ambulances du Soleil face a 3 requetes prud'homales de l'equipe de NUIT
(COSTE audience 08/09, BERNAD 15/09, DRIOUECH 29/09) + 1 anticipe (ABELLO, arret depuis 05/09/2025).
Deadline reelle = VISIO CAPSTAN (avocat) du 26/08/2026. La note socle + 4 annexes doivent partir avant.

MISSION CRITIQUE — etablir la VERITE TERRAIN sur Soufiane DRIOUECH. Les corrections #3 et #4 en dependent ; si tu te trompes, on ecrit une fausseerte dans un document destine a un avocat.
A etablir avec preuve :
1. DATE D'EMBAUCHE exacte de Soufiane DRIOUECH (contrat, bulletins, registre du personnel). L'audit affirme qu'il est embauche en 2025 et que l'annexe lui prete a tort des donnees 2023.
2. Ses NUITS REELLEMENT TRAVAILLEES ET PAYEES (la memoire mentionne 53 nuits de septembre a decembre 2025 — confirme ou infirme, avec la sourc

[assistant] Les contrats sur disque donnent déjà une piste forte. Je vérifie en Postgres et j'extrais les PDF.

[assistant] Point 1 déjà établi. Je récupère l'atom d'audit complet (corrections #3 et #4) et les bulletins.

[assistant] Les bulletins 2025 de Driouech sont complets et payés. J'OCRise les arrêts et j'ouvre le registre des nuits.

[assistant] L'arrêt du 05/09/2025 est identifié. Je cherche maintenant l'arrêt de Joshua BERNAD.

[assistant] Deux arrêts distincts confirmés. Je précise les dates de l'AT de Joshua et je compte les nuits de Driouech.

[assistant] Le registre 2025 est vide à partir de mai. Je vérifie le décompte nuits et les bulletins BERNAD 2026.

[assistant] Le compte tombe. Je vérifie la structure exacte du décompte et l'absence d'arrêt chez Driouech.