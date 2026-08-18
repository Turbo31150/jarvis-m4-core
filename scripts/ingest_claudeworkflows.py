#!/usr/bin/env python3
"""
JARVIS OMEGA — Ingestion totale claudeworkflows.org
But: Aspirer les 4997 workflows, les analyser et les injecter
     comme nouveaux dominos dans jarvis_master.db
"""
import json, sqlite3, re, time, urllib.request, urllib.error
from datetime import datetime
from html.parser import HTMLParser

DB_PATH = "/home/pamerys/jarvis/jarvis_master.db"
URL = "https://www.claudeworkflows.org/"
OUTPUT_DIR = "/home/pamerys/jarvis/data/task_results"
LOG_FILE = "/home/pamerys/jarvis/data/task_results/domino_claudeworkflows_ingest.md"

# ─── Parser HTML ─────────────────────────────────────────────────────────────
class WorkflowParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.workflows = []
        self._in_card = False
        self._in_h2 = False
        self._in_badge = False
        self._in_meta = False
        self._current = {}
        self._tags = []
        self._depth = 0
        self._card_depth = 0
        self._meta_key = None
        self._current_text = ""
        self._in_value = False

    def handle_starttag(self, tag, attrs):
        attrs_d = dict(attrs)
        cls = attrs_d.get("class", "")
        self._depth += 1

        if "card" in cls and tag == "div":
            self._in_card = True
            self._card_depth = self._depth
            self._current = {"title": "", "tags": [], "meta": {}, "links": [], "value": 0}
            self._tags = []

        if self._in_card:
            if tag == "h2":
                self._in_h2 = True
                self._current_text = ""
            if "badge" in cls:
                self._in_badge = True
                self._current_text = ""
            if "value" in cls:
                self._in_value = True
                self._current_text = ""
            if "meta" in cls:
                self._in_meta = True
            if tag == "a" and "href" in attrs_d:
                href = attrs_d["href"]
                if href and href != "#":
                    self._current.setdefault("links", []).append(href)
            if "stat" in cls or "muted" in cls:
                self._current_text = ""

    def handle_endtag(self, tag):
        if self._in_h2 and tag == "h2":
            self._current["title"] = self._current_text.strip()
            self._in_h2 = False
        if self._in_badge and tag == "span":
            t = self._current_text.strip()
            if t:
                self._tags.append(t)
            self._in_badge = False
        if self._in_value and tag == "span":
            try:
                self._current["value"] = int(self._current_text.strip())
            except:
                pass
            self._in_value = False

        if self._in_card and self._depth == self._card_depth and tag == "div":
            self._current["tags"] = self._tags[:]
            if self._current.get("title"):
                self.workflows.append(dict(self._current))
            self._in_card = False
            self._current = {}
            self._tags = []

        self._depth -= 1

    def handle_data(self, data):
        if self._in_h2 or self._in_badge or self._in_value:
            self._current_text += data

# ─── Extraction JS data (le site charge les données via JS inline) ────────────
def extract_from_js(html: str) -> list:
    """Extraire les workflows depuis les données JS inline du HTML"""
    workflows = []

    # Pattern: const cards = [...] ou window.cards = [...]
    patterns = [
        r'const\s+cards\s*=\s*(\[.*?\]);',
        r'window\.cards\s*=\s*(\[.*?\]);',
        r'var\s+cards\s*=\s*(\[.*?\]);',
        r'let\s+cards\s*=\s*(\[.*?\]);',
    ]

    for pat in patterns:
        m = re.search(pat, html, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(1))
                print(f"  ✓ JS data trouvée: {len(data)} entrées")
                return data
            except Exception as e:
                print(f"  ✗ Parse JS: {e}")

    # Chercher les objets JSON inline
    # Format typique: {title:"...", tags:[...], value:...}
    obj_pattern = r'\{[^{}]*"title"\s*:\s*"[^"]*"[^{}]*\}'
    matches = re.findall(obj_pattern, html)
    for m in matches:
        try:
            obj = json.loads(m)
            if "title" in obj:
                workflows.append(obj)
        except:
            pass

    return workflows


