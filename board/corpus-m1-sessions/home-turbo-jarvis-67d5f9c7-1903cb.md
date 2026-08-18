[user] Review this change for security vulnerabilities.

Changed files (you may Read these and any other file in the repo):
  - scripts/install_skills_ecosystem.py

Unified diff (only + lines are new):

=== DIFF: scripts/install_skills_ecosystem.py ===
@@ -0,0 +1,124 @@
+#!/usr/bin/env python3
+"""
+install_skills_ecosystem.py
+Rassemble, convertit et installe toutes les commandes/skills depuis la branche local de 5.2 Go (sources.jsonl + skillsmp_skills)
+vers :
+ - Claude Code : ~/.claude/skills/
+ - Antigravity CLI / Gemini : ~/.gemini/skills/
+ - OpenClaw : ~/.openclaw/skills/ & /home/turbo/jarvis-cowork/skills/
+"""
+
+import os
+import sys
+import sqlite3
+import re
+
+DB_PATH = "/home/turbo/jarvis/jarvis_master.db"
+CLAUDE_SKILLS_DIR = os.path.expanduser("~/.claude/skills")
+GEMINI_SKILLS_DIR = os.path.expanduser("~/.gemini/skills")
+OPENCLAW_SKILLS_DIR = os.path.expanduser("~/.openclaw/skills")
+COWORK_SKILLS_DIR = "/home/turbo/jarvis-cowork/skills"
+
+
+def sanitize_name(name):
+    clean = re.sub(r"[^a-zA-Z0-9_-]", "-", name.strip().lower())
+    clean = re.sub(r"-+", "-", clean).strip("-")
+    return clean if clean else "skill-cmd"
+
+
+def ensure_dirs():
+    for d in [
+        CLAUDE_SKILLS_DIR,
+        GEMINI_SKILLS_DIR,
+        OPENCLAW_SKILLS_DIR,
+        COWORK_SKILLS_DIR,
+    ]:
+        os.makedirs(d, exist_ok=True)
+
+
+def install_skill(name, description, content):
+    name_clean = sanitize_name(name)
+    if not name_clean or len(name_clean) < 2:
+       

[assistant] Looking at this new script that installs third-party skill catalog entries into `~/.claude/skills/` and other executable-skill directories.

[assistant] I have enough to finalize. The key sinks:

1. **`corps` (untrusted third-party skill body) → written verbatim into `~/.claude/skills/<name>/SKILL.md`** — the Claude Code skill loader reads these as executable model instructions. Any catalog entry can inject arbitrary tool-invoking prompts.

2. **Description sanitizer defeats itself with backslash** — strips `\r\n\t` and replaces `"` with `'`, but leaves `\` alone. A description ending in `\` becomes `"…\"` inside the YAML, escaping the closing quote so parsing spills into subsequent lines — enabling injection of `allowed-tools:` / `additional-directories:` frontmatter keys the comment claims to prevent.

3. **Skill-name collision / silent override** — `sanitize_name` lets a catalog entry claim any name (`security-review`, `run`, `code-review`, `init`, …); the loop unconditionally `os.remove`s any file there and overwrites the existing `SKILL.md`. A malicious catalog wins over the user's real skills.