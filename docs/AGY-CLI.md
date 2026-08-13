# agy — Antigravity CLI : installation et câblage complet

Installé le 13/08/2026 sur la machine labo (M4). Version **1.1.12**.

## Origine

| Source | Version | Retenu |
|---|---|---|
| `~/m1-recover/cli/local-bin/agy` (disque M1 récupéré) | 1.1.11 | non |
| `~/m1-disk/.local/bin/agy` | **1.1.12** | **oui** |

> `~/m1-disk` n'est pas un disque hors ligne : c'est un **montage SSHFS
> `turbo@10.42.0.1:/home/turbo`**, c'est-à-dire **M6 en direct** (câble). Le
> binaire et les credentials viennent donc d'une machine vivante.

## Ce qui a été installé

| Élément | Chemin | Note |
|---|---|---|
| Binaire | `~/.local/bin/agy` | 201 Mo, ELF statique Go |
| Alias | `~/.local/bin/antigravity-cli` → `agy` | remplace le symlink cassé de M1 |
| PATH | ajouté par `agy install` à `.bashrc`, `.zshrc`, `.bash_profile`, `.profile` | |
| Token OAuth | `~/.gemini/antigravity-cli/antigravity-oauth-token` | chmod 600, **jamais versionné** |
| Réglages | `~/.gemini/antigravity-cli/settings.json` | workspaces réécrits en chemins locaux |

### Deux points de vigilance

1. **Token partagé avec M6.** Le même jeton OAuth sert désormais sur deux
   machines. Un rafraîchissement concurrent peut invalider la session de
   l'autre. Si `agy` réclame une reconnexion, lancer `agy` sans argument pour
   refaire le login (interactif, navigateur).
2. **`toolPermission: always-proceed`** — réglage repris de M6 : `agy` approuve
   automatiquement toutes les demandes d'outil, y compris les commandes shell.
   Pour repasser en mode confirmation, éditer `settings.json`.

## Vérification (faite)

```
$ agy --version
1.1.12
$ agy models          → 15 modèles
$ agy -p "Réponds en un mot: fonctionnel?" --model gemini-3.7-flash-low
Opérationnel.
```

## Modèles disponibles (compte Antigravity, 0 token facturé côté API Anthropic)

| ID | Nom |
|---|---|
| `gemini-3.7-flash-high` / `-medium` / `-low` | Gemini 3.7 Flash |
| `gemini-3.6-flash-high` / `-medium` / `-low` | Gemini 3.6 Flash |
| `gemini-3.5-flash-high` / `-medium` / `-low` | Gemini 3.5 Flash |
| `gemini-3.1-pro-high` / `-low` | Gemini 3.1 Pro |
| `claude-sonnet-4-6` | Claude Sonnet 4.6 (Thinking) |
| `claude-opus-4-6-thinking` | Claude Opus 4.6 (Thinking) |
| `gpt-oss-120b-medium` | GPT-OSS 120B |

## Tous les paramètres

### Options de session

| Flag | Effet |
|---|---|
| `-p`, `--print`, `--prompt` | un prompt, réponse imprimée, non interactif |
| `-i`, `--prompt-interactive` | prompt initial puis session interactive |
| `-c`, `--continue` | reprend la conversation la plus récente |
| `--conversation <ID>` | reprend une conversation précise |
| `--model <id>` | modèle de la session (voir table ci-dessus) |
| `--effort low\|medium\|high` | effort de raisonnement |
| `--agent <nom>` | agent de la session |
| `--mode accept-edits\|plan` | mode d'exécution de l'agent |
| `--add-dir <chemin>` | ajoute un dossier au workspace (répétable) |
| `--project <ID>` / `--new-project` | rattache ou crée un projet |
| `--output-format text\|json\|stream-json` | format en mode print |
| `--json-schema <schéma\|fichier>` | force une sortie structurée |
| `--print-timeout <durée>` | délai du mode print (défaut 5m) |
| `--sandbox` | restrictions terminal |
| `--dangerously-skip-permissions` | auto-approuve tout (à éviter) |
| `--disable-slash-commands` | désactive commandes slash et skills |
| `--log-file <chemin>` | fichier de log |

### Sous-commandes

| Commande | Rôle |
|---|---|
| `agy agents` / `agy agent` | liste les agents (actuellement : aucun) |
| `agy models` | liste les modèles |
| `agy plugin list\|install\|uninstall\|enable\|disable` | plugins (actuellement : aucun) |
| `agy changelog` | notes de version |
| `agy install` | (re)configure PATH et profils shell |
| `agy update` | met à jour le CLI |
| `agy help <sous-commande>` | aide détaillée |

## Recettes

```bash
# Réponse courte, 0 token facturé
agy -p "résume ce fichier" --model gemini-3.7-flash-low

# Sortie JSON structurée exploitable par un script
agy -p "extrais les erreurs" --output-format json --json-schema ./schema.json

# Session sur le dépôt jarvis, mode plan (aucune écriture)
agy -i "audite l'orchestrateur" --add-dir ~/jarvis --mode plan

# Reprendre le dernier échange
agy -c
```

## Emplacements d'état

| Chemin | Contenu |
|---|---|
| `~/.gemini/antigravity-cli/` | token, settings, conversations, logs, cache |
| `~/.gemini/antigravity-cli/cli.log` | log courant (symlink) |
| `~/.gemini/antigravity/` | état partagé avec l'application Antigravity |

L'application de bureau Antigravity n'est **pas** installée ici
(`/opt/Antigravity-x64` absent) : seul le CLI fonctionne. Sur M6, elle est en
`~/apps/Antigravity-x64`.
