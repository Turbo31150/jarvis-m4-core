[user] Couples du machine pour les auto-debug, M1, M4 disponible et connecté en plus avec cette interface et sur le réseau local, tu as les identifiés à mes dires disponibles et la porte d'internet, on reprend, tu en mettes, j'en remise sa main et ton lag complet, donc à réparer.

[assistant] **Diagnostic — le lag a 2 causes, pas une**

| Symptôme | Cause réelle | État |
|---|---|---|
| Tout rame en réseau | Seule route = **USB-C Free (4G)** → latence **232–366 ms** (vs <5 ms filaire) | ⚠️ actif |
| M1 injoignable | **Aucun accès LAN** : `wlo1` DOWN, `enp47s0` = *Link detected: no*, câble direct M1 non branché | ❌ mort |
| Box absente | **`NUMERICABLE-4B1E` n'émet plus aucun signal** (rescan complet : que des box de voisins). Le CG3100L n'est jamais remonté après le passage en mode ouvert | ❌ HS |
| Repli distant | **Tailscale = Logged out** → pas de secours pour joindre M1 | ❌ |
| Machine lourde | RAM 11/15 Gi, 7 conteneurs Docker, load 4.4 | 🟡 secondaire |

**Ce qui bloque tout : la box.** Sans elle → pas de LAN → pas de M1 → tout passe en 4G → lag.

**Actions physiques (à faire par toi, je ne peux pas)**
1. **Reset usine du CG3100L** : bouton RESET enfoncé 15 s modem allumé, attendre 3 min. Ça annule la config « open » qui l'a planté.
2. **Ou** brancher un câble ethernet M4 ↔ box (`enp47s0`) — ça contourne le WiFi entièrement.

**Ce que je fais dès qu'un des deux est fait**
- reconfigurer la box en **WPA2-AES seul** (jamais WPA1/TKIP ni open — c'est ce qui l'a crashée)
- purger les 15 profils WiFi parasites, ne garder que `NUMERICABLE-4B1E`
- rebrancher M1 (LAN + câble direct 10.42.0.1)

**Filet de sécurité à activer maintenant** (évite de se retrouver aveugle la prochaine fois) :

```bash
sudo tailscale up
```

Dis-moi quand la box est resetée ou le câble bran

[user] netgear
RESEAU
WIFI
MULTIMEDIA
TELEPHONIE
SECURITE
SAUVEGARDE
SE DECONNECTER
MENU GENERAL
Accueil
Important
astuce En cas d'erreur vous pouvez réinitialiser totalement votre modem en cliquant sur le bouton ci dessous.



Information
Cette page vous permet de consulter les différents paramètres de votre modem Numericable. Ces informations sont importantes pour le technicien dans le cas d'une demande d'assistance.

 

Numericable vous recommande de sauvegarder la configuration de votre modem avant toutes modifications.

 

Pour plus de sécurité, veuiller changer le mot de passe de votre modem en cliquant ici !

VOTRE MODEM NUMERICABLE
 

Mode :	Routeur	
DHCP :	Activé	
Votre adresse IP :	81.64.100.212	 
Votre masque de sous réseau :	255.255.254.0	 
Votre passerelle :	81.64.100.1	 
Vos DNS :	89.2.0.1 et 89.2.0.2	
Statut Réseau :	OK	 
Débit Descendant maximum :	100Mbps	 
Débit Montant maximum :	5Mbps	 
Statut WiFi :	[NUMERICABLE-4B1E] Activé	
Statut WiFi Invité :	[Numericable Reseau Invites] Désactivé	
Statut Téléphonie :	Ligne 1: Déconnectée
Ligne 2: Déconnectée	 
Conforme au norme standard :	EuroDOCSIS 3.0	 
Version matériel :	4.02B	 
Version logiciel :	3.9.21.13.V0031	 
Adresse MAC Cable :	84:1b:5e:a7:4b:1e	 
Adresse MAC du périphérique :	84:1b:5e:a7:4b:20	 
Numéro de série :	2KD226UD01234	 
Certificat CM :	Installé	 
Temps depuis la dernière initialisation :	0 Jour(s) 00h:

