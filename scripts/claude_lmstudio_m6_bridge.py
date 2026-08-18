#!/usr/bin/env python3
"""
claude_lmstudio_m6_bridge.py — Câblage Haute Vitesse Claude Code ↔ Bibliothèque Vivante ↔ LM Studio M6
Rôle :
  - Déroute les requêtes d'inférence lourde de Claude Code vers LM Studio M6 (port 1234)
  - Injecte dynamiquement le contexte pertinent de la Bibliothèque Vivante (board.db - 47k chunks)
  - Assure le fallback transparent vers Ollama local si besoin
"""

import os
import sys
import json
import sqlite3
import urllib.request
import urllib.error
from pathlib import Path

BOARD_DB = Path.home() / "labo" / "remi-board-kit" / "board.db"
LMSTUDIO_URL = os.environ.get("LMSTUDIO_URL", "http://127.0.0.1:1234/v1/chat/completions")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434/api/chat")

def get_living_library_context(query: str, limit: int = 5) -> str:
    """Extrait les chunks les plus pertinents de board.db via FTS5."""
    if not BOARD_DB.exists():
        return ""
    try:
        with sqlite3.connect(BOARD_DB) as cx:
            # Recherche FTS5
            tokens = [t.strip() for t in query.split() if len(t.strip()) > 3][:4]
            if not tokens:
                return ""
            match_expr = " OR ".join(tokens)
            rows = cx.execute("""
                SELECT c.text, s.title, d.display_name
                FROM chunks_fts f
                JOIN chunks c ON f.rowid = c.id
                JOIN sources s ON c.source_id = s.id
                JOIN domains d ON c.domain_id = d.id
                WHERE chunks_fts MATCH ?
                LIMIT ?
            """, (match_expr, limit)).fetchall()
            
            if not rows:
                return ""
            
            context_blocks = []
            for text, title, domain in rows:
                context_blocks.append(f"[{domain} | {title}]\n{text[:400]}")
            return "\n\n---\n\n".join(context_blocks)
    except Exception as e:
        return f"(Erreur RAG: {e})"

def query_lmstudio_m6(prompt: str, system_prompt: str = "Tu es l'expert d'inférence M6 du Board JARVIS.") -> str:
    """Interroge LM Studio M6 avec injection RAG de la Bibliothèque Vivante."""
    context = get_living_library_context(prompt)
    full_system = f"{system_prompt}\n\n[CONTEXTE EXTRAIT DE LA BIBLIOTHÈQUE VIVANTE (47K CHUNKS)]:\n{context}" if context else system_prompt
    
    payload = {
        "model": "qwen3.5-9b",
        "messages": [
            {"role": "system", "content": full_system},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 2048
    }

    # 1. Tentative LM Studio
    try:
        req = urllib.request.Request(
            LMSTUDIO_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        # 2. Fallback transparent Ollama
        try:
            ollama_payload = {
                "model": "qwen3:1.7b",
                "messages": [
                    {"role": "system", "content": full_system},
                    {"role": "user", "content": prompt}
                ],
                "stream": False
            }
            req = urllib.request.Request(
                OLLAMA_URL,
                data=json.dumps(ollama_payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["message"]["content"]
        except Exception as e_ol:
            return f"Erreur Inférence (LM Studio: {e} | Ollama: {e_ol})"

def main():
    if len(sys.argv) < 2:
        print("Usage: claude_lmstudio_m6_bridge.py '<votre question/instruction>'")
        sys.exit(1)
    
    prompt = " ".join(sys.argv[1:])
    response = query_lmstudio_m6(prompt)
    print(response)

if __name__ == "__main__":
    main()
