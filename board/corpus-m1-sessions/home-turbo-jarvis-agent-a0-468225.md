[user] ## Web Searcher: Panorama primaire — API publiques sans clé ni compte, quotas 2026

Research question: "Comment construire, en 2026, une ingestion documentaire multi-sources entièrement gratuite et sans compte, pour alimenter une bibliothèque de connaissances locale ? Contexte concret : une machine Linux mono-poste (Ubuntu, noyau 6.8, 48 Gio de RAM, GPU NVIDIA, Ollama et LM Studio en local) qui alimente déjà une base SQLite de 81 968 sujets et 10 423 fiches, via un script Python qui appelle `curl`, `gh` et `yt-dlp`. Aucune API payante ne doit être utilisée, et la charge doit rester bornée (un démon d'ingestion tourne déjà en continu et un garde-fou coupe les tâches au-delà d'un load de 16).

Cinq volets à instruire, chacun avec des faits vérifiables et datés :

(1) QUELLES API PUBLIQUES RESTENT RÉELLEMENT OUVERTES EN 2026, sans clé, sans OAuth, sans compte ?
Établir un état des lieux sourcé et à jour pour : HackerNews (API Algolia et API Firebase officielle), StackExchange/StackOverflow (limites sans clé, quotas journaliers, filtres), Reddit (l'accès JSON anonyme renvoie désormais 403 — depuis quand exactement, quelle politique, quelles conditions d'usage, existe-t-il un accès non authentifié encore toléré, et quel est le coût/quota du parcours OAuth « installed app » gratuit ?), Lemmy et le Fediverse (Mastodon, Lobsters), Discourse (les forums qui exposent /latest.json), les listes de diffusion (LKML, lore.kernel.org et son API), Wikipedia/Wikimedia REST, arXiv, Openalex, Cr

[assistant] Search budget is exhausted. Falling back to direct fetches of the primary documentation pages.

[assistant] Web search budget for the session was exhausted, so I verified the primary docs by direct fetch instead. Key finding: **OpenAlex now appears to require a free API key** (`openalex.org/settings/api`) with a "$1/day" free cap — a break from the old no-key `mailto` polite pool, and directly relevant to the "no account" constraint. `api.stackexchange.com` is unreachable from this environment, so its 300/day-without-key quota could not be confirmed against a primary source.