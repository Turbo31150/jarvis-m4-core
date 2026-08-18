#!/usr/bin/env python3
"""Dispatcher deporte : sort la file de taches de jarvis_master.db et fait
machouiller les noeuds distants (M6 RJ45, M1 Tailscale). Le M4 ne fait que
piloter des sockets — zero inference locale, zero chaleur, zero token facture.
"""

import json
import sqlite3
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

DB = "/home/pamerys/jarvis/jarvis_master.db"

# Seuls les noeuds dont l'inference a ete verifiee au smoke test.
NOEUDS = [
    {
        "nom": "M6",
        "url": "http://10.42.0.230:1234/v1/chat/completions",
        "modele": "qwen/qwen3.5-9b",
        "api": "openai",
        "poids": 3,
    },
    {
        "nom": "M1-TS",
        "url": "http://100.112.114.32:11434/api/chat",
        "modele": "qwen2.5:1.5b",
        "api": "ollama",
        "poids": 1,
    },
]

GABARIT = (
    "Tu es un ingenieur JARVIS. Voici une tache du backlog :\n\n{titre}\n\n"
    "Reponds en francais, en 4 lignes maximum :\n"
    "1. Ce qu'il faut faire concretement\n"
    "2. Le fichier ou la commande a toucher\n"
    "3. Le risque principal\n"
    "4. Duree estimee\n"
    "Pas de preambule."
)


def interroger(noeud, invite, timeout=120):
    """Envoie l'invite au noeud et retourne le texte. Leve en cas d'echec."""
    if noeud["api"] == "openai":
        charge = {
            "model": noeud["modele"],
            "messages": [{"role": "user", "content": invite}],
            "max_tokens": 900,
            "temperature": 0.2,
        }
    else:
        charge = {
            "model": noeud["modele"],
            "messages": [{"role": "user", "content": invite}],
            "stream": False,
        }
    requete = urllib.request.Request(
        noeud["url"],
        data=json.dumps(charge).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(requete, timeout=timeout) as reponse:
        donnees = json.loads(reponse.read())
    if noeud["api"] == "openai":
        return donnees["choices"][0]["message"]["content"].strip()
    return donnees["message"]["content"].strip()


def traiter(tache, noeud):
    ident, titre = tache
    depart = time.time()
    try:
        texte = interroger(noeud, GABARIT.format(titre=titre))
        return {
            "id": ident,
            "titre": titre,
            "noeud": noeud["nom"],
            "sortie": texte,
            "secondes": round(time.time() - depart, 1),
            "ok": bool(texte),
        }
    except Exception as souci:
        return {
            "id": ident,
            "titre": titre,
            "noeud": noeud["nom"],
            "sortie": f"ECHEC: {type(souci).__name__}: {souci}",
            "secondes": round(time.time() - depart, 1),
            "ok": False,
        }


def main():
    lot = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    equipe = sys.argv[2] if len(sys.argv) > 2 else None

    base = sqlite3.connect(DB)
    requete = (
        "SELECT id, title FROM tasks WHERE status='pending' "
        "AND title NOT LIKE '[note]%'"
    )
    parametres = []
    if equipe:
        requete += " AND agent=?"
        parametres.append(equipe)
    requete += " ORDER BY id LIMIT ?"
    parametres.append(lot)
    taches = base.execute(requete, parametres).fetchall()
    if not taches:
        print("File vide — rien a deporter.")
        return

    # Repartition ponderee : M6 est 3x plus rapide, il prend 3 colis sur 4.
    tournee = []
    roue = [n for n in NOEUDS for _ in range(n["poids"])]
    for rang, tache in enumerate(taches):
        tournee.append((tache, roue[rang % len(roue)]))

    print(f"Deport de {len(taches)} taches sur {len(NOEUDS)} noeuds distants.")
    resultats = []
    with ThreadPoolExecutor(max_workers=4) as reservoir:
        travaux = {reservoir.submit(traiter, t, n): t for t, n in tournee}
        for travail in as_completed(travaux):
            issue = travail.result()
            resultats.append(issue)
            marque = "OK " if issue["ok"] else "KO "
            print(
                f"  {marque}[{issue['noeud']:6}] {issue['secondes']:5.1f}s  "
                f"#{issue['id']} {issue['titre'][:58]}"
            )

    # Persistance : la sortie du noeud rejoint la tache, statut a valider.
    for issue in resultats:
        if issue["ok"]:
            base.execute(
                "UPDATE tasks SET status='to_validate', machine=?, "
                "context=?, updated_at=datetime('now') WHERE id=?",
                (issue["noeud"], issue["sortie"][:4000], issue["id"]),
            )
    base.commit()

    reussies = sum(1 for r in resultats if r["ok"])
    print(f"\n{reussies}/{len(resultats)} traitees et rangees en to_validate.")
    for noeud in NOEUDS:
        siennes = [r for r in resultats if r["noeud"] == noeud["nom"]]
        if siennes:
            moyenne = sum(r["secondes"] for r in siennes) / len(siennes)
            bonnes = sum(1 for r in siennes if r["ok"])
            print(
                f"  {noeud['nom']:6} {bonnes}/{len(siennes)} — "
                f"{moyenne:.1f}s de moyenne"
            )


if __name__ == "__main__":
    main()
