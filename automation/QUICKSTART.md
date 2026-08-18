# 🚀 JARVIS Automation System - Quick Start Guide

## 5-Minute Setup

### Step 1: Set Telegram Credentials
```bash
export TELEGRAM_BOT_TOKEN='YOUR_BOT_TOKEN'
export TELEGRAM_CHAT_ID='YOUR_CHAT_ID'
```

**How to get these:**
1. Go to Telegram
2. Chat with @BotFather
3. Send `/newbot` and follow instructions to create your bot
4. Copy the token from BotFather
5. Send a message to your new bot
6. Get your chat ID from: `curl https://api.telegram.org/botTOKEN/getUpdates` (look for `chat.id`)

### Step 2: Install Cron Jobs
```bash
bash /home/turbo/automation/install-cron.sh
```

### Step 3: Verify Installation
```bash
# Check cron jobs
crontab -l

# Verify scripts work
python3 /home/turbo/automation/scripts/system-monitor.py
python3 /home/turbo/automation/scripts/linkedin-automation.py

# View dashboard
python3 /home/turbo/automation/dashboard.py
```

### Step 4: Add Content Templates
Edit your content:
```bash
nano /home/turbo/automation/templates/linkedin_content.md
nano /home/turbo/automation/templates/newsletter.md
nano /home/turbo/automation/templates/newsletter_subscribers.txt
```

### Step 5: Monitor Execution
```bash
# Watch logs in real-time
tail -f /home/turbo/automation/logs/*.log
```

## Schedule Overview

| Task | Time(s) | Frequency |
|------|---------|-----------|
| **LinkedIn** | 09:00, 14:00, 19:00 | Daily |
| **Codeur.com** | 10:00, 16:00 | Daily |
| **Email** | 08:00, 18:00 | Daily |
| **System Monitor** | Every 30 min | Continuous |

## What Each Automation Does

### 1️⃣ LinkedIn Automation
- Posts your prepared content
- Engages with relevant accounts
- Tracks metrics
- Alerts when engagement > 50 reactions
- Sends daily report at 20:00

**Content file:** `/home/turbo/automation/templates/linkedin_content.md`

### 2️⃣ Codeur.com Automation
- Checks for new client messages
- Auto-replies to common questions (pricing, timeline, technical)
- Detects high-value opportunities (€500+)
- Lists proposals ready to send
- Alerts on new opportunities

**Response templates:** `/home/turbo/automation/templates/codeur_replies/`

### 3️⃣ Email Automation
- Sends newsletter if content is ready
- Captures incoming leads
- Auto-replies based on patterns
- Detects VIP emails
- Alerts on high-value leads (€5000+)

**Newsletter:** `/home/turbo/automation/templates/newsletter.md`
**Subscribers:** `/home/turbo/automation/templates/newsletter_subscribers.txt`

### 4️⃣ System Monitoring
- Monitors CPU, RAM, Disk, GPU
- Checks service health
- Sends alerts if:
  - CPU > 80%
  - RAM > 85%
  - Disk > 85%
  - Critical services down
- Sends hourly summary

## Telegram Alert Levels

- 🔔 **INFO** - General updates (silent)
- ✅ **SUCCESS** - Task completed successfully
- ⚠️ **WARNING** - Medium priority alert
- ❌ **ERROR** - Task failed
- 🚨 **CRITICAL** - Immediate action needed

## Useful Commands

```bash
# Run all automations manually
python3 /home/turbo/automation/run-automation.py

# Run specific automation
python3 /home/turbo/automation/run-automation.py --script linkedin

# View system status
python3 /home/turbo/automation/dashboard.py

# View setup guide
python3 /home/turbo/automation/automation-scheduler.py

# Follow logs
tail -f /home/turbo/automation/logs/*.log

# Check scheduled tasks
crontab -l
systemctl list-timers

# Edit cron jobs
crontab -e

# Disable a task (temporary)
# Edit crontab and prefix line with #

# Restore crontab
crontab /tmp/crontab.backup.*
```

## Troubleshooting

