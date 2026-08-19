[assistant] LM Studio répond en 29 ms. Le gel est peut-être sur l'inférence elle-même. Je teste une vraie complétion et j'inspecte l'état système via SSH.

[assistant] Compris — c'est le **bureau graphique** de M6 qui est figé, pas les services (LM Studio répond, mais lentement : 16 s pour 10 tokens, signe de contention). Je passe en SSH pour diagnostiquer la session graphique.

[assistant] **Diagnostic posé : ce n'est pas un plantage, c'est un effondrement mémoire (thrashing).** M6 a 598 Mi de RAM libre, 18 Gi de swap consommés et un load de 19. GNOME est vivant mais affamé — chaque rafraîchissement d'écran attend des pages disque. Je mesure précisément qui mange la RAM.

[assistant] Cause racine identifiée précisément. Je vérifie qui sert réellement l'API avant de trancher, pour ne pas casser la production LLM.

[assistant] Tout est clair. **LM Studio (PID 182118) empile ses workers sans les décharger** : 3 modèles chargés simultanément (dont un doublon Qwen3.5-9B fantôme depuis 03h25 avec 8,5 Go en swap, et un Coder-14B en cours de chargement à l'instant, en état D). Aucun n'a de connexion active. Je libère la RAM immédiatement.

[assistant] `lms` est disponible. **13,1 Go sont immobilisés par deux instances IDLE du même Qwen3.5-9B** (doublon), pendant qu'un Coder-14B génère. Je décharge les deux IDLE — geste propre et réversible, LM Studio les rechargera à la demande.

[assistant] RAM disponible passée de **878 Mi à 7,4 Gi**, swap de 19 → 10 Gi, pression mémoire divisée par deux. Je ramène maintenant GNOME du swap vers la RAM.

[assistant] **Bureau M6 réparé** : GNOME Shell relancé, RSS 411 Mo, **swap = 0 Mo**, serveur X réactif. Je passe à tes deux demandes — inventaire des disques et de la mémoire compressée.

[assistant] Découverte capitale : **les deux dispositifs que tu demandes existent déjà sur M6.** Je vérifie leur réglage et j'attaque la cause racine.

[assistant] Le bureau se rétablit vite (pression mémoire 62 → **7,25**, load 19 → 10,9). J'ai trouvé la cause racine exacte dans la config. Je l'inspecte pour la corriger durablement.

[assistant] Cause racine confirmée : **`TTL enabled=False` sur Qwen3.5-9B** (jamais déchargé → l'instance fantôme de 03h25) et **garde-fou de chargement en mode `low`**. Je corrige la config, avec sauvegarde.

[assistant] Config corrigée. Mais LM Studio peut réécrire ses fichiers en se fermant — je pose donc un **garde-fou système indépendant** pour que le bureau ne puisse plus jamais être étouffé.

[assistant] Garde-fou actif. J'optimise maintenant le tampon SSD/zram et je vérifie l'état final.

[assistant] Un fichier existant (`99-zram-swappiness.conf`) écrasait mon réglage par ordre alphabétique. Je corrige et je protège explicitement la session graphique contre l'expulsion.

[assistant] La capture révèle la **cause racine profonde** : un cycle automatique de 15 min exécutait `lms load` en boucle. Je le traque.

[assistant] Écran noir alors que X répond à 0,00 s → c'est probablement une mise en veille DPMS ou un écran mal réactivé après la relance du shell. Je vérifie et je réveille l'affichage.

[assistant] La session X a changé depuis ma capture — **le cookie d'authentification n'est plus valide et la session 2 n'existe plus**. GDM a relancé quelque chose. J'inspecte l'état réel.

[assistant] Trouvé. **Ce n'est pas un plantage : le siège d'affichage est basculé sur une console texte (tty3), pas sur le bureau (tty2).** Une nouvelle session X tourne bien sur tty2 mais elle est inactive — d'où l'écran noir. Les logs le confirment (`systemd-logind: got pause` = Xorg a perdu les périphériques). Je rebascule.

[assistant] Bascule réussie : VT actif **tty3 → tty2**, session graphique **Active=yes**. Je confirme visuellement.

[assistant] DISPLAY réel = **`:1`** (la session a été recréée). L'écran HDMI-0 est bien connecté en 1920×1080, pas de veille DPMS — mais **`gnome-screenshot` a expiré**, ce qui pointe vers un compositeur bloqué. Je capture directement depuis X, sans passer par GNOME, pour trancher.

[assistant] M6 est **vivante** (ping 1,38 ms, LM Studio répond en 10 ms) — c'est **sshd seul qui est tombé**. Je cherche un canal de reprise.

[assistant] Le port **3389 (RDP)** est ouvert — c'est mon canal de reprise. Je fais d'abord un état précis des services.

[assistant] M6 se dégrade : **SSH et LM Studio sont tombés**, nginx et les services Python répondent encore. Signature d'un OOM killer. J'explore les canaux restants.

[assistant] LM Studio est **revenu tout seul**, mais sshd reste mort (rien n'écoute sur 22). Le port RDP est ma voie de reprise. Je vérifie l'outillage sur M4.

[assistant] **Port 9090 = Cockpit** (administration système web) — voie de reprise possible sans SSH. Je vérifie.

[assistant] Cockpit n'en est pas un (404), et sshd ne revient pas après plusieurs minutes. **J'ai perdu le canal d'administration sur M6.** Je prépare la voie de reprise graphique par RDP sur ton écran M4.

[assistant] RDP de M6 **négocie correctement** (X.224 Connection Confirm, protocole NLA) — `gnome-remote-desktop` est vivant. Je t'ouvre la connexion sur ton écran M4.