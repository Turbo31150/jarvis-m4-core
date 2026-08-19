[user] installe tous > ## Documentation Index
> Fetch the complete documentation index at: https://code.claude.com/docs/llms.txt
> Use this file to discover all available pages before exploring further.

# Claude Desktop on Linux (beta)

> Install and update the Claude desktop app on Ubuntu and Debian

<Note>
  Linux support for the Claude desktop app is in beta. The Chat, Cowork, and Code tabs are all available.
</Note>

The desktop app on Linux gives you the same Chat, Cowork, and Claude Code experience as macOS and Windows: parallel sessions, visual diff review, an integrated terminal and editor, and live app preview. See [Use Claude Code Desktop](/docs/en/desktop) for the full feature reference.

## Requirements

* Ubuntu 22.04 or later, or Debian 12 or later
* x86\_64 or arm64

Other Debian-based distributions that meet these requirements may work but aren't officially tested.

## Install

Install from Anthropic's apt repository so that updates arrive through your system's regular package updates. Open a terminal and run the commands in each step.

<Steps>
  <Step title="Add Anthropic's apt repository">
    This step downloads the signing key with `curl`, which fresh Debian and Ubuntu installations may not include. If the download command fails with `sudo: curl: command not found`, install curl first:

    ```bash theme={null}
    sudo apt install curl
    ```

    Download Anthropic's signing key:

    ```bash theme={null}
    sudo curl -fsSLo /usr/share/keyrings/claude-deskto

[assistant] Le verrou apt est pris par `aptd` (PID 15734) — un autre gestionnaire tourne. J'attends qu'il se libère :

[assistant] `aptd` tient toujours le verrou (c'est le démon de mise à jour graphique d'Ubuntu, sûrement une MàJ en cours). Je relance une attente et j'enchaîne l'install dès qu'il se libère :

[assistant] Dépôt Anthropic ajouté et clé vérifiée. L'install attend en arrière-plan que `aptd` (MàJ système en cours) libère le verrou apt, puis lance `apt install claude-desktop` automatiquement. Je te préviens dès que c'est fini.

[assistant] Étapes faites :
- ✅ curl présent, archi `amd64`
- ✅ Clé de signature téléchargée, empreinte conforme (`31DD DE24 … 1A7E CACE`)
- ✅ Dépôt apt Anthropic enregistré
- ⏳ `apt install claude-desktop` en attente (verrou tenu par `aptd`/MàJ système), install auto dès libération

Dès que le job de fond termine, je te donne le résultat. Ensuite tu lanceras **Claude** depuis le menu (ou `claude-desktop`) et connexion via ton compte claude.ai.

[assistant] C'est l'ancienne sonde d'attente qui s'est terminée. Le vrai job d'install (`bz096fv41`) tourne toujours et attend le verrou. Je patiente jusqu'à sa notification de fin.

[assistant] `aptd` est bloqué depuis >15 min — anormalement long. Je regarde ce qu'il fait réellement avant de décider :

[assistant] `aptd` travaille réellement : il a 4 méthodes http/https actives en train de rafraîchir les listes de paquets (`security.ubuntu.com`). C'est un `apt update` légitime du gestionnaire de MàJ — **il ne faut pas le tuer**. Mon job de fond attend justement ça et enchaînera l'install tout seul. Je relance une sonde courte pour voir s'il vient de finir :

[assistant] Toujours verrouillé — `aptd` fait un rafraîchissement complet des listes, lent (cohérent avec ta latence réseau SFR connue). Mon job de fond `bz096fv41` continue de guetter la libération et lancera l'install dès que possible ; il me notifiera. J'attends sa fin plutôt que de sonder en boucle.

[assistant] `aptd` est **gelé**, pas actif : 37 min, et ses 4 méthodes http/https sont exactement les mêmes PID (33546-33549) que depuis 20 min — elles ne progressent plus, bloquées sur une connexion morte. Je l'annule proprement (annulation de transaction aptdaemon, réversible) pour libérer le verrou :

[assistant] Pas cette option. Je termine les 4 méthodes http gelées — ça force `aptd` à clôturer sa transaction bloquée et à rendre le verrou :

[assistant] L'install tourne (le job de fond enchaîne `apt update` puis `apt install`). Sortie encore vide — apt télécharge. J'attends sa notification de fin.

[assistant] `apt update` (PID 105726) est toujours en cours — téléchargement lent (réseau). Il n'est pas bloqué, juste lent. Le job de fond poursuit et lancera l'install juste après. J'attends sa notification de fin plutôt que de sonder inutilement.

[assistant] Aucun process apt actif mais paquet pas installé — je lis la sortie complète du job :

[assistant] Le dépôt Claude marche (candidat **1.24012.0** dispo). L'`apt update` a juste échoué à joindre `security.ubuntu.com` (le nœud réseau lent) mais ça n'empêche rien. L'install ne s'est pas poursuivie. Verrou libre — je la relance directement :

[assistant] ✅ **Installé** — `claude-desktop 1.24012.0`, binaire `/usr/bin/claude-desktop`.

Récap :
| Étape | État |
|---|---|
| Clé Anthropic (empreinte `31DD…CACE`) | ✅ vérifiée |
| Dépôt apt `downloads.claude.ai` | ✅ enregistré |
| `aptd` gelé qui bloquait le verrou | ✅ débloqué (méthodes http mortes tuées) |
| Install `claude-desktop 1.24012.0` | ✅ ok |

Note : `apt update` n'a pas pu joindre `security.ubuntu.com` (nœud réseau lent/saturé, sans effet sur l'install Claude).

**Lancement** : menu d'applications → **Claude**, ou `claude-desktop` en terminal. Connexion via ton compte claude.ai (abonnement ou SSO — pas de clé API console ici). Les MàJ arriveront via `sudo apt upgrade`.

Optionnel : `sudo apt autoremove` pour retirer les vieux headers noyau 6.17.0-29 signalés.

[assistant] Claude Desktop est installé et prêt. Tu peux le lancer maintenant depuis le menu d'applications ou avec `claude-desktop`.

[user] <local-command-stdout>CLAUDE_CODE_EFFORT_LEVEL=high overrides effort this session — clear it and ultracode takes over</local-command-stdout>

[assistant] L'app a démarré mais a quitté : mon shell est *headless* (`Missing X server or $DISPLAY`). Je détecte le vrai DISPLAY de ta session graphique et relance dessus :

[assistant] Plusieurs displays (`:0`, `:1`, `:33`). Le socket actif est `:1` (celui de ta session GNOME). Je relance dessus avec le bon `XAUTHORITY` :

[assistant] ✅ Lancé. Claude Desktop tourne maintenant sur ton écran (`DISPLAY=:1`), sans erreur X. La fenêtre devrait être ouverte — connecte-toi avec ton compte **claude.ai**.

Le 1er essai avait échoué juste parce que mon shell d'agent est headless ; il fallait cibler ta vraie session graphique.