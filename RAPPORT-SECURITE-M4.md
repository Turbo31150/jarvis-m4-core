# Rapport de sécurisation — Machine M4 (pamerys-m4)
### Audit de session · preuve AVANT → APRÈS · confidentialité des données et du système
*Date : 2026-06-28 — fidèle au déroulé de la session.*

---

## 1. Objectif
Démontrer et renforcer la **confidentialité** des dossiers et du système M4, puis **ranger** toute l'infrastructure (apps → conteneurs organisés) avec un **index** et une **bibliothèque de commandes**. Méthode : **red-team autorisé** (se mettre dans la peau d'un attaquant ayant un accès local, sans mot de passe) pour prouver l'exposition réelle, puis durcir et **re-prouver**.

> **Principe directeur** : ne revendiquer que ce qui est **vérifiable**. Une preuve honnête (audit reproductible) vaut infiniment plus qu'une affirmation « c'est sécurisé ».

---

## 2. AVANT — état initial (vulnérable) · **prouvé**
Red-team local, accès utilisateur `pamerys`, **0 mot de passe**, ~3 minutes :

| # | Faille constatée | Preuve |
|---|---|---|
| 1 | **Aucun chiffrement disque** (pas de LUKS) | `/` et `/mnt/windows` en clair → disque volé = tout lisible |
| 2 | **773 bases SQLite en clair** | dont `jarvis-master.db` → table `linkedin_tokens` ; `rdv.db`, `planning.db`… lisibles sans clé |
| 3 | **Clé SSH `id_ed25519` sans passphrase** | utilisable telle quelle par un attaquant |
| 4 | **Token GitHub en clair** (`~/.git-credentials`) | `Turbo31150:ghp_…` |
| 5 | **~19 fichiers `.env` en clair** | `secrets.env`, `openclaw/.env`, `ollama/cloud.env`… |
| 6 | **« gitmore chiffré » inexistant** | git-crypt/sops/age **non installés** ; repos poussés en clair sur GitHub |
| 7 | **6 repos avec secrets réels sur GitHub** | clés Google `AIza`, tokens `ghp_`, 1 clé SSH privée |

**Mise au point technique faite en séance** : SHA-512 = *hachage irréversible*, **pas du chiffrement** ; le chiffrement « au repos » protège un **disque volé éteint**, pas un système en marche ; un conteneur Docker **n'est pas** une frontière de sécurité. → revendications corrigées pour rester défendables.

---

## 3. Actions mises en place (déroulé de la session)
1. **Coffre à secrets chiffré** `sops + age` (AES-256) — `~/jarvis/secrets-vault/` ; clé age `~/.config/sops/age/keys.txt` (chmod 600).
2. **Migration des secrets** vers le coffre (Telegram, Pinecone, Gemini, Anthropic, OpenClaw…) → `*.enc.env` versionnables (le **vrai** « gitmore chiffré »).
3. **Verrouillage** : 19 `.env` en `chmod 600` ; **docker secrets** (`redis_pass`, `pg_pass`).
4. **Nettoyage de 3 repos** (token GitHub, clé SSH, AWS de test) → rédaction + originaux **sauvegardés chiffrés** → commits locaux.
5. **Sauvegarde chiffrée** 16 Mo (coffre + 40 bases sensibles) → copie **locale + externe** (3-2-1 amorcé).
6. **Outils reproductibles** : `sec-audit.sh` (red-team rejouable), `cascade-harden-kit.sh` (réplication M1/M2/M5), `sec-decrypt.sh`.
7. **Organigramme conteneurs M4** : réseau `jarvis-bus`, **socle Redis** (bus), PostgreSQL, 2 sites conteneurisés + poussés au registry privé.
8. **Index + bibliothèque de commandes** : `jarvis-index.db` (SQLite), `INDEX.md`, `COMMANDS.md`, `CAHIER-DES-CHARGES-M4.md`.

---

## 4. APRÈS — état actuel (vérifiable)

| Domaine | AVANT | APRÈS | Statut |
|---|---|---|---|
| Gestion des secrets | clair partout | **coffre AES-256** (4 `.enc.env`) + docker secrets | ✅ corrigé |
| Tokens dans les repos | en clair, suivis | **rédigés** + originaux chiffrés au coffre (3 repos) | ✅ local (push sur GO) |
| Sauvegarde | aucune | **backup chiffré 16 Mo** (local + externe) | ✅ corrigé |
| Capacité d'audit | aucune | **audit red-team reproductible** (`sec-audit.sh`) | ✅ corrigé |
| Infra conteneurs | éparpillée | **organigramme** (jarvis/business/data) + bus Redis | 🟢 amorcé |
| Documentation | aucune | index SQL + bibliothèque commandes + CdC | ✅ corrigé |

---

## 5. Preuve AVANT / APRÈS (synthèse honnête)

| Point | AVANT | APRÈS |
|---|---|---|
| Secrets applicatifs (API keys…) | clair | **chiffrés AES-256** ✅ |
| Mot de passe Redis/Postgres | n/a | **docker secrets** ✅ |
| Sauvegarde de récupération | ❌ | **chiffrée, 2 copies** ✅ |
| « gitmore » (secrets chiffrés versionnables) | inexistant | **opérationnel** ✅ |
| Re-jouer l'audit à tout moment | ❌ | **`bash sec-audit.sh`** ✅ |

---

## 6. Reste à faire — transparence (ne PAS prétendre « invulnérable »)
Ces points **étaient** vulnérables et **le restent** tant que non traités — roadmap dans le cahier des charges :

| Résiduel | Pourquoi | Vague |
|---|---|---|
| **Disque non chiffré** (LUKS) | non appliqué | à planifier |
| **773 SQLite encore en clair** | SQLCipher non encore appliqué | V3 (30-data) |
| **Clé SSH sans passphrase** | `ssh-keygen -p` à exécuter par toi | V1 |
| **Tokens non régénérés** | ton choix (clés déclarées mortes/sans valeur) | au choix |
| **3 repos non poussés** + secrets dans l'historique GitHub | pas de réécriture d'historique (décision) | V8 (sur GO) |
| **Clé Pinecone en dur** dans le code | à révoquer | V1 |

> **Conclusion honnête** : on est passé de **« tout exposé en clair »** à **« secrets applicatifs chiffrés, sauvegardés, auditables et documentés »**. La **couche secrets est sécurisée** ; le durcissement complet (disque, bases, rotation, push propre) est **engagé et planifié**, pas terminé. C'est *cette* honnêteté qui rend la preuve crédible devant un client ou un expert.

---

## 7. Annexes (livrables de la session)
- `~/jarvis/CAHIER-DES-CHARGES-M4.md` — plan d'exécution (organigramme + todo V1→V8)
- `~/jarvis/stacks/INDEX.md` · `COMMANDS.md` · `jarvis-index.db` — index + bibliothèque de commandes
- `~/jarvis/scripts/sec-audit.sh` · `cascade-harden-kit.sh` · `sec-decrypt.sh` — outils
- `~/jarvis/secrets-vault/*.enc.env` — coffre chiffré · `~/jarvis/backups/*.age` — sauvegarde chiffrée
- `~/alkymia-communication/` — site V2.1 + posts (volet commercial)
