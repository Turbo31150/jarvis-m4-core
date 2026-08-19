[user] Contexte : machine ASUS TUF F15 (M4) de Pamerys, écosystème JARVIS local. On vient de réparer le son et le widget vocal. Objectif : implémenter le système « application directe » = l'utilisatrice dit une commande à voix haute → l'action s'exécute directement, en branchant une bibliothèque de 432 actions déjà consolidée.

NE CASSE RIEN de ce qui marche : le son (PipeWire), le service `jarvis-voice-widget.service` (déjà réparé, DISPLAY=:1), le serveur Whisper STT sur :8789. Tout doit rester 0-token (aucun appel LLM facturé) et local.

## Fichiers clés à analyser AVANT de coder
1. `/home/pamerys/jarvis/voice_commands_unified.json` — LA bibliothèque (432 entrées), format : `[{"command": "...", "type": "url|shell|web|action", "action": "...", "source": "..."}]`
2. `/home/pamerys/jarvis/scripts/vocal-router.sh` — le routeur vocal existant (analyse comment il lit les commandes et exécute)
3. `/home/pamerys/jarvis/scripts/voice_widget.py` — le widget vocal (analyse comment il matche une phrase transcrite → commande, et comment il exécute ; il lit actuellement `/home/pamerys/jarvis/voice_commands.json` qui n'a que 21 entrées)
4. `/home/pamerys/jarvis/voice_commands.json` — l'ancien fichier (21 entrées, format `[{"command","type","action"}]`)

## Tâche
a) Comprendre le mécanisme actuel de matching (phrase transcrite → commande) et d'exécution dans voice_widget.py / vocal-router.sh.
b) Brancher `voice_commands_unified.json` (432 actions) comme source de commandes, en gardant la rétro-co

[assistant] Maintenant j'analyse la bibliothèque unifiée (432 entrées) et le commander.py de référence.

[assistant] J'examine le commander.py de référence, les exemples des types web/action/shell, et le mécanisme d'actions.

[assistant] Je vérifie le mécanisme d'actions (INDEX.json) et cherche d'éventuelles commandes shell destructives dans la bibliothèque.

[assistant] J'ai tout le contexte nécessaire. Résumé de l'analyse.

- `voice_widget.py` : matching via `_norm_cmd` (accents/minuscules) + `match_command` (égalité ou 1 mot en trop), exécution via `execute_command` (dispatch `url`/`text`/`shell`). Lit `voice_commands.json` (21 entrées).
- `voice_commands_unified.json` : 432 entrées, types = shell(304), action(75), web(43), url(7), text(3). Champ `source` en plus.
- `commander.py` : normalisation accents via `unicodedata.normalize('NFKD')` (plus robuste que la table manuelle).
- Type `action` = ids pointant vers `.actions/INDEX.json` (seul INDEX présent est dans windows_recovery, pas de moteur d'exécution actif). Type `web` = souvent des ancres non-URL (metadata scrapée), parfois de vraies URLs.
- Pas de `rm -rf`/`dd`/`mkfs` dans la biblio, mais présence de `sudo`, `systemctl restart`. Le garde-fou reste indispensable.

Je crée un module dispatcher autonome propre, puis je le branche.

[assistant] Deux bugs réels détectés. Correction : (1) tolérance de mots trop faible pour « s'il te plaît » (4 tokens), (2) certains champs `action` sont des entiers (metadata web) et cassent `re.match`. Je corrige le module.

[assistant] Tout fonctionne (432 chargées, 320 actionnables direct). Je branche maintenant le dispatcher dans `voice_widget.py`, en conservant les noms `match_command`/`execute_command` attendus par `_on_recording_done`.

[assistant] Vérification que `voice_widget.py` importe proprement et délègue bien au dispatcher.

[assistant] API Error: Connection closed mid-response. The response above may be incomplete.