#!/usr/bin/env python3
"""board3 — conseil à 3 modèles LM Studio M6 interrogés EN PARALLELE (0 token cloud).

    board3.py <fichier|-> [--models a,b,c]

Chaque modèle reçoit le même texte avec une consigne de rôle différente, puis on
agrège : verdict majoritaire + points sur lesquels ils divergent. Les modèles
tournent réellement en même temps (ThreadPool), pas l'un après l'autre.
"""
import json, sys, urllib.request, concurrent.futures as cf, time

# Un siège = (endpoint, modèle). Constaté le 19/08/2026 : LM Studio M6 LISTE 5
# modèles mais n'en a que 2 en state=loaded ; demander un modèle not-loaded
# rend 400 après un JIT-load de 88 s. On ne câble donc que du chargé, et on
# complète le 3e siège avec Ollama local pour avoir 3 voix réellement simultanées.
M6 = "http://10.42.0.230:1234/v1/chat/completions"
OL = "http://127.0.0.1:11434/v1/chat/completions"
DEFAUT = [(M6, "qwen3.5-9b"), (M6, "qwen2.5-coder-14b-instruct"), (OL, "qwen2.5:7b")]

ROLES = {
    0: ("SCEPTIQUE", "Tu cherches ce qui sonne faux, creux ou invérifiable. "
                     "Cite la phrase exacte qui pose problème. Sois bref et dur."),
    1: ("CLIENT", "Tu es dirigeant de PME française, non technique. Dis si ça te "
                  "donne envie de répondre, et ce que tu ne comprends pas."),
    2: ("TECHNICIEN", "Tu es ingénieur. Dis si les affirmations techniques tiennent "
                      "et ce qu'il manque comme preuve."),
}

def demande(i, siege, texte):
    endpoint, modele = siege
    role, consigne = ROLES[i]
    corps = json.dumps({
        "model": modele,
        "messages": [
            {"role": "system", "content": f"Tu es le siège {role} d'un conseil de relecture. {consigne} Réponds en français, 8 lignes maximum."},
            {"role": "user", "content": texte},
        ],
        # qwen3.5-9b est un modèle à raisonnement : il dépense le budget en
        # reasoning_content avant d'écrire. Trop bas = content vide, finish=length.
        "temperature": 0.3, "max_tokens": 2000,
    }).encode()
    t0 = time.time()
    try:
        req = urllib.request.Request(endpoint, data=corps, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as r:
            d = json.load(r)
        msg = d["choices"][0]["message"]
        contenu = (msg.get("content") or "").strip()
        if not contenu:
            raisonnement = (msg.get("reasoning_content") or "").strip()
            contenu = ("[content vide, finish=%s] repli sur le raisonnement : %s"
                       % (d["choices"][0].get("finish_reason"), raisonnement[:600])
                       if raisonnement else "[VIDE]")
        return {"role": role, "modele": modele, "ok": bool(contenu and contenu != "[VIDE]"),
                "ms": int((time.time()-t0)*1000), "texte": contenu}
    except Exception as e:
        return {"role": role, "modele": str(modele), "ok": False,
                "ms": int((time.time()-t0)*1000), "texte": f"[ECHEC] {e}"}

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "-"
    modeles = DEFAUT
    texte = sys.stdin.read() if src == "-" else open(src, encoding="utf-8").read()

    print(f"── Conseil M6 · {len(modeles)} modèles EN PARALLELE ──")
    for i, (ep, m) in enumerate(modeles):
        hote = "M6" if "10.42.0.230" in ep else "OL1"
        print(f"   siège {ROLES[i][0]:<10} → {m}  [{hote}]")
    t0 = time.time()
    with cf.ThreadPoolExecutor(max_workers=len(modeles)) as ex:
        res = list(ex.map(lambda a: demande(a[0], a[1], texte), enumerate(modeles)))
    total = int((time.time()-t0)*1000)

    somme = sum(r["ms"] for r in res)
    for r in res:
        print(f"\n{'='*60}\n## {r['role']} — {r['modele']}  ({r['ms']} ms)\n")
        print(r["texte"])
    print(f"\n{'='*60}")
    print(f"Mur : {total} ms · cumul séquentiel évité : {somme} ms "
          f"(gain {somme-total} ms). Réponses : {sum(r['ok'] for r in res)}/{len(res)}")

main()
