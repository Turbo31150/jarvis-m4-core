#!/bin/bash
# GPU OC + CPU MSR M4 — RTX 3050 Laptop + i5-11400H Max Performance
# Exécuté au démarrage de session graphique

# ASUS Turbo Mode (débloque TDP CPU+GPU max)
echo 0 | sudo tee /sys/devices/platform/asus-nb-wmi/throttle_thermal_policy >/dev/null
echo performance | sudo tee /sys/firmware/acpi/platform_profile >/dev/null
echo 1 | sudo tee /sys/devices/platform/asus-nb-wmi/panel_od >/dev/null

# GPU power control (no autosuspend)
echo on | sudo tee /sys/bus/pci/devices/0000:01:00.0/power/control >/dev/null 2>/dev/null

# GPU OC via nvidia-settings (CoolBits 28 requis)
nvidia-settings -a '[gpu:0]/GpuPowerMizerMode=1'
nvidia-settings -a '[gpu:0]/GPUGraphicsClockOffsetAllPerformanceLevels=150'
nvidia-settings -a '[gpu:0]/GPUMemoryTransferRateOffsetAllPerformanceLevels=1000'

# CPU MSR PL2=100W (si wrmsr disponible)
if command -v wrmsr &>/dev/null; then
  sudo modprobe msr 2>/dev/null
  sudo wrmsr -a 0x610 0x00438320001f8640 2>/dev/null
fi

# CPU perf lock
echo 100 | sudo tee /sys/devices/system/cpu/intel_pstate/min_perf_pct >/dev/null
for cpu in /sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference; do
  echo performance | sudo tee "$cpu" >/dev/null
done

echo "✅ M4 Full OC actif: GPU +150MHz/+1000VRAM | CPU PL2=100W | ASUS Turbo"
