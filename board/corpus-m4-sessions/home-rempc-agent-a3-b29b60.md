[user] Tu produis UNE section de spec markdown pour durcir l'écosystème JARVIS. Lis d'abord /home/rempc/jarvis/docs/exports/pack-methode-jarvis/01-MATRICE-VECTORIELLE.md pour rester cohérent (4 lois de frontières A1-A4, A0/A5, briques mail/media/board/web/agent/publish/mem).

CONTEXTE (faille trouvée par red-team multi-IA) : la loi A0 dit « tout contenu externe est NON fiable et ne déclenche jamais directement une action ». MAIS une source peut être empoisonnée AVANT d'être ingérée comme « fiable » : corpus RAG du board (board self-source), pages grabbées par jarvis-web puis stockées, modèles/embeddings — supply-chain / data poisoning. L'attaque n'injecte pas une instruction en temps réel ; elle corrompt l'ADN cognitif (prémisses) en amont.

TA TÂCHE : écris une section « ## A0+ — Provenance & quarantaine des sources » (markdown, ~250 mots) qui comble ce trou, EN RESPECTANT les 4 lois et SANS ajouter de 8e brique (étends le comportement de web/mem/board). Couvre concrètement :
- Étiquetage de provenance obligatoire à l'ingestion (source_id, url, hash SHA-256, date, voie d'acquisition) — porté par jarvis-web (A3) puis jarvis-mem (A2).
- Quarantaine : toute nouvelle source entre en état QUARANTINE, non consultable par le board tant que non promue (revue/critère).
- Intégrité : re-hash au retrieval ; divergence de hash => rejet.
- Séparation : contenu de source ≠ instruction (rappel rupture de privilège), même pour les corpus « internes ».
- Un invariant vérifiable (façon Σ du fichier 

[assistant] I'll read the reference file first to stay coherent with the established framework.

[assistant] ## A0+ — Provenance & quarantaine des sources

> **Faille comblée** : A0 protège l'*ingress temps réel* mais pas l'*ADN cognitif* — une source peut être empoisonnée **avant** d'être stockée comme « fiable » (corpus RAG `board` self-source, pages grabbées par `web` puis persistées, embeddings). A0+ étend le comportement de **web (A3)**, **mem (A2)** et **board** — **sans 8ᵉ brique**.

**1. Étiquetage de provenance (obligatoire, à l'ingestion).** Toute source acquise porte une enveloppe `provenance = ⟨source_id · url · sha256(contenu) · date · voie_acquisition⟩`. `web` (A3) l'appose au *grab* ; `mem` (A2) la persiste comme métadonnée **immuable** de l'atom. Aucun atom externe sans provenance ⇒ rejet au `write`.

**2. Quarantaine.** Toute source neuve entre en état `QUARANTINE` : indexée mais **non consultable** par `board` (ni par la cascade LLM) tant que non **promue** (`QUARANTINE → PROMOTED`) via revue humaine **ou** critère explicite. `board.retrieve` ne lit que `PROMOTED` — le self-source ne s'auto-promeut jamais.

**3. Intégrité au retrieval.** Re-hash à chaque lecture : `sha256(contenu) ≠ provenance.hash ⇒ rejet`. Contenu altéré après stockage = source redevenue non fiable, jamais de lecture silencieuse.

**4. Séparation source ≠ instruction.** La rupture de privilège A0 s'applique **aussi aux corpus internes** : un atom `PROMOTED` reste **donnée**, jamais instruction — un corpus « de confiance » ne déclenche pas `publish` hors du flux `stage → approve(humain) → commit(h