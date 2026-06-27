#!/bin/bash
sudo /usr/sbin/iptables-restore < /home/pamerys/jarvis/infra/config/iptables-rules.v4
# Charger ipset AbuseIPDB si dispo
if command -v ipset >/dev/null 2>&1 && [ -f /home/pamerys/jarvis/.secrets/abuseipdb.key ]; then
  bash /home/pamerys/jarvis/scripts/abuseipdb-blacklist-sync.sh &
fi
echo "iptables + ipset restaurés"
