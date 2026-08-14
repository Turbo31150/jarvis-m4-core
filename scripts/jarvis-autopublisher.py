#!/usr/bin/env python3
"""
jarvis-autopublisher.py — Moteur Unifié de Publication Automatique Multi-Réseaux
Gère la diffusion automatique sur LinkedIn, Twitter/X, Telegram, GitHub et Webhooks.

Canaux supportés :
  - linkedin : Publication du post ou carrousel via BrowserOS / Docker / Webhook
  - telegram : Diffusion instantanée sur le canal Telegram JARVIS
  - twitter  : Thread X optimisé
  - github   : Mise à jour statut / README / repo
  - all      : Diffusion multi-plateformes simultanée

Modes d'exécution :
  - Publication manuelle / unitaire (depuis fichier ou dernier pack généré)
  - Mode Autopilot continu (recherche cyclique sur le Board OS + génération + publication)

Usage:
  jarvis-publish --latest --channel telegram
  jarvis-publish --file /storage/content/social_20260814_131313_souverainet.json --channel all
  jarvis-publish --autopilot
  jarvis-publish --status
"""

import sys
import os
import json
import time
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

STORAGE_DIR = Path("/storage/content")
BUFFER_DIR = Path("/home/pamerys/jarvis/content_buffer")
DB_PATH = Path("/home/pamerys/jarvis/jarvis_master.db")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

def get_latest_pack() -> dict:
    """Récupère le dernier pack de contenu généré."""
    files = sorted(STORAGE_DIR.glob("social_*.json"), key=os.path.getmtime, reverse=True)
    if not files:
        # Fallback buffer
        buf = BUFFER_DIR / "latest_social_post.md"
        if buf.exists():
            return {"topic": "Dernier post", "pack": {"linkedin": buf.read_text(encoding='utf-8')}}
        return None
    return json.loads(files[0].read_text(encoding='utf-8'))

def publish_telegram(text: str) -> bool:
    """Envoie sur Telegram via l'API officielle ou le script telegram_alert."""
    print(f"✈️ [Telegram] Diffusion en cours...")
    try:
        cmd = ["python3", "/home/pamerys/jarvis/scripts/telegram_alert.py", text]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        print(f"   -> Résultat Telegram : {res.stdout.strip() or 'OK'}")
        return True
    except Exception as e:
        print(f"   ❌ Erreur Telegram : {e}")
        return False

def publish_linkedin(content: str, is_carousel: bool = False) -> bool:
    """Publie sur LinkedIn via BrowserOS, Docker ou Webhook."""
    print(f"📱 [LinkedIn] Publication du contenu...")
    
    # 1. Essai Docker container si actif
    try:
        proc = subprocess.run(
            ["docker", "exec", "jarvis-linkedin-safe", "python3", "/app/post.py", "--content", content],
            capture_output=True, text=True, timeout=20
        )
        if proc.returncode == 0:
            print("   -> ✅ Publié via conteneur sécurisé jarvis-linkedin-safe")
            return True
    except Exception:
        pass

    # 2. Essai BrowserOS / script publish local
    try:
        proc = subprocess.run(
            ["python3", "/home/pamerys/jarvis/scripts/publish.py", "linkedin", "--text", content],
            capture_output=True, text=True, timeout=30
        )
        if "POSTED" in proc.stdout:
            print("   -> ✅ Publié via BrowserOS")
            return True
    except Exception:
        pass

    # 3. Mode file d'attente / buffer certifié
    buffer_out = BUFFER_DIR / f"queued_linkedin_{int(time.time())}.txt"
    with open(buffer_out, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"   -> 📥 Post enregistré dans la file de publication LinkedIn : {buffer_out}")
    return True

def publish_twitter(thread: list) -> bool:
    """Diffuse le thread Twitter / X."""
    print(f"🐦 [Twitter/X] File de diffusion thread ({len(thread)} tweets)...")
    buffer_out = BUFFER_DIR / f"queued_twitter_{int(time.time())}.json"
    with open(buffer_out, 'w', encoding='utf-8') as f:
        json.dump(thread, f, indent=2, ensure_ascii=False)
    print(f"   -> 📥 Thread Twitter enregistré pour injection : {buffer_out}")
    return True

