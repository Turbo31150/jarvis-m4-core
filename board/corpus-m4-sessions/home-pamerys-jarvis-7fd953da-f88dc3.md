[user] <local-command-stdout>CLAUDE_CODE_EFFORT_LEVEL=high overrides effort this session — clear it and ultracode takes over</local-command-stdout>

[user] <local-command-stdout>[38;2;255;120;20m↯[39m Fast mode ON · $10/$50 per Mtok</local-command-stdout>

[user] Base directory for this skill: /home/pamerys/.claude/plugins/cache/claude-plugins-official/superpowers/6.1.1/skills/systematic-debugging

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

**Violating the letter of this process is violating the spirit of debugging.**

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## When to Use

Use for ANY technical issue:
- Test failures
- Bugs in production
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues

**Use this ESPECIALLY when:**
- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You've already tried multiple fixes
- Previous fix didn't work
- You don't fully understand the issue

**Don't skip when:**
- Issue seems simple (simple bugs have root causes too)
- You're in a hurry (rushing guarantees rework)
- Manager wants it fixed NOW (systematic is faster than thrashing)

## The Four Phases

You MUST complete each phase before proceeding to the next.

### Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

1. **Read Error Messages Carefully**
   - Don't skip past errors or warnings
   - They often contain the exact solution
   - Read stack traces completely
   - Note line numbers, file paths

[assistant] Je détecte d'abord le matériel réel avant d'installer quoi que ce soit — pas de paquets au hasard.

[assistant] Matériel identifié — **tous les drivers sont déjà chargés et fonctionnels** (NVIDIA RTX 3050 ✓, Intel UHD ✓, WiFi AX201 ✓, Ethernet Realtek ✓, audio ✓). Le seul qui ne marche pas = **le Bluetooth** (service arrêté + désactivé). Je le règle.

[assistant] Tout est prêt côté matériel/paquets. Il ne manque qu'à **relancer et activer le service**.

[assistant] ✅ **Bluetooth activé** — service `active` + `enabled`, contrôleur "JARVIS · PAMERYS · M4" `Powered: yes`. Il apparaît maintenant dans les réglages, tu peux appairer.

Maintenant je vérifie proprement s'il manque un driver — je scanne les pilotes recommandés + tout périphérique sans module.

[assistant] Les 4 "sans driver" sont normaux (host bridge, SRAM, ISA, GNA — aucun driver requis). Un seul point réel : la version du driver NVIDIA. Je compare l'installé vs le recommandé.

[assistant] Bilan — **ton ASUS TUF F15 (FX506HC) est déjà 100 % piloté**. Rien à installer, tout le matériel a son driver chargé. Le seul élément mort était le Bluetooth, corrigé.

| Composant | Driver | État |
|---|---|---|
| **Bluetooth** Intel AX201 | btintel/btusb | ✅ **réparé** (service activé + `Powered: yes`) |
| GPU NVIDIA RTX 3050 | nvidia-595 (= recommandé) | ✅ à jour |
| iGPU Intel UHD (TigerLake) | i915/xe | ✅ |
| WiFi 6 AX201 | iwlwifi | ✅ |
| Ethernet Realtek RTL8168 | r8169 | ✅ |
| Audio | snd_hda_intel | ✅ |
| Plateforme ASUS (Fn, rétroéclairage clavier) | asus_nb_wmi / asus_wmi | ✅ (LED `asus::kbd_backlight` détectée) |
| Firmware / microcode | linux-firmware + intel-microcode | ✅ installés |

Les 4 périphériques "sans driver" (host bridge, SRAM, ISA, GNA) sont normaux — aucun pilote requis.

**Seule option restante** (facultative, non installée) : `asusctl` + `supergfxctl` pour piloter courbes de ventilo, Aura RGB et bascule GPU hybride/dédié. Ça vient d'un PPA tiers — dis-moi si tu le veux, je l'ajoute proprement.

Au passage tu as collé `http://192.168.0.1/Numconfig.asp` (page config box/routeur) — sans rapport avec les drivers. Tu voulais faire quoi avec ?

[assistant] PPA absent, cargo absent. La voie propre sur Ubuntu 24.04 = le PPA communautaire **g-los** (maintenu, builds noble). Je l'ajoute et j'installe.

[assistant] PPA g-los supprimé (n'existe plus). La seule voie propre restante = **build depuis les sources** (méthode officielle asus-linux.org). Je prépare les dépendances + Rust, puis je compile les deux.

[assistant] Dépendances OK. J'installe Rust via rustup (toolchain stable, requise pour asusctl récent).

[assistant] Rust 1.97.1 prêt. Je compile **supergfxctl** puis **asusctl** depuis les dépôts officiels asus-linux.

[assistant] Cloné : supergfxctl 5.2.7, asusctl 6.3.8. Je compile supergfxctl (build long, en arrière-plan).

[assistant] Pendant la compilation, je vérifie les besoins d'asusctl (sa GUI peut demander des libs en plus).

[assistant] asusctl (avec sa GUI rog-control-center) demande des libs supplémentaires. Je les installe pendant que supergfxctl compile.

[assistant] Je laisse supergfxctl finir de compiler — je serai notifié. En attendant je lance la compilation d'asusctl en parallèle (deux cœurs distincts, ça gagne du temps).

[assistant] Les deux compilations tournent en arrière-plan. J'attends leurs notifications de fin avant d'installer et d'activer les services.

[assistant] Peu importe le suivi de tâches — j'attends simplement la fin des deux compilations (je serai notifié). Rien à faire d'ici là.

[assistant] supergfxd est `active` + `enabled` ✅. La commande `supergfxctl -g` se bloque (dbus pas encore prêt / lecture interactive). Je coupe et je requête avec timeout.

[assistant] ✅ **supergfxctl opérationnel** — daemon actif, mode GPU actuel = **Hybrid** (Optimus), PM auto sur la RTX 3050. asusctl compile encore (build plus lourd avec la GUI). J'attends sa fin.

[assistant] Tout est installé et fonctionnel. Récapitulatif complet :

| Outil | Version | Service | Ce que ça pilote |
|---|---|---|---|
| **asusctl** | 6.3.8 | `asusd` active | Profils ventilo (Quiet/Balanced/Performance), RGB clavier Aura, LEDs, batterie (seuil de charge), armoury/firmware |
| **supergfxctl** | 5.2.7 | `supergfxd` active/enabled | Bascule GPU : Hybrid ↔ Integrated (autonomie) ↔ dGPU |
| **Bluetooth** | bluez 5.72 | `bluetooth` active/enabled | (réparé en début de session) |

État lu sur ta machine : profil ventilo = **Balanced**, mode GPU = **Hybrid**.

**Commandes utiles au quotidien :**
```bash
asusctl profile set Performance     # ventilo à fond (jeu)
asusctl profile set Quiet           # silencieux (batterie)
asusctl profile get                 # profil courant
asusctl leds -h                     # rétroéclairage clavier / Aura
asusctl -c 60                       # limiter charge batterie à 60%
supergfxctl -m Integrated           # couper la RTX 3050 → grosse autonomie (reboot/logout requis)
supergfxctl -m Hybrid               # remettre Optimus
supergfxctl -g                      # mode GPU actuel
```
Une **GUI** est aussi installée : cherche **« ROG Control Center »** dans tes applis (mêmes réglages en graphique).

Notes :
- `supergfxctl -m Integrated` demande de fermer la session (X redémarre) pour couper physiquement le GPU NVIDIA — c'est là qu'on gagne le plus de batterie.
- Sources dans `~/build-asus/` : pour mettre à jour plus tard → `cd ~/build-asus/asusct