### Telegram alerts not working?
```bash
# Verify credentials
echo "Bot token: $TELEGRAM_BOT_TOKEN"
echo "Chat ID: $TELEGRAM_CHAT_ID"

# Test connection
curl -X POST https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage \
  -d chat_id=$TELEGRAM_CHAT_ID \
  -d text="Test message"
```

### Cron jobs not running?
```bash
# Check cron logs
tail -f /var/log/syslog | grep CRON

# Verify permissions
ls -la /home/turbo/automation/scripts/

# Check Python path
which python3

# Run manually to test
python3 /home/turbo/automation/scripts/linkedin-automation.py
```

### Script errors?
```bash
# Check individual log
tail -20 /home/turbo/automation/logs/linkedin.log

# Test import
python3 -c "import yaml; import psutil; print('OK')"

# Run script directly
python3 /home/turbo/automation/scripts/linkedin-automation.py
```

## Configuration Files

Edit these to customize behavior:

```bash
/home/turbo/automation/config/linkedin.yml      # LinkedIn settings
/home/turbo/automation/config/codeur.yml        # Codeur.com settings
/home/turbo/automation/config/email.yml         # Email settings
/home/turbo/automation/config/monitoring.yml    # System monitor thresholds
/home/turbo/automation/config/telegram.yml      # Telegram settings
```

## File Structure

```
/home/turbo/automation/
├── config/                          # Configuration YAML files
│   ├── linkedin.yml
│   ├── codeur.yml
│   ├── email.yml
│   ├── monitoring.yml
│   └── telegram.yml
├── scripts/                         # Automation scripts
│   ├── linkedin-automation.py
│   ├── codeur-automation.py
│   ├── email-automation.py
│   └── system-monitor.py
├── templates/                       # Content templates
│   ├── linkedin_content.md
│   ├── newsletter.md
│   ├── newsletter_subscribers.txt
│   └── codeur_replies/
│       ├── pricing_response.txt
│       ├── timeline_response.txt
│       └── technical_response.txt
├── logs/                            # Execution logs
├── telegram-alerts.py               # Alert system core
├── run-automation.py                # Manual runner
├── dashboard.py                     # Status dashboard
├── automation-scheduler.py           # Scheduling helper
├── install-cron.sh                  # Cron installer
├── setup.sh                         # Initial setup
├── README.md                        # Full documentation
└── QUICKSTART.md                    # This file
```

## Advanced Configuration

### Customize Thresholds

Edit `/home/turbo/automation/config/monitoring.yml`:
```yaml
cpu:
  critical_threshold: 80  # Alert when CPU > 80%
  warning_threshold: 70   # Warning when CPU > 70%

disk:
  critical_threshold: 85  # Alert when disk > 85%
```

### Change Schedule Times

Edit `/home/turbo/automation/config/linkedin.yml`:
```yaml
schedule:
  - hour: 9
    minute: 0
  - hour: 14
    minute: 0
  - hour: 19
    minute: 0
```

Then reinstall cron:
```bash
bash /home/turbo/automation/install-cron.sh
```

### Add More LinkedIn Content

Create multiple content files:
```bash
/home/turbo/automation/templates/linkedin_content_1.md
/home/turbo/automation/templates/linkedin_content_2.md
/home/turbo/automation/templates/linkedin_content_3.md
```

The script will randomly pick one each time it runs.

## Next Steps

1. ✅ Set Telegram credentials
2. ✅ Run `bash install-cron.sh`
3. ✅ Edit your content templates
4. ✅ Test manually: `python3 /home/turbo/automation/scripts/linkedin-automation.py`
5. ✅ Monitor logs: `tail -f /home/turbo/automation/logs/*.log`
6. ✅ Check status: `python3 /home/turbo/automation/dashboard.py`

## Support

For issues, check the logs first:
```bash
grep ERROR /home/turbo/automation/logs/*.log
```

---

**🎉 You're all set! Your automations are now running 24/7.**

JARVIS Automation System | *Productivity. Intelligence. Scale.*
