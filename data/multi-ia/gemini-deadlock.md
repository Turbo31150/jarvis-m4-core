Sur Linux, un thread en **état D (`TASK_UNINTERRUPTIBLE`)** attend une ressource dans l'espace noyau et **ignore tous les signaux POSIX** (y compris `kill -9`). Si le sémaphore noyau NVIDIA est verrouillé (souvent parce que Xorg a crashé/zombifié ou que la 2e carte a rencontré une erreur de bus PCIe / GPU fall-off), **il n'existe pas d'appel système pour libérer directement un sémaphore noyau**.

Cependant, vous pouvez tenter une séquence de **récupération bas niveau (PCIe bus reset + rechargement de modules)** sans redémarrer le serveur.

---

### Séquence de déblocage étape par étape

#### Étape 1 : Couper l'environnement graphique et tuer les accès CUDA
Xorg détient le verrou modeset. Il faut libérer les descripteurs de fichiers sur `/dev/nvidia*`.

```bash
# 1. Basculer en mode multi-utilisateur sans serveur X (arrête gdm, lightdm, sddm)
sudo systemctl isolate multi-user.target

# 2. Tuer tout ce qui touche encore aux devices nvidia
sudo fuser -k -9 /dev/nvidia*
sudo killall -9 Xorg Xwayland llama-server 2>/dev/null || true
```
> **Risques :** Fermeture brutale de votre session graphique et de toutes les applications ouvertes. Les processus en état D ne disparaîtront pas immédiatement de la table des processus tant que le verrou noyau n'est pas levé.

---

#### Étape 2 : Forcer le Reset et le Rescan PCIe du GPU défaillant
La 2nde carte a chuté du bus (device handle perdu dans `nvidia-smi` mais présente dans `lspci`).

1. Récupérez l'identifiant PCIe (BDF) de la 2e carte :
   ```bash
   lspci -D | grep -i nvidia
   # Exemple : 0000:01:00.0
   ```
2. Tentez un reset matériel PCIe :
   ```bash
   GPU_BDF="0000:01:00.0"  # Remplacer par votre BDF exact

   # Tenter le reset PCIe direct
   echo 1 | sudo tee /sys/bus/pci/devices/$GPU_BDF/reset
   ```
3. Si le reset échoue ou ne débloque rien, retirez et rescanniez la carte sur l'arbre PCI :
   ```bash
   # Désassocier le driver et retirer le device du bus
   echo "$GPU_BDF" | sudo tee /sys/bus/pci/devices/$GPU_BDF/driver/unbind 2>/dev/null || true
   echo 1 | sudo tee /sys/bus/pci/devices/$GPU_BDF/remove
   sleep 2

   # Forcer le rescan PCI par le noyau
   echo 1 | sudo tee /sys/bus/pci/rescan
   ```
> **Risques :** 
> - Si le pilote NVIDIA tente d'accéder au mapping mémoire (MMIO) pendant la suppression, cela peut déclencher un **Kernel Panic / Oops**.
> - En PCIe standard sans slot Hot-Plug serveur, le unbind/remove peut être ignoré si le refcount noyau est supérieur à 0.

---

#### Étape 3 : Décharger et recharger les modules noyau NVIDIA
Si le reset PCIe a libéré la transaction en attente, déchargez le pilote :

```bash
# Déchargement de toute la pile nvidia
sudo modprobe -r nvidia_uvm nvidia_drm nvidia_modeset nvidia
```

Si `modprobe -r` réussit, rechargez le pilote et réinitialisez l'environnement :
```bash
# Rechargement
sudo modprobe nvidia
sudo modprobe nvidia_modeset
sudo modprobe nvidia_uvm
sudo modprobe nvidia_drm

# Vérification
sudo nvidia-smi
```
> **Risques :** Si `modprobe -r` renvoie `Module nvidia is in use`, **ne faites pas `rmmod -f`** (force). Forcer le déchargement d'un module avec des threads bloqués en état D provoque un crash immédiat du noyau.

---

#### Étape 4 (Si échec) : Reboot propre via Magic SysRq (Sans coupure électrique)
Si `nvidia-modeset` reste figé en D-state et que les modules refusent de se décharger, le noyau est définitivement deadlocké. Pour éviter toute corruption de disques (FS) :

```bash
# Active SysRq
echo 1 | sudo tee /proc/sys/kernel/sysrq

# Sync des caches disques
echo s | sudo tee /proc/sysrq-trigger
# Remontage en lecture seule
echo u | sudo tee /proc/sysrq-trigger
# Reboot immédiat
echo b | sudo tee /proc/sysrq-trigger
```

---

### Diagnostiquer la cause racine
Pour voir pourquoi la carte a lâché avant le blocage :
```bash
dmesg -T | grep -E "NVRM|nvidia|AER|Xid" | tail -n 30
```
- **Xid 79 (GPU fallen off the bus)** : Problème d'alimentation 12VHPWR/PCIe, riser défectueux ou surchauffe VRM.
- **Xid 31 / 45** : Page fault MMU ou timeout du contrôleur mémoire GPU.
