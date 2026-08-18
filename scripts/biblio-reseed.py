#!/usr/bin/env python3
"""biblio-reseed.py — réamorce la todolist de la Bibliothèque Vivante (0-token, déterministe).
Insère un lot de sujets FRAIS (sujet × angle, rotation persistée) en `pending` dans
biblio_topics. Le daemon biblio_filler (déjà en boucle) les remplit ensuite tout seul.
Aucun LLM ici (pas de parsing fragile) : nouveauté garantie par la matrice + rotation.
Idempotent : INSERT OR IGNORE (contrainte UNIQUE kind,domain,topic).
"""

import sqlite3
import os

DB = os.path.expanduser("~/jarvis/jarvis_master.db")
STATE = os.path.expanduser("~/jarvis/data/.biblio_reseed_offset")
BATCH = 10

DOMAINS = {
    "IA locale & LLM": [
        "quantization GGUF",
        "RAG hybride",
        "speculative decoding",
        "KV cache",
        "MoE routing",
        "prompt caching",
        "batching continu",
        "distillation",
    ],
    "Voix & STT": [
        "Whisper turbo",
        "diarization",
        "VAD streaming",
        "TTS custom",
        "wake word",
        "latence sub-300ms",
        "multilingue",
    ],
    "Prospection B2B": [
        "deliverability",
        "warmup domaine",
        "scoring leads",
        "séquence multicanal",
        "LinkedIn outreach",
        "SPF DKIM DMARC",
        "bounce handling",
    ],
    "Sécurité & RGPD": [
        "chiffrement at-rest",
        "audit secrets",
        "hardening SSH",
        "DMARC reporting",
        "registre RGPD",
        "pare-feu nftables",
        "rotation clés",
    ],
    "Infra & cluster": [
        "systemd hardening",
        "GPU MIG",
        "Prometheus exporter",
        "btrfs snapshot",
        "WoL cluster",
        "backpressure",
        "watchdog",
    ],
    "Business & admin": [
        "Factur-X EN16931",
        "TVA seuils",
        "PDP facturation",
        "Stripe webhook",
        "auto-entrepreneur",
        "guichet unique INPI",
    ],
}
ANGLES = [
    "fonctionnement 2026",
    "pièges courants",
    "mise en œuvre pas à pas",
    "benchmark comparatif",
]


def flat():
    out = []
    for dom, subs in DOMAINS.items():
        for s in subs:
            for a in ANGLES:
                out.append((dom, f"{s} — {a}"))
    return out


def main():
    items = flat()
    off = 0
    try:
        off = int(open(STATE).read().strip())
    except Exception:
        pass
    batch = [items[(off + i) % len(items)] for i in range(BATCH)]
    # busy_timeout obligatoire : jarvis_master.db est écrite en continu par
    # biblio-filler, task-autogen et le hub. Sans lui, sqlite3 abandonne
    # IMMÉDIATEMENT en « database is locked » — c'est ce qui faisait échouer ce
    # service en boucle. 60 s et non 30 : mesuré ce jour, une lecture agrégée sur
    # ~490k lignes de `tasks` tient le verrou 40 à 60 s.
    c = sqlite3.connect(DB, timeout=60)
    c.execute("PRAGMA busy_timeout=60000")
    n = 0
    cur = c.cursor()
    for dom, topic in batch:
        cur.execute(
            "INSERT OR IGNORE INTO biblio_topics(kind,domain,topic,status,priority,source) "
            "VALUES('knowledge',?,?,'pending',6,'reseed')",
            (dom, topic),
        )
        n += cur.rowcount
    c.commit()
    open(STATE, "w").write(str((off + BATCH) % len(items)))
    pending = c.execute(
        "SELECT count(*) FROM biblio_topics WHERE status='pending'"
    ).fetchone()[0]
    print(
        f"reseed: +{n} nouveaux (offset {off}->{(off + BATCH) % len(items)}), pending={pending}"
    )


if __name__ == "__main__":
    main()
