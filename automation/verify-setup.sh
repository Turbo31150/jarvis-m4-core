#!/bin/bash
# Verify JARVIS Automation System Setup

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  JARVIS Automation System - Setup Verification                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

PASS=0
FAIL=0

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
        ((PASS++))
    else
        echo -e "${RED}✗${NC} $1 (missing)"
        ((FAIL++))
    fi
}

check_executable() {
    if [ -x "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 (executable)"
        ((PASS++))
    else
        echo -e "${RED}✗${NC} $1 (not executable)"
        ((FAIL++))
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
        ((PASS++))
    else
        echo -e "${RED}✗${NC} $1 (missing)"
        ((FAIL++))
    fi
}

echo -e "${BLUE}📁 Directory Structure${NC}"
echo "────────────────────────────────────────────────────────────────"
check_dir "/home/turbo/automation"
check_dir "/home/turbo/automation/config"
check_dir "/home/turbo/automation/scripts"
check_dir "/home/turbo/automation/templates"
check_dir "/home/turbo/automation/logs"
echo ""

echo -e "${BLUE}⚙️  Configuration Files${NC}"
echo "────────────────────────────────────────────────────────────────"
check_file "/home/turbo/automation/config/linkedin.yml"
check_file "/home/turbo/automation/config/codeur.yml"
check_file "/home/turbo/automation/config/email.yml"
check_file "/home/turbo/automation/config/monitoring.yml"
check_file "/home/turbo/automation/config/telegram.yml"
echo ""

echo -e "${BLUE}🐍 Automation Scripts${NC}"
echo "────────────────────────────────────────────────────────────────"
check_executable "/home/turbo/automation/scripts/linkedin-automation.py"
check_executable "/home/turbo/automation/scripts/codeur-automation.py"
check_executable "/home/turbo/automation/scripts/email-automation.py"
check_executable "/home/turbo/automation/scripts/system-monitor.py"
echo ""

echo -e "${BLUE}📝 Content Templates${NC}"
echo "────────────────────────────────────────────────────────────────"
check_file "/home/turbo/automation/templates/linkedin_content.md"
check_file "/home/turbo/automation/templates/newsletter.md"
check_file "/home/turbo/automation/templates/newsletter_subscribers.txt"
check_dir "/home/turbo/automation/templates/codeur_replies"
check_file "/home/turbo/automation/templates/codeur_replies/pricing_response.txt"
check_file "/home/turbo/automation/templates/codeur_replies/timeline_response.txt"
check_file "/home/turbo/automation/templates/codeur_replies/technical_response.txt"
echo ""

echo -e "${BLUE}🔧 System Files${NC}"
echo "────────────────────────────────────────────────────────────────"
check_executable "/home/turbo/automation/telegram-alerts.py"
check_executable "/home/turbo/automation/run-automation.py"
check_executable "/home/turbo/automation/dashboard.py"
check_executable "/home/turbo/automation/automation-scheduler.py"
check_executable "/home/turbo/automation/install-cron.sh"
check_executable "/home/turbo/automation/setup.sh"
echo ""

echo -e "${BLUE}📚 Documentation${NC}"
echo "────────────────────────────────────────────────────────────────"
check_file "/home/turbo/automation/README.md"
check_file "/home/turbo/automation/QUICKSTART.md"
check_file "/home/turbo/automation/INSTALL_SUMMARY.txt"
echo ""

echo -e "${BLUE}🐍 Python Dependencies${NC}"
echo "────────────────────────────────────────────────────────────────"
python3 -c "import yaml" 2>/dev/null && echo -e "${GREEN}✓${NC} yaml" && ((PASS++)) || echo -e "${RED}✗${NC} yaml (missing)" && ((FAIL++))
python3 -c "import requests" 2>/dev/null && echo -e "${GREEN}✓${NC} requests" && ((PASS++)) || echo -e "${RED}✗${NC} requests (missing)" && ((FAIL++))
python3 -c "import psutil" 2>/dev/null && echo -e "${GREEN}✓${NC} psutil" && ((PASS++)) || echo -e "${RED}✗${NC} psutil (missing)" && ((FAIL++))
echo ""

echo -e "${BLUE}🔐 Environment Variables${NC}"
echo "────────────────────────────────────────────────────────────────"
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo -e "${YELLOW}⚠${NC}  TELEGRAM_BOT_TOKEN not set"
    ((FAIL++))
else
    echo -e "${GREEN}✓${NC} TELEGRAM_BOT_TOKEN is set"
    ((PASS++))
fi

if [ -z "$TELEGRAM_CHAT_ID" ]; then
    echo -e "${YELLOW}⚠${NC}  TELEGRAM_CHAT_ID not set"
    ((FAIL++))
else
    echo -e "${GREEN}✓${NC} TELEGRAM_CHAT_ID is set"
    ((PASS++))
fi
echo ""

echo -e "${BLUE}⏰ Cron Jobs${NC}"
echo "────────────────────────────────────────────────────────────────"
CRON_COUNT=$(crontab -l 2>/dev/null | grep -c "automation" || echo "0")
if [ "$CRON_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Cron jobs installed ($CRON_COUNT entries)"
    ((PASS++))
else
    echo -e "${YELLOW}⚠${NC}  No cron jobs found (run: bash /home/turbo/automation/install-cron.sh)"
fi
echo ""

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "Summary: ${GREEN}$PASS passed${NC}, ${RED}$FAIL issues${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! System is ready.${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Set Telegram credentials:"
    echo "   export TELEGRAM_BOT_TOKEN='...'"
    echo "   export TELEGRAM_CHAT_ID='...'"
    echo ""
    echo "2. Install cron jobs:"
    echo "   bash /home/turbo/automation/install-cron.sh"
    echo ""
    echo "3. Monitor logs:"
    echo "   tail -f /home/turbo/automation/logs/*.log"
    exit 0
else
    echo -e "${RED}❌ Setup incomplete. Fix the issues above.${NC}"
    exit 1
fi
