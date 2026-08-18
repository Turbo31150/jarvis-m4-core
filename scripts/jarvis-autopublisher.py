#!/usr/bin/env python3
"""
jarvis-autopublisher.py — Moteur de Publication Multi-Réseaux (statuts HONNÊTES)

PRINCIPE (règle ~/jarvis/CLAUDE.md : « Preuve avant affirmation ») :
  Aucun canal n'est déclaré publié sans preuve. Chaque canal renvoie un statut
  explicite parmi :

    PUBLIÉ       — la publication a réellement eu lieu (preuve : réponse API OK,
                   code retour 0 du poster, marqueur POSTED…)
    MIS EN FILE  — le contenu a seulement été écrit sur disque. RIEN n'est parti.
    ÉCHEC        — une publication a été tentée et a échoué (raison affichée)
    NON CÂBLÉ    — aucun connecteur n'existe pour ce canal ; il le dit, il ne
                   simule pas un succès
    IGNORÉ       — rien à publier pour ce canal

GARDE-FOU HUMAIN :
  Les publications publiques irréversibles (LinkedIn) ne sont PAS tentées par
  défaut. Il faut le drapeau explicite --allow-live. Sans ce drapeau le contenu
  est mis en file et le statut le dit.
  Telegram (canal de notification interne déjà câblé) est tenté par défaut ;
  --dry-run coupe tout accès réseau.

CODE DE SORTIE :
  0 — tous les canaux demandés sont réellement PUBLIÉ
  2 — rien n'a échoué mais au moins un canal est MIS EN FILE / NON CÂBLÉ
  1 — au moins un canal en ÉCHEC

Usage:
  jarvis-autopublisher.py --latest --channel telegram
  jarvis-autopublisher.py --file /storage/content/social_xxx.json --channel all
  jarvis-autopublisher.py --autopilot
  jarvis-autopublisher.py --status
"""

import sys
import os
import json
import time
import argparse
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from dataclasses import dataclass, field

STORAGE_DIR = Path("/storage/content")
BUFFER_DIR = Path("/home/pamerys/jarvis/content_buffer")
DB_PATH = Path("/home/pamerys/jarvis/jarvis_master.db")
VAULT_SECRETS = Path("/home/pamerys/jarvis/secrets-vault/secrets.enc.env")

# ─────────────────────────── Statuts ───────────────────────────
PUBLISHED = "PUBLIÉ"
QUEUED = "MIS EN FILE"
FAILED = "ÉCHEC"
NOT_WIRED = "NON CÂBLÉ"
SKIPPED = "IGNORÉ"

ICON = {
    PUBLISHED: "✅",
    QUEUED: "📥",
    FAILED: "❌",
    NOT_WIRED: "🔌",
    SKIPPED: "➖",
}


@dataclass
class ChannelResult:
    """Statut vérifiable d'un canal. `status` ne vaut PUBLISHED que sur preuve."""

    channel: str
    status: str
    detail: str = ""
    artifact: str = ""  # fichier écrit ou identifiant du message publié
    attempts: list = field(default_factory=list)  # journal des tentatives réelles

    @property
    def really_published(self) -> bool:
        return self.status == PUBLISHED

    def show(self):
        print(
            f"   {ICON.get(self.status, '•')} {self.channel} : {self.status}"
            f"{' — ' + self.detail if self.detail else ''}"
        )
        for a in self.attempts:
            print(f"        · tentative : {a}")
        if self.artifact:
            print(f"        · artefact  : {self.artifact}")


# ─────────────────────────── Secrets ───────────────────────────
def resolve_telegram_credentials() -> tuple:
    """Cherche le token/chat_id : environnement d'abord, coffre sops ensuite.

    Retourne (token, chat_id, source). Valeurs vides si introuvable.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN") or ""
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    if token and chat_id:
        return token, chat_id, "environnement"

    if VAULT_SECRETS.exists():
        try:
            out = subprocess.run(
                ["sops", "-d", str(VAULT_SECRETS)],
                capture_output=True,
                text=True,
                timeout=20,
            )
            if out.returncode == 0:
                for line in out.stdout.splitlines():
                    if "=" not in line or line.strip().startswith("#"):
                        continue
                    k, _, v = line.partition("=")
                    k, v = k.strip(), v.strip().strip('"').strip("'")
                    if k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_TOKEN") and not token:
                        token = v
                    elif k == "TELEGRAM_CHAT_ID" and not chat_id:
                        chat_id = v
                if token and chat_id:
                    return token, chat_id, "coffre sops"
        except Exception:
            pass

    return token, chat_id, "introuvable"


def get_latest_pack() -> dict:
    """Récupère le dernier pack de contenu généré (ou None)."""
    files = (
        sorted(STORAGE_DIR.glob("social_*.json"), key=os.path.getmtime, reverse=True)
        if STORAGE_DIR.exists()
        else []
    )
    if not files:
        buf = BUFFER_DIR / "latest_social_post.md"
        if buf.exists():
            return {
                "topic": "Dernier post (buffer)",
                "pack": {"linkedin": buf.read_text(encoding="utf-8")},
            }
        return None
    return json.loads(files[0].read_text(encoding="utf-8"))


def queue_to_disk(name: str, payload, as_json: bool = False) -> Path:
    """Écrit le contenu dans la file disque. Ce n'est PAS une publication."""
    BUFFER_DIR.mkdir(parents=True, exist_ok=True)
    ext = "json" if as_json else "txt"
    out = BUFFER_DIR / f"queued_{name}_{int(time.time())}.{ext}"
    with open(out, "w", encoding="utf-8") as f:
        if as_json:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        else:
            f.write(payload)
    return out


