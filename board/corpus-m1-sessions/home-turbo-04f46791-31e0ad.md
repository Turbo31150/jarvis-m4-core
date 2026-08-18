[assistant] **[OPUS]** Cause trouvée — ce n'est pas Claude Code, c'est la RAM.

## Diagnostic

| Preuve | Constat |
|---|---|
| Signature Oops | `__lruvec_stat_mod_folio+0x48` — **identique** sur boot -5 et boot -1 |
| Victimes | `llama-server`, `python3`, `nordvpnd`, `npm exec chrome`, `HeapHelper` — **aléatoires** |
| Registre corrompu | `RAX: ff558df4e6704000` au lieu de `ffff8df4e6704000` → **2 bits inversés** dans un pointeur noyau |
| MCE | `MC27_STATUS` Corrected Error (L3/IO) à 22:40 — 3 min avant l'Oops |
| Fin | `Fixing recursive fault but reboot is needed!` ×2 → écran mort |

**Cause racine — mélange de kits RAM hors spec :**

| Canal | Barrettes | Kit nominal | Tourne à |
|---|---|---|---|
| A | 2× 8 Go `CMW16GX4M2D3600C18` | 3600 CL18 | **3400** |
| B | 2× 16 Go `CMH32GX4M2E3200C16` | **3200** CL16 | **3400** |

4 DIMMs de deux kits différents, dont un kit certifié 3200, tous forcés à 3400 MT/s sur le contrôleur mémoire du 5700X3D. Aucune ECC pour rattraper. Résultat : bit flips silencieux → corruption des page tables → Oops quand le noyau libère la mémoire d'un process.

**Rôle de Claude Code** : déclencheur, pas coupable. `npm exec chrome` (le MCP chrome-devtools) et les MCP Node allouent/libèrent massivement → exposent le défaut. Comme `llama-server` l'avait fait à 17:50.

★ Insight ─────────────────────────────────────
`__lruvec_stat_mod_folio` ne plante jamais par bug logiciel : c'est un simple incrément de compteur sur une structure `pglist_data`. Si son pointeur est i

[assistant] Sentinelle posée et déjà déclenchée (exit 1 = comportement voulu). Je bascule sur LM Studio.

[assistant] **Réponse : le crash a effacé le réglage.**

`~/.lmstudio/.internal/http-server-config.json` → `"networkInterface": "127.0.0.1"`, fichier écrit à **22:42**. L'Oops noyau a frappé à **22:44:02**, avant que LM Studio persiste le réglage LAN sur disque. Au redémarrage (22:46) il est reparti sur son défaut localhost. Le `socat` sur `192.168.122.1:1234` est l'interface libvirt, pas le LAN — d'où `lan:000` sur `192.168.0.10`.

Je remets le LAN.

[assistant] Le `socat` était un fantôme (process déjà mort — cohérent avec l'instabilité). Je relance.

[assistant] Un `socat` se régénère en boucle (pid 3252 → 110640) et squatte le port. Je trouve son parent.

[assistant] Architecture comprise : `socat-lms-lan.service` **est** le pont LAN prévu (`192.168.0.10:1234 → 127.0.0.1:1234`). LM Studio doit donc rester en localhost. Ma modif `0.0.0.0` était contraire à ce design — je la remets et je relance le vrai serveur.

[assistant] `--bind` existe, et mon premier appel a laissé l'état sur `0.0.0.0`. Je force explicitement.

[assistant] LAN restauré. Et j'ai la **vraie** cause racine, plus précise que mon hypothèse initiale.

[assistant] Le script dit lui-même : *« jamais 0.0.0.0 pour ne pas entrer en conflit avec le bind localhost de LM Studio »*. La variable d'env contredisait ce design. Je l'aligne et j'automatise.

[assistant] ## Bilan

**Deux problèmes distincts, les deux traités.**

### 1. Le crash — matériel, pas Claude Code

| | |
|---|---|
| Signature | `__lruvec_stat_mod_folio+0x48` sur 2 boots (17:50 et 22:44) |
| Victimes | `llama-server`, `python3`, `nordvpnd`, `npm exec chrome`, `HeapHelper` — aléatoires |
| Preuve | `RAX: ff558df4e6704000` au lieu de `ffff8df4e6704000` → **2 bits inversés** |
| Cause | 2 kits RAM différents (3600C18 + **3200**C16), 4 DIMMs, tous à **3400 MT/s**, sans ECC |

Claude Code n'est que le déclencheur : les MCP Node/Chrome allouent massivement et exposent le bit flip — exactement comme `llama-server` l'avait fait 5 h plus tôt.

### 2. LM Studio hors réseau — conflit de port révélé par le crash

`LMS_SERVER_HOST=0.0.0.0` contre `socat-lms-lan.service` qui tenait déjà `192.168.0.10:1234`. Course au démarrage : le crash a inversé l'ordre, socat a gagné, LMS n'a plus rien pu bind → **plus aucun LLM**, ni LAN ni localhost.

✅ **Rétabli** — `localhost:1234 → 200`, `192.168.0.10:1234 → 200`, 7 modèles servis (`qwen3.5-9b` ×5, nomic-embed, gpt-oss-20b).

### Automatisation posée

| Élément | Rôle |
|---|---|
| `~/jarvis/scripts/kernel-oops-sentinel.sh` | Détecte Oops (boot précédent + courant), MCE, kits RAM mixtes |
| `kernel-oops-sentinel.timer` (user) | Au boot +2 min, puis chaque heure · **actif** |
| Table `kernel_oops` de `jarvis_logs.db` | Historique traçable · 1ʳᵉ entrée : `CRASH_PRECEDENT+RAM_MIXTE` |
| `LMS_SERVER_HOST=127.0.0.1` | Conflit socat supprimé durab