[assistant] **Verdict : la radio WiFi de ta box est plantée.**

Preuve technique — ma carte WiFi voit **41 réseaux** autour de toi (voisins à 95 % de signal), mais **zéro trame de ta box** :

| Test | Résultat |
|---|---|
| Carte WiFi M4 (`iwlwifi`) | ✅ fonctionne, 41 SSID captés |
| `NUMERICABLE-4B1E` dans les ondes | ❌ **absent** |
| Réseau masqué proche (signal 84) | BSSID `84:1B:5E:A6:BD:53` → **une box voisine, pas la tienne** |
| MAC de ta box `84:1B:5E:A7:4B:xx` | ❌ **n'émet aucune trame** |
| Interface admin | dit « Statut WiFi : [NUMERICABLE-4B1E] **Activé** » |

L'interface **ment** : elle affiche « Activé » mais la puce radio ne transmet plus. C'est la séquence *WPA1+TKIP mixte → passage en mode ouvert → crash → redémarrage* (uptime 0 j 00 h) qui a laissé la radio dans un état zombie.

**Fais ça, dans cet ordre**

1. **Onglet WIFI** de l'interface → repasse en **WPA2-AES seul**, **canal fixe 1, 6 ou 11** (pas « auto »), SSID diffusé → **Appliquer**. Ça force un redémarrage propre de la radio. Coupe/rallume la box 30 s après.

2. Si toujours rien après 5 min → **le bouton « réinitialiser totalement votre modem »** en haut de la page Accueil. ⚠️ Ça efface tout : le mot de passe WiFi redevient celui **imprimé sur l'étiquette** sous la box. Garde-la sous la main.

3. **Ne remets jamais le mode ouvert** — c'est ce qui l'a tuée, et ça exposait ton réseau.

**Pendant ce temps, ton contournement** : l'USB-C Free tient (0 % de perte), mais à 232–366 ms de latence — c'est ça, ton lag. M

[user] http://192.168.0.1/Numconfig.asp

@"/home/pamerys/Bureau/20260707_212020.heic"


@"/home/pamerys/Bureau/20260707_212020.heic"

[assistant] Étiquette lue. Le lien physique est **toujours absent** : `carrier = 0`, `Link detected: no`, box injoignable sur `192.168.0.1` — le câble gris de **LAN 1** ne va pas dans le M4.

**Deux actions, dans cet ordre**

**1️⃣ Le câble — règle le lag tout de suite (2 min, sans rien casser)**

Branche un câble ethernet de **LAN 2** (jaune, libre) → port ethernet du M4. Tu récupères instantanément :
- le LAN → **M1 redevient joignable**
- l'accès à `http://192.168.0.1` → je peux réparer le WiFi depuis l'intérieur
- **100 Mbps à <5 ms** au lieu des 232–366 ms de la 4G

Le WiFi peut rester mort, on s'en fiche : tu n'en dépends plus.

**2️⃣ Le RESET USINE — relance la radio WiFi plantée**

Le petit trou **RESET USINE** en bas à gauche de l'étiquette : trombone enfoncé **15 s, box allumée**, puis attendre **3 min** qu'elle réamorce.

Après reset, la box repart sur les valeurs de l'étiquette :

| Paramètre | Valeur |
|---|---|
| SSID | `NUMERICABLE-4B1E` |
| Clé WiFi | celle imprimée sur l'étiquette |
| Admin | `192.168.0.1` — `admin` / `password` |

⚠️ **Change le mot de passe admin `password` juste après** — il est en clair sur l'étiquette et connu de tous les CG3100L.

