#!/usr/bin/env python3
"""
jarvis_community_scraper.py — Scraper autonome 0-API complet (Requestly logic reproduction).
Sources gratuites sans clé API :
  1. HuggingFace (Trending models, papers, GGUF releases, datasets)
  2. GitHub (Trending repositories IA, agents, LLM, Python, C++)
  3. Reddit via RSS (r/LocalLLaMA, r/MachineLearning, r/ArtificialIntelligence)
  4. HackerNews AI / Dev
  5. ArXiv AI / CL / CV via API XML gratuite

Synthétise et injecte dans la Bibliothèque Vivante (~/jarvis/jarvis_master.db)
avec le backend LLM local sur 127.0.0.1:1234.
"""

import sqlite3
import os
import json
import time  # utilisé par le backoff de call_local_llm_synth (retry sur 400 intermittent)
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

DB_PATH = os.path.expanduser("~/jarvis/jarvis_master.db")
LLM_ENDPOINT = "http://127.0.0.1:1234/v1/chat/completions"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 (JARVIS-Autonomous-Scraper/2.0)"
}


def fetch_url(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=12) as response:
            return response.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"[Scraper] Erreur fetch ({url}): {e}")
        return ""


def scrape_huggingface():
    print("[HuggingFace] Scraping des modèles et papiers tendance...")
    items = []
    raw = fetch_url(
        "https://huggingface.co/api/models?sort=downloads&direction=-1&limit=15"
    )
    if raw:
        try:
            models = json.loads(raw)
            for m in models:
                items.append(
                    {
                        "source": "HuggingFace",
                        "title": m.get("id", ""),
                        "description": f"Modèle HF populaire: {m.get('id')}. Downloads: {m.get('downloads')}, Likes: {m.get('likes')}, Pipeline: {m.get('pipeline_tag')}",
                        "url": f"https://huggingface.co/{m.get('id')}",
                    }
                )
        except Exception as e:
            print(f"[HuggingFace] Erreur parse JSON: {e}")
    return items


def scrape_github():
    print("[GitHub] Scraping des projets IA/LLM tendance...")
    items = []
    raw = fetch_url(
        "https://api.github.com/search/repositories?q=topic:llm+topic:ai+created:>2026-01-01&sort=stars&order=desc&per_page=15"
    )
    if raw:
        try:
            data = json.loads(raw)
            for repo in data.get("items", []):
                items.append(
                    {
                        "source": "GitHub",
                        "title": repo.get("full_name", ""),
                        "description": f"Dépôt GitHub: {repo.get('full_name')} - {repo.get('description')}. Stars: {repo.get('stargazers_count')}, Langage: {repo.get('language')}",
                        "url": repo.get("html_url", ""),
                    }
                )
        except Exception as e:
            print(f"[GitHub] Erreur parse JSON: {e}")
    return items


import feedparser
from bs4 import BeautifulSoup


def scrape_reddit_rss():
    print(
        "[Reddit RSS] Scraping r/LocalLLaMA, r/MachineLearning, r/ArtificialIntelligence avec feedparser..."
    )
    items = []
    for sub in ["LocalLLaMA", "MachineLearning", "ArtificialIntelligence"]:
        try:
            feed = feedparser.parse(
                f"https://www.reddit.com/r/{sub}/.rss", agent=HEADERS["User-Agent"]
            )
            for entry in feed.entries[:10]:
                title = entry.get("title", "")
                link = entry.get("link", "")
                summary = BeautifulSoup(
                    entry.get("summary", ""), "html.parser"
                ).get_text()[:300]
                if title:
                    items.append(
                        {
                            "source": f"Reddit r/{sub}",
                            "title": title,
                            "description": f"Discussion Reddit r/{sub}: {title}. Extraits: {summary}",
                            "url": link,
                        }
                    )
        except Exception as e:
            print(f"[Reddit RSS] Erreur feedparser {sub}: {e}")
    return items


