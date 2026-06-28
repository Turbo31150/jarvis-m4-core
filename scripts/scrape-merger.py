#!/usr/bin/env python3
"""scrape-merger.py — Merge résultats codeur workers + envoi Telegram résumé."""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path

import requests

TELEGRAM_BOT_TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN", "8369376863:REVOKED-USE-ENV-VAR"
)
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "2010747443")


def send_telegram(msg: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(
            url,
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": msg,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=15,
        )
        return r.ok
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    parser.add_argument(
        "--output", default="/home/pamerys/jarvis/data/scrape/codeur_merged.json"
    )
    parser.add_argument("--telegram", action="store_true")
    args = parser.parse_args()

    all_projects = {}
    all_matched = {}
    worker_stats = []

    for fpath in args.files:
        p = Path(fpath)
        if not p.exists():
            print(f"[WARN] Fichier manquant: {fpath}")
            continue
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        worker_stats.append(
            {
                "worker": data.get("worker", "?"),
                "total": data.get("total", 0),
                "matched": data.get("matched", 0),
            }
        )
        for proj in data.get("projects", []):
            all_projects[proj["id"]] = proj
        for proj in data.get("matched_projects", []):
            all_matched[proj["id"]] = proj

    merged = {
        "merged_at": datetime.now().isoformat(),
        "workers": worker_stats,
        "total_unique": len(all_projects),
        "total_matched": len(all_matched),
        "projects": list(all_projects.values()),
        "matched_projects": sorted(
            all_matched.values(), key=lambda x: x.get("budget_min_eur", 0), reverse=True
        ),
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"[MERGE] {len(all_projects)} projets uniques | {len(all_matched)} matchés")
    for ws in worker_stats:
        print(
            f"  Worker {ws['worker']}: {ws['total']} scrapés, {ws['matched']} matchés"
        )
    print(f"[OK] → {args.output}")

    if args.telegram:
        top5 = list(merged["matched_projects"])[:5]
        lines = [
            f"📊 <b>Codeur.com Scrape Massif — {datetime.now().strftime('%d/%m %H:%M')}</b>",
            f"{len(all_projects)} projets scrapés | {len(all_matched)} matchent\n",
        ]
        if top5:
            lines.append("<b>Top 5 par budget :</b>")
            for p in top5:
                kw = ", ".join(p.get("keywords_matched", [])[:3])
                lines.append(
                    f'• <a href="{p["url"]}">{p["title"][:50]}</a>\n'
                    f"  💰 {p['budget']} | 🏷 {kw or 'général'}"
                )
        else:
            lines.append("Aucun projet matché.")
        ok = send_telegram("\n".join(lines))
        print(f"[TELEGRAM] {'OK' if ok else 'ÉCHEC'}")


if __name__ == "__main__":
    main()