# ─────────────────────────── Telegram ───────────────────────────
def publish_telegram(text: str, dry_run: bool = False) -> ChannelResult:
    """Envoie sur Telegram et VÉRIFIE la réponse de l'API (401 signalé, pas masqué)."""
    print("✈️  [Telegram] Tentative de diffusion...")
    r = ChannelResult("telegram", FAILED)

    token, chat_id, source = resolve_telegram_credentials()
    if not token or not chat_id:
        r.status = QUEUED
        r.detail = (
            "aucun TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID (ni environnement ni coffre sops) "
            "— contenu écrit sur disque, RIEN n'est parti"
        )
        r.artifact = str(queue_to_disk("telegram", text))
        return r

    if dry_run:
        r.status = QUEUED
        r.detail = f"--dry-run : aucun appel réseau (identifiants trouvés via {source})"
        r.artifact = str(queue_to_disk("telegram", text))
        return r

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    body = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )

    http_code, raw = None, ""
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            http_code = resp.getcode()
            raw = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        http_code = e.code
        raw = e.read().decode("utf-8", "replace")
    except Exception as e:
        r.status = FAILED
        r.detail = f"appel API impossible : {type(e).__name__} — {e}"
        r.attempts.append(f"POST api.telegram.org → exception {type(e).__name__}")
        r.artifact = str(queue_to_disk("telegram", text))
        return r

    try:
        payload = json.loads(raw)
    except Exception:
        payload = {}

    ok = bool(payload.get("ok"))
    desc = payload.get("description", raw[:160])
    r.attempts.append(f"POST api.telegram.org → HTTP {http_code} ok={ok}")

    if http_code == 200 and ok:
        msg_id = (payload.get("result") or {}).get("message_id", "?")
        r.status = PUBLISHED
        r.detail = f"message_id={msg_id} (identifiants : {source})"
        r.artifact = f"telegram:message_id={msg_id}"
        return r

    # Échec réel : on le DIT, on ne renvoie plus « OK ».
    r.status = FAILED
    r.detail = f"API refusée — HTTP {http_code} : {desc} (identifiants : {source})"
    if http_code == 401:
        r.detail += " → token révoqué/invalide, régénérer via BotFather puis mettre à jour le coffre"
    r.artifact = str(queue_to_disk("telegram", text))
    return r


