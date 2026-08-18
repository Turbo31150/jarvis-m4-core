# 🤖 JARVIS Automation System

Complete automation framework for LinkedIn, Codeur.com, Email, and System Monitoring with Telegram alerts.

## 📋 Features

### 1. LinkedIn Automation
- **Schedule**: Daily at 09:00, 14:00, 19:00
- **Actions**:
  - Post technical content
  - Engage with relevant accounts
  - Track engagement metrics
  - Alert when engagement > 50
  - Daily performance report

### 2. Codeur.com Management
- **Schedule**: Daily at 10:00, 16:00
- **Actions**:
  - Check for new client messages
  - Auto-reply to common patterns
  - Detect high-value opportunities
  - List proposals ready to send
  - Alert on new opportunities (€500+)

### 3. Email Workflow
- **Schedule**: Daily at 08:00, 18:00
- **Actions**:
  - Send newsletter if content ready
  - Capture incoming leads
  - Auto-reply with templates
  - VIP email detection
  - Alert on high-value leads

### 4. System Monitoring
- **Schedule**: Every 30 minutes
- **Metrics**:
  - CPU usage (alert if > 80%)
  - RAM usage (alert if > 85%)
  - Disk usage (alert if > 85%)
  - GPU status
  - Service health
  - Top processes
- **Reports**: Hourly summary to Telegram

## 🛠️ Installation

### Quick Setup
```bash
cd /home/turbo/automation
bash setup.sh
```

### Manual Setup

1. **Install dependencies**:
```bash
pip3 install pyyaml requests psutil
```

2. **Configure Telegram**:
```bash
export TELEGRAM_BOT_TOKEN='your_bot_token'
export TELEGRAM_CHAT_ID='your_chat_id'
```

Get your bot token from @BotFather on Telegram.
Get your chat ID by messaging your bot and checking logs.

3. **Create content templates**:
```bash
# Edit these files with your content:
- /home/turbo/automation/templates/linkedin_content.md
- /home/turbo/automation/templates/newsletter.md
- /home/turbo/automation/templates/newsletter_subscribers.txt
```

## 📅 Scheduling

### Option 1: Cron Jobs (Simple)

```bash
# Edit your crontab
crontab -e

# Add these lines:
0 9,14,19 * * * /home/turbo/automation/scripts/linkedin-automation.py
0 10,16 * * * /home/turbo/automation/scripts/codeur-automation.py
0 8,18 * * * /home/turbo/automation/scripts/email-automation.py
*/30 * * * * /home/turbo/automation/scripts/system-monitor.py
```

### Option 2: Systemd Timers (Recommended)

Create `/etc/systemd/system/linkedin-automation.service`:
```ini
[Unit]
Description=JARVIS Automation - LinkedIn
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /home/turbo/automation/scripts/linkedin-automation.py
StandardOutput=journal
StandardError=journal
```

Create `/etc/systemd/system/linkedin-automation.timer`:
```ini
[Unit]
Description=JARVIS Automation Timer - LinkedIn

[Timer]
OnCalendar=*-*-* 09,14,19:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now linkedin-automation.timer
```

## 📁 Project Structure

```
/home/turbo/automation/
├── config/
│   ├── linkedin.yml          # LinkedIn settings
│   ├── codeur.yml            # Codeur.com settings
│   ├── email.yml             # Email settings
│   ├── monitoring.yml        # System monitoring settings
│   └── telegram.yml          # Telegram configuration
├── scripts/
│   ├── linkedin-automation.py
│   ├── codeur-automation.py
│   ├── email-automation.py
│   └── system-monitor.py
├── templates/
│   ├── linkedin_content.md
│   ├── newsletter.md
│   ├── newsletter_subscribers.txt
│   └── codeur_replies/
│       ├── pricing_response.txt
│       ├── timeline_response.txt
│       └── technical_response.txt
├── logs/
│   ├── linkedin.log
│   ├── codeur.log
│   ├── email.log
│   ├── monitoring.log
│   ├── telegram.log
│   └── cron.log
├── telegram-alerts.py        # Alert system
├── automation-scheduler.py   # Scheduling helper
├── setup.sh                  # Setup script
└── README.md
```

## 🔔 Telegram Alert Levels

- **ℹ️ INFO**: General updates (no notification)
- **✅ SUCCESS**: Task completed successfully
- **⚠️ WARNING**: Medium priority (CPU 70-80%, RAM 75-85%)
- **❌ ERROR**: Task failed
- **🚨 CRITICAL**: Immediate action needed (CPU > 80%, disk > 85%, service down)