def scrape_hackernews():
    print("[HackerNews] Scraping des actualités IA/LLM...")
    items = []
    raw_top = fetch_url("https://hacker-news.firebaseio.com/v0/topstories.json")
    if raw_top:
        try:
            top_ids = json.loads(raw_top)
            count = 0
            for item_id in top_ids[:40]:
                raw_story = fetch_url(
                    f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
                )
                if raw_story:
                    story = json.loads(raw_story)
                    title = story.get("title", "")
                    if any(
                        k in title.lower()
                        for k in [
                            "ai",
                            "llm",
                            "gpt",
                            "model",
                            "qwen",
                            "deepseek",
                            "claude",
                            "gpu",
                            "cuda",
                            "agent",
                        ]
                    ):
                        items.append(
                            {
                                "source": "HackerNews",
                                "title": title,
                                "description": f"Article HN: {title}. Score: {story.get('score')}, Comments: {story.get('descendants')}",
                                "url": story.get(
                                    "url",
                                    f"https://news.ycombinator.com/item?id={item_id}",
                                ),
                            }
                        )
                        count += 1
                        if count >= 10:
                            break
        except Exception as e:
            print(f"[HackerNews] Erreur parse: {e}")
    return items


def scrape_arxiv():
    print("[ArXiv AI] Scraping des derniers papiers d'analyse cs.AI / cs.CL...")
    items = []
    url = "http://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.CL&sortBy=submittedDate&sortOrder=descending&max_results=10"
    raw_xml = fetch_url(url)
    if raw_xml:
        try:
            root = ET.fromstring(raw_xml)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall("atom:entry", ns):
                title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
                summary = (
                    entry.find("atom:summary", ns).text.strip().replace("\n", " ")[:300]
                )
                link = entry.find("atom:id", ns).text
                items.append(
                    {
                        "source": "ArXiv Paper",
                        "title": title,
                        "description": f"Papier ArXiv: {title}. Summary: {summary}",
                        "url": link,
                    }
                )
        except Exception as e:
            print(f"[ArXiv] Erreur parse XML: {e}")
    return items


