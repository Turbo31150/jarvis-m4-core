[user] Base directory for this skill: /home/turbo/.claude/skills/remplir-bibliotheque

# Bibliothèque Vivante Infinie — remplissage 0-token

Porté du pattern « banque annuelle » de M4 : remplissage par lots, idempotent,
anti-surchauffe GPU, cache SQL, todoliste dynamique qui se régénère toute seule.

Moteur : **LM Studio M1 `:1234`** (qwen3.5-9b) prioritaire → fallback `jarvis_dispatcher.ask()` (Ollama).
Cœur : `~/jarvis/cli/biblio_filler.py`.

## 1. Voir l'avancement
```bash
python3 ~/jarvis/cli/biblio_filler.py --status
```

## 2. Remplir un lot maintenant (à la demande)
```bash
bash ~/.claude/skills/remplir-bibliotheque/scripts/remplir.sh 6      # 6 items
```

## 3. Remplissage perpétuel (daemon)
```bash
systemctl --user status  biblio-filler.service     # état
systemctl --user start   biblio-filler.service     # lancer l'infini
systemctl --user stop    biblio-filler.service     # arrêter
journalctl --user -u biblio-filler.service -f      # suivre en direct
```
Le daemon boucle : lot de 3 toutes les 90 s, pause si GPU ≥ 84 °C, auto-alimente la
todoliste quand elle se vide.

## 4. Où va le contenu
| Type | Destination |
|---|---|
| Commandes | Postgres `cmdlib` (container `jv-infra-biblio-db`) + `Documents/Commande_Directe_Bibliotheque/command_list.md` (section « 🌱 Bibliothèque vivante ») |
| Fiches connaissance | SQLite `jarvis_master.db` table `biblio_knowledge` + `~/jarvis/data/biblio_knowledge/*.md` |
| Todoliste | `jarvis_master.db` table `biblio_topics` |
| Cache 0-token | `

[assistant] Moteur déjà actif (81 045 topics, +4-5/lot). LMS :1234 refuse → fallback dispatcher. Je passe à l'extension demandée : scan disque + dominos + hook sur chaque échange.

[assistant] Tout le socle existe (disk_index 386k, dominos 5 529, biblio 10 435). Je cherche le scanner existant avant d'en écrire un.

[assistant] Le scan tourne en fond (pas de `--help`). Je lis les interfaces au lieu de les exécuter.

[assistant] Socle inventorié. J'écris le cycle unifié (delta disque → blocs → dominos → index). Vérification des schémas cibles :

[assistant] Socle clair. J'écris le moteur de cycle (delta disque → blocs → dominos → index, 0 token) :

[assistant] Cycle en fond. Pendant ce temps, j'ajoute la capture des échanges (demande + réponse) au moteur :

[assistant] Hook validé (`{}`, exit 0, échange archivé, verrou OK). J'ajoute la lecture du transcript pour le côté réponse, puis je câble :

[assistant] Défaut détecté : le cap tronque **et** le marqueur avance → le reste du disque ne serait jamais rattrapé. Je corrige (rattrapage par backlog) :

[assistant] Maintenant le cœur : ne compter que le travail réel et ne pas avancer le marqueur si le backlog reste.

[assistant] Le `--full` ne doit plus forcer un cap géant — le backlog progresse tick par tick :

[assistant] Pendant le rattrapage : timer systemd (pour que le cycle tourne aussi hors session) + vérification LMS :

[assistant] Deux vrais défauts : la bibliothèque se remplit de bruit (dépendances tierces, `conftest`, `test_*`, `__version__`). Je filtre :

[assistant] 212 des 216 blocs étaient du bruit — filtre indispensable. Le rattrapage tourne encore avec l'ancien code : je le relance :

[assistant] `pkill -f` a tué son propre shell (le motif matchait la ligne de commande). Je relance sans ce piège :

[assistant] Ancien process bien arrêté. Test du filtre (en fond, le `find` complet prend ~90 s) :