# ─────────────────────────── LinkedIn ───────────────────────────
def publish_linkedin(content: str, allow_live: bool = False) -> ChannelResult:
    """Publie sur LinkedIn UNIQUEMENT si --allow-live et si un poster répond vraiment."""
    print("📱 [LinkedIn] Traitement du contenu...")
    r = ChannelResult("linkedin", QUEUED)

    if not allow_live:
        r.detail = (
            "publication publique non tentée sans --allow-live "
            "(garde-fou : action irréversible sous contrôle humain)"
        )
        r.artifact = str(queue_to_disk("linkedin", content))
        return r

    # 1) Conteneur dédié — on vérifie son EXISTENCE avant de prétendre l'utiliser
    container = "jarvis-linkedin-safe"
    try:
        chk = subprocess.run(
            [
                "docker",
                "ps",
                "--filter",
                f"name=^/{container}$",
                "--format",
                "{{.Names}}",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if chk.stdout.strip() == container:
            proc = subprocess.run(
                [
                    "docker",
                    "exec",
                    container,
                    "python3",
                    "/app/post.py",
                    "--content",
                    content,
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if proc.returncode == 0:
                r.status = PUBLISHED
                r.detail = f"publié via le conteneur {container}"
                r.artifact = f"docker:{container}"
                r.attempts.append(f"docker exec {container} → code 0")
                return r
            r.attempts.append(
                f"docker exec {container} → code {proc.returncode} : "
                f"{(proc.stderr or proc.stdout).strip()[:120]}"
            )
        else:
            r.attempts.append(f"conteneur {container} absent (aucune exécution)")
    except Exception as e:
        r.attempts.append(f"docker indisponible : {type(e).__name__} — {e}")

    # 2) Poster BrowserOS local — succès seulement si le marqueur POSTED est présent
    publisher = Path("/home/pamerys/jarvis/scripts/publish.py")
    if publisher.exists():
        try:
            proc = subprocess.run(
                ["python3", str(publisher), "linkedin", "--text", content],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if proc.returncode == 0 and "POSTED" in proc.stdout:
                r.status = PUBLISHED
                r.detail = "publié via BrowserOS (marqueur POSTED confirmé)"
                r.artifact = "browseros:linkedin"
                r.attempts.append("publish.py linkedin → POSTED")
                return r
            r.attempts.append(
                f"publish.py linkedin → code {proc.returncode}, pas de marqueur POSTED : "
                f"{(proc.stdout or proc.stderr).strip()[:120]}"
            )
        except Exception as e:
            r.attempts.append(f"publish.py inutilisable : {type(e).__name__} — {e}")
    else:
        r.attempts.append(f"{publisher} introuvable")

    # 3) Aucun poster n'a abouti → file d'attente, statut honnête
    r.status = QUEUED
    r.detail = (
        "aucun poster LinkedIn n'a abouti — contenu écrit sur disque, RIEN n'est parti"
    )
    r.artifact = str(queue_to_disk("linkedin", content))
    return r


# ─────────────────────────── Twitter / X ───────────────────────────
def publish_twitter(thread: list, allow_live: bool = False) -> ChannelResult:
    """Aucun connecteur X/Twitter n'existe dans ce dépôt : on le dit."""
    print(f"🐦 [Twitter/X] Traitement du thread ({len(thread)} tweets)...")
    r = ChannelResult("twitter", QUEUED)
    r.artifact = str(queue_to_disk("twitter", thread, as_json=True))
    r.detail = (
        "canal NON CÂBLÉ (aucune API X/Twitter configurée dans ce script) — "
        "contenu écrit sur disque, RIEN n'est parti"
    )
    if allow_live:
        r.attempts.append(
            "--allow-live sans effet : aucun connecteur X/Twitter n'est implémenté"
        )
    return r


# ─────────────────────────── GitHub ───────────────────────────
def publish_github(content: str, allow_live: bool = False) -> ChannelResult:
    """Canal accepté par la CLI mais jamais implémenté ici : statut NON CÂBLÉ."""
    print("🐙 [GitHub] Traitement...")
    r = ChannelResult("github", NOT_WIRED)
    r.detail = (
        "aucune publication GitHub n'est implémentée dans ce moteur "
        "(scripts/publish.py sait pousser un README mais n'est volontairement "
        "pas branché ici : écriture publique irréversible)"
    )
    r.artifact = str(queue_to_disk("github", content))
    return r


# ─────────────────────────── Orchestration ───────────────────────────
def publish_pack(
    pack_data: dict, channels: list, allow_live: bool = False, dry_run: bool = False
) -> list:
    """Publie sur les canaux demandés et renvoie la liste des statuts réels."""
    topic = pack_data.get("topic", "Analyse Board JARVIS")
    pack = pack_data.get("pack", {})
    wanted = set(channels)
    every = "all" in wanted

    print(f"\n🚀 === Publication demandée pour : '{topic}' ===")
    if not allow_live:
        print(
            "   ⚠️  Mode par défaut : les publications publiques ne sont PAS tentées "
            "(--allow-live pour les autoriser)."
        )
    if dry_run:
        print("   ⚠️  --dry-run : aucun appel réseau ne sera émis.")

    results = []

    if every or "telegram" in wanted:
        tg_text = (
            pack.get("telegram_summary")
            or f"⚡ [JARVIS] Nouvelle publication sur: {topic}"
        )
        results.append(publish_telegram(tg_text, dry_run=dry_run))

    if every or "linkedin" in wanted:
        li_text = pack.get("linkedin")
        if li_text:
            results.append(publish_linkedin(li_text, allow_live=allow_live))
        else:
            results.append(
                ChannelResult(
                    "linkedin", SKIPPED, "aucun contenu 'linkedin' dans le pack"
                )
            )

    if every or "twitter" in wanted:
        tweets = pack.get("twitter_thread", [])
        if tweets:
            results.append(publish_twitter(tweets, allow_live=allow_live))
        else:
            results.append(
                ChannelResult("twitter", SKIPPED, "aucun 'twitter_thread' dans le pack")
            )

    if every or "github" in wanted:
        gh_content = pack.get("github") or pack.get("linkedin") or ""
        if gh_content:
            results.append(publish_github(gh_content, allow_live=allow_live))
        else:
            results.append(
                ChannelResult(
                    "github", SKIPPED, "aucun contenu destiné à GitHub dans le pack"
                )
            )

    return results


def print_summary(results: list) -> int:
    """Affiche un bilan sans ambiguïté et calcule le code de sortie."""
    published = [r for r in results if r.status == PUBLISHED]
    queued = [r for r in results if r.status == QUEUED]
    unwired = [r for r in results if r.status == NOT_WIRED]
    failed = [r for r in results if r.status == FAILED]
    skipped = [r for r in results if r.status == SKIPPED]

    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║  BILAN DE PUBLICATION — statuts vérifiés                 ║")
    print("╚══════════════════════════════════════════════════════════╝")
    for r in results:
        r.show()

    print("\n── Récapitulatif ──")
    print(
        f"   ✅ RÉELLEMENT PUBLIÉ : {len(published)}"
        f"{' → ' + ', '.join(r.channel for r in published) if published else ''}"
    )
    print(
        f"   📥 EN ATTENTE (disque, rien n'est parti) : {len(queued)}"
        f"{' → ' + ', '.join(r.channel for r in queued) if queued else ''}"
    )
    print(
        f"   🔌 NON CÂBLÉ : {len(unwired)}"
        f"{' → ' + ', '.join(r.channel for r in unwired) if unwired else ''}"
    )
    print(
        f"   ❌ ÉCHEC : {len(failed)}"
        f"{' → ' + ', '.join(r.channel for r in failed) if failed else ''}"
    )
    if skipped:
        print(
            f"   ➖ IGNORÉ (rien à publier) : {len(skipped)}"
            f" → {', '.join(r.channel for r in skipped)}"
        )

    actionable = [r for r in results if r.status != SKIPPED]
    if failed:
        print(
            "\n⛔ Au moins un canal a ÉCHOUÉ : la diffusion demandée n'a pas eu lieu."
        )
        return 1
    if queued or unwired:
        print(
            "\n⚠️  Une publication a été demandée mais n'a PAS eu lieu "
            "(contenu seulement mis en file / canal non câblé)."
        )
        return 2
    if actionable and all(r.really_published for r in actionable):
        print("\n🎉 Tous les canaux demandés ont réellement publié.")
        return 0
    print("\n⚠️  Aucun canal n'a réellement publié.")
    return 2


# ─────────────────────────── Autopilot ───────────────────────────
def run_autopilot_cycle(allow_live: bool = False, dry_run: bool = False) -> int:
    """Cycle complet : génération d'un pack puis publication, avec statuts réels."""
    domains = [
        (
            "souverainete",
            "Souveraineté des modèles open source et architectures locales",
        ),
        ("inference-locale", "Optimisation VRAM et quantification GGUF sur cluster"),
        ("rag-retrieval", "RAG haute précision avec découpage et indexation FTS5"),
        (
            "orchestration-agents",
            "Orchestration multi-agents et répartition de charge 0-token",
        ),
        ("cout-energie", "Rentabilité énergétique et coût réel du calcul IA local"),
    ]
    domain_id, topic = domains[int(time.time()) % len(domains)]
    print(f"\n🤖 [Autopilot] Cycle sur le domaine '{domain_id}' : '{topic}'")

    generator = Path("/home/pamerys/jarvis/scripts/jarvis-board-publisher.py")
    if generator.exists():
        gen = subprocess.run(
            [str(generator), topic, "--domain", domain_id],
            capture_output=False,
            text=True,
        )
        if gen.returncode != 0:
            print(
                f"   ❌ Génération échouée (code {gen.returncode}) — aucun pack neuf."
            )
    else:
        print(f"   ❌ Générateur introuvable : {generator}")

    pack = get_latest_pack()
    if not pack:
        print("❌ [Autopilot] Aucun pack disponible : rien n'a été publié.")
        return 1

    results = publish_pack(pack, ["all"], allow_live=allow_live, dry_run=dry_run)
    code = print_summary(results)
    if code == 0:
        print("🎉 [Autopilot] Cycle terminé — contenu réellement diffusé.")
    else:
        print(
            "⚠️  [Autopilot] Cycle terminé SANS diffusion complète (voir bilan ci-dessus)."
        )
    return code


# ─────────────────────────── Statut ───────────────────────────
def show_status():
    """État réel du pipeline : ce qui est en attente n'est PAS publié."""
    print("=== État du Moteur de Publication ===")

    packs = list(STORAGE_DIR.glob("social_*")) if STORAGE_DIR.exists() else []
    print(f"📦 Packs archivés dans {STORAGE_DIR} : {len(packs)}")
    if packs:
        latest = max(packs, key=os.path.getmtime)
        print(
            f"   Dernier pack : {latest.name} ({time.ctime(os.path.getmtime(latest))})"
        )

    queued = sorted(BUFFER_DIR.glob("queued_*")) if BUFFER_DIR.exists() else []
    print(
        f"\n📥 File d'attente ({BUFFER_DIR}) : {len(queued)} élément(s) "
        f"— ⚠️ NON PUBLIÉS, simples fichiers sur disque"
    )
    for q in queued:
        print(f"   • {q.name} ({time.ctime(os.path.getmtime(q))})")

    print("\n🔌 Câblage réel des canaux :")
    token, chat_id, source = resolve_telegram_credentials()
    if token and chat_id:
        print(
            f"   • telegram : identifiants présents ({source}) — validité vérifiée à l'envoi"
        )
    else:
        print("   • telegram : NON CÂBLÉ (aucun token/chat_id)")

    try:
        chk = subprocess.run(
            [
                "docker",
                "ps",
                "--filter",
                "name=^/jarvis-linkedin-safe$",
                "--format",
                "{{.Names}}",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        has_container = chk.stdout.strip() == "jarvis-linkedin-safe"
    except Exception:
        has_container = False
    poster = Path("/home/pamerys/jarvis/scripts/publish.py").exists()
    print(
        f"   • linkedin : conteneur jarvis-linkedin-safe {'présent' if has_container else 'ABSENT'}"
        f" · publish.py {'présent' if poster else 'ABSENT'}"
        f" — tentative réelle uniquement avec --allow-live"
    )
    print("   • twitter  : NON CÂBLÉ (aucune API X configurée)")
    print("   • github   : NON CÂBLÉ (publication volontairement non branchée)")


# ─────────────────────────── CLI ───────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Moteur de Publication Réseaux Sociaux JARVIS (statuts honnêtes)"
    )
    parser.add_argument(
        "--channel",
        "-c",
        choices=["linkedin", "twitter", "telegram", "github", "all"],
        default="all",
        help="Canal de publication cible",
    )
    parser.add_argument(
        "--file", "-f", help="Chemin vers un fichier JSON de pack social"
    )
    parser.add_argument(
        "--latest", "-l", action="store_true", help="Utiliser le dernier pack généré"
    )
    parser.add_argument(
        "--autopilot", "-a", action="store_true", help="Cycle de publication autonome"
    )
    parser.add_argument(
        "--daemon", "-d", type=int, help="Mode daemon : un cycle toutes les N secondes"
    )
    parser.add_argument(
        "--status", "-s", action="store_true", help="Afficher l'état réel du pipeline"
    )
    parser.add_argument(
        "--allow-live",
        action="store_true",
        help="Autoriser les tentatives de publication publique irréversible "
        "(LinkedIn). Sans ce drapeau, le contenu est mis en file.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="N'émettre aucun appel réseau (tout est mis en file)",
    )

    args = parser.parse_args()

    if args.status:
        show_status()
        return 0

    if args.autopilot:
        return run_autopilot_cycle(allow_live=args.allow_live, dry_run=args.dry_run)

    if args.daemon:
        print(
            f"🔄 Mode Démon (cycle toutes les {args.daemon} s). "
            f"Le bilan de chaque cycle indique ce qui est réellement parti."
        )
        last = 2
        while True:
            try:
                last = run_autopilot_cycle(
                    allow_live=args.allow_live, dry_run=args.dry_run
                )
                time.sleep(args.daemon)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Erreur cycle : {type(e).__name__} — {e}")
                last = 1
                time.sleep(30)
        return last

    pack = None
    if args.file:
        p = Path(args.file)
        if p.exists():
            pack = json.loads(p.read_text(encoding="utf-8"))
        else:
            print(f"❌ Fichier introuvable : {p}")
            return 1
    else:
        pack = get_latest_pack()

    if not pack:
        print(
            "❌ Aucun pack de contenu trouvé. Utilisez --autopilot pour en générer un."
        )
        return 1

    channels = [args.channel]
    results = publish_pack(
        pack, channels, allow_live=args.allow_live, dry_run=args.dry_run
    )
    return print_summary(results)


if __name__ == "__main__":
    sys.exit(main())
