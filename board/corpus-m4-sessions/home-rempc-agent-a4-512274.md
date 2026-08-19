[user] Audit de cohérence, READ-ONLY (n'édite AUCUN fichier). Cible : le dossier /home/rempc/Bureau/franck/ (lis 00-LISEZ-MOI-FRANCK.md et tout ecosysteme/*.md).

Cherche des incohérences CONCRÈTES et vérifiables :
1. **Numérotation des invariants Σ** : le fichier `05-DURCISSEMENT-REDTEAM.md` utilise `Σ.7` (provenance) et `Σ.8` (policy) ; le fichier `06-CONTRATS-RUNTIME-V2.md` utilise aussi des `Σ7…Σ13`. Repère TOUTE collision de numéro et propose une renumérotation cohérente unique.
2. **Cross-références** : chaque renvoi entre fichiers (« voir 03 », « §9.x », etc.) pointe-t-il vers quelque chose qui existe ?
3. **Noms des 7 briques et verbes** cohérents partout (mail/media/board/web/publish/agent/mem) ?
4. **Contradictions** entre les 4 lois (v1, fichier 01) et les contrats v2 (fichier 06) ?
5. **Table des fichiers** du 00-LISEZ-MOI correspond-elle aux fichiers réellement présents ?

RENVOIE une punch-list ordonnée (plus grave d'abord), format : `[fichier] · problème · correctif proposé`. C'est de la donnée pour moi, pas un message à un humain. Si tout est cohérent, dis-le explicitement.
<context_window_protection>
  <priority_instructions>
    Every byte a tool returns enters your conversation memory and costs reasoning capacity for the rest of the session. The context-mode tools let you do the work in a sandbox and surface only the derived answer — the raw bytes stay out. Think-in-Code: program the analysis, do not compute it by reading raw data into your conversation.
  </prior

[assistant] I'll start by exploring the target directory and loading the context-mode tools.

[assistant] This is a nuanced coherence audit requiring careful cross-referencing of specific text. The files are small (707 lines total), so I'll read them all directly to have exact content for analysis.

[assistant] Let me verify the archive contents (to check if the exported pack is stale relative to the v2 files) and confirm no other cross-references were missed.

[assistant] Audit complete. I read all 10 markdown files plus inspected the archive. Below is the ordered punch-list (most severe first), format `[fichier] · problème · correctif`.

---

## PUNCH-LIST — incohérences vérifiées

### 🔴 GRAVE — collisions de numéro Σ (le cœur de la demande)

**1. [05-DURCISSEMENT-REDTEAM.md ↔ 06-CONTRATS-RUNTIME-V2.md] · Collision dure Σ.7 et Σ.8 — même numéro, sens différents.**
- `05` définit : **Σ.7 = Provenance & quarantaine** (A0+, ligne 19) · **Σ.8 = Policy déterministe hors-LLM + least-privilege dégradé** (A5+, ligne 34).
- `06 §9.7` (liste "Σ v2 consolidé", ligne 104) réassigne : **Σ.7 = pureté canaux / secrets 0600** · **Σ.8 = codes fermés / identity least-agency**.
- Un lecteur qui consolide les invariants obtient deux définitions contradictoires pour Σ.7 et Σ.8. La provenance de `05` réapparaît en plus sous `06 Σ.11` ("provenance+non-escalade publish") → **doublon sémantique** ; et l'invariant A5+ de `05` (∂autorise/∂force_modèle = 0, dégradé ⊆ normal) **n'a aucun slot** dans la liste de `06`.
- **Correctif — renumérotation unique (préserver 05, décaler 06)** : `05` a publié Σ.7/Σ.8 en premier et porte une doctrine distincte (A0+/A5+) → les garder canoniques. Décaler tous les invariants runtime de `06` de +2 :

  | Concept | Ancien (06) | Nouveau |
  |---|---|---|
  | Provenance & quarantaine (A0+) | — | **Σ.7** (de 05, fusionner avec l'actuel Σ.11 provenance) |
  | Policy déterministe / dégradé monotone (A5+) | — | **Σ.8** (de 05) |
  | pureté ca