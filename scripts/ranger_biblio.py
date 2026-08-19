#!/usr/bin/env python3
# ranger_biblio.py — range les enseignements de la session dans la Bibliotheque Vivante.
#
# Un enseignement = un bloc, dans SON domaine, avec son embedding (M6, 768d).
# Regle de la maison : tout chiffre porte sa date, sinon il se perime en silence.
#
# Idempotent : l id du bloc derive du sha256 de son texte, donc relancer ne cree
# pas de doublon. Les sources portent un id stable prefixe "s_sess20260819_".

import hashlib, json, sqlite3, sys, urllib.request
from datetime import datetime

BOARD = "/home/pamerys/jarvis/board/board.db"
M6    = "http://10.42.0.230:1234/v1/embeddings"
MOD   = "text-embedding-nomic-embed-text-v1.5"
DATE  = "2026-08-19"

# (domaine, titre, texte)
FICHES = [
("fiabilite-exploitation", "Le faux succes : un code retour 0 ne prouve rien",
f"""# Le faux succes — mesures du {DATE}

Cinq occurrences du meme defaut ont ete relevees en une seule session. Toutes
partagent la signature : code de retour 0, sortie non vide, resultat sans rapport
avec la realite. Aucune ne levait d erreur.

1. `lm-ask.sh --big` — le drapeau n etait pas parse et partait dans le prompt. Le
   modele repondait litteralement a la chaine « --big ... ».
2. Preambule d un skill dont chaque commande finit par `|| echo "<defaut>"`. Toutes
   « reussissaient » en fabriquant des valeurs (`PROACTIVE=true`, `REPO_MODE=unknown`).
   Le workflow entier aurait pu se derouler sur un profil inexistant.
3. Flux RSS Google Trends : le meme `<link>` sur ses 10 items. Hacher l URL seule
   faisait s ecraser 9 signaux sur 10 dans un `ON CONFLICT`. 10 vus, 1 en base.
4. Deadlock `threading.Lock` : 7 threads vivants, processus a l etat S, aucune
   exception, aucun log. Le job avait l air de travailler pendant qu il ne faisait rien.
5. `| tail -24` sur un job de fond : la sortie paraissait vide parce que `tail`
   retient tout jusqu a la fin du pipe.

ENSEIGNEMENT : ce qui prouve, c est une valeur qu on peut recompter. Pas un exit code,
pas une sortie non vide, pas l absence d erreur."""),

("fiabilite-exploitation", "Le home fantome : des outils portes qui se taisent",
f"""# Le home fantome — mesures du {DATE}

Des outils portes d une machine a l autre gardent les chemins de leur machine
d origine et echouent sans bruit.

MESURES :
- `skillmp_cascade_taches` : 898 blocs de prechargement pointent vers `/home/turbo/...`
  (le home de M6). **898 sur 898 sont absents** sur M4. Le « contexte precharge »
  affiche par la cascade etait donc entierement fictif.
- `~/jarvis/bin/cascade-massive.sh` : reference comme point d entree par un skill,
  **inexistant sur disque**. Toute la chaine plan → file etait rompue, en silence.
- 26 skills invocables dependent d un runtime `gstack` **introuvable sur tout le disque**
  (12/12 binaires absents). Leurs preambules sortent en exit 0.
- Un autre skill : 9 copies installees, **toutes avec `scripts/` et `templates/` vides**.
  Ses 5 hooks declares pointent vers des fichiers absents et sortent en exit 0.
- SKILL.md du parc : 101 chemins `~/jarvis/...` existants contre 36 absents (74 % valides).

ENSEIGNEMENT : avant de faire confiance a un outil porte, verifier que les chemins
qu il cite existent SUR CETTE MACHINE. `[ -f ]` coute moins cher qu un diagnostic."""),

("inference-locale", "Reasoning-runaway : les modeles qwen3 laissent content vide",
f"""# Reasoning-runaway sur qwen3 / qwen3.5 — mesures du {DATE}

Sur `/v1/chat/completions`, les modeles a raisonnement rangent tout dans
`reasoning_content` et laissent `content` **vide**. Mesure sur qwen3-4b :
**0 caractere de contenu contre 677 de raisonnement**.

CE QUI NE MARCHE PAS : augmenter `max_tokens`. Un script du parc etait monte a 2500
« pour laisser finir le raisonnement » — le content restait vide. Le budget n est pas
le probleme : le modele n emet simplement jamais sa conclusion sur cet endpoint.

CE QUI MARCHE : `/v1/completions` avec `<think></think>` **pre-ferme** dans le prompt.
Le modele n a plus de phase de raisonnement a remplir et repond directement.
Verifie sur qwen3-4b ET qwen3.5-9b.

IMPACT MESURE sur le parc :
- 94 fichiers appellent `chat/completions`, **33 actifs sans aucune parade**.
- `jarvis-table-ronde` : TOUS les tours servaient du raisonnement brut etiquete.
- `multi-llm-orchestrate.py` : le backend au **poids le plus lourd (1.5)** rendait une
  chaine vide, le vote se calculait sans lui. Verdict FAIBLE 0,538 → **FORT 1.0** apres correction.
- Le cockpit :8899 rendait `{{ok:true, reply:""}}` — un faux succes parfait.

Note : qwen3-4b reemet parfois `</think>` en tete malgre la parade. A retirer."""),

("inference-locale", "Debit M6 selon le parallelisme, et pourquoi Ollama serialise",
f"""# Debit mesure du parc LLM — {DATE}

EMBEDDINGS sur M6 (LM Studio, 4 GPU, cable direct 10.42.0.230, RTT 1,4 ms) :
- 1 worker : 1,6/s
- 6 workers : 7,5/s
- 12 workers : 7,2/s
- **24 workers : 34,3/s**

M6 encaisse le parallelisme. **Ollama local, non** : 6 appels paralleles prennent
5,3 s CHACUN — il serialise. Augmenter les workers face a Ollama n apporte rien.

GENERATION : qwen3-4b repond en **2,7 s** la ou qwen3.5-9b, charge a 32768 de contexte,
prend des dizaines de secondes pour un resultat equivalent sur des reponses courtes.

CONSEQUENCE OPERATIONNELLE : 1 427 signaux vectorises en **2 min 32** a 24 workers,
M4 a 56 C. Le meme travail sur Ollama CPU local avait fait monter le M4 a **94 C**.
Une boucle sequentielle laissait les 4 GPU de M6 a **0-1 % d utilisation** : le goulot
n etait pas le materiel, c etait la boucle."""),

("rag-retrieval", "Appariement : le recouvrement lexical bat bm25",
f"""# Apparier une tache a un outil — mesures du {DATE}

CONSTAT : **bm25 ne discrimine pas** sur ce corpus. Sur 400 titres tires au hasard,
un score de -21,57 donnait un appariement faux (`/content-perf-harvester` pour une
tache d embeddings) tandis que -16,77 en donnait un juste. Le score seul est inutilisable.

CE QUI DISCRIMINE : le recouvrement lexical **pondere par emplacement** —
un mot dans le slug vaut 3, dans le nom 2, dans la description 1.

Deux filtres indispensables :
- **mots de moins de 4 lettres ecartes** : `pre` appariait « Pre-remplissage » a « Pre-earnings ».
- **vocabulaire de structure ecarte** (`use`, `skill`, `triggers`, `when`, `user`...) :
  presque tous les SKILL.md contiennent « Triggers on mentions », donc ce mot appariait
  n importe quoi a n importe quoi.

RESULTAT : sur 12 792 taches, part avec un skill reellement apparie **0 → 91 %**,
longueur du contexte precharge 84 → 512 caracteres. Paliers de confiance calibres sur
500 titres : >=7 pts forte, 5-6 bonne, 3-4 indicative, <3 abstention.

PRINCIPE : mieux vaut une case vide qu un aiguillage faux. Un mauvais appariement
non signale coute plus cher a l agent qu une absence de suggestion."""),

("rag-retrieval", "Clustering : average-link, et le centrage par source",
f"""# Clusteriser des signaux heterogenes — mesures du {DATE}

**1. single-link CHAINE.** A seuil 0,60 sur 428 signaux, un seul cluster absorbait
**395 des 428**. A liaison A-B et B-C, A et C se retrouvent groupes sans rien de commun.
average-link (scipy) supprime l effet : meme seuil, plus gros cluster = 40.

**2. L embedding capture le SITE avant le SUJET.** A 428 signaux, **16 clusters sur 16
etaient mono-source**. La matrice de similarite le montre : freework 0,681 en interne
contre 0,393-0,481 vers les autres ; n8n-forum 0,569 contre 0,456-0,504. Un cluster
mono-source n est pas un signal de marche, c est un signal de site.
Correction : **centrer par source** (soustraire a chaque vecteur le centroide de sa
propre source, puis renormer). Ecart intra/inter **+0,110 → -0,011**. Zero inference.

**3. Le centrage ne cree pas de signal absent.** A 428 signaux les clusters
multi-sources obtenus se formaient sur du recouvrement lexical superficiel
(« consultant », « validation »). **Le volume etait le probleme** : a 1 855 signaux,
**50 %** de clusters multi-sources au seuil 0,147, et ils sont coherents a l inspection.

**4. Ne JAMAIS melanger deux modeles d embedding.** Ils placent le meme texte a des
endroits differents et **aucun chiffre du resultat ne le signalerait**. Le garde-fou
doit refuser et le dire : 428 vecteurs Ollama ecartes face a 1 427 vecteurs M6."""),

("vente-prospection", "Moissonner des signaux publics : ce qui repond et ce qui pollue",
f"""# Moisson multi-sources — mesures du {DATE}

ACCESSIBLE sans authentification (HTTP 200) : Hacker News API, GitHub search issues,
`community.n8n.io/latest.json`, Stack Overflow API, FreeWork, pages publiques LinkedIn.
BLOQUE (403) : Reddit `.json`, Indeed, Malt.
SANS VALEUR : Google Trends FR generaliste ne remonte que du divertissement.

**Le bruit qui se fait passer pour un signal.** Le cluster le mieux note de tout un
corpus — 13 membres, cohesion 0,914, **meilleur score de la table** — etait compose a
77 % de « Voir cette offre ». Une regex trop large capturait le texte des boutons.
Le clustering etait JUSTE (des textes identiques doivent etre a 0,91) et le modele a
repondu **4 fois INSUFFISANT** au lieu d inventer un besoin marche a partir de libelles
de navigation. **La metrique la plus flatteuse du run etait celle du bruit.**
Ampleur : 51 signaux pollues sur 257 (20 %), dont une source a 26/39 (67 %).

PARADES : filtre de qualite generique a l insertion, qui journalise ce qu il ecarte ;
extracteur cible sur le motif d URL des vraies offres uniquement.

VOLUME : la pagination fait passer de 428 a 1 855 signaux en 114 s. Le rate-limit
GitHub (10 req/min sans auth) doit declencher un **arret propre de la source** avec
conservation de ce qui est acquis, jamais une boucle de reessais."""),

("cluster-m1", "Pannes du parc : LM Studio apres reboot, navigateur fige, Wayland",
f"""# Pannes reelles du parc — {DATE}

**M6 : LM Studio ne se releve pas apres un redemarrage.** Symptome : ping 1,4 ms, SSH
et Ollama ouverts, moteur llama.cpp vivant, 4 GPU charges en VRAM — mais **rien
n ecoute sur 1234**. Le watchdog `lms-watchdog/agent.py` tourne et ne fait pas son
travail. `lms server start` par SSH ne rend pas la main en 90 s ; **lance en detache**
il finit par reveiller l application. Erreur possible ensuite : « Timed out waiting for
LM Studio daemon » quand la RAM de M6 est a 89 %.

**Navigateur fige apres plusieurs heures.** BrowserOS a 9 h 17 d uptime acceptait le
CDP et creait des onglets, mais aucune navigation n aboutissait. **Test qui tranche :
`example.com` echoue exactement comme le site vise** alors que l hote repond HTTP 200
en 0,107 s → la panne est dans le navigateur, pas dans le reseau ni dans le site.

**Redemarrer une application graphique sous Wayland.** `setsid nohup` la detache du
socket graphique : le processus tourne avec **0 renderer**, donc aucune fenetre, et ses
ports de service ne s ouvrent pas. Il faut preserver `DISPLAY`, `WAYLAND_DISPLAY` et
`XDG_RUNTIME_DIR`.

**CDP et Chrome >= 111.** Tout handshake WebSocket portant un header `Origin` est
refuse en 403. Corriger cote client (`suppress_origin`) plutot qu en relancant Chrome
avec `--remote-allow-origins`, qui affaiblirait sa protection pour toutes les pages.
Le parametre `?url=` de `PUT /json/new` peut etre ignore : naviguer explicitement
via `Page.navigate` et attendre `Page.loadEventFired`."""),

("orchestration-agents", "Thermique : pourquoi le repli CPU local doit etre interdit",
f"""# Incident thermique et politique de repli — {DATE}

FAITS : le backend GPU distant est tombe en cours de traitement. La cascade a
automatiquement bascule sur Ollama **CPU local**. Le poste de controle est passe de
**27 C a 94 C**.

Ce qui n a PAS marche : `renice` sur le processus d inference. Ollama **relance un
`llama-server` neuf a chaque requete**, la priorite abaissee ne survit pas.

Ce qui a marche : arreter le travail. 94 C → 61 C en une trentaine de secondes.

POLITIQUE RETENUE : le repli CPU local est **interdit par defaut**. Sans le backend
distant, on **s arrete et on le dit**, au lieu de cuire le poste de controle en silence.
Trois garde-fous : sonde du backend distant a l entree (arret si muet), controle
thermique dans la boucle (arret a 85 C avec conservation du travail), et variable
d environnement explicite pour lever la regle en connaissance de cause.

COROLLAIRE : rendre les traitements longs **reprenables**. Un `DELETE` en tete de
script rend tout arret coûteux — il faut sauter ce qui est deja fait et commiter au
fur et a mesure. Ici : 16 clusters sur 33 conserves malgre l arret d urgence."""),
]


