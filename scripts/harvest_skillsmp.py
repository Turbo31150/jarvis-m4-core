#!/usr/bin/env python3
"""
SkillsMP Omnigather Script
Moissonne, déduplique, audite et normalise les skills depuis l'API SkillsMP.
"""
import os
import sys
import json
import time
import hashlib
import urllib.request
import urllib.parse
from datetime import datetime

BASE_DIR = os.path.expanduser("~/jarvis/skills-library")
RAW_DIR = os.path.join(BASE_DIR, "raw")
NORMALIZED_DIR = os.path.join(BASE_DIR, "normalized")
KNOWLEDGE_DIR = os.path.join(BASE_DIR, "knowledge")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

CHECKPOINT_FILE = os.path.join(BASE_DIR, "CHECKPOINT.json")
INDEX_FILE = os.path.join(BASE_DIR, "INDEX.jsonl")

KEYWORDS = [
    "AI agents", "agent orchestration", "LLM", "MCP", "Gemini CLI", "Claude Code",
    "Codex", "prompt engineering", "system prompt", "memory", "RAG", "knowledge base",
    "autonomous agent", "multi-agent", "Linux", "DevOps", "Docker", "Docker Compose",
    "Kubernetes", "CI/CD", "GitHub Actions", "Python", "JavaScript", "TypeScript",
    "FastAPI", "Node.js", "security", "cybersecurity", "automation", "workflow",
    "browser automation", "research", "web scraping", "data analysis", "SQL",
    "PostgreSQL", "Redis", "cloud", "self-hosting", "local AI", "Ollama", "LM Studio",
    "Open source", "sovereignty", "privacy", "EU AI Act", "monitoring", "observability",
    "testing", "benchmarking", "performance", "trading bot", "business automation",
    "content creation", "SEO", "YouTube", "LinkedIn", "documentation",
    "project management", "Jarvis OS", "terminal agent", "shell automation"
]

for d in [BASE_DIR, RAW_DIR, NORMALIZED_DIR, KNOWLEDGE_DIR, REPORTS_DIR, LOGS_DIR]:
    os.makedirs(d, exist_ok=True)

def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "last_keyword_idx": 0,
        "last_page": 1,
        "processed_items": 0,
        "unique_items": 0,
        "duplicate_items": 0,
        "failed_items": 0,
        "api_requests": 0,
        "seen_ids": [],
        "status": "running"
    }

def save_checkpoint(cp):
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(cp, f, indent=2)