def fetch_html(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def normalize_to_domino(wf: dict, idx: int) -> dict:
    """Convertir un workflow claudeworkflows en domino JARVIS"""
    title = wf.get("title", wf.get("problem", wf.get("name", f"workflow-{idx}")))
    tags = wf.get("tags", wf.get("categories", []))
    if isinstance(tags, str):
        tags = [tags]

    # Déterminer le backend
    backend = "lm-ask"
    tag_str = " ".join(tags).lower()
    if any(t in tag_str for t in ["mcp", "api"]):
        backend = "mcp"
    elif any(t in tag_str for t in ["git", "github"]):
        backend = "git"
    elif any(t in tag_str for t in ["docker"]):
        backend = "docker"
    elif any(t in tag_str for t in ["cli", "bash", "shell", "terminal"]):
        backend = "shell"
    elif any(t in tag_str for t in ["python"]):
        backend = "python"
    elif any(t in tag_str for t in ["multi-agent", "subagent", "orchestrat"]):
        backend = "orchestrator"

    # Générer des steps basés sur les tags
    steps = ["init.context", "llm.analyze", "llm.generate"]
    if "multi-agent" in tag_str or "subagent" in tag_str:
        steps = ["init.context", "agent.spawn", "agent.orchestrate", "agent.merge", "output.report"]
    elif "debug" in tag_str or "troubleshoot" in tag_str:
        steps = ["init.context", "log.analyze", "llm.diagnose", "fix.apply", "verify.result"]
    elif "test" in tag_str or "tdd" in tag_str:
        steps = ["init.context", "test.generate", "test.run", "fix.iterate", "test.validate"]
    elif "git" in tag_str or "github" in tag_str:
        steps = ["git.status", "git.analyze", "llm.generate", "git.commit", "git.push"]
    elif "context" in tag_str or "memory" in tag_str:
        steps = ["context.load", "llm.compress", "context.save", "context.verify"]
    elif "prompt" in tag_str:
        steps = ["prompt.load", "llm.optimize", "prompt.test", "prompt.save"]
    elif "research" in tag_str or "brief" in tag_str:
        steps = ["query.build", "web.search", "llm.synthesize", "report.generate"]
    elif "automation" in tag_str or "hook" in tag_str:
        steps = ["trigger.detect", "action.prepare", "action.execute", "log.result"]

    slug = re.sub(r"[^a-z0-9\-]", "-", title.lower())[:60].strip("-")

    # Logique (description courte)
    logique = f"Workflow importé claudeworkflows.org — tags: {', '.join(tags[:5])}"
    value = wf.get("value", wf.get("score", 0))
    if value:
        logique += f" — score communauté: {value}"

    return {
        "serie": slug or f"cw-workflow-{idx}",
        "verdict": "imported",
        "danger": "low",
        "steps": json.dumps(steps),
        "backend": backend,
        "next_serie": "",
        "logique": logique,
    }


def ingest_all():
    print("=" * 60)
    print(f"JARVIS OMEGA — Ingestion claudeworkflows.org")
    print(f"Démarrage: {datetime.now().isoformat()}")
    print("=" * 60)

    # Fetch HTML
    print("\n[1/4] Téléchargement claudeworkflows.org...")
    try:
        html = fetch_html(URL)
        print(f"  ✓ HTML récupéré: {len(html):,} caractères")
    except Exception as e:
        print(f"  ✗ Erreur fetch: {e}")
        return []

    # Extraction JS data
    print("\n[2/4] Extraction des données workflows...")
    workflows = extract_from_js(html)

    if not workflows:
        # Fallback: parser HTML
        print("  → Fallback: parsing HTML cards...")
        parser = WorkflowParser()
        try:
            parser.feed(html)
            workflows = parser.workflows
        except Exception as e:
            print(f"  ✗ Erreur parser: {e}")

    # Extraction via regex des objets dans le JS
    if not workflows:
        print("  → Extraction regex avancée...")
        # Chercher les données dans les scripts
        script_blocks = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
        for script in script_blocks:
            if 'title' in script and 'tags' in script:
                # Essayer d'extraire des objets JSON
                arr_m = re.search(r'\[(\{.*\})\]', script, re.DOTALL)
                if arr_m:
                    try:
                        data = json.loads('[' + arr_m.group(1) + ']')
                        if data:
                            workflows = data
                            print(f"  ✓ Script block: {len(data)} workflows")
                            break
                    except:
                        pass

    # Extraction depuis les cards HTML
    if not workflows:
        print("  → Extraction cards HTML directs...")
        card_pattern = re.compile(
            r'<div[^>]*class=["\'][^"\']*card[^"\']*["\'][^>]*>(.*?)</div>\s*</div>\s*</div>',
            re.DOTALL
        )
        for i, m in enumerate(card_pattern.finditer(html)):
            card_html = m.group(0)
            h2 = re.search(r'<h2[^>]*>(.*?)</h2>', card_html, re.DOTALL)
            badges = re.findall(r'<span[^>]*class=["\'][^"\']*badge[^"\']*["\'][^>]*>(.*?)</span>', card_html, re.DOTALL)
            links = re.findall(r'href=["\']([^"\']+)["\']', card_html)
            if h2:
                title = re.sub(r'<[^>]+>', '', h2.group(1)).strip()
                tags = [re.sub(r'<[^>]+>', '', b).strip() for b in badges]
                workflows.append({
                    "title": title,
                    "tags": tags,
                    "links": links,
                })

    print(f"  → {len(workflows)} workflows extraits")

    if not workflows:
        print("  ✗ Aucun workflow extrait - dump HTML pour debug")
        with open("/tmp/claudeworkflows_debug.html", "w") as f:
            f.write(html[:50000])
        return []

    # Normalize
    print("\n[3/4] Normalisation en dominos JARVIS...")
    dominos = []
    for i, wf in enumerate(workflows):
        try:
            d = normalize_to_domino(wf, i)
            dominos.append(d)
        except Exception as e:
            pass

    print(f"  ✓ {len(dominos)} dominos normalisés")

    # Insert DB
    print("\n[4/4] Injection dans jarvis_master.db...")
    # WAL : un seul écrivain à la fois sur une base très sollicitée,
    # il faut attendre au lieu d'échouer sur "database is locked".
    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.execute("PRAGMA busy_timeout=120000")
    cur = conn.cursor()

    # Table étendue pour stocker les workflows bruts
    cur.execute("""
        CREATE TABLE IF NOT EXISTS claudeworkflows_library (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            imported_at TEXT DEFAULT (datetime('now')),
            source_url TEXT,
            title TEXT,
            tags TEXT,
            value INTEGER DEFAULT 0,
            links TEXT,
            backend TEXT,
            domino_serie TEXT,
            steps TEXT,
            logique TEXT
        )
    """)

    inserted = 0
    skipped = 0
    for i, (wf, d) in enumerate(zip(workflows, dominos)):
        try:
            # Table library complète
            cur.execute("""
                INSERT OR IGNORE INTO claudeworkflows_library
                (source_url, title, tags, value, links, backend, domino_serie, steps, logique)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                URL,
                wf.get("title", wf.get("problem", wf.get("name", ""))),
                json.dumps(wf.get("tags", wf.get("categories", []))),
                wf.get("value", wf.get("score", 0)),
                json.dumps(wf.get("links", [])),
                d["backend"],
                d["serie"],
                d["steps"],
                d["logique"],
            ))

            # Table domino_chains
            cur.execute("""
                INSERT OR IGNORE INTO domino_chains
                (serie, verdict, danger, steps, backend, next_serie, logique)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                "cw-" + d["serie"],
                d["verdict"],
                d["danger"],
                d["steps"],
                d["backend"],
                d["next_serie"],
                d["logique"],
            ))

            inserted += 1
        except Exception as e:
            skipped += 1
            if skipped < 5:
                print(f"  ⚠ Skip #{i}: {e}")

    conn.commit()

    # Stats finales
    total_lib = cur.execute("SELECT COUNT(*) FROM claudeworkflows_library").fetchone()[0]
    total_dom = cur.execute("SELECT COUNT(*) FROM domino_chains").fetchone()[0]
    by_backend = cur.execute("""
        SELECT backend, COUNT(*) as cnt FROM domino_chains
        WHERE verdict='imported'
        GROUP BY backend ORDER BY cnt DESC LIMIT 10
    """).fetchall()

    conn.close()

    print(f"\n  ✓ Insérés: {inserted}")
    print(f"  ✗ Skippés: {skipped}")
    print(f"  → Total claudeworkflows_library: {total_lib}")
    print(f"  → Total domino_chains: {total_dom}")
    print(f"\n  Distribution backends:")
    for backend, cnt in by_backend:
        print(f"    {backend}: {cnt}")

    # Rapport domino
    report = f"""# domino:claudeworkflows-ingest
statut: completed
ts: {datetime.now().isoformat()}
source: {URL}

## Résultats
- Workflows extraits: {len(workflows)}
- Dominos insérés: {inserted}
- Dominos skippés: {skipped}
- Total library: {total_lib}
- Total domino_chains: {total_dom}

## Distribution backends
"""
    for backend, cnt in by_backend:
        report += f"- {backend}: {cnt}\n"

    report += f"\n## Workflows top-valeur\n"
    top = sorted(workflows, key=lambda x: x.get("value", x.get("score", 0)), reverse=True)[:20]
    for wf in top:
        title = wf.get("title", wf.get("problem", wf.get("name", "")))
        tags = wf.get("tags", [])
        val = wf.get("value", wf.get("score", 0))
        report += f"- [{val}] {title} — {', '.join(str(t) for t in tags[:3])}\n"

    with open(LOG_FILE, "w") as f:
        f.write(report)

    print(f"\n  ✓ Rapport: {LOG_FILE}")
    return workflows


if __name__ == "__main__":
    result = ingest_all()
    print(f"\n✅ Ingestion terminée — {len(result)} workflows traités")