def embed(texte):
    req = urllib.request.Request(M6, data=json.dumps({"model": MOD, "input": texte[:6000]}).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)["data"][0]["embedding"]


def main():
    from array import array
    c = sqlite3.connect(BOARD, timeout=60)
    c.execute("PRAGMA journal_mode=WAL")
    dom_ok = {r[0] for r in c.execute("SELECT id FROM domains")}
    n_src = n_chunk = n_saute = 0
    for domaine, titre, texte in FICHES:
        if domaine not in dom_ok:
            print(f"  domaine inconnu, ignore : {domaine}"); continue
        sha = hashlib.sha256(texte.encode()).hexdigest()
        sid = "s_sess20260819_" + sha[:16]
        cid = sid + "_0"
        if c.execute("SELECT 1 FROM chunks WHERE id=?", (cid,)).fetchone():
            n_saute += 1; continue
        c.execute("""INSERT INTO sources (id,domain_id,expert_id,kind,title,authors,year,
                     url,local_path,content_sha256,ingested_at)
                     VALUES (?,?,'','md',?,'JARVIS session',2026,'','',?,?)
                     ON CONFLICT(id) DO NOTHING""",
                  (sid, domaine, titre, sha, datetime.now().isoformat(timespec="seconds")))
        n_src += 1
        try:
            v = embed(texte); blob = array("f", v).tobytes(); dim = len(v)
        except Exception as e:
            print(f"  embedding indisponible ({type(e).__name__}) — bloc insere SANS vecteur")
            blob, dim = None, 0
        c.execute("""INSERT INTO chunks (id,source_id,domain_id,expert_id,chunk_idx,text,
                     token_count,embedding,embedding_dim,embedding_model)
                     VALUES (?,?,?,'',0,?,?,?,?,?)""",
                  (cid, sid, domaine, texte, len(texte)//4, blob, dim, MOD if dim else ""))
        n_chunk += 1
        print(f"  [{domaine:<24}] {titre[:58]}")
    c.commit()
    tot = c.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    c.close()
    print(f"\n  {n_chunk} bloc(s) ajoute(s), {n_src} source(s), {n_saute} deja present(s)")
    print(f"  bibliotheque : {tot} blocs")


if __name__ == "__main__":
    main()
