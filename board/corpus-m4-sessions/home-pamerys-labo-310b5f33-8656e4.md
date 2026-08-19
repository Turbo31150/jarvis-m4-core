[assistant] Vérification faite — **aucune clé USB de stockage n'est détectée**.

| Élément | État |
|---|---|
| Périphériques USB stockage | 1 seul : `sda` = **disque JARVIS-M1** (931 G, monté sur `/media/pamerys/JARVIS-M1`) — c'est ton disque M1, pas une clé |
| Événements kernel récents | 21:28:46 → `usb 3-3.3: USB disconnect` · 21:30:04 → rebranchement d'un **clavier HP Basic USB** (CHICONY) sur le port 3-3.4 |
| Nouvelle partition/mount | aucune |

★ Insight ─────────────────────────────────────
`lsblk` + `dmesg` sont complémentaires : `lsblk` dit ce qui *existe* comme bloc-device, `dmesg` dit ce qui vient de *changer*. Ici les deux concordent — le kernel n'a énuméré aucun périphérique `usb-storage`, donc le problème est en amont du système de fichiers (port, câble ou clé), pas un souci de montage.
─────────────────────────────────────────────────

Deux pistes probables :
1. **Tu l'as branchée sur le port 3-3.3** — celui qui a fait un *disconnect* à 21:28, puis c'est le clavier qui a repris la main sur 3-3.4. Le hub semble instable.
2. La clé est dans un port non alimenté ou mal enfoncée (aucune énumération USB du tout = le kernel ne la voit pas physiquement).

Rebranche-la (idéalement sur un port en façade directe, pas le hub), puis dis-moi — je relance la détection. Si tu veux surveiller en direct pendant que tu la branches, lance dans ton terminal :

```
! sudo dmesg -w | grep -i --line-buffered "usb\|sd[b-z]"
```

[user] indtalle tt les deriver pource hardawar m4  lz pzrfection udit rechzezrchhe depperecherch orfrevre

[assistant] Audit matériel complet d'abord — on installe ensuite seulement ce qui manque réellement.

[assistant] Machine identifiée : **ASUS TUF — Intel i5-11400H (Tiger Lake-H, HM570) + NVIDIA RTX 3050 Mobile**, Ubuntu 24.04.4 / kernel 6.17. Deuxième passe : état des pilotes propriétaires, microcode et firmware.

[assistant] Base déjà solide (NVIDIA 595 DKMS actif sur les 2 kernels, microcode 0x58, thermald actif). Je cible les **manques réels**. Dernière vérif avant d'installer, pour éviter un conflit d'énergie :

[assistant] Tout est cohérent : firmware **à jour** (fwupd : aucun périphérique à flasher), `asus_wmi` chargé nativement, `power-profiles-daemon` actif en mode *performance*. J'installe uniquement le lot manquant et sans risque.

★ Insight ─────────────────────────────────────
Deux pièges que j'écarte volontairement ici : (1) **`tlp` est exclu** — il entre en conflit direct avec `power-profiles-daemon` déjà actif (deux démons qui écrivent les mêmes sysfs = profils qui s'annulent). (2) **`nvidia-driver-610` est ignoré** malgré sa disponibilité : le 595 est le *recommended* distro, compilé DKMS et validé sur tes deux kernels. Sauter vers 610 casserait potentiellement le build DKMS sur le 6.17 pour un gain nul.
─────────────────────────────────────────────────

[assistant] Installation terminée (exit 0). Vérification réelle des acquis — pas de déclaration sans preuve :

[assistant] Travail terminé et vérifié. Voici l'état réel.

## Matériel M4 identifié
**ASUS TUF** — Intel Core i5-11400H (Tiger Lake-H, chipset HM570) · NVIDIA RTX 3050 Laptop · Ubuntu 24.04.4 / kernel 6.17.0-40

## Ce qui était déjà parfait (rien touché)
| Composant | Pilote | État |
|---|---|---|
| GPU NVIDIA RTX 3050 | `nvidia` 595.71.05 (DKMS, recommended) | ✅ compilé sur les 2 kernels |
| iGPU Intel UHD | `i915` + DMC firmware v2.12 | ✅ |
| WiFi AX201 | `iwlwifi` fw 77.f39cc7f9.0 | ✅ |
| Bluetooth AX201 | `btintel` fw 249-27.23 | ✅ |
| Ethernet Realtek 8168 | `r8169` | ✅ |
| Ethernet USB ASIX (lien M6) | `ax88179` | ✅ |
| Audio HDA | `snd_hda_intel` + SOF signé | ✅ |
| NVMe ×2, Thunderbolt 4, ME, SPI, thermique | tous liés | ✅ |
| Microcode CPU | `intel-microcode` rev 0x58 | ✅ |
| BIOS / SSD / UEFI | fwupd : **aucune mise à jour disponible** | ✅ à jour |

## Ce que j'ai installé (les manques réels)
| Paquet | Apport concret |
|---|---|
| `intel-media-va-driver-non-free` 24.1.0 | Encodage/décodage matériel **complet** iGPU — vérifié : H264 + HEVC + VP9 + AV1 |
| `intel-opencl-icd` | OpenCL sur iGPU → 2 plateformes actives (`intel.icd` + `nvidia.icd`) |
| `lm-sensors` | Capteurs thermiques — service activé, relevé fonctionnel |
| `nvtop`, `intel-gpu-tools`, `vainfo`, `vulkan-tools`, `powertop` | Diagnostic et supervision GPU/énergie |

**Preuve d'accélération matérielle (ffmpeg voit les 3 chemins) :**
`av1_nvenc · h264_nvenc · hevc_nvenc` (NVIDIA) — `h264_qsv · hevc_qsv · av1_qsv` (In

[user] içnstalle tt paraétre duplisque extrait la loghique mais non l'esclavage a          
  l'utyilisation comme tous fond

[assistant] Je décode : capitaliser la **logique** de ce qui vient d'être fait en outil réutilisable 0-token — pas rester esclave d'une exécution manuelle à refaire à chaque fois. Je regarde le canon de tes séries avant d'écrire.

[assistant] Règle biblio-first : je vérifie d'abord qu'une série matériel n'existe pas déjà avant d'en créer une.

[assistant] Canon compris (série simple, autonome). Je crée la série qui **fige la logique** de l'audit qu'on vient de faire — rejouable sur n'importe quel nœud du parc, sans moi.

[assistant] Verdict de la série : **machine complète**. Un bug de chaînage sur le test fwupd (il affiche ⚠️ alors que tout est à jour) — je le corrige, puis je passe à ta question disque.

[assistant] Maintenant ta question disque — j'audite la géométrie réelle avant de proposer quoi que ce soit :

[assistant] Cartographie établie. Un point important avant de répondre : **on ne peut pas « étendre » `/`** ici, et je vais te dire pourquoi — puis te donner ce qui marche vraiment.