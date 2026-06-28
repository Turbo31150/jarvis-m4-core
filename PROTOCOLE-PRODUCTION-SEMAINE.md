# Protocole de production hebdomadaire — M4 (entreprise Jarvis-M4)

> Mise en production immédiate + cadence d'exploitation « une semaine de travail ». Automatisé par
> `~/jarvis/scripts/routine-production.sh` (cron **7h tous les jours**, léger, sans boucle — anti-surchauffe).
> Rapports quotidiens : `~/jarvis/reports/jour-AAAA-MM-JJ.md`.

## Statut production (renforcé)
| Renforcement | État |
|---|---|
| Limites mémoire sur tous les services | ✅ (sites 64M · redis/registry/portainer 256M · postgres 512M) |
| Redis non exposé (overlay-only + auth) | ✅ |
| Healthchecks | ✅ redis · postgres · 2 sites |
| Restart auto + persistance au reboot | ✅ (docker enabled, Swarm relance) |
| Gouverneur thermique actif | ✅ (cible 82 °C) |
| Sauvegardes chiffrées | ✅ quotidiennes + hebdo |

## Cadence hebdomadaire (la « semaine de travail »)
| Jour | Opérations automatiques |
|---|---|
| **Tous les jours (7h)** | Rapport santé services + RAM/thermique · **backup chiffré** (dump postgres + volume n8n) |
| **Lundi** | + **Audit sécurité complet** (`sec-audit.sh`) = kickoff semaine, liste le résiduel à durcir |
| **Mercredi** | + Revue mi-semaine (services, file n8n) *(à enrichir)* |
| **Vendredi** | + **Backup hebdo complet** (tous volumes) + **rotation** (purge > 14 j) |
| **Samedi/Dimanche** | + Maintenance légère (nettoyage images orphelines) |

## Protocole d'évolution (déployer sans casser)
1. **Modifier** un compose dans `~/jarvis/stacks/<entité>/`.
2. **Déployer** : `docker stack deploy -c <compose> <stack>` (rolling, zéro coupure).
3. **Vérifier** : `docker service ls` (1/1) + healthcheck + test HTTP.
4. **Rollback** si KO : `docker service rollback <service>`.
5. **Sauvegarder** avant toute migration risquée (volume) : voir `COMMANDS.md` (mots-clés *backup*).
6. **Committer + pousser** (`jarvis-m4-core`), secrets jamais en clair (`.gitignore` + coffre sops+age).

## Reste à industrialiser (vagues V4→V8 du cahier des charges)
10-ia routeur LLM · migration n8n en queue Redis · sqlite-bridge · 40-voice · tradeoracle/healthcare/factures ·
gitleaks-scan + push des 3 repos nettoyés · **SQLCipher** sur les bases sensibles · **LUKS** (chiffrement disque).

## Commandes clés (bibliothèque)
```bash
bash ~/jarvis/scripts/routine-production.sh lun   # forcer une journée type
cat ~/jarvis/reports/jour-$(date +%F).md          # rapport du jour
sqlite3 ~/jarvis/stacks/jarvis-index.db "SELECT command FROM commands WHERE label LIKE '%backup%'"
docker service ls; docker stack ls                # état production
```
