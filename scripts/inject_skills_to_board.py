#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JARVIS OS — INJECTION MAÎTRESSE DES 2 143 SKILLS DANS BOARD.DB & FTS5
Lit skills_library.db et injecte chaque compétence/session comme source & chunks dans board.db
pour permettre l'accès instantané via 'jarvis-board ask'.
"""

import os
import sys
import sqlite3
import hashlib
import json
from datetime import datetime

SKILLS_DB_PATH = "/home/pamerys/Workspaces/jarvis-linux/skills-library/skills_library.db"
BOARD_DB_PATH = "/home/pamerys/jarvis/board/board.db"

def calculate_sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

def chunk_text(text: str, chunk_size: int = 1200) -> list:
    """Découpe le texte en morceaux de taille contrôlée."""
    chunks = []
    lines = text.split("\n")
    current_chunk = []
    current_length = 0

    for line in lines:
        if current_length + len(line) > chunk_size and current_chunk:
            chunks.append("\n".join(current_chunk))
            current_chunk = [line]
            current_length = len(line)
        else:
            current_chunk.append(line)
            current_length += len(line)

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks

def main():
    print("=== [INJECTION DES 2 143 SKILLS DANS BOARD.DB] Démarrage ===")
    
    if not os.path.exists(SKILLS_DB_PATH):
        print(f"[ERROR] Base skills_library.db introuvable: {SKILLS_DB_PATH}")
        sys.exit(1)

    if not os.path.exists(BOARD_DB_PATH):
        print(f"[ERROR] Base board.db introuvable: {BOARD_DB_PATH}")
        sys.exit(1)

    conn_skills = sqlite3.connect(SKILLS_DB_PATH)
    conn_board = sqlite3.connect(BOARD_DB_PATH)

    cursor_skills = conn_skills.cursor()
    cursor_board = conn_board.cursor()

    cursor_skills.execute("SELECT id, name, author, url, repository, category, tags, sha256, raw_path, normalized_path FROM skills")
    skills_rows = cursor_skills.fetchall()

    print(f"Trouvé {len(skills_rows)} compétences dans skills_library.db.")

    inserted_sources = 0
    inserted_chunks = 0
    skipped_sources = 0

    domain_id = "biblio-vivante"

    for row in skills_rows:
        skill_id, name, author, url, repository, category, tags, sha256, raw_path, normalized_path = row
        
        # Charger le contenu du fichier de skill
        content = ""
        target_path = raw_path or normalized_path or ""
        if target_path and os.path.exists(target_path):
            try:
                with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                pass

        if not content:
            content = f"Skill Name: {name}\nCategory: {category}\nTags: {tags}\nRepository: {repository}"

        source_sha256 = sha256 or calculate_sha256(content)
        source_id = f"src_{skill_id}"
        kind = "md" if "Skill" in str(category) else "transcript"

        try:
            cursor_board.execute("""
                INSERT OR IGNORE INTO sources (
                    id, domain_id, expert_id, kind, title, authors, year, url, local_path, content_sha256, ingested_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                source_id,
                domain_id,
                "expert_biblio",
                kind,
                name or skill_id,
                json.dumps([author or "Claude/SkillsMP"]),
                2026,
                url or repository or f"local://skills/{skill_id}",
                target_path,
                source_sha256,
                datetime.now().isoformat()
            ))

            if cursor_board.rowcount > 0:
                inserted_sources += 1
                
                # Découpage en chunks
                text_chunks = chunk_text(content)
                for idx, chunk_str in enumerate(text_chunks):
                    chunk_id = f"chk_{skill_id}_{idx}"
                    token_cnt = len(chunk_str.split())

                    cursor_board.execute("""
                        INSERT OR IGNORE INTO chunks (
                            id, source_id, domain_id, expert_id, chunk_idx, text, token_count
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        chunk_id,
                        source_id,
                        domain_id,
                        "expert_biblio",
                        idx,
                        chunk_str,
                        token_cnt
                    ))
                    if cursor_board.rowcount > 0:
                        inserted_chunks += 1
            else:
                skipped_sources += 1

        except Exception as e:
            print(f"[WARN] Erreur d'injection pour {skill_id}: {e}")

    conn_board.commit()

    cursor_board.execute("SELECT count(*) FROM sources")
    total_sources = cursor_board.fetchone()[0]

    cursor_board.execute("SELECT count(*) FROM chunks")
    total_chunks = cursor_board.fetchone()[0]

    conn_skills.close()
    conn_board.close()

    print(f"=== [INJECTION RÉUSSIE] ===")
    print(f"Sources injectées : {inserted_sources} ({skipped_sources} déjà existantes)")
    print(f"Chunks injectés : {inserted_chunks}")
    print(f"Total Sources dans Board OS : {total_sources}")
    print(f"Total Chunks FTS5 dans Board OS : {total_chunks}")

if __name__ == "__main__":
    main()
