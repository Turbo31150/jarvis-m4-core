#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
codeur-veille.py — Monitoring Codeur.com for AI/automation projects with Telegram alerts.

Usage:
    # Daemon mode (checks every 30 minutes by default):
    python3 codeur-veille.py

    # Single check (for cron):
    python3 codeur-veille.py --once

    # Custom interval (in minutes):
    python3 codeur-veille.py --interval 15

    # Dry run (no Telegram, just print):
    python3 codeur-veille.py --once --dry-run

    # Force daily dashboard now:
    python3 codeur-veille.py --once --force-dashboard

Environment variables (or hardcoded fallback below):
    TELEGRAM_BOT_TOKEN  — Telegram bot token from @BotFather
    TELEGRAM_CHAT_ID    — Telegram chat ID to send alerts to

Cron example (every 30 min):
    */30 * * * * cd /home/pamerys/IA/Core/jarvis && python3 scripts/codeur-veille.py --once

Files:
    Seen projects DB : /home/pamerys/IA/Core/jarvis/data/codeur-seen-projects.json
    Log file         : /home/pamerys/IA/Core/jarvis/logs/codeur-veille.log
"""

import argparse
import json
import logging
import os
import re
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, date
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path("/home/pamerys/IA/Core/jarvis")
SEEN_PROJECTS_FILE = BASE_DIR / "data" / "codeur-seen-projects.json"
DB_PATH = BASE_DIR / "data" / "jarvis-master.db"
LOG_FILE = BASE_DIR / "logs" / "codeur-veille.log"
DAILY_SENT_FLAG = Path("/tmp/codeur-daily-sent")

# ---------------------------------------------------------------------------
# Telegram credentials (env vars take priority, fallback to hardcoded)
# ---------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8369376863:AAF-7YGDbun8mXWwqYJFj-eX6P78DeIu9Aw")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "2010747443")

# ---------------------------------------------------------------------------
# Search config
# ---------------------------------------------------------------------------
CODEUR_BASE_URL = "https://www.codeur.com"
PAGES_TO_SCRAPE = 3  # Number of listing pages to check (35 projects/page)

MATCH_KEYWORDS = [
    "ia", "intelligence artificielle", "machine learning", "chatbot",
    "automatisation", "python", "api", "scraping", "trading", "agent",
    "voice", "vocal", "whisper", "gpu", "docker", "n8n", "workflow",
    "llm", "react", "node", "nodejs",
]

MIN_BUDGET_EUR = 500
TECH_KEYWORDS = ["python", "ia", "llm", "react", "node", "nodejs", "intelligence artificielle",
                 "machine learning", "chatbot", "automatisation", "agent", "n8n", "workflow"]

DEFAULT_INTERVAL_MINUTES = 30
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 10

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("codeur-veille")
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
fh.setLevel(logging.DEBUG)
fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(fh)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(ch)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_seen_projects() -> dict:
    """Load the set of already-seen project IDs."""
    if SEEN_PROJECTS_FILE.exists():
        try:
            with open(SEEN_PROJECTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning("Could not load seen projects file, starting fresh: %s", e)
    return {}


def save_seen_projects(seen: dict) -> None:
    """Persist seen project IDs to JSON."""
    SEEN_PROJECTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SEEN_PROJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump(seen, f, ensure_ascii=False, indent=2)


def fetch_page(url: str) -> str | None:
    """Fetch a page with retries."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "fr-FR,fr;q=0.9",
    }
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            logger.warning("Fetch attempt %d/%d failed for %s: %s", attempt, MAX_RETRIES, url, e)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)
    logger.error("All %d fetch attempts failed for %s", MAX_RETRIES, url)
    return None


def parse_budget(text: str) -> int:
    """Extract the minimum budget value in EUR from budget text. Returns 0 if unknown."""
    text = text.strip()
    # "Moins de 500 €" -> 0 (below threshold)
    if re.search(r"moins\s+de\s+500", text, re.IGNORECASE):
        return 0
    # Extract numbers from text like "500 € à 1 000 €", "1 000 € à 10 000 €", "10 000 € et plus"
    numbers = re.findall(r"([\d\s]+)\s*€", text)
    if numbers:
        raw = numbers[0].replace(" ", "").replace("\u202f", "").replace("\xa0", "")
        try:
            return int(raw)
        except ValueError:
            pass
    if "et plus" in text.lower():
        return 10000
    return 0


def budget_is_ok(budget_text: str) -> bool:
    """Return True if the budget is >= MIN_BUDGET_EUR."""
    return parse_budget(budget_text) >= MIN_BUDGET_EUR


