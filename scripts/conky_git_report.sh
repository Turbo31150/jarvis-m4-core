#!/bin/bash
# Dernier commit jarvis-linux
cd /home/pamerys/Workspaces/jarvis-linux 2>/dev/null && \
git log -n 1 --pretty=format:"%h %s%n%an · %cd" --date=short 2>/dev/null || echo "N/A"
