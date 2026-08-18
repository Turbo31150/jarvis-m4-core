#!/bin/bash
export ANTHROPIC_BASE_URL="http://127.0.0.1:8792/v1"
export ANTHROPIC_API_KEY="antigravity"
claude "$@"
