[user] REGLES ABSOLUES: (1) ZERO invention — chaque fait ancre a un chemin/id/commande reel, sinon ne le rapporte PAS et mets-le en gaps. (2) READ-ONLY strict: aucune ecriture, aucun envoi, aucun upload, aucun rclone copy/move, aucun INSERT. Tu observes et tu rapportes. (3) Si une piece manque ou est ambigue -> gaps/contradictions, jamais combler par deduction. (4) Cite les montants/dates au caractere pres depuis la source.
SOURCE = MEMOIRE SQL (Postgres jarvis_main). Tu reconstruis TOUT ce que la memoire contient sur le dossier prud hommes Nuit Soleil.
Commandes (docker exec jarvis-postgres psql -U jarvis -d jarvis_main -t -A -c "..."):
- memory_atoms: SELECT id,created_at,content FROM memory_atoms WHERE content ILIKE ANY (ARRAY['%prud%','%soufiane%','%driouech%','%joshua%','%bernad%','%abello%','%coste%','%capstan%','%astreinte%','%amplitude%','%resiliation%']) ORDER BY created_at DESC LIMIT 60;
- decisions: SELECT id,created_at,decision FROM decisions WHERE decision ILIKE ANY(ARRAY['%prud%','%soleil%','%capstan%','%coste%','%bernad%','%driouech%','%abello%']) ORDER BY id DESC LIMIT 40;
- memory_timeline: idem filtre, LIMIT 40.
Lis le CONTENU COMPLET des atomes cles (INDEX etat 28/07, verdict red-team, visio Capstan 26/08, qui-sait-quoi Capstan, drive versement, 5 corrections coherence, livrables residuels, clotures 27/07 et 28/07). Restitue: cadre juridique tranche, etat par salarie (audience, quantum reclame, exposition reelle, pieces), pipeline mail avocat connu, expositions/DO

[assistant] Je vais interroger la mémoire SQL Postgres pour reconstruire le dossier prud'hommes Nuit Soleil. Commençons par les trois requêtes principales en parallèle.

[assistant] Les colonnes diffèrent. Vérifions les schémas des tables `decisions` et `memory_timeline`.

[assistant] Schémas identifiés. Corrigeons les requêtes decisions/timeline et lisons le fichier atoms.

[assistant] La timeline est riche. Maintenant listons les IDs d'atomes correspondants pour cibler les atomes clés, puis lisons leur contenu complet.

[assistant] J'ai la cartographie. Lisons maintenant le contenu complet des atomes clés. Commençons par le bloc INDEX / verdict red-team / 5 corrections / drive / livrables / clôtures.

[assistant] Bloc central lu. Lisons maintenant: visio Capstan deadline, qui-sait-quoi Capstan, drive versement, clôtures 27/07 et 28/07, cross-check IA, Q6.

[assistant] Bloc clôtures et cadre lu. Maintenant les atomes par salarié — Soufiane + organisation/rémunération de nuit.

[assistant] Soufiane complet. Maintenant lisons le bloc Joshua BERNAD + Abello + Coste prud'homal.

[assistant] J'ai lu l'ensemble du corpus mémoire. Je dispose de tout le matériel pour restituer le dossier de façon dense et ancrée. Je produis la synthèse structurée.