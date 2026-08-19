[user] Diagnostique un service de transcription vocale mort sur cette machine (M1, Ubuntu, hôte turbo-MS-7C56, utilisateur turbo).

PROBLÈME
Le port 9743 ne répond pas. Une sonde sur http://127.0.0.1:9743/health échoue. D'après la documentation interne, 9743 = « WhisperFlow STT » (speech-to-text), utilisé notamment par une application Android compagnon (Lumenflow) pour la transcription d'appels.

TA MISSION
1. Identifier le programme derrière WhisperFlow : quel exécutable, lancé par quoi. Cherche largement — `systemctl list-units --all | grep -iE 'whisper|stt|lumen'`, idem en `systemctl --user`, puis grep de "9743" dans /home/turbo/jarvis (bin/, scripts/, .claude/skills/), /home/turbo/.config/systemd/user/, /etc/systemd/system/, /home/turbo/Workspaces, et `docker ps -a`.
2. Établir la cause de l'arrêt : jamais démarré au boot ? planté ? modèle Whisper absent ? VRAM insuffisante ? dépendance Python cassée ? Lis les journaux de l'unité si elle existe.
3. Vérifier s'il y a un CONFLIT DE RESSOURCE : cette machine a 5 GPU NVIDIA et fait tourner des LLM (LM Studio port 1234, Ollama port 11434). Un service Whisper qui squatte de la VRAM est un problème connu ici. Relève l'état GPU avec `nvidia-smi --query-gpu=index,name,memory.used,memory.total,temperature.gpu --format=csv` et regarde si un processus whisper y figure (`nvidia-smi --query-compute-apps=pid,used_memory,name --format=csv`).

PIÈGES DE CET ENVIRONNEMENT
- `sleep` en avant-plan est bloqué par le harnais (exit 144) — utilise `tim

[assistant] Found the lead: `/etc/systemd/system/jarvis-whisper-bridge.service` contains 9743. Let me dig in.

[assistant] Now let me read the bridge script and identify who holds 9742, plus the WhisperFlow autostart unit.

[assistant] The reference points to `jarvis-whisper-api.service` on 9743 — and the user unit list showed it **masked**. Let me confirm.

[assistant] Journal is empty — let me pin down the exact timeline and check the model cache.

[assistant] Confirmed: `jarvis_whisper_api.py` prints "Starting on :9743". Now the timeline and who disabled it.

[assistant] Timeline is now clear — a deliberate escalating shutdown. Let me confirm the "why" and check the boot orchestrator's skip.

[assistant] Found the smoking gun in memory. Let me read it fully and take a final GPU reading.

[assistant] One last check — whether the acoustic-loop guard is still armed (it determines if restarting is safe).

[assistant] Diagnostic terminé. Le port 9743 n'est pas tombé en panne : il a été **coupé volontairement**, avec un triple verrou.

## 1. Le programme derrière 9743

| Élément | Valeur |
|---|---|
| Unité | `jarvis-whisper-api.service` (scope **système**, pas user) |
| Exécutable | `/home/turbo/IA/Core/jarvis/core/jarvis_whisper_api.py` (Flask) |
| Preuve du port | ligne 863 : `print(f"[JARVIS Whisper API] Starting on :9743 ...")` |
| Bind | `0.0.0.0:9743` (LAN, atteint par le S9/Lumenflow) |
| Modèle | `large-v3-turbo`, `int8_float16`, `CUDA_VISIBLE_DEVICES=3` |

Ne pas confondre avec les 3 autres briques vocales, toutes vivantes :
- `jarvis-whisper.service` (user) → `whisper-server.py` sur **:8789** — dictée PTT, PID 3935, **2148 MiB sur GPU1**
- `jarvis-lumen.service` (user) → hub Multi-IA STT/TTS
- `jarvis-whisper-bridge.service` (système, `disabled`) → `whisper_bridge.py`, proxy **9742 → 9743**. Le port 9742 est actuellement squatté par `jv-dg-gateway.py` (PID 3941), pas par le bridge.

## 2. Cause de l'arrêt — coupure délibérée, pas un plantage

Trois verrous indépendants, posés en escalade :

| Date (ctime) | Verrou | Fichier |
|---|---|---|
| 2026-07-16 21:02 | **masque scope user** | `~/.config/systemd/user/jarvis-whisper-api.service` → symlink vers `/dev/null` |
| 2026-07-22 23:46 | **`Restart=no`** | `/etc/systemd/system/jarvis-whisper-api.service.d/zz-norestart.conf` |
| 2026-07-23 00:35 | **unité renommée** | `/etc/systemd/system/jarvis-whisper-api.service.DISABLED-turbo` (pl