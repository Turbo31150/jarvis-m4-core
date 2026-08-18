#!/usr/bin/env python3
"""
Automation Scheduler - Manages cron jobs and systemd timers
"""
import os
import sys
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict

class AutomationScheduler:
    def __init__(self):
        self.setup_logging()
        self.script_dir = Path("/home/turbo/automation/scripts")
        self.log_dir = Path("/home/turbo/automation/logs")
        
    def setup_logging(self):
        """Setup logging"""
        log_dir = Path("/home/turbo/automation/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger("AutomationScheduler")
        handler = logging.FileHandler(log_dir / "scheduler.log")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def get_cron_entries(self) -> List[str]:
        """Generate cron entries for all tasks"""
        entries = [
            "# LinkedIn Automation - 9:00, 14:00, 19:00",
            "0 9,14,19 * * * /home/turbo/automation/scripts/linkedin-automation.py >> /home/turbo/automation/logs/cron.log 2>&1",
            "",
            "# Codeur.com Automation - 10:00, 16:00",
            "0 10,16 * * * /home/turbo/automation/scripts/codeur-automation.py >> /home/turbo/automation/logs/cron.log 2>&1",
            "",
            "# Email Automation - 8:00, 18:00",
            "0 8,18 * * * /home/turbo/automation/scripts/email-automation.py >> /home/turbo/automation/logs/cron.log 2>&1",
            "",
            "# System Monitoring - Every 30 minutes",
            "*/30 * * * * /home/turbo/automation/scripts/system-monitor.py >> /home/turbo/automation/logs/cron.log 2>&1",
        ]
        return entries
    
    def generate_systemd_timer(self, script_name: str, schedule: Dict) -> str:
        """Generate systemd timer unit file"""
        unit_name = script_name.replace('.py', '')
        
        template = f"""[Unit]
Description=JARVIS Automation - {unit_name}
After=network-online.target

[Timer]
OnBootSec=5min
OnUnitActiveSec={schedule.get('interval', '1h')}
Persistent=true

[Install]
WantedBy=timers.target
"""
        return template
    
    def generate_systemd_service(self, script_name: str) -> str:
        """Generate systemd service unit file"""
        unit_name = script_name.replace('.py', '')
        script_path = self.script_dir / script_name
        
        template = f"""[Unit]
Description=JARVIS Automation Service - {unit_name}
After=network.target

[Service]
Type=oneshot
User={os.getenv('USER', 'root')}
WorkingDirectory=/home/turbo/automation
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 {script_path}
StandardOutput=journal
StandardError=journal
SyslogIdentifier={unit_name}

[Install]
WantedBy=multi-user.target
"""
        return template
    
    def print_setup_instructions(self):
        """Print setup instructions"""
        print("\n" + "="*70)
        print("SETUP INSTRUCTIONS FOR AUTOMATION SYSTEM")
        print("="*70 + "\n")
        
        print("1. TELEGRAM CONFIGURATION:")
        print("-" * 70)
        print("Set environment variables for Telegram:")
        print("  export TELEGRAM_BOT_TOKEN='your_bot_token'")
        print("  export TELEGRAM_CHAT_ID='your_chat_id'")
        print("\nGet your bot token from @BotFather on Telegram")
        print("Get your chat ID by sending a message to your bot\n")
        
        print("2. CRON INSTALLATION (Recommended for quick setup):")
        print("-" * 70)
        print("Edit your crontab:")
        print("  crontab -e")
        print("\nAdd these lines:")
        cron_entries = self.get_cron_entries()
        for entry in cron_entries:
            if entry and not entry.startswith('#'):
                print(f"  {entry}")
        print()
        
        print("3. SYSTEMD INSTALLATION (Recommended for production):")
        print("-" * 70)
        print("Create service files in /etc/systemd/system/:")
        print()
        
        services = [
            'linkedin-automation',
            'codeur-automation',
            'email-automation',
            'system-monitor'
        ]
        
        for service in services:
            print(f"  # Create /etc/systemd/system/{service}.service")
            print(f"  # Create /etc/systemd/system/{service}.timer")
            print()
        
        print("Then reload and enable:")
        print("  sudo systemctl daemon-reload")
        print("  sudo systemctl enable --now linkedin-automation.timer")
        print("  sudo systemctl enable --now codeur-automation.timer")
        print("  sudo systemctl enable --now email-automation.timer")
        print("  sudo systemctl enable --now system-monitor.timer")
        print()
        
        print("4. TEMPLATES & CONFIGURATION:")
        print("-" * 70)
        print("Create content templates in /home/turbo/automation/templates/:")
        print("  • linkedin_content.md - LinkedIn posts")
        print("  • newsletter.md - Email newsletter")
        print("  • newsletter_subscribers.txt - Subscriber list")
        print()
        
        print("5. VERIFY SETUP:")
        print("-" * 70)
        print("Test scripts individually:")
        print("  python3 /home/turbo/automation/scripts/linkedin-automation.py")
        print("  python3 /home/turbo/automation/scripts/system-monitor.py")
        print()
        
        print("Check logs:")
        print("  tail -f /home/turbo/automation/logs/*.log")
        print()
        
        print("Monitor timers (systemd):")
        print("  systemctl list-timers")
        print()

if __name__ == "__main__":
    scheduler = AutomationScheduler()
    scheduler.print_setup_instructions()
