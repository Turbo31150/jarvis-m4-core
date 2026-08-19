#!/usr/bin/env python3
"""routage_modeles — repartit une tache vers le modele qui lui convient. 0 token.

CE QUE LA MESURE DIT (M6, 19/08/2026, 4 GPU) :
  qwen3.5-9b seul, 4 paralleles          : 27,2 tok/s
  qwen2.5-coder-14b seul, 4 paralleles   : 24,6 tok/s
  LES DEUX ENSEMBLE, 8 paralleles        : 24,4 tok/s

Faire tourner deux modeles en meme temps N AUGMENTE PAS le debit : ils se partagent
les MEMES GPU. Le goulot est la capacite de calcul, pas le nombre de modeles.
En sequentiel les memes 945 tokens sortent a 25,8 tok/s — soit legerement mieux.

L interet du multi-modele n est donc PAS la vitesse, c est :
  1. la SPECIALISATION — envoyer chaque tache au modele fait pour elle
  2. la DIVERSITE — deux avis independants sur une meme question, quand l enjeu
     justifie de payer deux fois le temps de calcul

Ne pas confondre : lancer deux modeles pour "aller plus vite" est une fausse bonne
idee, mesuree comme telle.
"""

import json, re, sys, urllib.request

M6 = "http://10.42.0.230:1234"

# Chaque profil : (fragment du nom du modele, contexte max utile, ce pour quoi il est fait)
PROFILS = [
    ("coder",  8192,  "code, scripts, regex, SQL, configuration, debug"),
    ("qwen3.5", 32768, "redaction, synthese, analyse, texte long"),
    ("qwen3-4b", 8192, "reponses courtes et repetitives, classification, extraction"),
    ("gemma",    8192, "repli court quand le 4b n est pas charge"),
    ("deepseek", 8192, "raisonnement explicite, verification d une conclusion"),
]

# "classe" a ete RETIRE : ambigu entre "class" (code) et "classe ce message"
# (classification). Mesure du 19/08 : "Classe ce message en 1 mot" partait vers le
# modele code. Un mot ambigu dans une liste de mots-cles route a l envers en silence.
MOTS_CODE = ("code", "script", "python", "bash", "sql", "regex", "json", "yaml",
             "fonction", "bug", "erreur", "stacktrace", "compil",
             "refactor", "test unitaire", "endpoint", "def ", "import ")
MOTS_COURT = ("classe", "categorise", "extrais", "oui ou non", "liste", "un mot",
              "en 5 mots", "en 10 mots", "resume en une phrase")

def catalogue():
    """Modeles listes par l API. ATTENTION : liste le CATALOGUE, pas la memoire."""
    try:
        with urllib.request.urlopen(M6 + "/v1/models", timeout=8) as r:
            return [m["id"] for m in json.load(r).get("data", []) if "embed" not in m["id"]]
    except Exception:
        return []

def etat(mod, timeout=75):
    """Etat REEL d un modele. Trois valeurs, pas deux.

    LM Studio charge a la demande : un modele du catalogue absent de la memoire est
    charge au premier appel. Mesure du 19/08 sur M6 :
        coder-14b      0,5 s   -> deja en memoire
        qwen3.5-9b    24,3 s   -> charge a la demande
        deepseek-8b   55,9 s   -> charge a la demande
        gemma-4-26b   erreur   -> echoue vraiment (trop gros pour la RAM restante)
    Un seuil unique a 12 s classait donc les deux du milieu comme indisponibles.
    Retourne ("chaud"|"tiede"|"mort", secondes)."""
    import time as _t
    t0 = _t.time()
    try:
        body = {"model": mod, "prompt": "ok", "max_tokens": 1, "temperature": 0}
        req = urllib.request.Request(M6 + "/v1/completions", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=timeout).read()
        d = _t.time() - t0
        return ("chaud" if d < 3 else "tiede"), round(d, 1)
    except Exception:
        return "mort", round(_t.time() - t0, 1)

def _repond(mod, timeout=75):
    return etat(mod, timeout)[0] != "mort"