def matches_keywords(text: str) -> list[str]:
    """Return list of matched MATCH_KEYWORDS found in text (case insensitive)."""
    text_lower = text.lower()
    found = []
    for kw in MATCH_KEYWORDS:
        pattern = r"(?<![a-zA-Zéèêëàâùûôîïç])" + re.escape(kw) + r"(?![a-zA-Zéèêëàâùûôîïç])"
        if re.search(pattern, text_lower):
            found.append(kw)
    return found


def matches_tech_keywords(text: str) -> list[str]:
    """Return list of matched TECH_KEYWORDS (stricter filter for dashboard)."""
    text_lower = text.lower()
    found = []
    for kw in TECH_KEYWORDS:
        pattern = r"(?<![a-zA-Zéèêëàâùûôîïç])" + re.escape(kw) + r"(?![a-zA-Zéèêëàâùûôîïç])"
        if re.search(pattern, text_lower):
            found.append(kw)
    return found


def extract_project_id(href: str) -> str | None:
    """Extract project ID from href like /projects/480355-some-slug."""
    m = re.search(r"/projects/(\d+)", href)
    return m.group(1) if m else None


def parse_projects(html: str) -> list[dict]:
    """Parse project listings from the Codeur.com projects page HTML.

    Fix 2026-04: container is <div class="projects-list"> (not id="projects-list").
    Cards are <a href="/projects/XXXXX-slug"> inside a nested <div class="row">.
    Budget is in <span title="Budget">, proposals in <span title="Offres">,
    date in <span class="whitespace-nowrap">, description in <div class="line-clamp-3">.
    """
    soup = BeautifulSoup(html, "html.parser")
    projects = []

    # Primary: div with class "projects-list" (Tailwind, 2026-04 structure)
    container = soup.find("div", class_="projects-list")
    if not container:
        # Fallback: legacy id-based container
        container = soup.find("div", id="projects-list")

    if container:
        cards = container.find_all("a", href=re.compile(r"^/projects/\d+"))
    else:
        # Last resort: scan entire page
        cards = soup.find_all("a", href=re.compile(r"^/projects/\d+"))

    for card in cards:
        href = card.get("href", "")
        pid_match = re.search(r"/projects/(\d+)", href)
        if not pid_match:
            continue
        project_id = pid_match.group(1)

        # Title: <h3> inside the card
        h3 = card.find("h3")
        title = h3.get_text(strip=True) if h3 else card.get("aria-label", "Sans titre")

        # Description: <div class="line-clamp-3"> (new layout)
        desc_div = card.find("div", class_=lambda c: c and "line-clamp-3" in c)
        description = desc_div.get_text(strip=True) if desc_div else ""

        # Full card text for keyword matching
        card_text = card.get_text(" ", strip=True)

        # Budget: <span title="Budget">
        budget_span = card.find("span", title="Budget")
        if budget_span:
            budget = budget_span.get_text(strip=True)
        else:
            budget_match = re.search(
                r"((?:Moins de\s+)?\d[\d\s\xa0]*€(?:\s*[àa]\s*\d[\d\s\xa0]*€)?(?:\s*et plus)?)",
                card_text,
            )
            budget = budget_match.group(1).strip() if budget_match else "Non specifie"

        # Proposals: <span title="Offres">
        offres_span = card.find("span", title="Offres")
        if offres_span:
            offres_text = offres_span.get_text(strip=True)
            proposals_match = re.search(r"(\d+)", offres_text)
            nb_proposals = proposals_match.group(1) if proposals_match else "0"
        else:
            proposals_match = re.search(r"(\d+)\s*[Oo]ffres?", card_text)
            nb_proposals = proposals_match.group(1) if proposals_match else "0"

        # Posted date: <span class="whitespace-nowrap"> (new layout)
        date_span = card.find("span", class_=lambda c: c and "whitespace-nowrap" in c)
        if date_span:
            posted = date_span.get_text(strip=True)
        else:
            all_dates = re.findall(r"Il y a\s+\S+(?:\s+\S+)?", card_text)
            posted = all_dates[0].strip() if all_dates else "Date inconnue"

        url = CODEUR_BASE_URL + href

        projects.append({
            "id": project_id,
            "title": title,
            "description": description,
            "budget": budget,
            "nb_proposals": nb_proposals,
            "posted": posted,
            "url": url,
            "full_text": card_text,
        })

    return projects


