#!/bin/bash
# Status services pour conky (texte simple)
WEB=$(curl -s --max-time 1 http://127.0.0.1:9761/health 2>/dev/null && echo "WebAPI :9761 OK" || echo "WebAPI :9761 OFF")
LMS=$(curl -s --max-time 1 http://127.0.0.1:11235/v1/models 2>/dev/null | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    n=len(d.get('data',[]))
    print(f'LMStudio :11235 OK ({n} modeles)')
except:
    print('LMStudio :11235 OFF')
" 2>/dev/null || echo "LMStudio :11235 OFF")
echo "$WEB"
echo "$LMS"