def disponibles(sonder=True, chauds_seulement=False):
    """Modeles reellement CHARGES.

    /v1/models liste le catalogue, pas la memoire : mesure du 19/08, qwen3.5-9b
    apparaissait dans /v1/models apres avoir ete decharge par expiration de son TTL.
    Un appel de generation partait alors en timeout de 280 s au lieu d echouer vite.
    On sonde donc chaque modele avec un appel d un token avant de s en servir."""
    cat = catalogue()
    if not sonder or not cat:
        return cat
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=min(6, len(cat))) as ex:
        etats = list(ex.map(lambda m: etat(m)[0], cat))
    ok = {"chaud"} if chauds_seulement else {"chaud", "tiede"}
    # les modeles deja chauds d abord : sur une tache courte, 24 s de chargement
    # coutent plus cher que la generation elle-meme
    return ([m for m, e in zip(cat, etats) if e == "chaud"] +
            ([m for m, e in zip(cat, etats) if e == "tiede"] if "tiede" in ok else []))

def choisir(tache, longueur_attendue=0):
    """Retourne (modele, raison). None si aucun modele n est servi."""
    dispo = disponibles()
    if not dispo:
        return None, "M6 ne sert aucun modele"
    t = (tache or "").lower()

    def trouve(frag):
        """Cherche le fragment avec une LIMITE a gauche.

        Sans cela "4b" matche dans "coder-14b-instruct" : deuxieme fois dans la
        meme session qu une recherche de sous-chaine route a l envers en silence
        (la premiere etait "rman" dans "performance"). Une recherche de fragment
        sans frontiere est un piege, pas un raccourci."""
        motif = re.compile(r"(?<![0-9a-z])" + re.escape(frag.lower()))
        return next((m for m in dispo if motif.search(m.lower())), None)

    # La brievete se teste AVANT le code : une consigne courte prime sur un mot-cle
    # technique isole, sinon "classe ce message" part vers le modele de code.
    if (longueur_attendue and longueur_attendue < 60) or any(k in t for k in MOTS_COURT):
        m = trouve("qwen3-4b") or trouve("gemma") or trouve("deepseek")
        if m: return m, "reponse courte -> petit modele, plus rapide a amorcer"
    if any(k in t for k in MOTS_CODE):
        m = trouve("coder")
        if m: return m, "tache de code -> modele specialise code"
    if False:
        m = trouve("qwen3-4b") or trouve("gemma") or trouve("deepseek")
        if m: return m, "reponse courte -> petit modele, plus rapide a amorcer"
    if len(t) > 4000:
        m = trouve("qwen3.5")
        if m: return m, "prompt long -> modele a grand contexte (32k)"
    m = trouve("qwen3.5") or dispo[0]
    return m, "par defaut -> modele generaliste"

def deux_avis(question, max_tokens=300):
    """Interroge DEUX modeles differents sur la meme question.

    A n utiliser que quand l enjeu justifie de payer deux fois le calcul : la mesure
    montre qu on ne gagne pas de temps, on gagne un second regard."""
    dispo = disponibles()
    if len(dispo) < 2:
        raise RuntimeError(
            f"il faut 2 modeles CHARGES, {len(dispo)} repond(ent) : {dispo}. "
            f"Catalogue annonce : {catalogue()}. Charger avec : lms load <modele>")
    from concurrent.futures import ThreadPoolExecutor
    def _un(mod):
        body = {"model": mod,
                "prompt": f"<|im_start|>user\n{question}<|im_end|>\n"
                          f"<|im_start|>assistant\n<think></think>\n\n",
                "max_tokens": max_tokens, "temperature": 0.4, "stop": ["<|im_end|>"]}
        req = urllib.request.Request(M6 + "/v1/completions",
                                     data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=280) as r:
            t = ((json.load(r).get("choices") or [{}])[0].get("text") or "").strip()
        for marq in ("</think>", "<think></think>"):
            if t.startswith(marq): t = t[len(marq):].strip()
        return mod, t
    with ThreadPoolExecutor(max_workers=2) as ex:
        return list(ex.map(_un, dispo[:2]))

if __name__ == "__main__":
    if "--avis" in sys.argv:
        q = " ".join(a for a in sys.argv[1:] if not a.startswith("--")) \
            or "Un TJM de 600 EUR/jour est-il defendable pour un freelance IA a Toulouse ?"
        for mod, t in deux_avis(q):
            print(f"\n── {mod} ──\n{t[:600]}")
    else:
        print("modeles servis :", disponibles(), "\n")
        for t in ("Ecris un script python qui lit un CSV",
                  "Classe ce message en 1 mot : urgent ou normal",
                  "Redige une synthese de marche en 400 mots",
                  "Corrige cette regex qui ne matche pas"):
            m, r = choisir(t)
            print(f"  {str(m):<30} {r:<52} <- {t[:40]}")
