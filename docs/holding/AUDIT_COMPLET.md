# AUDIT COMPLET JARVIS OS — 2026-08-17 23:43:36 (régénéré par jarvis_audit_protocol.sh)

> Audit **READ-ONLY** reproductible · aucun service modifié · cascade déterministe 0-token.
> Source : `scripts/jarvis_audit_protocol.sh` · détail historique : AUDIT_CONTAINERS_N8N.md, AUDIT_GITHUB_ARCHI.md, AUDIT_CMDLIB_COMMANDE.md.


## 1. Système — 🟡 ORANGE

| Métrique | Valeur |
|---|---|
| Services failed (system / user) | 0 / 1 |
| RAM | 10050/15759 MiB (63%) |
| Swap | 0/0 MiB (0%) |
| Load (1m) / cœurs | 0.83 / 12 |
| Zombies / D-state | 3 (seuil 10) / 0 |
| GPU | GPU0 44°C 16/4096MiB  |

## 2. Containers — 🟡 ORANGE

| Métrique | Valeur |
|---|---|
| Containers jv-* up | 0 / 24 |
| Unhealthy | 0 |
| Restarting | 0 |
| Restart-loop (RestartCount≥3) | 0 |
| Réseaux jvnet-* | 0 |

## 3. n8n — 🟢 VERT

| Métrique | Valeur |
|---|---|
| Webhook /healthz | HTTP 200 |
| Workflows actifs | 65 / 65 |
| Exéc 24h (historique) | ✅ 0 / ❌ 0 → taux 0% |
| Exéc FRAIS (depuis restart ? UTC) | ✅ 0 / ❌ 0 → taux 0% |

> Distinction clé : le taux **24h** peut être pollué par des erreurs **antérieures** au dernier restart du container (ex. bug historique déjà corrigé). Le verdict n8n se fonde sur le taux **FRAIS** (exécutions depuis le démarrage réel du container).

## 4. cmdlib (PostgreSQL) — 🟡 ORANGE

| Métrique | Valeur |
|---|---|
| Container PG (détecté dynamiquement) | data_postgres.1.li9vv3qa8gebvngmh2kofuzg3 |
| Health | healthy |
| Table commands | n/a |
| Table holding_index | n/a |
| Table library_series | n/a |

## 5. Git — 🟡 ORANGE

| Métrique | Valeur |
|---|---|
| Branche | refonte-prof-ia-symbiose |
| Ahead / Behind upstream | 0 / 0 |
| Fichiers non commités | 845 |
| Remote origin | https://github.com/Turbo31150/jarvis-m4-core.git |

## 6. LLM — 🔴 ROUGE

| Probe (multi-essai 3×/2s) | État |
|---|---|
| LMS :1234 | DOWN |
| Proxy :18800/health | ok |
| Gateway :9742 | up |
| lm-ask.sh (1 essai) | ko (non bloquant) |

---

## VERDICT GLOBAL : 🔴 ROUGE

| Domaine | Verdict |
|---|---|
| Système | 🟡 ORANGE |
| Containers | 🟡 ORANGE |
| n8n | 🟢 VERT |
| cmdlib | 🟡 ORANGE |
| Git | 🟡 ORANGE |
| LLM | 🔴 ROUGE |

## Anomalies détectées

- P2 · 1 service(s) systemd **user** en échec : docs-externes-refresh.service
- P2 · 0/24 containers jv-* up (manquants)
- P2 · cmdlib : requête psql sans retour (DB pas prête ?) sur data_postgres.1.li9vv3qa8gebvngmh2kofuzg3
- P1 · remote 'origin' ≠ jarvis-core (=https://github.com/Turbo31150/jarvis-m4-core.git) → `git push origin` viserait le mauvais dépôt
- P2 · 845 fichier(s) non commité(s)
- P1 · LMS :1234 DOWN (3 essais échoués)


_Régénéré le 2026-08-17 23:43:36 par `scripts/jarvis_audit_protocol.sh` (read-only, 0-token)._
