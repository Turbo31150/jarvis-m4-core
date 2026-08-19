#!/usr/bin/env python3
# candidatures_freework.py — une candidature par mission, ancree sur SA description.
#
# REGLE ABSOLUE : les seuls faits enonçables sur Franck sont ceux de FAITS ci-dessous,
# tous verifies. Aucune reference client, aucun chiffre non fourni, aucune promesse
# de resultat. Si la mission demande une competence que Franck n a pas, la candidature
# DOIT le dire — un recruteur qui decouvre l ecart en entretien ne rappelle pas.
#
# N ENVOIE RIEN. Ecrit en base et sur disque, pour relecture puis copie manuelle.

import json, re, sqlite3, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

DB  = "/home/pamerys/jarvis/jarvis_master.db"
M6  = "http://10.42.0.230:1234/v1/completions"
OUT = "/home/pamerys/jarvis/campagnes/candidatures-freework-20260819"

FAITS = """- architecte IA independant, base a Toulouse, disponible en freelance
- n8n auto-heberge, avec des workflows en production sur son propre serveur
- modeles de langage executes en local sur GPU (LM Studio, Ollama), sans cloud
- bases documentaires interrogeables en local (recherche plein texte + vecteurs)
- parc personnel : 2 machines, 5 GPU, dont une station 4 GPU
- l EU AI Act est en phase d application stricte depuis le 1er aout 2026"""

INTERDITS = """INTERDITS ABSOLUS — la candidature est rejetee sinon :
- AUCUNE reference client, AUCUN projet passe, AUCUN nom d entreprise : il n en est pas fourni
- AUCUN chiffre invente (annees d experience, %, euros, taille d equipe, nombre de projets)
- AUCUNE promesse de resultat
- premiere personne, jamais de troisieme personne
- pas de formule creuse ("je me permets", "n hesitez pas", "fort de mon experience")
- pas d emoji"""

def modele():
    try:
        with urllib.request.urlopen("http://10.42.0.230:1234/v1/models", timeout=8) as r:
            ids = [m["id"] for m in json.load(r).get("data", []) if "embed" not in m["id"]]
        for pref in ("qwen3.5-9b", "qwen3-4b"):
            for i in ids:
                if pref in i: return i
        return ids[0] if ids else None
    except Exception:
        return None

