#!/bin/bash
# Exporte l'état des services systemd (--user ET système) en métriques Prometheus textfile.
# Remplace collector.systemd (bloqué par AppArmor dans le container node-exporter).
OUT=/home/pamerys/jarvis/data/node-exporter-textfile
TMP=$(mktemp "$OUT/.tmp.XXXXXX")
emit() { # $1=scope label, $2=systemctl flag
  systemctl ${2} list-units --type=service --all --plain --no-legend 2>/dev/null \
    | awk -v s="$1" '{u=$1; sub(/\.service$/,"",u);
        if (u ~ /[^A-Za-z0-9_@.:-]/) next;            # skip noms systemd-échappés
        a=($3=="active")?1:0; f=($3=="failed")?1:0;
        printf "jarvis_service_active{service=\"%s\",scope=\"%s\"} %d\n",u,s,a;
        printf "jarvis_service_failed{service=\"%s\",scope=\"%s\"} %d\n",u,s,f}'
}
{
  echo "# HELP jarvis_service_active systemd service actif (1) / inactif (0)"
  echo "# TYPE jarvis_service_active gauge"
  echo "# HELP jarvis_service_failed systemd service en échec (1) / sinon (0)"
  echo "# TYPE jarvis_service_failed gauge"
  emit user "--user"
  emit system ""
} > "$TMP" 2>/dev/null
chmod 644 "$TMP"; mv "$TMP" "$OUT/jarvis_services.prom"
grep 'jarvis_service_active{.*scope="user"' "$OUT/jarvis_services.prom" | sed 's/jarvis_service_active/jarvis_user_service_active/;s/,scope="user"//' > "$OUT/jarvis_user_services.prom" 2>/dev/null
