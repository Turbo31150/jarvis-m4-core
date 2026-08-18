#!/usr/bin/env python3
"""Banc de test transcription : TTS -> Whisper :8789 -> compare à l'attendu.
Mesure précision mot-à-mot, liste les écarts, propose des corrections candidates.
NB: la voix TTS n'est pas la vraie voix → certains écarts sont des artefacts TTS.
"""

import base64
import json
import subprocess
import urllib.request
import re
import os

VOICE = os.path.expanduser("~/jarvis/models/piper/fr_FR-siwis-medium.onnx")
URL = "http://127.0.0.1:8789/"

PHRASES = [
    # école
    "Je prépare ma séquence de calcul mental pour mes élèves de CE2.",
    "Les enfants travaillent la lecture et la compréhension ce matin.",
    "Je dois corriger les cahiers avant le conseil d'école de jeudi.",
    "Mon élève bénéficie d'une AESH et d'un dossier à la MDPH.",
    "La séance d'éducation musicale commence après la récréation.",
    # mairie / admin
    "Je remplis le CERFA pour la déclaration préalable de travaux.",
    "Le permis de construire est en cours d'instruction à l'urbanisme.",
    "J'envoie un courrier au Trésor public concernant la facture.",
    # civique
    "J'écris à la députée de notre circonscription au sujet de l'école.",
    "Le dossier sera transmis à la préfecture et au rectorat.",
    # perso / appris
    "Envoie le message à mon mail pro puis à mail franck.",
    "Nous habitons à Montlaur près de Saint Orens de Gameville.",
    "Madame Domingues prépare la réunion à Labège.",
    # courant
    "Aujourd'hui je vais au marché acheter du pain et des légumes.",
    "Le rendez-vous chez le médecin est prévu jeudi après-midi.",
    "Mon fils a oublié son cartable à la maison ce matin.",
]


def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", s.lower())).strip()


def wer(ref, hyp):
    r, h = norm(ref).split(), norm(hyp).split()
    # distance d'édition mots
    dp = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, len(h) + 1):
            cur = dp[j]
            dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + (r[i - 1] != h[j - 1]))
            prev = cur
    return dp[len(h)], len(r)


def transcribe(wav):
    raw = open(wav, "rb").read()
    body = json.dumps(
        {"audio": base64.b64encode(raw).decode(), "format": "wav", "language": "fr"}
    ).encode()
    req = urllib.request.Request(
        URL, data=body, headers={"Content-Type": "application/json"}
    )
    return json.loads(urllib.request.urlopen(req, timeout=90).read()).get("text", "")


def main():
    tot_err = tot_words = 0
    fails = []
    for i, p in enumerate(PHRASES):
        subprocess.run(
            ["piper", "-m", VOICE, "-f", f"/tmp/b{i}.wav"],
            input=p.encode(),
            stderr=subprocess.DEVNULL,
        )
        out = transcribe(f"/tmp/b{i}.wav")
        e, n = wer(p, out)
        tot_err += e
        tot_words += n
        mark = "OK " if e == 0 else f"{e}/{n}"
        print(f"[{mark}] {p}")
        if e:
            print(f"        => {out!r}")
            fails.append((p, out))
    acc = 100 * (1 - tot_err / max(tot_words, 1))
    print(
        f"\n=== PRÉCISION GLOBALE: {acc:.1f}%  ({tot_err} erreurs / {tot_words} mots) ==="
    )
    print(f"=== {len(PHRASES) - len(fails)}/{len(PHRASES)} phrases parfaites ===")


if __name__ == "__main__":
    main()
