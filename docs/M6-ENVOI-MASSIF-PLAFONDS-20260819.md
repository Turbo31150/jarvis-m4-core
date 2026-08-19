# 🔌 M6 — CE QUE LE CÂBLE ET LE NŒUD TIENNENT VRAIMENT
**Mesuré le 2026-08-19 après-midi depuis M4 · banc reproductible · aucune valeur déclarative**

Déclencheur : Turbo — « câble respecte envoi massif ». Le tableur LM Studio annonçait
1 Gb/s, `parallel: 4` et 5 modèles sur 4 GPU. Trois de ces quatre affirmations sont fausses.

---

## 1. LE FIL — 280 Mbit/s, PAS 1 Gb/s

| Mesure | Valeur | Méthode |
|---|---|---|
| Lien négocié (`ethtool`) | 1000 Mb/s | déclaratif |
| **Débit TCP réel vers :80 / :5678 / :9108** | **~280 Mbit/s** | push TCP 8 s, 3 services |
| Taux d'exploitation du gigabit | **28 %** | 280/1000 |
| RTT (300 paquets 1400 o, 2 ms) | 1,42 ms · **0 % perte** | `ping -s 1400` |
| Erreurs / drops interface | 0 err RX · 0 err TX · 16 drop TX | `ip -s link` |

### Cause racine — l'adaptateur gigabit est sur un bus USB 2.0
```
ID 0b95:1790 ASIX AX88179 Gigabit Ethernet
/sys/bus/usb/devices/3-3.1/speed = 480      <-- USB 2.0
Bus 003 root_hub .......... 480M            <-- plafond du bus
  |__ Port 002  Mass Storage (SSD M1) ..... 480M   <-- MÊME BUS, en concurrence
  |__ Port 003  Hub ....................... 480M
      |__ Port 001  cdc_ncm (le câble M6) . 480M
```
Un adaptateur *gigabit* branché derrière un **hub USB 2.0**. Le bus sature avant le fil.
**Aggravant** : le SSD M1 (931 Go) partage ce même bus 480 Mbit/s — chaque envoi massif
entre en concurrence avec les accès disque.

### ✅ Correctif — physique, gratuit, ×3,3 attendu
Deux contrôleurs rapides sont **libres** sur cette machine :
```
Bus 004 root_hub .... 20000M/x2   (USB 3.2 Gen 2x2)
Bus 002 root_hub .... 10000M      (USB 3.2 Gen 2)
```
→ **Débrancher l'AX88179 du hub et le mettre en direct sur un port bleu/rouge (bus 2 ou 4).**
Vérification après coup : `cat /sys/class/net/enxf8e43b9b67d4/../speed` doit afficher **5000**.

---

## 2. LM STUDIO — LE VRAI GOULOT : 33,6 Mbit/s

| Service sur M6 | Débit d'ingestion |
|---|---|
| `:80` | 280,5 Mbit/s |
| `:9108` (BrowserOS) | 278,5 Mbit/s |
| `:5678` (n8n) | 268,7 Mbit/s |
| **`:1234` (LM Studio)** | **33,6 Mbit/s** |

Même machine, même câble, même instant : LM Studio n'avale que **12 %** de ce que le fil
lui apporte. Le goulot est **applicatif**, pas réseau. Rebrancher l'USB ne le corrigera pas.

---

## 3. LA CONCURRENCE CASSE LE NŒUD — `parallel: 4` EST FAUX

| Requêtes simultanées | Résultat |
|---|---|
| 1 | passe (lentement) |
| **2** | **`HTTPError`** |
| 4 | 2 réussies / 2 `Remote end closed connection` |
| 8 et 16 | **`Connection refused`** — le port cesse d'accepter |

Le nœud **se relève seul** (vérifié : :1234 de nouveau debout, 4 modèles chargés, aucun
service annexe perdu). Mais **l'envoi massif doit être sérialisé** : concurrence **1**.

---

## 4. LATENCE EFFONDRÉE — 4 MODÈLES SE DISPUTENT LA VRAM

- CLAUDE.md (matin, 2 modèles chargés) : **2,9 à 7,4 s**
- Mesure de cet après-midi (4 modèles résidents) : **75,6 s pour 10 tokens**

