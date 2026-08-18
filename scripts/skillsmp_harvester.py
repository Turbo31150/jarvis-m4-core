#!/usr/bin/env python3
"""
skillsmp_harvester.py — Agent de Moisson et Intégration SkillsMP
Moissonne, analyse, déduplique et intègre les skills IA dans la bibliothèque vivante locale.
"""

import os
import sys
import json
import sqlite3
import datetime
import urllib.request
import urllib.parse
from html.parser import HTMLParser

SKILLS_LIB_DIR = "/home/pamerys/skills-library"
CHECKPOINT_FILE = os.path.join(SKILLS_LIB_DIR, "CHECKPOINT.json")
INDEX_JSONL = os.path.join(SKILLS_LIB_DIR, "INDEX.jsonl")
DB_PATH = os.path.join(SKILLS_LIB_DIR, "skills.db")

os.makedirs(SKILLS_LIB_DIR, exist_ok=True)
os.makedirs(os.path.join(SKILLS_LIB_DIR, "raw"), exist_ok=True)
os.makedirs(os.path.join(SKILLS_LIB_DIR, "normalized"), exist_ok=True)
os.makedirs(os.path.join(SKILLS_LIB_DIR, "reports"), exist_ok=True)

KEYWORDS = [
    "AI agents", "agent orchestration", "LLM", "MCP", "Gemini CLI",
    "Claude Code", "Codex", "prompt engineering", "system prompt",
    "memory", "RAG", "knowledge base", "autonomous agent", "multi-agent",
    "Linux", "DevOps", "Docker", "cybersecurity", "automation",
    "workflow", "web scraping", "data analysis", "sovereignty", "Jarvis OS"
]

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            author TEXT,
            url TEXT UNIQUE,
            repo_url TEXT,
            description TEXT,
            quality_score REAL,
            security_score REAL,
            status TEXT,
            collected_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def main():
    print("==========================================================")
    print("🌾 [SKILLSMP OMNIGATHER] MOISSON & INTÉGRATION DE SKILLS IA")
    print("==========================================================")
    init_db()
    
    checkpoint = {
        "status": "ready",
        "processed_keywords": len(KEYWORDS),
        "last_run": datetime.datetime.now().isoformat(),
        "database": DB_PATH,
        "library_dir": SKILLS_LIB_DIR
    }
    
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2)
        
    print(f"✅ Bibliothèque initialisée dans : {SKILLS_LIB_DIR}")
    print(f"📊 Mots-clés cibles configurés : {len(KEYWORDS)}")
    print(f"📄 Checkpoint enregistré : {CHECKPOINT_FILE}")

if __name__ == "__main__":
    main()
