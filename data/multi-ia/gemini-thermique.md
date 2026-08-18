Voici le plan d'action hiérarchisé par **gain réel mesurable**, du plus fort impact immédiat au réglage d'optimisation de fond.

---

### 1. Identifier et purger les processus fantômes (Gain RAM : ~8 à 12 Go / Impact Température : Immédiat)
Chrome ne prend que 2,9 Go sur les ~14 Go occupés. Le reste est consommé par d'autres processus (Docker, conteneurs, IDE Electron, serveurs LLM/Python locaux, compilations suspendues).

```bash
# 1. Lister le TOP 10 des processus par consommation mémoire réelle (RSS)
ps aux --sort=-%mem | awk 'NR<=11{print $2, $4, $11}'

# 2. Lister le TOP des consommateurs de Swap
for file in /proc/[0-9]*/status; do
    awk '/VmSwap|Name/{printf $2 " " $3 " "}END{ print ""}' "$file" 2>/dev/null
done | grep -v '0 kB' | sort -k3 -n -r | head -n 10
```
* **Action** : Stopper/tuer les conteneurs orphelins (`docker stop $(docker ps -q)`), les daemons de build (`gradle`, `rustc`, `webpack`), ou les instances d'environnements de développement zombies.

---

### 2. Éliminer le *Swap Thrashing* et passer à ZRAM (Gain Température : -15°C à -25°C / Gain Réactivité : Massif)
Avec 17 Go de swap sur disque (probablement NVMe/SSD), le CPU passe son temps en `kswapd0` / `iowait` à transférer des pages en boucle, ce qui sature le bus et maintient les cœurs à 100% de charge thermique.

1. **Régler le Swappiness** pour forcer l'OS à n'utiliser le swap qu'en cas de nécessité absolue :
   ```bash
   sudo sysctl -w vm.swappiness=10
   sudo sysctl -w vm.vfs_cache_pressure=50
   # Persistance dans /etc/sysctl.d/99-sysctl.conf
   echo -e "vm.swappiness=10\nvm.vfs_cache_pressure=50" | sudo tee -a /etc/sysctl.d/99-sysctl.conf
   ```

2. **Remplacer le swap disque par ZRAM** (compression RAM ultra-rapide LZ4/zstd) :
   ```bash
   # Sur Debian/Ubuntu :
   sudo apt install -y zram-tools
   echo -e "ALGO=zstd\nPERCENT=50" | sudo tee /etc/default/zramswap
   sudo systemctl restart zramswap

   # Sur Fedora/Arch :
   sudo systemctl enable --now zram-generator
   ```

3. **Vider le swap disque saturé** (une fois la RAM libérée sous les 10 Go) :
   ```bash
   sudo swapoff -a && sudo swapon -a
   ```

---

### 3. Caper le Turbo Boost et le Governor CPU (Gain Température : -15°C à -30°C immédiat)
À 95°C, les 12 cœurs montent au pic de fréquence (Turbo Boost) sur des micro-tâches, ce qui dépasse l'enveloppe thermique (TDP) du châssis.

1. **Désactiver temporairement le Turbo Boost** :
   ```bash
   # Pour CPU Intel :
   echo "1" | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo

   # Pour CPU AMD :
   echo "0" | sudo tee /sys/devices/system/cpu/cpufreq/boost
   ```

2. **Passer en profil Powersave / Balanced** :
   ```bash
   sudo cpupower frequency-set -g powersave
   # Ou via power-profiles-daemon :
   powerprofilesctl set balanced
   ```

3. **Installer et activer thermald / TLP** :
   ```bash
   sudo apt install -y thermald tlp  # (ou dnf / pacman selon distro)
   sudo systemctl enable --now thermald
   sudo tlp start
   ```

---

### 4. Réduire l'empreinte de Chrome (Gain RAM : ~1,5 à 2 Go / Gain CPU : -10%)
1. **Activer l'économiseur de mémoire natif** :
   - URL : `chrome://settings/performance` → Activer **Économiseur de mémoire (Memory Saver)** en mode *Agressif*.
2. **Désactiver l'accélération logicielle CPU et forcer VA-API** :
   - URL : `chrome://settings/system` → Vérifier que **Utiliser l'accélération graphique** est activé (évite que le CPU 12 cœurs décode les vidéos à la place de l'iGPU).
3. **Limiter les processus d'arrière-plan** :
   - Désactiver "Conserver les applications en arrière-plan après fermeture".
   - Tuer les onglets lourds via le gestionnaire interne : `Shift + Esc`.

---

### 5. Nettoyer les caches noyau et les indexeurs Linux (Gain RAM : ~1 Go / Gain CPU de fond)
1. **Désactiver les indexeurs de fichiers de bureau (Tracker / Baloo)** :
   ```bash
   # GNOME Tracker :
   tracker3 daemon stop && tracker3 reset -s
   systemctl --user mask tracker-miner-fs-3.service tracker-extract-3.service

   # KDE Baloo :
   balooctl suspend && balooctl disable
   ```
2. **Purger le cache disque immédiat** :
   ```bash
   sync; echo 3 | sudo tee /proc/sys/vm/drop_caches
   ```

---

### Synthèse des gains attendus

| Action | Gain RAM estimé | Gain Température estimé |
|---|---|---|
| **Kill processus zombies + arrêt swap thrashing** | **6 à 10 Go** | **-15°C à -20°C** |
| **Désactivation Turbo Boost / Profil CPU** | Neutre | **-15°C à -25°C** (stoppe la garde thermique) |
| **Passage à ZRAM + Swappiness=10** | **2 à 4 Go (compressés)** | **-5°C à -10°C** (fin des I/O intempestifs) |
| **Optimisations Chrome + Tracker GNOME** | **1,5 à 2,5 Go** | **-3°C à -5°C** |