def generer(prompt, mod, max_tokens=520):
    corps = {"model": mod,
             "prompt": f"<|im_start|>user\n{prompt}<|im_end|>\n"
                       f"<|im_start|>assistant\n<think></think>\n\n",
             "max_tokens": max_tokens, "temperature": 0.4, "stop": ["<|im_end|>"]}
    req = urllib.request.Request(M6, data=json.dumps(corps).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        t = ((json.load(r).get("choices") or [{}])[0].get("text") or "").strip()
    for m in ("</think>", "<think></think>", "<think>"):
        if t.startswith(m): t = t[len(m):].strip()
    return t

# ── FILTRE DETERMINISTE POST-GENERATION ──────────────────────────────────────
# Une interdiction dans le prompt NE SUFFIT PAS. Mesure du 19/08 : sur 24
# candidatures generees avec un "INTERDITS ABSOLUS" explicite, 8 (33 %) citaient
# une competence jamais fournie. Le modele lit "n8n" et "automatisation" dans une
# offre Ansible/Oracle et produit "maitrise des playbooks Ansible pour bases RAC,
# Dataguard, RMAN". Il n invente pas au hasard : il EXTRAPOLE une competence
# adjacente, ce qu aucune consigne ne bloque de maniere fiable.
#
# La parade est structurelle : apres generation, on cherche dans le texte tout
# terme technique absent des faits autorises. S il y en a un, le texte est REJETE
# et regenere avec ce terme nomme explicitement comme interdit. Deterministe,
# verifiable, sans inference.

VOCABULAIRE_INTERDIT = [
    # entrainement / adaptation de modeles — Franck ne le fait pas
    "lora", "qlora", "peft", "fine-tuning", "finetuning", "entrainer", "entraîner",
    "aligner", "alignement", "rlhf", "distillation",
    # modeles nommes — aucun n est dans les faits
    "llama", "mistral", "gemma", "falcon", "gpt-4", "claude 3",
    # infra et outils jamais mentionnes
    "ansible", "terraform", "kubernetes", "k8s", "openshift", "helm",
    "airflow", "databricks", "snowflake", "sagemaker", "vertex ai", "bedrock",
    "langchain", "llamaindex", "haystack", "mlflow", "kubeflow",
    "oracle", "rac", "dataguard", "rman", "talend", "tibco", "sap", "abap",
    "power platform", "sharepoint", "salesforce", "cloudera",
    # promesses chiffrees
    "ans d experience", "ans d'expérience", "années d expérience",
]

# Les termes sont cherches avec des LIMITES DE MOT. Sans cela "rman" matche dans
# "perfoRMANce", "rac" dans "caRACtere", "sap" dans "diSPArite" : premier essai du
# 19/08, 22 rejets sur 24 dont une majorite de faux positifs. Un filtre qui rejette
# tout ne vaut pas mieux qu un filtre qui ne rejette rien.
_MOTS_INTERDITS = re.compile(
    r"(?<![a-zà-ÿ])(" + "|".join(
        re.escape(v).replace(r"\ ", r"[ -]") for v in VOCABULAIRE_INTERDIT
    ) + r")(?![a-zà-ÿ])", re.I)

# NOMMER une techno n est pas mentir ; SE L ATTRIBUER l est.
#   « votre mission exige Ansible, que je ne pratique pas »  -> correct, et demande
#   « mon expertise en playbooks Ansible »                   -> mensonge
# On ne cherche donc le terme interdit que dans une fenetre PRECEDEE d une marque
# d appropriation, et on annule si une negation apparait juste avant.
_APPROPRIATION = re.compile(
    r"(?:je\s+(?:maitrise|maîtrise|pratique|connais|utilise|deploie|déploie|conçois|"
    r"concois|realise|réalise|gere|gère|exploite)|"
    r"m(?:on|es|a)\s+(?:expertise|experience|expérience|maitrise|maîtrise|pratique|"
    r"competence|compétence|stack|parc|infrastructure)|"
    r"j(?:e\s+suis|ai)\s|"
    r"expert\s+(?:en|sur)|specialise|spécialisé|rompu\s+a)", re.I)
_NEGATION = re.compile(
    r"(?:ne\s+(?:pratique|maitrise|maîtrise|connais|utilise)\s+pas|"
    r"pas\s+d(?:e|')\s*(?:experience|expérience|pratique)|"
    r"absent[e]?\s+de|non\s+couvert|que\s+je\s+ne)", re.I)

def contamination(texte, fenetre=140):
    """Termes interdits que le texte S ATTRIBUE. Une simple mention ne compte pas."""
    t = texte or ""
    out = set()
    for m in _MOTS_INTERDITS.finditer(t):
        deb = max(0, m.start() - fenetre)
        avant = t[deb:m.start()]
        if not _APPROPRIATION.search(avant):
            continue                      # terme seulement mentionne : acceptable
        if _NEGATION.search(t[deb:m.end() + 60]):
            continue                      # explicitement nie : acceptable, et souhaite
        out.add(m.group(1).lower())
    return sorted(out)

def prompt_pour(m):
    tjm = f"{m['tjm_min']}-{m['tjm_max']} EUR/jour" if m["tjm_min"] else "non affiche"
    return f"""Redige une candidature pour cette mission freelance, en francais.

LA MISSION (seule source autorisee a son sujet) :
Intitule : {m['titre']}
Lieu     : {m['ville']} {m['region']}
TJM      : {tjm}
Client   : {m['client'] or '(non precise)'}
Description : {(m['description'] or '')[:1800]}

CE QUE JE PEUX DIRE DE MOI (seuls faits autorises, rien d autre) :
{FAITS}

{INTERDITS}

STRUCTURE :
1. Une phrase qui reprend le besoin CENTRAL de la mission, tel qu il est ecrit.
2. Deux ou trois points precis reliant CE besoin a ce que je fais reellement.
3. **Si la mission exige une technologie absente de mes faits** (par exemple un cloud
   precis, un ERP, un outil proprietaire), DIS-LE franchement en une phrase, sans
   t excuser, et precise ce qui reste transferable.
4. Une phrase de disponibilite.

160 mots MAXIMUM. Reponds uniquement par la candidature."""

def main():
    limite = 0
    for a in sys.argv:
        if a.startswith("--limit="): limite = int(a.split("=")[1])
    mod = modele()
    if not mod:
        print("M6 injoignable — aucune generation"); return 2
    print(f"modele : {mod}")

    import os; os.makedirs(OUT, exist_ok=True)
    c = sqlite3.connect(DB, timeout=60); c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE IF NOT EXISTS candidatures_freework (
        url TEXT PRIMARY KEY, titre TEXT, ville TEXT, tjm TEXT, valide_jusqu TEXT,
        texte TEXT, n_mots INTEGER, genere_le TEXT, statut TEXT DEFAULT 'A_RELIRE')""")
    q = """SELECT * FROM freework_missions
           WHERE (LOWER(ville) LIKE '%toulouse%' OR LOWER(region) LIKE '%occitanie%'
                  OR LOWER(ville) LIKE '%montpellier%' OR LOWER(ville) LIKE '%haute-garonne%')
             AND (valide_jusqu='' OR valide_jusqu >= date('now'))
           ORDER BY CAST(NULLIF(tjm_max,'') AS INT) DESC"""
    missions = [dict(r) for r in c.execute(q)]
    faits = {r[0] for r in c.execute("SELECT url FROM candidatures_freework WHERE texte<>''")}
    todo = [m for m in missions if m["url"] not in faits]
    if limite: todo = todo[:limite]
    print(f"{len(missions)} mission(s) Occitanie valides · {len(todo)} a rediger\n")
    c.close()

    lock = __import__("threading").Lock()
    n = [0]
    def worker(m):
        mauvais = []
        for essai in range(4):
            try:
                sup = ""
                if essai > 0 and mauvais:
                    sup = ("\n\nATTENTION — ta version precedente citait ces termes que tu "
                           "N AS PAS LE DROIT d employer, car ils ne figurent NULLE PART dans "
                           "les faits fournis : " + ", ".join(mauvais) + ". "
                           "Ne les mentionne sous AUCUNE forme. Si la mission les exige, "
                           "ecris simplement que tu ne les pratiques pas.")
                t = generer(prompt_pour(m) + sup, mod)
                if not t or len(t) < 80:
                    raise RuntimeError("trop court")
                mauvais = contamination(t)
                if mauvais:
                    raise RuntimeError("contamination: " + ",".join(mauvais))
                cc = sqlite3.connect(DB, timeout=60)
                cc.execute("""INSERT INTO candidatures_freework
                    (url,titre,ville,tjm,valide_jusqu,texte,n_mots,genere_le,statut)
                    VALUES (?,?,?,?,?,?,?,datetime('now'),'A_RELIRE')
                    ON CONFLICT(url) DO UPDATE SET texte=excluded.texte,
                      n_mots=excluded.n_mots, genere_le=excluded.genere_le""",
                    (m["url"], m["titre"], m["ville"],
                     f"{m['tjm_min']}-{m['tjm_max']}" if m["tjm_min"] else "",
                     m["valide_jusqu"], t, len(t.split())))
                cc.commit(); cc.close()
                with lock:
                    n[0] += 1
                    print(f"  [{n[0]}/{len(todo)}] {len(t.split()):>3} mots · {m['titre'][:52]}")
                return True
            except Exception as e:
                if essai == 3:
                    with lock:
                        print(f"  ABANDON {m['titre'][:40]} apres 4 essais : {e}")
                time.sleep(4)
        return False

    with ThreadPoolExecutor(max_workers=4) as ex:
        list(as_completed([ex.submit(worker, m) for m in todo]))

    # export lisible
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    rows = c.execute("SELECT * FROM candidatures_freework ORDER BY valide_jusqu").fetchall()
    p = f"{OUT}/CANDIDATURES.md"
    with open(p, "w", encoding="utf-8") as f:
        f.write("# Candidatures FreeWork — Occitanie\n\n")
        f.write(f"Generees le {datetime.now():%d/%m/%Y a %H:%M} · {len(rows)} missions\n\n")
        f.write("> AUCUNE n a ete envoyee. Aucun compte FreeWork n est connecte.\n")
        f.write("> A relire, puis a coller manuellement sur chaque annonce.\n\n---\n\n")
        for r in rows:
            f.write(f"## {r['titre']}\n\n")
            f.write(f"- **Lieu** : {r['ville']}  ·  **TJM** : {r['tjm'] or 'non affiche'}"
                    f"  ·  **valide jusqu au** : {r['valide_jusqu']}\n")
            f.write(f"- {r['url']}\n\n{r['texte']}\n\n---\n\n")
    c.close()
    print(f"\n{len(rows)} candidature(s) en base · export : {p}")

if __name__ == "__main__":
    sys.exit(main() or 0)
