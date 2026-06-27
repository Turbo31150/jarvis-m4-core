#!/usr/bin/env bash
# Lance le JARVIS Voice Widget (toujours sur /usr/bin/python3 pour pynput)
export DISPLAY="${DISPLAY:-:1}"
exec /usr/bin/python3 /home/pamerys/jarvis/scripts/voice-widget.py "$@"
