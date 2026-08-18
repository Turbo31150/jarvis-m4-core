#!/usr/bin/env python3
"""codeur-scraper-worker.py — Worker codeur.com scalable avec pages paramétrables."""

import argparse
import json
import re
import time
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

CODEUR_BASE_URL = "https://www.codeur.com"
MAX_RETRIES = 3
RETRY_DELAY = 8

KEYWORDS = [
    "python",
    "ia",
    "intelligence artificielle",
    "machine learning",
    "chatbot",
    "automatisation",
    "api",
    "scraping",
    "trading",
    "agent",
    "voice",
    "vocal",
    "whisper",
    "gpu",
    "docker",
    "n8n",
    "workflow",
    "llm",
    "react",
    "node",
    "nodejs",
    "développement",
    "developpement",
    "web",
    "application",
    "wordpress",
    "plugin",
    "integration",
    "backend",
    "frontend",
    "fastapi",
    "django",
    "flask",
    "rust",
    "typescript",
    "javascript",
    "php",
    "laravel",
    "symfony",
    "angular",
    "vue",
    "mobile",
    "flutter",
    "swift",
    "kotlin",
    "android",
    "ios",
    "saas",
    "erp",
    "crm",
    "ecommerce",
    "shopify",
    "prestashop",
    "magento",
    "woocommerce",
    "stripe",
    "sql",
    "postgresql",
    "mongodb",
    "redis",
    "elasticsearch",
    "graphql",
    "devops",
    "kubernetes",
    "terraform",
    "aws",
    "azure",
    "gcp",
    "linux",
    "data",
    "analyse",
    "dashboard",
    "bi",
    "powerbi",
    "tableau",
    "reporting",
    "seo",
    "marketing",
    "email",
    "newsletter",
    "automation",
    "bot",
    "blockchain",
    "crypto",
    "nft",
    "web3",
    "solidity",
    "video",
    "audio",
    "streaming",
    "ffmpeg",
]

MIN_BUDGET_EUR = 300


def fetch_page(url: str) -> str | None:
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
        "Accept-Language": "fr-FR,fr;q=0.9",
    }
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            print(f"[WARN] Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
    return None


def parse_budget(text: str) -> int:
    text = text.strip()
    if re.search(r"moins\s+de\s+500", text, re.IGNORECASE):
        return 200
    if re.search(r"moins\s+de\s+300", text, re.IGNORECASE):
        return 100
    numbers = re.findall(r"([\d\s\xa0 ]+)\s*€", text)
    if numbers:
        raw = numbers[0].replace(" ", "").replace(" ", "").replace("\xa0", "")
        try:
            return int(raw)
        except ValueError:
            pass
    if "et plus" in text.lower():
        return 10000
    return 0


def parse_projects(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    projects = []
    container = soup.find("div", class_="projects-list") or soup.find(
        "div", id="projects-list"
    )
    cards = (
        container.find_all("a", href=re.compile(r"^/projects/\d+"))
        if container
        else soup.find_all("a", href=re.compile(r"^/projects/\d+"))
    )

    for card in cards:
        href = str(card.get("href", ""))
        m = re.search(r"/projects/(\d+)", href)
        if not m:
            continue
        pid = m.group(1)
        h3 = card.find("h3")
        title = (
            h3.get_text(strip=True) if h3 else str(card.get("aria-label", "Sans titre"))
        )
        desc_div = card.find("div", class_=lambda c: bool(c and "line-clamp-3" in c))
        description = desc_div.get_text(strip=True) if desc_div else ""
        card_text = card.get_text(" ", strip=True)
        budget_span = card.find("span", title="Budget")
        budget = budget_span.get_text(strip=True) if budget_span else "Non spécifié"
        offres_span = card.find("span", title="Offres")
        nb_proposals = "0"
        if offres_span:
            nm = re.search(r"(\d+)", offres_span.get_text(strip=True))
            nb_proposals = nm.group(1) if nm else "0"
        date_span = card.find(
            "span", class_=lambda c: bool(c and "whitespace-nowrap" in c)
        )
        posted = date_span.get_text(strip=True) if date_span else "?"

        kw_found = []
        searchable = f"{title} {description} {card_text}".lower()
        for kw in KEYWORDS:
            pattern = (
                r"(?<![a-zA-Zéèêëàâùûôîïç])"
                + re.escape(kw)
                + r"(?![a-zA-Zéèêëàâùûôîïç])"
            )
            if re.search(pattern, searchable):
                kw_found.append(kw)

        projects.append(
            {
                "id": pid,
                "title": title,
                "description": description,
                "budget": budget,
                "budget_min_eur": parse_budget(budget),
                "nb_proposals": int(nb_proposals),
                "posted": posted,
                "url": CODEUR_BASE_URL + href,
                "keywords_matched": kw_found,
                "scraped_at": datetime.now().isoformat(),
            }
        )
    return projects


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", default="1-3", help="Range: 1-7 or single: 5")
    parser.add_argument("--output", default="/tmp/codeur_out.json")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--min-budget", type=int, default=MIN_BUDGET_EUR)
    args = parser.parse_args()

    if "-" in args.pages:
        start, end = map(int, args.pages.split("-"))
        pages = list(range(start, end + 1))
    else:
        pages = [int(args.pages)]

    all_projects = []
    matched = []

    for page_num in pages:
        url = f"{CODEUR_BASE_URL}/projects?page={page_num}"
        print(f"[INFO] Page {page_num}/{pages[-1]} → {url}")
        html = fetch_page(url)
        if not html:
            print(f"[WARN] Page {page_num} non récupérée")
            continue
        projects = parse_projects(html)
        print(f"  → {len(projects)} projets parsés")
        all_projects.extend(projects)
        # Respect rate-limiting
        if page_num < pages[-1]:
            time.sleep(2)

    for p in all_projects:
        if p["budget_min_eur"] >= args.min_budget or p["keywords_matched"]:
            matched.append(p)

    print(
        f"\n[RESULT] Total: {len(all_projects)} | Matchés (budget≥{args.min_budget}€ OU keyword): {len(matched)}"
    )

    output = {
        "worker": args.pages,
        "scraped_at": datetime.now().isoformat(),
        "pages": pages,
        "total": len(all_projects),
        "matched": len(matched),
        "projects": all_projects,
        "matched_projects": matched,
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"[OK] Sauvegardé → {args.output}")

    if args.dry_run:
        print("\n=== TOP 10 MATCHÉS ===")
        for p in sorted(matched, key=lambda x: x["budget_min_eur"], reverse=True)[:10]:
            kw = ", ".join(p["keywords_matched"][:4])
            print(f"  [{p['budget']}] {p['title'][:60]}")
            print(f"       🔗 {p['url']}")
            print(f"       🏷  {kw}")


if __name__ == "__main__":
    main()
