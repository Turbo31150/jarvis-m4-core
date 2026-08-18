[user] ## Adversarial Claim Verifier (voter 2/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Comment construire, en 2026, une ingestion documentaire multi-sources entièrement gratuite et sans compte, pour alimenter une bibliothèque de connaissances locale ? Contexte concret : une machine Linux mono-poste (Ubuntu, noyau 6.8, 48 Gio de RAM, GPU NVIDIA, Ollama et LM Studio en local) qui alimente déjà une base SQLite de 81 968 sujets et 10 423 fiches, via un script Python qui appelle `curl`, `gh` et `yt-dlp`. Aucune API payante ne doit être utilisée, et la charge doit rester bornée (un démon d'ingestion tourne déjà en continu et un garde-fou coupe les tâches au-delà d'un load de 16).

Cinq volets à instruire, chacun avec des faits vérifiables et datés :

(1) QUELLES API PUBLIQUES RESTENT RÉELLEMENT OUVERTES EN 2026, sans clé, sans OAuth, sans compte ?
Établir un état des lieux sourcé et à jour pour : HackerNews (API Algolia et API Firebase officielle), StackExchange/StackOverflow (limites sans clé, quotas journaliers, filtres), Reddit (l'accès JSON anonyme renvoie désormais 403 — depuis quand exactement, quelle politique, quelles conditions d'usage, existe-t-il un accès non authentifié encore toléré, et quel est le coût/quota du parcours OAuth « installed app » gratuit ?), Lemmy et le Fediverse (Mastodon, Lobsters), Discourse (les forums qui exposent /latest.json), les listes de diffusion (LKML, lore.kernel.org et son API), Wikipedia/Wikimedi

[assistant] Primary source confirmed. Now checking the "annual public data file is free" sub-claim and its current status.

[assistant] Verification complete. Primary source confirmed verbatim, plus corroboration on the free/no-account distribution channel.