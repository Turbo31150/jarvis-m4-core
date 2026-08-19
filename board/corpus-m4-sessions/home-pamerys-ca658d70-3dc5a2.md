[assistant] La page de doc d'abord, puis j'installe l'extension (« câbler » Chrome à OpenClaw).

[assistant] La doc est claire. Je passe à l'installation sur la machine : vérification du CLI OpenClaw, puis `openclaw browser extension install`.

[assistant] Le CLI installé ne connaît pas la commande `browser` — je vérifie la syntaxe disponible dans cette version.

[assistant] Pas de commande `browser` dans cette version (2026.7.1-2) — la doc décrit une version plus récente. Je vérifie s'il y a un plugin navigateur désactivé, sinon je mets à jour OpenClaw.

[assistant] Le plugin `browser` existe dans les extensions stock. Je vérifie son état et l'active si besoin.

[assistant] Le plugin stock `browser` existe (avec l'extension Chrome embarquée) mais n'est pas chargé. Je regarde la config OpenClaw.

[assistant] Le plugin `browser` n'est pas du tout chargé malgré `enabledByDefault: true`. Je passe en debug pour voir pourquoi le loader l'écarte.

[assistant] La commande `browser` est active. Je lance maintenant l'installation de l'extension.

[assistant] Gateway opérationnel (port 18789, plugin browser chargé). Je persiste un token d'auth (sinon il change à chaque redémarrage et casse l'appairage), puis je vérifie le statut navigateur.

[assistant] Le `config get` a renvoyé une valeur masquée (`__OPENCLAW_REDACTED__`) que j'ai écrite par erreur. Je corrige directement dans le JSON.

[assistant] La chaîne d'appairage est générée. Reste le mismatch de token — je soupçonne le drop-in systemd `ollama-cloud.conf` qui injecte un vieux token en variable d'environnement.

[assistant] Le service embarque un vieux token en dur (`Environment=GATEWAY_TOKEN=...`) qui écrase la config. Je le retire.

[assistant] Le client passe. Je corrige le token dans `.bashrc`, configure le profil navigateur en mode « extension », puis vérifie avec le doctor.

[assistant] La chaîne d'appairage est prête. La page du popup s'ouvre peut-être en onglet — je prends une capture d'écran X11 pour voir l'état et automatiser la saisie avec xdotool.

[user] [Image: original 6400x2160, displayed at 2000x675. Multiply coordinates by 3.20 to map to original image.]

[user] [Image: original 6400x2160, displayed at 2000x675. Multiply coordinates by 3.20 to map to original image.]

[user] [Image: original 6400x2160, displayed at 2000x675. Multiply coordinates by 3.20 to map to original image.]

[assistant] L'extension est bien active (le nom « OpenClaw Br » se résout) mais `popup.html` n'existe pas dans cette version. Je lis le manifest installé pour trouver le bon fichier.

[assistant] Pas de popup dans cette version — c'est une page d'options (`options.html`). Je navigue l'onglet dessus.

[user] [Image: original 2484x1356, displayed at 2000x1092. Multiply coordinates by 1.24 to map to original image.]

[assistant] La frappe a été déformée (clavier AZERTY + omnibox). Je passe par le presse-papier : xclip + Ctrl+V, bien plus fiable.

[user] [Image: original 2484x1356, displayed at 2000x1092. Multiply coordinates by 1.24 to map to original image.]

[assistant] La page « OpenClaw Browser Relay » est ouverte : il manque le Gateway token (port par défaut 18792). Je vérifie que le gateway écoute bien ce port relay, puis je colle le token et je sauvegarde.

[assistant] Le relay écoute sur 18799 (pas 18792). Je règle donc Port=18799 + token dans la page d'options. D'abord un contrôle rapide que le gateway est sain.

[user] [Image: original 2484x1356, displayed at 2000x1092. Multiply coordinates by 1.24 to map to original image.]