def score_project_llm(project: dict) -> int:
    """Score a project 0-10 using local LLM via lm-ask.sh."""
    prompt = (
        f"Score ce projet Codeur de 0-10 pour un dev Python/IA freelance: "
        f"{project['title']} | Budget: {project['budget']} | "
        f"{project['description'][:200]}. "
        f"Réponds juste le score (un seul chiffre entre 0 et 10)."
    )
    try:
        result = subprocess.run(
            ["bash", "/home/pamerys/jarvis/scripts/lm-ask.sh", prompt],
            capture_output=True, text=True, timeout=30
        )
        output = result.stdout.strip()
        # Extract first number found
        m = re.search(r"\b(\d{1,2})\b", output)
        if m:
            score = int(m.group(1))
            return min(10, max(0, score))
    except Exception as e:
        logger.warning("LLM scoring failed: %s", e)
    # Fallback: keyword-based score
    return len(project.get("matched_kw", [])) * 2


def send_telegram(bot_token: str, chat_id: str, message: str) -> bool:
    """Send a Telegram message. Returns True on success."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(url, json=payload, timeout=15)
            if resp.ok:
                return True
            logger.warning("Telegram API error (attempt %d): %s", attempt, resp.text)
        except requests.RequestException as e:
            logger.warning("Telegram send attempt %d failed: %s", attempt, e)
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY_SECONDS)
    logger.error("Failed to send Telegram message after %d attempts", MAX_RETRIES)
    return False


def format_telegram_message(project: dict) -> str:
    """Format a project into a Telegram alert message."""
    score_str = f" [score: {project['llm_score']}/10]" if "llm_score" in project else ""
    return (
        f"\U0001f514 Nouveau projet Codeur.com{score_str}\n"
        f"\U0001f4cb {project['title']}\n"
        f"\U0001f4b0 {project['budget']}\n"
        f"\U0001f465 {project['nb_proposals']} propositions\n"
        f"\U0001f517 {project['url']}\n"
        f"\U0001f4c5 {project['posted']}"
    )


def send_daily_dashboard(
    all_projects: list[dict],
    matched_projects: list[dict],
    dry_run: bool = False,
    force: bool = False,
) -> None:
    """Send a daily summary dashboard via Telegram (once per day).

    Checks /tmp/codeur-daily-sent to avoid duplicate sends.
    Scores each matched project with local LLM and shows top 3.
    """
    today_str = date.today().isoformat()

    # Check if already sent today (unless forced)
    if not force and DAILY_SENT_FLAG.exists():
        try:
            sent_date = DAILY_SENT_FLAG.read_text(encoding="utf-8").strip()
            if sent_date == today_str:
                logger.debug("Daily dashboard already sent today (%s), skipping.", today_str)
                return
        except IOError:
            pass

    # Score matched projects with LLM and sort
    scored = []
    for p in matched_projects:
        score = score_project_llm(p)
        p["llm_score"] = score
        scored.append(p)
    scored.sort(key=lambda x: x.get("llm_score", 0), reverse=True)

    top3 = scored[:3]
    nb_total = len(all_projects)
    nb_match = len(matched_projects)

    lines = [
        f"\U0001f4cb <b>Codeur Today ({today_str})</b>",
        f"{nb_total} projets scrapés, {nb_match} matchent ton profil\n",
    ]

    if top3:
        lines.append("<b>Top 3 :</b>")
        for i, p in enumerate(top3, 1):
            score_label = p.get("llm_score", "?")
            kw = ", ".join(p.get("matched_kw", []))[:40]
            lines.append(
                f"{i}. <a href=\"{p['url']}\">{p['title']}</a>\n"
                f"   \U0001f4b0 {p['budget']} | score: {score_label}/10\n"
                f"   \U0001f3f7 {kw}"
            )
    else:
        lines.append("Aucun projet correspondant aujourd'hui.")

    message = "\n".join(lines)

    if dry_run:
        print("\n=== DAILY DASHBOARD ===")
        print(message.replace("<b>", "").replace("</b>", "").replace("<a href=\"", "").replace("\">", " ").replace("</a>", ""))
        print("=== END ===\n")
    else:
        ok = send_telegram(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message)
        if ok:
            logger.info("Daily dashboard sent via Telegram.")
            try:
                DAILY_SENT_FLAG.write_text(today_str, encoding="utf-8")
            except IOError as e:
                logger.warning("Could not write daily flag: %s", e)
        else:
            logger.error("Failed to send daily dashboard.")


def save_to_db(projects: list[dict], applied_pids: set[str]) -> None:
    """Save matched projects into the codeur_projects SQLite table."""
    if not projects:
        return
    try:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        ts = datetime.now().isoformat()
        for p in projects:
            keywords = ",".join(p.get("matched_kw", []))
            score = p.get("llm_score", len(p.get("matched_kw", [])) * 10)
            c.execute(
                "INSERT OR IGNORE INTO codeur_projects "
                "(pid, title, budget, offers_count, keywords, score, scanned_at, applied) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    p["id"],
                    p["title"],
                    p["budget"],
                    int(p.get("nb_proposals", 0)),
                    keywords,
                    score,
                    ts,
                    1 if p["id"] in applied_pids else 0,
                ),
            )
        conn.commit()
        conn.close()
        logger.info("Saved %d project(s) to SQLite", len(projects))
    except Exception as e:
        logger.error("Failed to save projects to SQLite: %s", e)


def run_check(dry_run: bool = False, force_dashboard: bool = False) -> int:
    """Run a single check cycle. Returns number of new matching projects found."""
    seen = load_seen_projects()
    all_projects_list: list[dict] = []
    all_projects_map: dict[str, dict] = {}
    matched_projects: list[dict] = []
    new_matches = 0

    for page_num in range(1, PAGES_TO_SCRAPE + 1):
        url = f"{CODEUR_BASE_URL}/projects?page={page_num}"
        logger.info("Fetching project listing page %d/%d", page_num, PAGES_TO_SCRAPE)
        html = fetch_page(url)
        if not html:
            continue

        projects = parse_projects(html)
        logger.info("  Parsed %d project(s) from page %d", len(projects), page_num)

        for p in projects:
            if p["id"] not in all_projects_map:
                all_projects_map[p["id"]] = p
                all_projects_list.append(p)

        if len(projects) < 10:
            break

    logger.info("Total unique projects scraped: %d", len(all_projects_map))

    for pid, project in all_projects_map.items():
        if pid in seen:
            continue

        # Filter budget >= 500
        if not budget_is_ok(project["budget"]):
            logger.debug("Skipping %s — budget too low: %s", pid, project["budget"])
            seen[pid] = {"title": project["title"], "reason": "budget_low", "seen_at": datetime.now().isoformat()}
            continue

        # Filter: must match at least one tech keyword
        searchable = f"{project['title']} {project['description']} {project['full_text']}"
        tech_kw = matches_tech_keywords(searchable)
        if not tech_kw:
            logger.debug("Skipping %s — no tech keyword match: %s", pid, project["title"])
            seen[pid] = {"title": project["title"], "reason": "no_keyword", "seen_at": datetime.now().isoformat()}
            continue

        # Broad keyword match (for Telegram label)
        matched_kw = matches_keywords(searchable)
        project["matched_kw"] = matched_kw if matched_kw else tech_kw

        # LLM score
        llm_score = score_project_llm(project)
        project["llm_score"] = llm_score

        logger.info(
            "NEW MATCH: [%s] %s (budget: %s, keywords: %s, score: %d/10)",
            pid, project["title"], project["budget"],
            ", ".join(project["matched_kw"]), llm_score,
        )
        matched_projects.append(project)
        new_matches += 1

        msg = format_telegram_message(project)

        if dry_run:
            print("\n" + msg + "\n")
        else:
            send_telegram(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, msg)

        seen[pid] = {
            "title": project["title"],
            "budget": project["budget"],
            "keywords": project["matched_kw"],
            "llm_score": llm_score,
            "notified": True,
            "seen_at": datetime.now().isoformat(),
        }

    applied_pids: set[str] = set()
    save_to_db(matched_projects, applied_pids)
    save_seen_projects(seen)

    # Daily dashboard (once per day)
    send_daily_dashboard(
        all_projects=all_projects_list,
        matched_projects=matched_projects,
        dry_run=dry_run,
        force=force_dashboard,
    )

    logger.info("Check complete. New matches: %d", new_matches)
    return new_matches


def main():
    parser = argparse.ArgumentParser(description="Monitor Codeur.com for AI/automation projects")
    parser.add_argument("--once", action="store_true", help="Run a single check and exit")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL_MINUTES, help="Check interval in minutes (default: 30)")
    parser.add_argument("--dry-run", action="store_true", help="Print matches to stdout instead of sending Telegram")
    parser.add_argument("--force-dashboard", action="store_true", help="Force send daily dashboard even if already sent today")
    args = parser.parse_args()

    logger.info(
        "=== codeur-veille started (mode: %s, interval: %dm) ===",
        "once" if args.once else "daemon", args.interval,
    )

    if args.once:
        run_check(dry_run=args.dry_run, force_dashboard=args.force_dashboard)
    else:
        while True:
            try:
                run_check(dry_run=args.dry_run, force_dashboard=args.force_dashboard)
            except Exception as e:
                logger.exception("Unexpected error during check cycle: %s", e)
            logger.info("Next check in %d minutes...", args.interval)
            time.sleep(args.interval * 60)


if __name__ == "__main__":
    main()
