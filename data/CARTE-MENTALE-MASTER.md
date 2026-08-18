# 🧠🗺 CARTE MENTALE MAÎTRESSE — Écosystème JARVIS

> Vue unifiée des 3 axes du système + le planning qui les relie. Généré 0-token.
> Détails : [`CARTE-MENTALE-GITHUB.md`] (repos) · [`CARTE-MENTALE.md`] (dominos) · [`CHRONOLOGIE-NARRATION.md`] (temps).

```
                          ÉCOSYSTÈME JARVIS
                                 │
     ┌───────────────────────────┼───────────────────────────┐
     │                           │                           │
  📦 REPOS                    🁣 DOMINOS                  🕰 CHRONOLOGIE
  (structure)                 (action)                    (temps)
     │                           │                           │
 170 dépôts GitHub          397 dominos runnables       10 184 entrées
 15 thèmes · 18 publics     + ~31 chaînes GitHub        2025-10-31 → 2026-07-23
     │                           │                           │
     └───────────────┬───────────┴───────────┬───────────────┘
                     │                       │
              🗂 PLANNING UNIFIÉ (le liant)  │
              jarvis-plan.py · 9 192 tâches │
              (backlog + master + domino 397 + report 7218)
                     │
              🖥 COCKPIT :8899 (3 cartes live) + timers auto (refresh 20min · batch 30min)
```

## 📦 Axe REPOS — 170 dépôts (structure du système)
Top thèmes : Alkymia/Sites (27) · IA/ML/Tools (23) · Trading (21) · JARVIS core/OS/cluster (15) ·
PassCerfa (5) · SQL/Backup (5) · n8n (5) · M4/Machines (5) · Mirra (3) · Voice (3) · Divers (53).
**18 publics** (dont `jarvis-os-public` = pitch commercial, à surveiller ; 8 forks tiers sans risque).
→ Détail : `CARTE-MENTALE-GITHUB.md`.

## 🁣 Axe DOMINOS — 397 actions runnables (comportement)
- **154+ compilés** (base vive `domino_chains`+`action_series`) + **184 séries** biblio + **5 agent-chains** jarvis-core.
- Sources GitHub : `labo-bibliotheque-centrale` (source-of-truth) · `jarvis-core` (moteur) · `jarvis-linux` (7 chaînes n8n prod) · `jarvis-cowork` (vocal).
- Runner `dominos`, repo privé `jarvis-dominos`, AUTO illimité + batch planifié, garde-fous dry-run/danger.
→ Détail : `CARTE-MENTALE.md`.

## 🕰 Axe CHRONOLOGIE — 10 184 entrées sur 9 mois (évolution)
Fondations trading (nov.2025) → orchestrateur cluster (fév.2026) → expansion produit (avr.–mai) →
**pic infra multi-machine (05/06)** → audits 360/sécurité (fin juin) → verticalisation métier
(PassCerfa/PDP, OMEGA Mairie — juillet). Fil rouge : traçabilité + doctrine 0-token/cluster local.
→ Détail narratif : `CHRONOLOGIE-NARRATION.md` · brut : `CHRONOLOGIE.md`.

## 🗂 Le LIANT — Planning unifié
`jarvis-plan.py` fusionne les 3 axes en **9 192 tâches** actionnables préchargées (overlay dédié,
sources en lecture seule). Le cockpit `:8899` affiche Dominos + Chronologie en cartes live,
auto-rafraîchies par 2 timers systemd. Chaque tâche porte sa commande prête (`dominos <x>`, `xdg-open <report>`).

## 🔑 Chiffres-clés
| | |
|---|---|
| Repos GitHub | 170 (18 publics) |
| Dominos runnables | 397 (+ ~31 chaînes GitHub) |
| Chronologie | 10 184 entrées (9 mois) |
| Tâches planning | 9 192 (préchargées) |
| Timers auto | 2 (plan-refresh 20min · dominos-batch 30min) |
| Secrets exposés | 0 (selftest ✅) |