[assistant] Le relay atteint bien le gateway mais le token est rejeté — le endpoint `/extension` attend le token d'appairage dérivé (celui de la chaîne `#8920…`), pas le token brut. J'essaie avec.

[user] [Image: original 2484x1356, displayed at 2000x1092. Multiply coordinates by 1.24 to map to original image.]

[assistant] Toujours rejeté. Probable incompatibilité de protocole entre l'extension Web Store 2026.2.26 et le gateway 2026.7.1. Je regarde comment le gateway valide le token côté code.

[user] [Image: original 2484x1356, displayed at 2000x1092. Multiply coordinates by 1.24 to map to original image.]

[assistant] `chrome://extensions` est ouvert, mode développeur déjà actif. Je clique « Charger l'extension non empaquetée » et je saisis le chemin dans le dialogue de fichier.

[user] [Image: original 6400x2160, displayed at 2000x675. Multiply coordinates by 3.20 to map to original image.]

[user] [Image: original 6400x2160, displayed at 2000x675. Multiply coordinates by 3.20 to map to original image.]

[user] [Image: original 6400x2160, displayed at 2000x675. Multiply coordinates by 3.20 to map to original image.]

[user] [Image: original 2484x1356, displayed at 2000x1092. Multiply coordinates by 1.24 to map to original image.]

[assistant] L'extension ne semble pas chargée (rien dans les Preferences). Je filtre la page extensions sur « openclaw » pour en avoir le cœur net.

[user] [Image: original 2484x1356, displayed at 2000x1092. Multiply coordinates by 1.24 to map to original image.]

[assistant] La recherche est saisie mais la liste n'est pas encore filtrée. Je recapture après un délai.

[user] [Image: original 2484x1356, displayed at 2000x1092. Multiply coordinates by 1.24 to map to original image.]

[user] [Image: original 2936x2012, displayed at 2000x1371. Multiply coordinates by 1.47 to map to original image.]

[user] [Image: original 2484x1356, displayed at 2000x1092. Multiply coordinates by 1.24 to map to original image.]

[assistant] Le dialogue est resté ouvert — Enter n'a pas suffi. Je clique explicitement sur « Choisir ».

[assistant] Le dialogue n'existe plus (fermé). Vérifions si l'extension s'est chargée cette fois.

[user] [Image: original 2048x1152, displayed at 2000x1125. Multiply coordinates by 1.02 to map to original image.]

[assistant] ## Bilan — câblage de l'extension Chrome OpenClaw

**Tout le côté serveur est installé et vert.** Il ne reste qu'un geste manuel de 30 secondes dans Chrome (détaillé ci-dessous), car Chrome a été relancé en cours de route par la session Codex qui tourne en parallèle et affiche maintenant le sélecteur de profils — je ne choisis pas un profil à ta place.

### Ce qui est fait
1. **Plugin `browser` activé** dans OpenClaw (il existait mais n'était pas chargé) → la commande `openclaw browser …` fonctionne.
2. **Gateway réparé et démarré** : le service systemd pointait vers une installation morte (2026.3.11, `/usr/lib`) avec un vieux token en dur. Réinstallé proprement (2026.7.1-2), token d'authentification **persisté** (il changeait à chaque redémarrage), `~/.bashrc` mis à jour (il exportait l'ancien token qui écrasait tout). Le gateway écoute sur :18789 et le relay extension sur :18799.
3. **Diagnostic `openclaw browser doctor`** : gateway OK, plugin OK, profil `chrome (extension)` OK — il ne manque que la connexion de l'extension.
4. **Découverte importante** : l'extension « OpenClaw Browser Relay » déjà installée depuis le Web Store (v2026.2.26) est **incompatible** avec ce gateway (elle parle HTTP, le nouveau gateway attend du WebSocket). C'est elle qui affichait « Gateway token rejected ». Il faut charger la version fournie avec le CLI.
5. Garde-fou thermique respecté : seul le gateway est relancé, les boucles domino/cowork restent OFF, température à 65 °C. Mémoire sauvegardée