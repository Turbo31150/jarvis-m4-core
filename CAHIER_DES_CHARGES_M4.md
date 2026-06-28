# Cahier des charges — Optimisation & Autonomie M4 (ASUS TUF F15)

> Version 1.0 · 2026-06-27 · Machine : pamerys-m4 (FX506HC) · Identité : pamerys

## 1. Contexte
M4 = nœud laptop du cluster JARVIS, isolé (M1/M2/M5 offline). Doit fonctionner **autonome**.
- CPU : Tiger Lake-H 6c/12t · GPU : **RTX 3050 Mobile** (driver désactivé) + Intel UHD
- RAM 15 Go · NVMe 468 Go (38%) · Session **Wayland** · CPU-only pour le LLM

## 2. Objectifs
| # | Objectif | Mesurable |
|---|---|---|
| O1 | Performance CPU **soutenue** (anti-throttling) | Maintenir >2.7 GHz all-core, <90°C |
| O2 | Réactiver le **dGPU RTX 3050** | `nvidia-smi` fonctionnel |
| O3 | **Profil complet** de la machine | Bench CPU+RAM+NVMe+GPU documenté |
| O4 | Cascade LLM locale robuste | Ollama local + cloud + LM Studio :1234 |
| O5 | Identité **pamerys** pure | 0 résidu /home/turbo actif |

## 3. Périmètre
**Inclus** : undervolt CPU (O1), déblocage driver nvidia (O2), benchmarks (O3), wiring cascade (O4).
**Exclus** : remplacement pâte thermique (matériel), achat composants.

## 4. Contraintes & risques
| Contrainte | Impact | Mitigation |
|---|---|---|
| Châssis thermalement limité (95°C) | Throttling | Undervolt > overclock |
| Undervolt parfois **locké par BIOS** (Plundervolt) | Pas d'UV possible | Vérifier MSR 0x150 avant |
| dGPU réactivation = **reboot** | Coupure session | Préparer config, reboot planifié |
| Undervolt agressif = **crash** | Instabilité | Paliers prudents (-50/-80mV), test stabilité |

## 5. Méthode (workflow structuré récurrent)
1. **Todolist dynamique** : chaque tâche trackée (pending→in_progress→completed)
2. **Cascade de délégation** (CLAUDE.md) : tâches routinières → `lm-ask.sh` (Ollama local), orchestration/décisions critiques → Opus
3. **Plan validé** avant toute action irréversible (reboot, undervolt)
4. **Vérification** : chaque changement mesuré (bench avant/après)

## 6. Critères d'acceptation
- [ ] O1 : boost soutenu mesuré (bench après undervolt > bench avant)
- [ ] O2 : `nvidia-smi` liste le RTX 3050 après reboot
- [ ] O3 : tableau bench CPU/RAM/NVMe/GPU complet
- [ ] O4 : `lm-ask.sh` répond en solo (Ollama) + `--cloud` après signin
- [ ] O5 : `grep -rl /home/turbo` sur configs actives = vide

## 7. Plan d'exécution (todolist)
Voir tâches #7+ : bench complet → faisabilité undervolt → préparation dGPU → application UV → reboot/validation.