## 🧪 Testing

### Test Individual Scripts

```bash
# Test LinkedIn automation
python3 /home/turbo/automation/scripts/linkedin-automation.py

# Test Codeur automation
python3 /home/turbo/automation/scripts/codeur-automation.py

# Test Email automation
python3 /home/turbo/automation/scripts/email-automation.py

# Test System monitoring
python3 /home/turbo/automation/scripts/system-monitor.py

# Test Telegram alerts
python3 -c "from telegram_alerts import get_alerts, AlertLevel; get_alerts().send_message('Test', AlertLevel.INFO)"
```

### View Logs

```bash
# Follow all logs
tail -f /home/turbo/automation/logs/*.log

# Watch specific log
tail -f /home/turbo/automation/logs/monitoring.log

# Search for errors
grep ERROR /home/turbo/automation/logs/*.log
```

### Check Scheduled Tasks

```bash
# Cron jobs
crontab -l

# Systemd timers
systemctl list-timers
sudo systemctl status linkedin-automation.timer
```

## ⚙️ Configuration

### LinkedIn Settings (`config/linkedin.yml`)
- Schedule times
- Content source file
- Engagement thresholds
- Alert settings

### Codeur Settings (`config/codeur.yml`)
- Message check frequency
- Auto-reply triggers
- Opportunity detection thresholds
- Budget minimum

### Email Settings (`config/email.yml`)
- Newsletter schedule
- Lead detection keywords
- VIP detection keywords
- Response templates

### Monitoring Settings (`config/monitoring.yml`)
- CPU/RAM/Disk thresholds
- Services to monitor
- Check intervals
- Alert preferences

## 🚨 Troubleshooting

### Scripts not running

1. **Check permissions**:
```bash
ls -la /home/turbo/automation/scripts/
```

2. **Check Python path**:
```bash
which python3
```

3. **Test import**:
```bash
python3 -c "import yaml; import psutil; print('OK')"
```

### Telegram alerts not working

1. **Verify credentials**:
```bash
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID
```

2. **Test connection**:
```bash
curl -X POST https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage \
  -d chat_id=$TELEGRAM_CHAT_ID \
  -d text="Test message"
```

### Cron jobs not executing

1. **Check crontab**:
```bash
crontab -l
```

2. **Check syslog**:
```bash
tail -f /var/log/syslog | grep CRON
```

3. **Check mail**:
```bash
mail
```

## 📊 Monitoring the System

### Real-time Log Monitoring
```bash
tail -f /home/turbo/automation/logs/monitoring.log
```

### Daily Summary
Enable in `config/monitoring.yml`:
```yaml
reporting:
  daily_report: true
  report_time: "07:00"
```

### Custom Alerts
Modify thresholds in config files:
```yaml
cpu:
  critical_threshold: 80
  warning_threshold: 70
```

## 🔒 Security

### Environment Variables
```bash
export TELEGRAM_BOT_TOKEN='...'
export TELEGRAM_CHAT_ID='...'
export LINKEDIN_API_KEY='...'
export CODEUR_API_KEY='...'
export EMAIL_PASSWORD='...'
```

### Log Rotation
Logs are automatically rotated (max 10MB, 5 backups).

### Safe Defaults
- All operations are logged
- Failed tasks trigger alerts
- Sensitive data not logged
- Retry logic with exponential backoff

## 📈 Performance Tips

1. **Optimize check intervals**:
   - LinkedIn: 5 hours apart (less frequently if needed)
   - Codeur: 6 hours apart
   - Email: 10 hours apart
   - Monitoring: Every 30 mins

2. **Use connection pooling**:
   - Reuse HTTP sessions
   - Batch API calls

3. **Monitor resource usage**:
   - Keep CPU below 50% on average
   - RAM usage under 2GB
   - Disk I/O reasonable

## 🎯 Next Steps

1. ✅ Run `bash setup.sh`
2. ✅ Configure Telegram environment variables
3. ✅ Edit templates with your content
4. ✅ Test scripts individually
5. ✅ Enable cron or systemd timers
6. ✅ Monitor logs for success

## 📝 License

JARVIS Automation System - Private Use Only

## 🤝 Support

For issues or improvements, check the logs:
```bash
grep ERROR /home/turbo/automation/logs/*.log
```

---

**JARVIS Cowork Automation** | Productivity. Intelligence. Scale.
