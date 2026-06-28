#!/usr/bin/env python3
"""Initialise/seed la bibliothèque de transcription (jarvis_lexicon.db).

Idempotent : relançable sans doublon (UPSERT sur (term, category)).
Délègue à lexicon.cmd_init().
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lexicon  # noqa: E402

if __name__ == "__main__":
    lexicon.cmd_init()
