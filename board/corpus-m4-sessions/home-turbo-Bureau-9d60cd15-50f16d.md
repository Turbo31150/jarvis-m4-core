[user] répa'rtrion syst(eme bug fige immediat(ement mauvauis srésolution meme en mettant la boinn eil rebascuèle

[assistant] Je vais utiliser le skill de débogage systématique pour diagnostiquer ce problème d'affichage (résolution qui rebascule + gel système).

[user] Base directory for this skill: /home/turbo/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/systematic-debugging

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
   - Note line numbers, file paths, 

[assistant] Aucun processus n'utilise le montage. Je démonte et lance la réparation `e2fsck` (930 Go — je la lance en arrière-plan avec journal).

[assistant] ## ✅ Bilan de l'intervention

**1. Résolution qui rebasculait — RÉPARÉ à la source.** Ce n'était ni la TV ni le pilote : **trois scripts autostart se battaient entre eux** à chaque login/événement d'affichage — un forçait 1920×1080, un autre imposait 5 s plus tard un MetaMode NVIDIA 1280×720 avec underscan (l'origine de l'image bizarre 1252×1022), le troisième forçait 1280×720 avec panning. S'y ajoutait un `monitors.xml` GNOME stockant un mode 1360×768 qui n'existe plus sur la TV LG. Actions :
- Les 3 scripts sont désactivés (déplacés dans `~/.config/autostart-disabled/`, rien n'est supprimé).
- `monitors.xml` sauvegardé en `monitors.xml.bak-fige` puis purgé — GNOME le régénérera proprement.
- Underscan NVIDIA résiduel remis à zéro. **HDMI-0 est maintenant en 1920×1080+0+0 plein cadre**, et plus rien ne viendra l'écraser.

**2. Disque JARVIS-M1 (`/dev/sdb2`, 930 Go) — RÉPARÉ.** Le fsck au boot échouait (i-nœuds orphelins corrompus, erreur EFSBADCRC du 8 août) et le disque était monté en lecture seule dégradée. `e2fsck -f -y` a corrigé les erreurs, la seconde passe est **clean (RC=0)**, et le disque est **remonté en lecture-écriture** sur `/mnt/m1`. SMART : PASSED — le disque physique va bien, c'était une corruption logique (probablement un arrêt brutal lors d'un gel).

**3. « Erreur GPU 1 et crash » — pas de panne matérielle.** Aucune erreur Xid au kernel ; l'échec `nvidia-persistenced` était une course au démarrage (les `/dev/nvidia*` existent et les deux cartes répondent). 

[user] Stop hook feedback:
Système instable: 4 services failed, 0 zombies. Lancer service-auto-repair ou system-stabilization-mode avant de quitter.

[assistant] Je sonde l'endpoint LM Studio distant que vous m'indiquez (192.168.0.12:1234 — M2) et je regarde pourquoi `ccr` crashe réellement.