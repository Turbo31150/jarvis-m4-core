#!/usr/bin/env sh
# Healthcheck minimal : port 8902 ouvert + /health 200
PORT="${PORT:-8902}"
wget -q -O /dev/null --timeout=3 "http://127.0.0.1:${PORT}/health" || exit 1
exit 0
