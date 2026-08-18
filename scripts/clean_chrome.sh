#!/bin/bash
pkill -f chrome || true
pkill -f google-chrome || true
rm -rf ~/.config/google-chrome/Default/Web\ Data-journal 2>/dev/null || true
rm -rf ~/.config/google-chrome/Default/Service\ Worker/CacheStorage/* 2>/dev/null || true
rm -rf ~/.config/google-chrome/Default/Cache/* 2>/dev/null || true
