#!/usr/bin/env python3
"""
Automation System Dashboard - View status and logs
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

class AutomationDashboard:
    def __init__(self):
        self.log_dir = Path("/home/turbo/automation/logs")
        
    def get_recent_logs(self, log_file: str, lines: int = 5) -> List[str]:
        """Get recent log entries"""
        log_path = self.log_dir / log_file
        
        if not log_path.exists():
            return ["No logs found"]
        
        try:
            with open(log_path, 'r') as f:
                all_lines = f.readlines()
                return [line.strip() for line in all_lines[-lines:]]
        except Exception as e:
            return [f"Error reading logs: {str(e)}"]
    
    def get_log_stats(self) -> Dict:
        """Get statistics from logs"""
        stats = {
            "linkedin": {"success": 0, "errors": 0, "last_run": None},
            "codeur": {"success": 0, "errors": 0, "last_run": None},
            "email": {"success": 0, "errors": 0, "last_run": None},
            "monitoring": {"success": 0, "errors": 0, "last_run": None},
        }
        
        for script_name, script_key in [
            ("linkedin.log", "linkedin"),
            ("codeur.log", "codeur"),
            ("email.log", "email"),
            ("monitoring.log", "monitoring"),
        ]:
            log_path = self.log_dir / script_name
            if log_path.exists():
                with open(log_path, 'r') as f:
                    lines = f.readlines()
                    stats[script_key]["success"] = sum(1 for l in lines if "Complete" in l)
                    stats[script_key]["errors"] = sum(1 for l in lines if "ERROR" in l or "error" in l)
                    
                    # Get last run time
                    if lines:
                        try:
                            last_line = lines[-1]
                            if " - " in last_line:
                                timestamp_str = last_line.split(" - ")[0]
                                stats[script_key]["last_run"] = timestamp_str
                        except:
                            pass
        
        return stats
    
    def get_system_status(self) -> Dict:
        """Get current system status"""
        status = {}
        
        # Check if scripts are executable
        script_dir = Path("/home/turbo/automation/scripts")
        scripts = ["linkedin-automation.py", "codeur-automation.py", "email-automation.py", "system-monitor.py"]
        
        status["scripts"] = {}
        for script in scripts:
            script_path = script_dir / script
            status["scripts"][script] = {
                "exists": script_path.exists(),
                "executable": os.access(script_path, os.X_OK) if script_path.exists() else False
            }
        
        # Check config files
        config_dir = Path("/home/turbo/automation/config")
        configs = ["linkedin.yml", "codeur.yml", "email.yml", "monitoring.yml", "telegram.yml"]
        
        status["config"] = {}
        for config in configs:
            config_path = config_dir / config
            status["config"][config] = config_path.exists()
        
        # Check templates
        template_dir = Path("/home/turbo/automation/templates")
        templates = ["linkedin_content.md", "newsletter.md", "newsletter_subscribers.txt"]
        
        status["templates"] = {}
        for template in templates:
            template_path = template_dir / template
            status["templates"][template] = template_path.exists()
        
        return status
    
    def display_dashboard(self):
        """Display the dashboard"""
        print("\n" + "="*80)
        print("�� JARVIS AUTOMATION SYSTEM - DASHBOARD")
        print("="*80 + "\n")
        
        # System Status
        print("📊 SYSTEM STATUS")
        print("-" * 80)
        sys_status = self.get_system_status()
        
        print("\n  Scripts:")
        for script, info in sys_status["scripts"].items():
            status_icon = "✓" if info["exists"] and info["executable"] else "✗"
            print(f"    {status_icon} {script}")
        
        print("\n  Configuration:")
        for config, exists in sys_status["config"].items():
            status_icon = "✓" if exists else "✗"
            print(f"    {status_icon} {config}")
        
        print("\n  Templates:")
        for template, exists in sys_status["templates"].items():
            status_icon = "✓" if exists else "✗"
            print(f"    {status_icon} {template}")
        
        # Log Statistics
        print("\n" + "="*80)
        print("📈 LOG STATISTICS")
        print("-" * 80)
        
        stats = self.get_log_stats()
        
        for script_name, data in stats.items():
            print(f"\n  {script_name.upper()}:")
            print(f"    ✓ Successful runs: {data['success']}")
            print(f"    ✗ Errors: {data['errors']}")
            if data['last_run']:
                print(f"    ⏱️  Last run: {data['last_run']}")
        
        # Recent Logs
        print("\n" + "="*80)
        print("📋 RECENT LOGS")
        print("-" * 80)
        
        for log_file, label in [
            ("monitoring.log", "System Monitor"),
            ("linkedin.log", "LinkedIn"),
            ("codeur.log", "Codeur"),
            ("email.log", "Email"),
        ]:
            print(f"\n  {label}:")
            logs = self.get_recent_logs(log_file, lines=2)
            for log_line in logs:
                if log_line:
                    print(f"    {log_line[:70]}...")
        
        # Next Scheduled Tasks
        print("\n" + "="*80)
        print("⏰ NEXT SCHEDULED TASKS")
        print("-" * 80)
        print("""
  LinkedIn:     09:00, 14:00, 19:00
  Codeur:       10:00, 16:00
  Email:        08:00, 18:00
  Monitoring:   Every 30 minutes
        """)
        
        # Configuration Reminders
        print("="*80)
        print("⚠️  CONFIGURATION REMINDERS")
        print("-" * 80)
        
        if not os.getenv("TELEGRAM_BOT_TOKEN"):
            print("  ⚠️  TELEGRAM_BOT_TOKEN not set. Alerts will not work!")
        if not os.getenv("TELEGRAM_CHAT_ID"):
            print("  ⚠️  TELEGRAM_CHAT_ID not set. Alerts will not work!")
        
        if os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"):
            print("  ✓ Telegram alerts configured")
        
        print("\n" + "="*80)
        print("💡 QUICK COMMANDS")
        print("-" * 80)
        print("""
  Run all tasks:           python3 /home/turbo/automation/run-automation.py
  Run specific task:       python3 /home/turbo/automation/run-automation.py --script linkedin
  View this dashboard:     python3 /home/turbo/automation/dashboard.py
  View setup guide:        python3 /home/turbo/automation/automation-scheduler.py
  View recent logs:        tail -f /home/turbo/automation/logs/*.log
  Check cron jobs:         crontab -l
  Check timers:            systemctl list-timers
        """)
        print("="*80 + "\n")

if __name__ == "__main__":
    dashboard = AutomationDashboard()
    dashboard.display_dashboard()
