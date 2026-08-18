#!/bin/bash
# Keep LMS model warm via periodic minimal request
HOST="${1:-127.0.0.1:1234}"
MODEL="${2:-qwen/qwen3.5-9b}"
while true; do
  curl -sS -m 30 -X POST "http://$HOST/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"k\"}],\"max_tokens\":1,\"stream\":false}" \
    -o /dev/null -w "[$(date '+%H:%M:%S')] $MODEL on $HOST = HTTP %{http_code} t=%{time_total}s\n" 2>&1
  sleep 25
done
