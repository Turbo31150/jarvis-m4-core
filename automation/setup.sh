#!/bin/bash
# Setup script for JARVIS Automation System

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  JARVIS Automation System - Setup & Configuration              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found"
    exit 1
fi
echo "✓ Python 3 found: $(python3 --version)"

# Check pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not found"
    exit 1
fi
echo "✓ pip3 found"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip3 install -q pyyaml requests psutil

echo "✓ Dependencies installed"

# Create necessary directories
echo ""
echo "📁 Creating directory structure..."
mkdir -p /home/turbo/automation/{config,scripts,logs,templates/{codeur_replies}}
echo "✓ Directories created"

# Make scripts executable
chmod +x /home/turbo/automation/scripts/*.py
chmod +x /home/turbo/automation/telegram-alerts.py
chmod +x /home/turbo/automation/automation-scheduler.py

echo "✓ Scripts made executable"

# Show configuration status
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "📋 Configuration Status:"
echo "════════════════════════════════════════════════════════════════"
echo ""

if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "⚠️  TELEGRAM_BOT_TOKEN not set"
    echo "   Set it with: export TELEGRAM_BOT_TOKEN='your_token'"
else
    echo "✓ TELEGRAM_BOT_TOKEN is set"
fi

if [ -z "$TELEGRAM_CHAT_ID" ]; then
    echo "⚠️  TELEGRAM_CHAT_ID not set"
    echo "   Set it with: export TELEGRAM_CHAT_ID='your_chat_id'"
else
    echo "✓ TELEGRAM_CHAT_ID is set"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🚀 Next Steps:"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "1. Configure Telegram Bot:"
echo "   export TELEGRAM_BOT_TOKEN='..'"
echo "   export TELEGRAM_CHAT_ID='..'"
echo ""
echo "2. Test individual scripts:"
echo "   python3 /home/turbo/automation/scripts/system-monitor.py"
echo ""
echo "3. Schedule with cron:"
echo "   python3 /home/turbo/automation/automation-scheduler.py"
echo ""
echo "4. Check logs:"
echo "   tail -f /home/turbo/automation/logs/*.log"
echo ""
echo "✓ Setup complete!"