def fetch_skills(query, page=1, limit=100):
    url = f"https://skillsmp.com/api/v1/skills/search?q={urllib.parse.quote(query)}&page={page}&limit={limit}&sortBy=stars"
    req = urllib.request.Request(url, headers={'User-Agent': 'Jarvis-Omnigather/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            if res.getcode() == 200:
                data = json.loads(res.read().decode('utf-8'))
                if data.get("success"):
                    return data.get("data", {})
    except Exception as e:
        print(f"[ERROR] Fetch failed for '{query}' (page {page}): {e}")
    return None

def audit_security(skill):
    desc = (skill.get("description") or "").lower()
    name = (skill.get("name") or "").lower()
    dangerous_terms = ["rm -rf", "eval", "exec", "exfiltration", "reverse shell", "crypto", "miner", "token stealer"]
    for term in dangerous_terms:
        if term in desc or term in name:
            return "DANGEROUS", 20
    return "SAFE", 90

def normalize_skill(skill):
    skill_id = skill.get("id")
    name = skill.get("name") or "Unnamed"
    author = skill.get("author") or "Unknown"
    desc = skill.get("description") or ""
    stars = skill.get("stars", 0)
    github_url = skill.get("githubUrl") or ""
    skill_url = skill.get("skillUrl") or ""
    
    sec_status, sec_score = audit_security(skill)
    quality_score = min(100, 40 + min(stars, 40) + (20 if desc else 0))

    markdown_content = f"""---
id: {skill_id}
name: "{name}"
author: "{author}"
repository: "{github_url}"
skill_url: "{skill_url}"
stars: {stars}
verified: false
quality_score: {quality_score}
security_score: {sec_score}
status: "{sec_status}"
collected_at: "{datetime.utcnow().isoformat()}"
---

# Résumé
{desc}

# Objectif
Skill d'automatisation/intégration pour {name}.

# Déclencheurs d’utilisation
Mots-clés associés: {name}, {author}

# Procédure
Consulter le dépôt source: {github_url}

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
"""
    return markdown_content, {
        "id": skill_id,
        "name": name,
        "author": author,
        "stars": stars,
        "github_url": github_url,
        "quality_score": quality_score,
        "security_status": sec_status
    }

def run_harvest(max_requests=50):
    cp = load_checkpoint()
    seen_ids = set(cp.get("seen_ids", []))
    req_count = 0

    print(f"[HARVEST] Démarrage moisson depuis le mot-clé idx={cp['last_keyword_idx']}, page={cp['last_page']}")

    while cp["last_keyword_idx"] < len(KEYWORDS) and req_count < max_requests:
        kw = KEYWORDS[cp["last_keyword_idx"]]
        page = cp["last_page"]

        print(f"[HARVEST] Explorer '{kw}' page {page}...")
        data = fetch_skills(kw, page=page, limit=100)
        req_count += 1
        cp["api_requests"] += 1

        if not data or not data.get("skills"):
            print(f"[HARVEST] Aucun résultat / fin de liste pour '{kw}'. Mot-clé suivant.")
            cp["last_keyword_idx"] += 1
            cp["last_page"] = 1
            save_checkpoint(cp)
            time.sleep(1)
            continue

        skills = data["skills"]
        new_count = 0
        dup_count = 0

        with open(INDEX_FILE, 'a') as idx_f:
            for s in skills:
                sid = s.get("id")
                if not sid or sid in seen_ids:
                    dup_count += 1
                    cp["duplicate_items"] += 1
                    continue

                seen_ids.add(sid)
                cp["unique_items"] += 1
                cp["processed_items"] += 1
                new_count += 1

                # Sauvegarde raw
                raw_path = os.path.join(RAW_DIR, f"{sid}.json")
                with open(raw_path, 'w') as rf:
                    json.dump(s, rf, indent=2)

                # Sauvegarde normalisée
                md_content, meta = normalize_skill(s)
                norm_path = os.path.join(NORMALIZED_DIR, f"{sid}.md")
                with open(norm_path, 'w') as nf:
                    nf.write(md_content)

                # Append index
                idx_f.write(json.dumps(meta) + "\n")

        print(f"[COLLECTED] {new_count} nouveaux, [DUPLICATES] {dup_count} doublons pour '{kw}' p.{page}")

        # Check pagination standard
        pagination = data.get("pagination", {})
        total_pages = pagination.get("totalPages", 1)

        if page >= total_pages or len(skills) < 100:
            cp["last_keyword_idx"] += 1
            cp["last_page"] = 1
        else:
            cp["last_page"] += 1

        cp["seen_ids"] = list(seen_ids)
        save_checkpoint(cp)
        time.sleep(1.2) # Rate limit propre

    # Rapport final de session
    report_filename = f"harvest-{datetime.now().strftime('%Y-%m-%d-%H%M')}.md"
    report_path = os.path.join(REPORTS_DIR, report_filename)
    with open(report_path, 'w') as rep_f:
        rep_f.write(f"""# Rapport de Moisson SkillsMP

- Date: {datetime.now().isoformat()}
- Total requêtes API session: {req_count}
- Total requêtes API cumulo: {cp['api_requests']}
- Total éléments uniques: {cp['unique_items']}
- Total doublons: {cp['duplicate_items']}
- Statut: {cp['status']}
- Dernier mot-clé index: {cp['last_keyword_idx']} ({KEYWORDS[min(cp['last_keyword_idx'], len(KEYWORDS)-1)]})
""")

    print(f"\n[DONE] Session terminée. Requêtes utilisées: {req_count}. Rapport généré: {report_filename}")

if __name__ == "__main__":
    run_harvest(max_requests=40)
