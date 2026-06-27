#!/usr/bin/env python3
"""linkedin-worker.py — Vérifie session LinkedIn + queue posts si CDP disponible."""

import json
import os
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

CDP_PORT = 9108
POSTS_QUEUE = Path("/home/pamerys/jarvis/data/scrape/linkedin_queue.json")
LOG = Path("/home/pamerys/jarvis/logs/scrape/linkedin.log")


def log(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def get_cdp_pages() -> list[dict]:
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{CDP_PORT}/json/list", timeout=5
        ) as r:
            return json.loads(r.read())
    except Exception:
        return []


def find_linkedin_page(pages: list[dict]) -> dict | None:
    for p in pages:
        if "linkedin.com" in p.get("url", ""):
            return p
    return None


def main() -> int:
    log("=== LinkedIn Worker démarré ===")

    pages = get_cdp_pages()
    if not pages:
        log(f"WARN: Browserless CDP non accessible sur port {CDP_PORT}")
        log(
            "INFO: Pour publier sur LinkedIn, ouvrez LinkedIn dans le navigateur connecté au CDP."
        )
        return 1

    log(f"CDP OK — {len(pages)} page(s) ouvertes")
    linkedin_page = find_linkedin_page(pages)

    if not linkedin_page:
        log("INFO: Aucune page LinkedIn ouverte dans le navigateur.")
        log("      Ouvrez https://www.linkedin.com/feed/ dans le navigateur CDP.")
        log(f"      Pages actives: {[p.get('url', '')[:50] for p in pages[:5]]}")
        return 1

    log(f"LinkedIn trouvé: {linkedin_page.get('url', '')[:70]}")
    ws_url = linkedin_page.get("webSocketDebuggerUrl", "")
    if not ws_url:
        log("WARN: Pas de WebSocket URL pour la page LinkedIn")
        return 1

    # Check queue
    if not POSTS_QUEUE.exists():
        log(f"INFO: Aucune queue de posts ({POSTS_QUEUE})")
        log("      Créez ce fichier JSON avec une liste de posts à publier.")
        _create_sample_queue()
        return 0

    with open(POSTS_QUEUE, encoding="utf-8") as f:
        queue = json.load(f)

    pending = [p for p in queue if not p.get("published")]
    log(f"Queue: {len(queue)} posts total, {len(pending)} en attente")

    if not pending:
        log("INFO: Tous les posts sont déjà publiés.")
        return 0

    # Import linkedin_publish_batch logic
    linkedin_script = Path("/home/pamerys/jarvis/data/scrape/linkedin_publish_batch.py")
    if not linkedin_script.exists():
        # Copy from container
        os.system(
            "docker cp jarvis-linkedin-safe:/app/infra/scripts/tools/linkedin_publish_batch.py "
            f"{linkedin_script} 2>/dev/null"
        )

    log(f"WS cible: {ws_url[:60]}")
    log(f"Prêt à publier {len(pending)} posts via CDP")
    log(
        "NOTE: Publication manuelle requise — lancez linkedin_publish_batch.py séparément"
    )
    log(f"      WS_URL={ws_url}")

    return 0


def _create_sample_queue() -> None:
    sample = [
        {
            "id": "sample_1",
            "text": "Exemple de post LinkedIn — à personnaliser",
            "published": False,
            "created_at": datetime.now().isoformat(),
        }
    ]
    POSTS_QUEUE.parent.mkdir(parents=True, exist_ok=True)
    with open(POSTS_QUEUE, "w", encoding="utf-8") as f:
        json.dump(sample, f, ensure_ascii=False, indent=2)
    log(f"Queue exemple créée: {POSTS_QUEUE}")


if __name__ == "__main__":
    sys.exit(main())
