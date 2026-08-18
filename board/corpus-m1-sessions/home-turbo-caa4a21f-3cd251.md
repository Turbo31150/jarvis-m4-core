[assistant] 192.168.1.11 ne répond pas du tout (ping KO, tous ports fermés). Je vérifie le réseau local et je cherche la machine sur le LAN pour tenter la connexion SSH.

[assistant] Le LAN est en **192.168.0.x** (pas .1.x) — et `192.168.0.11` existe bien dans la table ARP. Je sonde cette cible.

[assistant] La bonne cible est **192.168.0.11** (l'adresse `.1.11` était une erreur — le LAN est en `192.168.0.x`). SSH (22) est ouvert. Je me connecte avec les identifiants `pamrerys` / `060520520`.

[assistant] "Too many authentication failures" = trop de clés SSH proposées avant le mot de passe. Je force l'authentification par mot de passe uniquement.

[assistant] Identifiants refusés. La machine a SMB/RPC ouverts (135, 445) — probablement Windows (M4). Je récupère le nom réel de la machine pour valider le compte.

[assistant] Diagnostic clair, je m'arrête là (pas de brute-force de credentials).

## Résultat

**La cible réelle est `192.168.0.11`, pas `192.168.1.11`** — ton LAN est en `192.168.0.x`. L'adresse `.1.11` ne répond pas (elle n'existe pas sur ton réseau).

| Élément | État |
|---|---|
| Machine `192.168.0.11` | ✅ En ligne (ping OK, ~3 ms) |
| Type | 🪟 **Windows** (`OpenSSH_for_Windows_9.5`, ports SMB 135/445 ouverts) → c'est **M4** |
| SSH port 22 | ✅ Ouvert |
| Auth acceptées | `publickey`, `keyboard-interactive` |
| Login `pamrerys` / `060520520` | ❌ **Permission denied** |

**Le couple identifiant/mot de passe est rejeté.** Deux causes probables, vu que la demande vient d'une dictée vocale déformée (`m4 pamrerys`, puis `xela cxxxxinnnzxuiiiiion ssh`) :

1. **Le nom d'utilisateur est mal transcrit.** `pamrerys` ne ressemble pas à un compte Windows classique. Le vrai login est peut-être `pamre`, `Pam`, `Rémi`, un nom prénom, etc.
2. Le mot de passe `060520520` (une date ?) ne correspond pas à ce compte.

Je ne devine pas les credentials (ce serait du brute-force). Donne-moi le **nom d'utilisateur Windows exact** de M4 et je relance la connexion immédiatement. Pour le retrouver côté machine : sur M4, `whoami` dans un terminal, ou le nom affiché sur l'écran de connexion Windows.