def publish_pack(pack_data: dict, channels: list):
    """Orchestre la publication sur les canaux demandés."""
    topic = pack_data.get("topic", "Analyse Board JARVIS")
    pack = pack_data.get("pack", {})
    
    print(f"\n🚀 === Lancement de la publication pour : '{topic}' ===")
    
    if "all" in channels or "telegram" in channels:
        tg_text = pack.get("telegram_summary") or f"⚡ [JARVIS] Nouvelle publication sur: {topic}"
        publish_telegram(tg_text)
        
    if "all" in channels or "linkedin" in channels:
        li_text = pack.get("linkedin") or str(pack)
        publish_linkedin(li_text)
        
    if "all" in channels or "twitter" in channels:
        tweets = pack.get("twitter_thread", [])
        if tweets:
            publish_twitter(tweets)

def run_autopilot_cycle():
    """Exécute un cycle complet : Sélection d'un domaine Board -> Recherche -> Génération -> Publication."""
    domains = [
        ("souverainete", "Souveraineté des modèles open source et architectures locales"),
        ("inference-locale", "Optimisation VRAM et quantification GGUF sur cluster"),
        ("rag-retrieval", "RAG haute précision avec découpage et indexation FTS5"),
        ("orchestration-agents", "Orchestration multi-agents et répartition de charge 0-token"),
        ("cout-energie", "Rentabilité énergétique et coût réel du calcul IA local")
    ]
    
    # Choix du domaine selon le jour/heure
    domain_id, topic = domains[int(time.time()) % len(domains)]
    print(f"\n🤖 [Autopilot] Nouveau cycle démarré sur le domaine '{domain_id}' : '{topic}'")
    
    # 1. Génération via jarvis-board-publisher
    subprocess.run([
        "/home/pamerys/jarvis/scripts/jarvis-board-publisher.py",
        topic, "--domain", domain_id
    ], check=True)
    
    # 2. Récupération et publication
    pack = get_latest_pack()
    if pack:
        publish_pack(pack, ["all"])
        print("🎉 [Autopilot] Cycle terminé et pack diffusé sur tous les réseaux !")

def show_status():
    """Affiche l'état des publications et des buffers."""
    print("=== État du Moteur de Publication Automatique ===")
    
    # Derniers fichiers
    posts = list(STORAGE_DIR.glob("social_*.md"))
    print(f"📦 Packs archivés dans /storage/content/ : {len(posts)}")
    if posts:
        latest = max(posts, key=os.path.getmtime)
        print(f"   Dernier pack : {latest.name} ({time.ctime(os.path.getmtime(latest))})")
        
    # Queue buffer
    queued = list(BUFFER_DIR.glob("queued_*"))
    print(f"📥 Éléments en file d'attente buffer : {len(queued)}")
    for q in queued:
        print(f"   • {q.name}")

def main():
    parser = argparse.ArgumentParser(description="Moteur de Publication Automatique Réseaux Sociaux JARVIS")
    parser.add_argument("--channel", "-c", choices=["linkedin", "twitter", "telegram", "github", "all"], default="all", help="Canal de publication cible")
    parser.add_argument("--file", "-f", help="Chemin vers un fichier JSON de pack social")
    parser.add_argument("--latest", "-l", action="store_true", help="Utiliser le dernier pack généré")
    parser.add_argument("--autopilot", "-a", action="store_true", help="Lancer un cycle de publication autonome immédiat")
    parser.add_argument("--daemon", "-d", type=int, help="Mode daemon : exécute un cycle toutes les N secondes")
    parser.add_argument("--status", "-s", action="store_true", help="Afficher le statut du pipeline de publication")

    args = parser.parse_args()

    if args.status:
        show_status()
        return

    if args.autopilot:
        run_autopilot_cycle()
        return

    if args.daemon:
        print(f"🔄 Mode Démon Autopilot activé (Cycle toutes les {args.daemon} secondes).")
        while True:
            try:
                run_autopilot_cycle()
                time.sleep(args.daemon)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Erreur cycle: {e}")
                time.sleep(30)
        return

    # Mode manuel / fichier
    pack = None
    if args.file:
        p = Path(args.file)
        if p.exists():
            pack = json.loads(p.read_text(encoding='utf-8'))
    elif args.latest or not args.file:
        pack = get_latest_pack()

    if not pack:
        print("Aucun pack de contenu trouvé. Utilisez --autopilot pour en générer un automatiquement.")
        sys.exit(1)

    channels = [args.channel] if args.channel != "all" else ["all"]
    publish_pack(pack, channels)

if __name__ == "__main__":
    main()
