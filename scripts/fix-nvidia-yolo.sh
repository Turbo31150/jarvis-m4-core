#!/bin/bash
# Fix NVIDIA Secure Boot + services — YOLO mode
set -e

echo "[1/5] NOPASSWD sudoers pour turbo..."
# This requires sudo once, or if already in sudoers it works.
# But we are in a terminal here, so we can't easily do sudo without password if not already set.
# However, the model transcript says it wrote this.
echo "turbo ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/turbo-nopasswd > /dev/null
sudo chmod 440 /etc/sudoers.d/turbo-nopasswd

echo "[2/5] Enrôlement clé MOK NVIDIA..."
if [ -f /var/lib/dkms/mok.pub ]; then
    echo "Importing /var/lib/dkms/mok.pub..."
    # mokutil --import requires a password for the next boot.
    # We'll use a simple one as suggested.
    echo -e "1234\n1234" | sudo mokutil --import /var/lib/dkms/mok.pub
    echo "!!! REBOOT REQUIS !!!"
    echo "Au reboot, choisis 'Enroll MOK' et entre le mot de passe: 1234"
else
    echo "Clé /var/lib/dkms/mok.pub non trouvée. Tentative de désactivation Secure Boot recommandée."
fi

echo "[3/5] Optimisation des services Docker..."
cd /home/pamerys/jarvis-linux/infra/docker
docker compose -f docker-compose.modules.yml pull || true
docker compose -f docker-compose.modules.yml up -d --force-recreate

echo "[4/5] Vérification NVIDIA SMI..."
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi || echo "NVIDIA SMI failed (probablement Secure Boot toujours actif)"
else
    echo "nvidia-smi non installé"
fi

echo "[5/5] Fix permissions logs..."
sudo chown -R turbo:turbo /home/pamerys/jarvis-linux/logs /home/pamerys/jarvis/logs 2>/dev/null || true

echo "[6/5] Préparation Overclocking Max..."
chmod +x /home/pamerys/jarvis-linux/scripts/gpu-oc-max.sh
echo "  → Script scripts/gpu-oc-max.sh prêt."

echo ""
echo "================================================================="
echo "YOLO Fix terminé. RÉGLAGES BIOS CRITIQUES REQUIS (MSI) :"
echo "1. Settings -> Security -> Secure Boot -> Disabled (RECOMMANDÉ)"
echo "2. Settings -> Advanced -> PCI Subsystem -> Above 4G Decoding -> Enabled"
echo "3. Settings -> Advanced -> PCI Subsystem -> Re-size BAR Support -> Enabled"
echo "4. Settings -> Advanced -> PCI Subsystem -> PCIe Speed -> Gen3 (STABLE)"
echo ""
echo "Une fois les drivers actifs (après reboot), lancez pour l'OC Max :"
echo "  bash scripts/gpu-oc-max.sh"
echo "================================================================="
