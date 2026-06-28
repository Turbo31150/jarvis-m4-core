#!/usr/bin/env bash
# BDQT — reconstruction complète de la base qualité-transcription.
# Re-runnable : sert aussi de boucle d'apprentissage (réimporte les nouvelles
# voice_corrections produites par les miners/learners dans ~/jarvis.db).
# Usage: bdqt_rebuild.sh [--enrich]   (--enrich = vocabulaire école via sql-first, 0 token)
set -uo pipefail
cd "$(dirname "$0")"
echo "== [1/4] schema =="          ; python3 bdqt_core.py
echo "== [2/4] import corrections ==" ; python3 bdqt_import_corrections.py
echo "== [3/4] build lexicon =="     ; python3 bdqt_build_lexicon.py "$@"
echo "== [4/4] gen prompt =="        ; python3 bdqt_gen_prompt.py
echo "== stats =="
python3 - <<'PY'
import sqlite3, os
c = sqlite3.connect(os.path.expanduser("~/IA/Core/jarvis/db/transcription_quality.db"))
for t in ("corrections", "lexicon", "prompt_snippets", "transcription_log"):
    n = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  {t:18} {n}")
PY
echo "Pense à redémarrer le serveur pour recharger prompt/hotwords :"
echo "  systemctl --user restart jarvis-whisper"
