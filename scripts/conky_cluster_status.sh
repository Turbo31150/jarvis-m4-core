#!/bin/bash
# Status cluster pour conky (pas de substitution couleur dans shell)
M6_STATUS=$(curl -s --max-time 2 http://10.42.0.230:11434/api/tags 2>/dev/null | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    models=d.get('models',[])
    names=[m['name'] for m in models[:3]]
    print('UP: '+', '.join(names) if names else 'UP')
except:
    print('OFFLINE')
" 2>/dev/null || echo "OFFLINE")
echo "$M6_STATUS"
