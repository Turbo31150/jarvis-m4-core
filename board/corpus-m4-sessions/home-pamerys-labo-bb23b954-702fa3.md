[assistant] Les deux écrans connectés sont déjà actifs, aucune sortie n'est éteinte :

| Sortie | Écran | État | Résolution | Position |
|---|---|---|---|---|
| eDP-1 | laptop (principal) | 🟢 ON | 1920x1080 @144Hz | à gauche (+0+0) |
| HDMI-1 | écran 2 (externe) | 🟢 ON | 1920x1080 @50Hz | à droite (+1920+0) |

DP-1, HDMI-2, DP-1-0…3 = **déconnectés** (rien branché).

Donc « tous en marche » = déjà le cas : mode étendu, écran 2 à droite du laptop. Si un écran est noir malgré ça, c'est physique (câble/source). Tu veux que je change quelque chose — écran 2 en **miroir** du principal, le passer **principal**, ou monter son taux à 60Hz ?

[user] <local-command-stdout>CLAUDE_CODE_EFFORT_LEVEL=high overrides effort this session — clear it and ultracode takes over</local-command-stdout>

[user] <local-command-stdout>[38;2;255;120;20m↯[39m Fast mode ON · $10/$50 per Mtok</local-command-stdout>

[assistant] Écran 2 actif côté système (60Hz) mais noir physiquement. Je teste le signal en le forçant off→on, puis en miroir pour vérifier que l'image arrive.

[assistant] GNOME/mutter tourne. J'ai remis HDMI-1 en **miroir** (même image que le laptop) — le signal est renvoyé.

Regarde l'écran 2 maintenant :

- **Il affiche le bureau (copie du laptop)** → le signal passe, le "noir" venait du bureau étendu vide. Je le repasse en étendu proprement.
- **Toujours noir** → c'est physique : câble HDMI, port, ou entrée/source de l'écran (vérifie le bouton source du moniteur + le câble des 2 côtés).

Lequel des deux ?

[assistant] Le système voit bien l'écran (EDID valide, lien OK, 0 erreur kernel). Donc **le câble et le port marchent** — l'écran dialogue. Je vérifie sa résolution native : peut-être qu'on lui envoie 1080p alors qu'il attend mieux, d'où l'écran noir.

[assistant] C'est une **TV LCD 32"** (`32W_LCD_TV`), pas un moniteur PC — et les TV sont capricieuses sur le HDMI. L'EDID passe (dialogue DDC OK) mais l'image peut être rejetée. Je force un mode que **toutes les TV acceptent** (720p@60) pour faire apparaître une image :

[assistant] Signal envoyé en **720p60 miroir** (mode universel TV).

C'est une TV, donc si elle est **toujours noire**, ce n'est plus le PC — le PC envoie bien l'image. Vérifie **sur la TV avec la télécommande** :

1. **Bouton `SOURCE` / `INPUT`** → sélectionne le bon **HDMI** (HDMI1, HDMI2…) — celui où le câble est branché. C'est la cause n°1 d'écran noir sur TV.
2. Câble HDMI bien enfoncé des **2 côtés** (PC + TV).
3. Essaie l'**autre prise HDMI** de la TV si doute.

Dis-moi ce que la TV affiche quand tu changes la source (« pas de signal », logo HDMI, ou toujours noir) — j'ajuste ensuite (retour en 1080p ou étendu).

[assistant] PC envoie bien l'image (EDID + mode universel), mais la TV reste noire. Possible cause plus profonde : GPU hybride où le port HDMI est câblé sur un GPU secondaire qui ne "scanne" pas réellement. Je vérifie la topologie GPU + si le connecteur a bien un CRTC actif :

[assistant] Diagnostic clé trouvé : le port HDMI est câblé sur le **GPU Intel** (`card1`, celui qui rend GNOME), il a un **CRTC actif (CRTC 1)** et scanne réellement en 720p60. Donc **le PC envoie physiquement un vrai signal vidéo** — ce n'est ni PRIME, ni le NVIDIA, ni un souci logiciel.

L'EDID se lit sur des fils **séparés** (DDC) des fils vidéo (TMDS). Résultat : « connecté + noir » alors que tout est bon côté PC pointe vers **2 causes physiques** :

| Cause probable | Test |
|---|---|
| 🥇 **Câble HDMI abîmé** (fils DDC OK → détecté, fils vidéo cassés → noir) | **Change le câble** — cause n°1 de ce symptôme exact |
| 🥈 TV sur mauvaise **source** | Télécommande TV → `SOURCE` → le bon HDMI |

Vérif du lien vidéo côté PC :

[assistant] « Ça a marché déjà » → l'écran a déjà fonctionné, donc câble + TV sont bons. Le lien est `Good`. Je remets la config propre native — **1080p60 en écran étendu à droite** — et je force une redétection, ce qui relance souvent l'image :

[assistant] Config restaurée : **écran 2 en 1080p60, étendu à droite** du laptop. Tout est vert côté PC (lien Good, CRTC actif, GPU Intel qui scanne réellement).

État final :

| Écran | État | Résolution |
|---|---|---|
| eDP-1 (laptop) | 🟢 principal | 1920x1080 @144Hz |
| HDMI-1 (TV) | 🟢 étendu à droite | 1920x1080 @60Hz |

Si la TV affiche l'image maintenant → c'est bon. Si toujours noire malgré « ça a marché déjà », l'action physique restante est côté TV : **débranche/rebranche le câble HDMI** ou **change la source** sur la télécommande — le PC, lui, envoie un signal valide. Dis-moi ce que tu vois.