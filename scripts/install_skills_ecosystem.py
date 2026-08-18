#!/usr/bin/env python3
"""
install_skills_ecosystem.py
Rassemble, convertit et installe toutes les commandes/skills depuis la branche local de 5.2 Go (sources.jsonl + skillsmp_skills)
vers :
 - Claude Code : ~/.claude/skills/
 - Antigravity CLI / Gemini : ~/.gemini/skills/
 - OpenClaw : ~/.openclaw/skills/ & /home/pamerys/jarvis-cowork/skills/
"""

import os
import sys
import sqlite3
import re

DB_PATH = "/home/pamerys/jarvis/jarvis_master.db"
CLAUDE_SKILLS_DIR = os.path.expanduser("~/.claude/skills")
GEMINI_SKILLS_DIR = os.path.expanduser("~/.gemini/skills")
OPENCLAW_SKILLS_DIR = os.path.expanduser("~/.openclaw/skills")
COWORK_SKILLS_DIR = "/home/pamerys/jarvis-cowork/skills"


def sanitize_name(name):
    clean = re.sub(r"[^a-zA-Z0-9_-]", "-", name.strip().lower())
    clean = re.sub(r"-+", "-", clean).strip("-")
    return clean if clean else "skill-cmd"


def ensure_dirs():
    for d in [
        CLAUDE_SKILLS_DIR,
        GEMINI_SKILLS_DIR,
        OPENCLAW_SKILLS_DIR,
        COWORK_SKILLS_DIR,
    ]:
        os.makedirs(d, exist_ok=True)


def install_skill(name, description, content):
    name_clean = sanitize_name(name)
    if not name_clean or len(name_clean) < 2:
        return 0

    # Les descriptions viennent du catalogue skillsmp (contenu TIERS) : un saut
    # de ligne suivi de `---` y injecterait du frontmatter arbitraire
    # (allowed-tools compris) dans un SKILL.md que Claude Code charge.
    # On aplatit donc tout contrôle + guillemets, et on borne la longueur.
    desc_clean = description or name_clean
    desc_clean = re.sub(r"[\r\n\t]+", " ", desc_clean).replace('"', "'").strip()[:500]
    frontmatter = f"""---
name: "{name_clean}"
description: "{desc_clean}"
---

{content}
"""

    installed_count = 0
    dirs = [
        CLAUDE_SKILLS_DIR,
        GEMINI_SKILLS_DIR,
        OPENCLAW_SKILLS_DIR,
        COWORK_SKILLS_DIR,
    ]

    for d in dirs:
        target_folder = os.path.join(d, name_clean)
        if os.path.isfile(target_folder) or os.path.islink(target_folder):
            try:
                os.remove(target_folder)
            except Exception:
                continue
        os.makedirs(target_folder, exist_ok=True)
        target_file = os.path.join(target_folder, "SKILL.md")

        with open(target_file, "w", encoding="utf-8", errors="ignore") as f:
            f.write(frontmatter)
        installed_count += 1

    return installed_count


def main():
    print("🚀 Début de l'installation et du rassemblement des Skills CLI...")
    ensure_dirs()

    if not os.path.exists(DB_PATH):
        print(f"❌ Base de données introuvable : {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Sélection des 500 meilleures fiches exécutables de la branche 5.2G
    cur.execute("""
        SELECT slug, nom, description, corps 
        FROM skillsmp_skills 
        WHERE corps IS NOT NULL AND length(corps) > 100
        ORDER BY length(corps) DESC
        LIMIT 500;
    """)

    rows = cur.fetchall()
    print(f"📦 Extraits : {len(rows)} compétences/commandes prêtes à déployer.")

    count = 0
    for row in rows:
        slug, nom, desc, corps = row
        title = nom if nom else slug
        if install_skill(title, desc, corps):
            count += 1

    conn.close()
    print(
        f"\n✅ Terminé ! {count} compétences/commandes assemblées et déployées simultanément dans :"
    )
    print(f"  - Claude Code      : {CLAUDE_SKILLS_DIR}")
    print(f"  - Antigravity CLI  : {GEMINI_SKILLS_DIR}")
    print(f"  - OpenClaw         : {OPENCLAW_SKILLS_DIR}")
    print(f"  - Cowork Engine    : {COWORK_SKILLS_DIR}")


if __name__ == "__main__":
    main()