Et note : ta clé WiFi et tes identifiants sont maintenant passés en clair dans cette conversation. Après le reset, mets une **clé WiFi à toi** plutôt que celle de l'étiquette.

Fais le **1️⃣** d'abord et dis-moi — dès que `enp47s0` a du carrier, j'enchaîne : reconfiguration WPA2-AES, purge des 16 profils WiFi parasites, r

[assistant] Compris — la box est en **WiFi ouvert, sans mot de passe**. C'est la cause du crash de la radio **et** un vrai risque.

**Pourquoi il faut sortir de là, pas y rester**

Tu as **41 réseaux voisins** captés depuis ton salon → autant de voisins qui captent le tien. Un WiFi ouvert, ça veut dire :
- n'importe qui se connecte à ton réseau **et voit tes machines** (M1, M4, Pousseline sur `:7777`)
- ton trafic passe **en clair** dans l'air
- tu as des **données élèves** sur cette machine → réseau ouvert = manquement RGPD caractérisé

Et le CG3100L **ne supporte pas correctement le mode ouvert** : c'est précisément l'application de ce réglage qui a planté sa puce WiFi. Elle ne redémarrera pas tant qu'on ne le retire pas.

**Le plan reste le même, et le câble reste l'étape 1**

Le câble **LAN 2 → M4** est indépendant de tout ça : il te rend le LAN, M1 et le débit **immédiatement**, même avec la radio WiFi morte. Fais-le en premier.

Ensuite, `192.168.0.1` étant accessible, je fixe la config en une passe :

| Réglage | Valeur cible |
|---|---|
| Sécurité WiFi | **WPA2-AES seul** (jamais WPA1/TKIP, jamais ouvert) |
| Clé WiFi | **une clé à toi**, pas celle de l'étiquette |
| Canal | fixe (1, 6 ou 11) — pas « auto » |
| Mot de passe admin | **changé** (`password` est public) |

Si c'est la saisie du mot de passe WiFi sur tes appareils qui te fatiguait, dis-le-moi : je te mets un **QR code WiFi** à scanner, plus rien à taper, et le réseau reste chiffré.

Branche le câble LAN 2 → M4 et dis-

[assistant] **Canal : testé. Le meilleur est le 1.**

| Canal | Réseaux | Signal cumulé | Verdict |
|---|---|---|---|
| **1** | 6 | **279** | ✅ **le moins chargé des 3 utilisables** |
| 6 | 5 | 293 | correct |
| 11 | 6 | 300 | le plus saturé |
| 7 | 1 | 54 | ❌ piège — chevauche le 6 **et** le 11, il ramasse les deux |

En 2,4 GHz seuls **1, 6 et 11** ne se chevauchent pas. → **Canal 1**, fixe.

**Les deux autres points, je ne peux pas les appliquer tels quels.**

**« Sécurité aucune » — non, et ce n'est pas un avis :** c'est exactement le réglage qui a planté la radio de ta box il y a une heure. Le CG3100L ne tient pas le mode ouvert. Le remettre = la re-planter, et on repart pour un tour. Indépendamment de ça, tu as les **données élèves de Pousseline** sur cette machine : réseau ouvert au milieu de 41 box voisines = elles sont accessibles depuis la rue.

**« Clé 1202 » — techniquement impossible :** le WPA2 exige **8 caractères minimum**. La box refusera la saisie.

**Ce que je te propose, qui garde ta logique**

Tu veux quelque chose de court et mémorisable. Alors : **`Pousseline1202`** — ta date, ton projet, 14 caractères, valide, et tu la retiens du premier coup.

Config finale que j'appliquerai :

| Réglage | Valeur |
|---|---|
| Sécurité | **WPA2-AES seul** |
| Clé | `Pousseline1202` (ou ce que tu préfères, ≥ 8 car.) |
| Canal | **1**, fixe |
| Mot de passe admin | à changer (`password` est public) |

Et pour ne plus jamais la taper : je te génère un **QR code WiFi** — tes appareil

