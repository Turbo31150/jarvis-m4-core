#!/bin/bash
# Test all automation scripts

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  JARVIS Automation System - Complete Test Suite                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

PASS=0
FAIL=0

# Test 1: Verify directory structure
echo "🔍 Test 1: Directory Structure"
echo "────────────────────────────────────────────────────────────────"
for dir in config scripts templates logs; do
    if [ -d "/home/turbo/automation/$dir" ]; then
        echo "  ✓ $dir/"
        ((PASS++))
    else
        echo "  ✗ $dir/ (missing)"
        ((FAIL++))
    fi
done
echo ""

# Test 2: Configuration files
echo "🔍 Test 2: Configuration Files"
echo "────────────────────────────────────────────────────────────────"
for file in linkedin.yml codeur.yml email.yml monitoring.yml telegram.yml; do
    if [ -f "/home/turbo/automation/config/$file" ]; then
        echo "  ✓ config/$file"
        ((PASS++))
    else
        echo "  ✗ config/$file (missing)"
        ((FAIL++))
    fi
done
echo ""

# Test 3: Automation scripts
echo "🔍 Test 3: Automation Scripts"
echo "────────────────────────────────────────────────────────────────"
for script in linkedin-automation.py codeur-automation.py email-automation.py system-monitor.py; do
    if [ -x "/home/turbo/automation/scripts/$script" ]; then
        echo "  ✓ scripts/$script (executable)"
        ((PASS++))
    else
        echo "  ✗ scripts/$script (not executable)"
        ((FAIL++))
    fi
done
echo ""

# Test 4: Python syntax check
echo "🔍 Test 4: Python Syntax Check"
echo "────────────────────────────────────────────────────────────────"
for script in telegram-alerts.py run-automation.py dashboard.py automation-scheduler.py; do
    if python3 -m py_compile "/home/turbo/automation/$script" 2>/dev/null; then
        echo "  ✓ $script (valid)"
        ((PASS++))
    else
        echo "  ✗ $script (syntax error)"
        ((FAIL++))
    fi
done
for script in linkedin-automation.py codeur-automation.py email-automation.py system-monitor.py; do
    if python3 -m py_compile "/home/turbo/automation/scripts/$script" 2>/dev/null; then
        echo "  ✓ scripts/$script (valid)"
        ((PASS++))
    else
        echo "  ✗ scripts/$script (syntax error)"
        ((FAIL++))
    fi
done
echo ""

# Test 5: Dependencies
echo "🔍 Test 5: Python Dependencies"
echo "────────────────────────────────────────────────────────────────"
if python3 -c "import yaml" 2>/dev/null; then
    echo "  ✓ yaml module"
    ((PASS++))
else
    echo "  ✗ yaml module (missing)"
    ((FAIL++))
fi

if python3 -c "import requests" 2>/dev/null; then
    echo "  ✓ requests module"
    ((PASS++))
else
    echo "  ✗ requests module (missing)"
    ((FAIL++))
fi

if python3 -c "import psutil" 2>/dev/null; then
    echo "  ✓ psutil module"
    ((PASS++))
else
    echo "  ✗ psutil module (missing)"
    ((FAIL++))
fi
echo ""

# Test 6: System monitoring test
echo "🔍 Test 6: System Monitoring Test"
echo "────────────────────────────────────────────────────────────────"
echo "Running system-monitor.py..."
if timeout 10 python3 /home/turbo/automation/scripts/system-monitor.py >/dev/null 2>&1; then
    echo "  ✓ system-monitor.py executed successfully"
    ((PASS++))
else
    echo "  ✗ system-monitor.py execution failed"
    ((FAIL++))
fi
echo ""

# Test 7: Cron jobs
echo "🔍 Test 7: Cron Job Installation"
echo "────────────────────────────────────────────────────────────────"
CRON_COUNT=$(crontab -l 2>/dev/null | grep -c "automation" || echo "0")
if [ "$CRON_COUNT" -gt 0 ]; then
    echo "  ✓ Cron jobs installed ($CRON_COUNT entries)"
    ((PASS++))
else
    echo "  ⚠ No cron jobs found"
    ((FAIL++))
fi
echo ""

# Test 8: Log files
echo "🔍 Test 8: Log Files"
echo "────────────────────────────────────────────────────────────────"
if [ -f "/home/turbo/automation/logs/monitoring.log" ]; then
    LINES=$(wc -l < "/home/turbo/automation/logs/monitoring.log")
    echo "  ✓ monitoring.log ($LINES lines)"
    ((PASS++))
else
    echo "  ⚠ monitoring.log not yet created"
fi
echo ""

# Test 9: Documentation
echo "🔍 Test 9: Documentation"
echo "────────────────────────────────────────────────────────────────"
for doc in README.md QUICKSTART.md INSTALL_SUMMARY.txt MANIFEST.md; do
    if [ -f "/home/turbo/automation/$doc" ]; then
        SIZE=$(wc -c < "/home/turbo/automation/$doc")
        echo "  ✓ $doc ($SIZE bytes)"
        ((PASS++))
    else
        echo "  ✗ $doc (missing)"
        ((FAIL++))
    fi
done
echo ""

# Summary
echo "════════════════════════════════════════════════════════════════"
echo "📊 Test Results"
echo "════════════════════════════════════════════════════════════════"
TOTAL=$((PASS + FAIL))
echo "Passed:  $PASS / $TOTAL"
echo "Failed:  $FAIL / $TOTAL"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "✅ All tests passed! System is ready."
    echo ""
    echo "Next steps:"
    echo "1. Set Telegram credentials"
    echo "2. Edit content templates"
    echo "3. Monitor logs: tail -f /home/turbo/automation/logs/*.log"
    exit 0
else
    echo "❌ Some tests failed. Please review the output above."
    exit 1
fi