def call_local_llm_synth(item):
    prompt = f"""Tu es le synthétiseur de la Bibliothèque Vivante JARVIS OS.
Formate cette découverte web (Source: {item["source"]}) en une fiche de connaissances structurée.

Titre: {item["title"]}
Description: {item["description"]}
URL: {item["url"]}

Donne une synthèse concise et l'impact pour JARVIS OS.
"""
    # Trois réglages imposés par le nœud 127.0.0.1:1234 (qwen3.5-9b), vérifiés
    # le 2026-07-30 — les valeurs précédentes (user seul, max_tokens=250, timeout=10)
    # renvoyaient TOUJOURS content='' avec reasoning_content=979 car. et
    # finish_reason='length' : le budget partait entièrement dans le raisonnement.
    # Le scraper tombait donc systématiquement dans son except et écrivait une
    # pseudo-synthèse (« Synthèse automatique pour … ») — la bibliothèque se
    # remplissait de descriptions brutes en ayant l'air de fonctionner.
    #   1. bloc system OBLIGATOIRE : sans lui ce nœud renvoie une réponse figée
    #      hors-sujet (« Yes, I'm doing well… ») au lieu de traiter le prompt.
    #   2. max_tokens >= 1200 : il faut de la marge au-delà des ~900 tokens de
    #      raisonnement, sinon le texte n'est jamais atteint.
    #   3. timeout large : le premier appel paie le chargement JIT du modèle.
    #
    # 4e réglage : RÉESSAYER sur HTTP 400. Ce nœud renvoie un 400 « Bad Request »
    # intermittent quand les requêtes arrivent en rafale (rechargement de modèle en
    # cours). Preuve : un lot de 60 items a échoué 60 fois en 400, puis le MÊME
    # payload rejoué à la main est passé (5285 octets). Sans retry, une rafale
    # remplit la bibliothèque de fiches non synthétisées alors que le nœud est sain.
    # 5e réglage, celui qui règle vraiment le problème : ne PAS passer par
    # /v1/chat/completions. Sur ce modèle le raisonnement déborde n'importe quel
    # budget (mesuré : content='' avec finish_reason='length' même à max_tokens=1200),
    # donc augmenter le budget est une course perdue. On emprunte la voie éprouvée de
    # `bin/qwen-nothink.sh` : /v1/completions avec un prompt ChatML dont le bloc
    # <think></think> est DÉJÀ FERMÉ — le modèle ne peut plus ouvrir de raisonnement
    # et écrit directement la réponse.
    endpoint = LLM_ENDPOINT.replace("/v1/chat/completions", "/v1/completions")
    systeme = "Tu réponds en français, de façon factuelle et concise."
    chatml = (
        f"<|im_start|>system\n{systeme}<|im_end|>\n"
        f"<|im_start|>user\n{prompt}<|im_end|>\n"
        "<|im_start|>assistant\n<think>\n\n</think>\n\n"
    )
    payload = json.dumps(
        {
            "model": "qwen/qwen3.5-9b",
            "prompt": chatml,
            "max_tokens": 700,
            "temperature": 0.3,
            "stop": ["<|im_end|>"],
        }
    ).encode("utf-8")

    derniere_erreur = "aucune tentative"
    for tentative in range(1, 4):
        try:
            req = urllib.request.Request(
                endpoint, data=payload, headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            # /v1/completions renvoie `text`, pas `message.content`.
            texte = (data["choices"][0].get("text") or "").strip()
            if texte:
                return texte
            # Ne jamais maquiller une réponse vide en synthèse : la fiche serait
            # indistinguable d'une vraie et polluerait la bibliothèque.
            derniere_erreur = (
                "réponse vide "
                f"(finish_reason={data['choices'][0].get('finish_reason')})"
            )
        except Exception as e:
            derniere_erreur = str(e)
        if tentative < 3:
            time.sleep(2 * tentative)  # 2 s puis 4 s : laisse le modèle se recharger

    print(
        f"[Scraper] synthèse LLM indisponible après 3 tentatives ({derniere_erreur})"
        " — fiche marquée non synthétisée"
    )
    return (
        f"[NON SYNTHÉTISÉ — {derniere_erreur}]\n\n"
        f"{item['title']} ({item['url']})\nDescription brute : {item['description']}"
    )


def save_to_biblio(items):
    # WAL : un seul écrivain à la fois sur une base très sollicitée,
    # il faut attendre au lieu d'échouer sur "database is locked".
    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.execute("PRAGMA busy_timeout=120000;")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS biblio_topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        domain TEXT,
        topic TEXT UNIQUE,
        status TEXT DEFAULT 'pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS biblio_knowledge (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        domain TEXT,
        topic TEXT UNIQUE,
        title TEXT,
        content_md TEXT,
        backend TEXT,
        path TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )""")

    added_count = 0
    for item in items:
        try:
            topic_name = f"[{item['source']}] {item['title'][:120]}"
            cur.execute(
                "INSERT OR IGNORE INTO biblio_topics (domain, topic, status) VALUES (?, ?, 'scraped')",
                (item["source"], topic_name),
            )

            synth_text = call_local_llm_synth(item)
            content_md = f"# {item['title']}\n\n**Source** : {item['source']} | **URL** : {item['url']}\n\n## Description & Synthèse\n{synth_text}\n"

            cur.execute(
                """
            INSERT OR REPLACE INTO biblio_knowledge (domain, topic, title, content_md, backend, path)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    item["source"],
                    topic_name,
                    item["title"],
                    content_md,
                    "127.0.0.1:1234",
                    item["url"],
                ),
            )

            added_count += 1
            print(f"[Biblio] ✅ Injecté : {topic_name[:60]}...")
        except Exception as e:
            print(f"[Biblio] Erreur insertion {item['title']}: {e}")

    conn.commit()
    conn.close()
    print(
        f"\n[Terminé] ✨ Total fiches enrichies et injectées dans la Bibliothèque Vivante : {added_count}"
    )


def main():
    print("=========================================================")
    print("🕸️ SCRAPER AUTONOME UNIFIÉ — 0-API (HF, GitHub, Reddit RSS, HN, ArXiv)")
    print("   Inférence LLM locale via http://127.0.0.1:1234")
    print("=========================================================\n")

    all_items = []
    all_items.extend(scrape_huggingface())
    all_items.extend(scrape_github())
    all_items.extend(scrape_reddit_rss())
    all_items.extend(scrape_hackernews())
    all_items.extend(scrape_arxiv())

    print(
        f"\n[Scraper] 🌐 {len(all_items)} ressources web capturées (Reddit RSS inclus). Synthèse & Injection en cours...\n"
    )
    save_to_biblio(all_items)


if __name__ == "__main__":
    main()