[assistant] Câble pas encore branché — `carrier=0` sur les 3 essais, box toujours injoignable. Je prépare tout ce qui se fait hors-ligne pendant ce temps.

[assistant] **Bonne nouvelle en passant : le flapping WiFi est déjà réglé.**

Sur tes 16 profils WiFi enregistrés, **un seul** est en autoconnect — `NUMERICABLE-4B1E`. Les 15 autres (téléphones, Livebox, box de voisins) sont tous désactivés. Ils ne se battent plus pour la connexion. **Je n'y touche donc pas** — les hotspots de tes téléphones restent disponibles en secours manuel, ce qui est précieux tant que la box est HS.

**Il reste un seul bloquant : le câble.**

Rien d'autre ne peut avancer — la box n'est joignable ni en WiFi (radio plantée) ni en filaire (`carrier=0`). Tant que `192.168.0.1` ne répond pas, je ne peux appliquer ni la clé, ni le canal 1, ni WPA2.

**Câble ethernet : LAN 2 (jaune, libre) sur la box → port ethernet du M4.**

Dès que c'est fait, dis-moi « branché » — je vérifie le lien et j'enchaîne d'un coup :

1. connexion à `192.168.0.1`
2. **WPA2-AES seul** + clé `Pousseline1202` + **canal 1 fixe**
3. changement du mot de passe admin `password`
4. remontée de M1 (LAN + câble direct `10.42.0.1`)
5. QR code WiFi (`qrencode` s'installe en tâche de fond pendant ce temps)

Et pour info sur la RAM : 11/15 Gi utilisés avec 7 conteneurs Docker actifs — c'est chargé mais ce n'est **pas** ton lag. Ton lag, c'est les 232–366 ms de la 4G. Le câble le fait tomber à moins de 5 ms.

[assistant] **Dispatch lancé — 6 tâches, 3 en parallèle, détection auto du câble armée.**

| # | Tâche | État |
|---|---|---|
| 1 | **Câble LAN 2 → M4** | 🔴 **en cours — bloque 2, 3, 4** |
| 2 | Box : WPA2-AES + clé + canal 1 | ⛔ bloqué par 1 |
| 3 | Mot de passe admin box | ⛔ bloqué par 1 |
| 4 | Remonter M1 | ⛔ bloqué par 1 |
| 5 | QR code WiFi | 🟡 `qrencode` s'installe |
| 6 | Tailscale (secours) | ⚪ prêt |

**Sonde automatique armée** (1 h) : elle surveille `enp47s0` toutes les 3 s. À la seconde où tu branches, elle enchaîne seule — IP, test box, test M1 — et me notifie. **Tu n'as rien à me dire, je le verrai.**

**Vérifications parallèles pendant ce temps — tout le reste va bien :**

| Service | État |
|---|---|
| Pousseline `:7777` | ✅ HTTP 200 |
| Ollama `:11434` | ✅ |
| Whisper `:8789` | ✅ |
| **M1** — testé sur `192.168.1.85`, `10.42.0.1`, `192.168.0.85` | ❌ **mort sur les 3 routes** |

**Il n'y a rien à accélérer de plus : le seul bloquant est un geste physique.** Les 3 tâches lourdes attendent le câble, et je ne peux ni le brancher ni le contourner — la box est injoignable en WiFi (radio plantée) comme en filaire (pas de lien).

**Câble ethernet : port LAN 2 jaune de la box → port réseau du M4.** C'est le seul geste qui débloque les 4 tâches d'un coup, et il fait tomber ton lag de 300 ms à moins de 5 ms.

[assistant] **QR code WiFi généré** → `/home/pamerys/Bureau/QR-WiFi-NUMERICABLE-4B1E.png`

Scanne-le avec l'appareil photo → connexion automatique, plus jamais de mot de passe à taper. Tu peux l'imprimer et le coller près de la box pour les visiteurs.

⚠️ Il encode la config **cible** (`NUMERICABLE-4B1E` / `Pousseline1202` / WPA2). Il ne fonctionnera qu'**après** que j'aie appliqué la config sur la box — donc après le câble. Si tu changes la clé, dis-le-moi, je le régénère en 5 s.

**M1 sur `192.168.50.1` : non, et voici pourquoi c'est structurel**

| Test | Résultat |
|---|---|
| Ping `192.168.50.1` | ❌ 100 % de perte |
| Ports 22 / 80 / 1234 / 11434 | ❌ tous fermés |
| **Route empruntée** | `via 192.168.239.129 dev enx02093…` → **elle part dans la 4G Free** |

C'est le point clé : ta machine **n'est sur aucun réseau local**. Sa seule route est la clé 4G. Donc `192.168.50.1` n'est pas cherché sur ton LAN — il est envoyé vers Internet, où il n'existe pas.

J'ai testé M1 sur **4 adresses** : `192.168.1.85`, `10.42.0.1`, `192.168.0.85`, `192.168.50.1`. Toutes mortes, pour la même raison unique. **Ce n'est pas un problème d'adresse — aucune adresse ne marchera.** Tant que le M4 n'est pas raccordé physiquement à un réseau, M1 est hors d'atteinte, quel que soit son IP.

**État du dispatch**

| # | Tâche | État |
|---|---|---|
| 5 | QR code WiFi | ✅ **fait** |
| 1 | **Câble LAN 2 → M4** | 🔴 en cours — sonde armée |
| 2, 3, 4 | Config box, mdp admin, M1 | ⛔ bloqués par 1 |
| 6 | Tailscale | ⚪ p

[user] poursuit tout le paramétrage dispatche boriower os openclow navigateur plguin etc

[assistant] **BrowserOS lancé ✅ — mais OpenClaw, je ne le réactive pas, et c'est délibéré.**

**Ce qui tourne maintenant**

| Composant | État |
|---|---|
| BrowserOS v0.46.25 (Chromium 148) | ✅ **démarré**, 5 process |
| Serveur HTTP `:9200` | ✅ UP |
| CDP `:9100` | ✅ UP |
| Intégrations chargées | ✅ **45** |
| MCP déclarés (`.mcp.json`) | ✅ 23 serveurs |

**Ce que je refuse de lancer — OpenClaw / domino / cowork**

Tes garde-fous les ont mis en `disabled` après l'incident des **90 °C par boucle de rétroaction**, avec une consigne explicite : *ne jamais les réactiver sur M4 seul*. Or on est **exactement** dans ce cas :

| Condition | Maintenant |
|---|---|
| M1 disponible pour absorber la charge | ❌ **mort** (4 routes testées) |
| Température | 🔴 **83 °C — déjà au-dessus du seuil 82 °C** |
| RAM | 🟡 10/15 Gi, 7 conteneurs Docker |

Le simple lancement de BrowserOS a fait passer la machine de 77 → **83 °C**. Démarrer le dispatch OpenClaw par-dessus, sans M1 pour déporter, c'est rejouer la boucle à 90 °C — et cette fois tu n'as même pas de réseau pour reprendre la main.

**J'ai armé une surveillance thermique** (20 min) : alerte à 88 °C, arrêt recommandé à 93 °C. Je te préviens sans que tu aies à demander.

**Le déblocage reste le même, et il est unique**

OpenClaw et le dispatch parallèle n'ont de sens qu'avec **M1 pour porter la charge**. M1 revient avec le LAN. Le LAN revient avec le câble. **Câble LAN 2 → M4** débloque, dans l'ordre : M1 → dispatch multi-machines → OpenClaw sans risqu

[user] Back

Settings
Provider Settings
AI & Agents
Chat & Council Provider
Other
Customize BrowserOS
BrowserOS as MCP
Usage & Billing
Help
Docs
Features
Revisit Onboarding
BrowserOS MCP Server
Docs
Connect BrowserOS to MCP clients like Claude Code, Gemini CLI and others.

Server URL:
http://127.0.0.1:9001/mcp



Connected agents
Add BrowserOS as an MCP server in your AI agents — no copy-paste required.

1 of 4 connected
Claude Code
Connected
Disconnect
Claude Desktop
Connect
Cursor
Not installed
Get Cursor
VS Code
Connect
Codex
Connect
Zed
Not installed
Get Zed
Show manual setup

Available Tools
23 tools available


tabs
Manage browser tabs: list open pages (with their page ids), open a new page, or close one. Use the returned page id with snapshot/act/navigate.

tab_groups
Manage tab groups: list groups, group pages, update a group (title/color/collapsed), ungroup pages, or close a group. Page ids come from the tabs tool.

navigate
Navigate a page: load a url, or go back/forward/reload. Returns a fresh snapshot of the resulting page (navigation invalidates refs, so old [ref=eN] handles no longer apply).

snapshot
Capture the page as an indented accessibility tree. Each actionable element carries a stable [ref=eN] you pass to `act`. Iframe content is stitched in inline. Re-snapshot after navigation or large changes (refs are invalidated). This is the start of the loop: snapshot -> act -> (reads back a diff).

diff
Show what changed on the page since the last snapshot/diff - a cheap

[assistant] **BrowserOS MCP : vérifié, opérationnel — il ne manque qu'un redémarrage de session.**

| Contrôle | Résultat |
|---|---|
| Serveur MCP `:9001/mcp` | ✅ HTTP 200 |
| Port alternatif `:9201/mcp` (celui de ta config) | ✅ HTTP 200 — **les deux répondent, config correcte** |
| Enregistrement dans `~/.claude.json` | ✅ `browseros` présent |
| Ports ouverts | `9001`, `9201`, `9100` (CDP) |
| Outils annoncés | 23 |
| Température | 🟢 **redescendue à 79 °C** (pic 83 °C absorbé) |

**Le seul point à savoir :** j'ai cherché les outils `browseros` dans ma session — **ils n'y sont pas encore**. C'est normal et sans gravité : cette session Claude Code a démarré **avant** que je lance BrowserOS, donc elle n'a pas vu le serveur au moment de l'inventaire MCP. Le panneau affiche « Connected » côté BrowserOS, la config est bonne des deux côtés.

👉 **Redémarre la session Claude Code** et les 23 outils (`snapshot`, `act`, `navigate`, `read`, `grep`, `run`…) seront chargés. Aucune manipulation de config à faire — tout est déjà en place.

**État global du paramétrage**

| # | Tâche | État |
|---|---|---|
| 5 | QR code WiFi | ✅ fait — sur ton Bureau |
| 7 | Thermique post-BrowserOS | ✅ stabilisé 79 °C |
| — | BrowserOS + MCP + 45 intégrations | ✅ lancé |
| 1 | **Câble LAN 2 → M4** | 🔴 sonde armée, en attente |
| 2, 3, 4 | Box WPA2 · mdp admin · M1 | ⛔ bloqués par 1 |
| 6 | Tailscale | ⚪ prêt |

Tout ce qui était paramétrable **sans réseau local** est fait. OpenClaw reste volontairement à l'arrêt tant 

[assistant] Côté réseau, **non — rien n'est arrivé** :

| Contrôle | Résultat |
|---|---|
| `enp47s0` carrier | **0** — aucun signal électrique |
| Interface | **DOWN** |
| Box `192.168.0.1` | ❌ 100 % de perte |
| M1 (4 adresses) | ❌ toutes mortes |
| Seule route active | toujours la clé 4G Free |

Si tu parlais du **MCP BrowserOS**, alors oui — ça, c'est connecté ✅ (il te faut juste redémarrer la session Claude Code pour charger les 23 outils).

**Si tu as bien branché le câble**, alors le problème est ailleurs. Trois causes possibles, par ordre de fréquence :

1. **Le câble est mort** — c'est la panne n°1 sur les vieux câbles. Essaie celui qui est déjà dans **LAN 1** (le gris) : lui, tu sais qu'il fonctionne. Débranche-le de son appareil actuel et mets-le dans le M4.
2. **Mauvais port sur le M4** — le M4 a un port ethernet RJ45 ; vérifie que le clip du connecteur a fait « clic » des **deux** côtés.
3. **Aucune LED sur le port** — box comme M4 doivent allumer une petite LED verte/orange au branchement. **Pas de LED = pas de lien physique**, ça se voit à l'œil sans aucune commande.

Ma sonde tourne toujours en fond et surveille `enp47s0` toutes les 3 s. Je n'ai **rien** à faire de ton côté : refais le branchement, et si le lien s'établit, elle me prévient toute seule et j'enchaîne immédiatement sur la box, le WiFi et M1.

Dis-moi ce que tu vois sur les **LED des deux ports** — c'est le diagnostic le plus rapide.

[assistant] M1 est peut-être allumé, mais il reste **injoignable depuis le M4** — et c'est logique : les deux machines ne partagent aucun réseau. Le M4 n'a que la 4G, `enp47s0` et `wlo1` sont DOWN.

**Il existe un chemin qui contourne tout ça : Tailscale.** Il passe par Internet — donc par ta 4G — sans avoir besoin du LAN ni de la box. Je le lance.

[assistant] **Tailscale a généré ton lien de connexion.** C'est la voie qui joint M1 **sans câble et sans box** — elle passe par Internet via ta 4G.

Ouvre ce lien et connecte-toi (c'est une authentification, à toi de la faire — je n'y touche pas) :

```
https://login.tailscale.com/a/57d8e0b018ffd
```

Je relance le processus en fond pour qu'il se termine dès que tu as validé :

[assistant] **Source identifiée — et c'est bien une boucle de rétroaction.** Je coupe le plus gros poste.

[assistant] **BrowserOS coupé. Pic à 93 °C absorbé, ça redescend.**

| Instant | Temp | Load |
|---|---|---|
| Pic | 🔴 **93 °C** | 6,22 |
| Après fermeture | 🟠 88 °C | **4,34** ↓ |

BrowserOS n'apparaît plus dans le top CPU (2 process résiduels inoffensifs). Nouvelle veille armée : je te préviens au retour sous 80 °C, ou si ça remonte à 92 °C.

**Ce que le pic révèle — et ça valide la consigne d'origine**

Les process en cause au moment du pic :

| Process | CPU |
|---|---|
| BrowserOS (×2) | ~65 % |
| **MCP `jarvis-cluster`, `jarvis-agents`, `jarvis-memory`** | ~37 % |
| claude + claude-desktop | ~95 % |

Les serveurs MCP `jarvis-cluster` et `jarvis-agents` **tournent à vide en cherchant M1 et M2, qui sont injoignables**. C'est exactement la boucle de rétroaction qui avait mis le M4 à 90 °C en juin. Elle est repartie, non pas parce qu'on a réactivé le dispatch, mais parce que **M1 est absent** : les MCP retentent en boucle.

👉 C'est la démonstration nette qu'il ne faut **pas** lancer OpenClaw maintenant. Sans M1, chaque brique de dispatch ajoute de la chaleur sans produire de travail.

**Tailscale — l'action qui débloque vraiment**

Ton lien d'authentification est toujours valide, et c'est le seul chemin vers M1 qui ne dépende ni du câble ni de la box :

```
https://login.tailscale.com/a/57d8e0b018ffd
```

Connecte-toi dessus. Si M1 a aussi Tailscale, il apparaît immédiatement — via la 4G, sans LAN. Les MCP cluster cessent alors de boucler, la température retombe, et le dispatch redevie