Le tableur impose `ttl: 0` + `mlock` — les modèles **ne se déchargent jamais**. Avec
deepseek-r1-8B + qwen3.5-9B + coder-14B + embeddings résidents, la contention est permanente.
Le `n_gpu_layers: 999999 / 0 % CPU` annoncé n'est **pas** ce qu'on observe.

---

## 5. PIÈGE RÉPONSE VIDE — `reasoning_tokens`

```json
"usage": {"completion_tokens": 10,
          "completion_tokens_details": {"reasoning_tokens": 10}}
"content": ""            <-- VIDE, après 75 s facturées en latence
```
`qwen/qwen3.5-9b` et `deepseek-r1` sont des modèles **à raisonnement** : un `max_tokens`
faible est intégralement consommé par le raisonnement caché et le texte revient vide.
**Plancher `max_tokens` ≥ 512.** C'est la cause des « Pas de réponse » de la passerelle.

---

## 6. NON VÉRIFIÉ — À NE PAS CITER COMME ACQUIS

Le mappage 4-GPU du tableur (RTX 2060 / RTX 3080 / 2× GTX 1660S, 34 Go VRAM, VRAM par pôle)
**n'a pas pu être confirmé** : le **port 22 de M6 refuse la connexion**, aucun `nvidia-smi`
n'est atteignable depuis M4. Seuls l'endpoint HTTP et le fil ont été sondés.
Le script `/home/turbo/.local/bin/jarvis-boot-lock.sh` cité au tableur pointe l'utilisateur
`turbo`, pas `pamerys` — chemin non vérifiable depuis cette machine.

---

## 7. OUTIL DE MISE EN PLACE

`~/jarvis/bin/m6-envoi-massif` — calibré sur ces mesures :
concurrence 1 · plancher 512 tokens · backoff 5/15/40 s · repli Ollama · file SQLite
persistante (`~/jarvis/logs/m6_envoi_massif.db`) · journal `jarvis_logs.db`.

```bash
m6-envoi-massif ajouter prompts.txt --lot campagne   # 1 prompt par ligne
m6-envoi-massif vider   --lot campagne               # écoule sans casser le nœud
m6-envoi-massif etat                                 # file + état réel des modèles
```

---

## 8. ⚠️ ARBITRAGE ASSUMÉ SUR LE DÉLAI — À RELIRE QUAND M6 SERA SOIGNÉ

`TIMEOUT_S` est réglé à **120 s** et le **disjoncteur écarte M6 après 2 échecs** dans un lot.
Ce réglage est calibré sur un nœud **en état dégradé** (4 modèles résidents).

**Conséquence à connaître** : dans cet état, M6 met 75 s pour 10 tokens. Une génération
légitime de 512 tokens dépasserait donc largement 120 s et serait **coupée par le garde-fou**,
puis basculée en repli. Le garde-fou protège le débit du lot, pas la fidélité au nœud.

Il n'existe pas de bon réglage tant que le nœud est dans cet état : soit on attend des
minutes par demande, soit on coupe des générations valides. **Le vrai correctif est en amont.**

### Correctif amont — à faire sur la tour (hors de portée depuis M4)
Le port 22 de M6 refuse la connexion : ni SSH, ni `lms unload`, ni `nvidia-smi` depuis M4.
L'action doit être faite **devant la machine** :
1. Décharger `qwen2.5-coder-14b-instruct` et `deepseek-r1-0528-qwen3-8b` dans LM Studio.
2. Ne garder résidents que `qwen/qwen3.5-9b` + `text-embedding-nomic-embed-text-v1.5`
   — c'est la configuration où la latence mesurée était de **2,9 à 7,4 s**.
3. Le `ttl: 0` + `mlock` du tableur empêche tout déchargement automatique : c'est ce réglage
   qui transforme « 5 modèles disponibles » en « 4 modèles qui s'étranglent ».
4. Une fois soigné, remonter `TIMEOUT_S` à 240 s et relire cet arbitrage.

### Puis, pour le fil
Rebrancher l'AX88179 sur le bus 004 (20 Gb/s) ou 002 (10 Gb/s) — voir §1.
