#!/usr/bin/env python3
"""Étape 1 fine-tuning : extrait les enregistrements voix (colonne `audio` WAV)
de flow.sqlite History → fichiers .wav + manifeste JSONL {audio, text}.

Label = editedText (ta correction) > formattedText > asrText.
Sortie : ~/jarvis/voice_dataset/{wav/*.wav, manifest.jsonl}
Usage: bdqt_extract_audio.py [flow.sqlite]
"""

import json
import os
import shutil
import sqlite3
import sys
import tempfile

DEFAULT = "/mnt/windows/Users/clair/AppData/Roaming/Wispr Flow/flow.sqlite"
OUT = os.path.expanduser("~/jarvis/voice_dataset")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    os.makedirs(os.path.join(OUT, "wav"), exist_ok=True)
    tmp = tempfile.mktemp(suffix=".sqlite")
    shutil.copy(path, tmp)
    for e in ("-wal", "-shm"):
        if os.path.exists(path + e):
            shutil.copy(path + e, tmp + e)
    c = sqlite3.connect(tmp)
    c.row_factory = sqlite3.Row

    man = open(os.path.join(OUT, "manifest.jsonl"), "w", encoding="utf-8")
    n = skip = secs = 0
    for i, r in enumerate(
        c.execute(
            "SELECT rowid, asrText, formattedText, editedText, audio, duration, language "
            "FROM History WHERE audio IS NOT NULL AND length(audio)>1000"
        )
    ):
        text = (r["editedText"] or r["formattedText"] or r["asrText"] or "").strip()
        text = text.replace("\xa0", " ").replace("\n", " ").strip()
        if not text or len(text) < 2:
            skip += 1
            continue
        blob = r["audio"]
        if not (isinstance(blob, bytes) and blob[:4] == b"RIFF"):
            skip += 1
            continue
        fn = f"voice_{r['rowid']:05d}.wav"
        with open(os.path.join(OUT, "wav", fn), "wb") as f:
            f.write(blob)
        try:
            secs += float(r["duration"] or 0)
        except (TypeError, ValueError):
            pass
        man.write(
            json.dumps(
                {
                    "audio": f"wav/{fn}",
                    "text": text,
                    "lang": (r["language"] or "fr"),
                    "asr": (r["asrText"] or "")[:200],
                    "edited": bool(r["editedText"]),
                },
                ensure_ascii=False,
            )
            + "\n"
        )
        n += 1
    man.close()
    c.close()
    for f in (tmp, tmp + "-wal", tmp + "-shm"):
        try:
            os.remove(f)
        except OSError:
            pass
    print(f"[extract] {n} extraits, {skip} ignorés (sans texte/audio)")
    print(f"  durée totale ~{secs / 60:.1f} min de TA voix")
    print(f"  sortie: {OUT}/  (wav/ + manifest.jsonl)")
    print(
        f"  dont édités manuellement (labels les + fiables): "
        f"{sum(1 for line in open(os.path.join(OUT, 'manifest.jsonl')) if json.loads(line)['edited'])}"
    )


if __name__ == "__main__":
    main()
