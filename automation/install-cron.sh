#!/bin/bash
# Installation script for cron jobs

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  JARVIS Automation - Cron Installation                       ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Backup existing crontab
if crontab -l &>/dev/null; then
    echo "📋 Backing up existing crontab..."
    crontab -l > /tmp/crontab.backup.$(date +%s)
    echo "✓ Backup saved to /tmp/crontab.backup.*"
fi

# Create temporary cron file
CRON_FILE=$(mktemp)
cat > "$CRON_FILE" << 'CRON_JOBS'
# JARVIS Automation System - Cron Jobs
# Install date: $(date)

# ============================================================
# LinkedIn Automation - 9:00, 14:00, 19:00
# ============================================================
0 9 * * * /home/turbo/automation/scripts/linkedin-automation.py >> /home/turbo/automation/logs/cron.log 2>&1

0 14 * * * /home/turbo/automation/scripts/linkedin-automation.py >> /home/turbo/automation/logs/cron.log 2>&1

0 19 * * * /home/turbo/automation/scripts/linkedin-automation.py >> /home/turbo/automation/logs/cron.log 2>&1

# ============================================================
# Codeur.com Automation - 10:00, 16:00
# ============================================================
0 10 * * * /home/turbo/automation/scripts/codeur-automation.py >> /home/turbo/automation/logs/cron.log 2>&1

0 16 * * * /home/turbo/automation/scripts/codeur-automation.py >> /home/turbo/automation/logs/cron.log 2>&1

# ============================================================
# Email Automation - 8:00, 18:00
# ============================================================
0 8 * * * /home/turbo/automation/scripts/email-automation.py >> /home/turbo/automation/logs/cron.log 2>&1

0 18 * * * /home/turbo/automation/scripts/email-automation.py >> /home/turbo/automation/logs/cron.log 2>&1

# ============================================================
# System Monitoring - Every 30 minutes
# ============================================================
*/30 * * * * /home/turbo/automation/scripts/system-monitor.py >> /home/turbo/automation/logs/cron.log 2>&1

# ============================================================
# End of JARVIS Automation System
# ============================================================
CRON_JOBS

echo "📝 Installing cron jobs..."
crontab "$CRON_FILE"
rm "$CRON_FILE"

echo "✓ Cron jobs installed successfully"
echo ""

echo "📋 Installed cron schedule:"
echo "────────────────────────────────────────────────────────"
crontab -l | grep -v "^#" | grep -v "^$" || echo "No active jobs"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "✓ Setup complete! Your automations are now scheduled."
echo ""
echo "To verify installation:"
echo "  crontab -l                    # List cron jobs"
echo ""
echo "To monitor execution:"
echo "  tail -f /home/turbo/automation/logs/cron.log"
echo ""
echo "To disable a specific automation:"
echo "  crontab -e"
echo "  (Comment out the line with #)"
echo "═══════════════════════════════════════════════════════════════"
