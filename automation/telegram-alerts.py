#!/usr/bin/env python3
"""
Telegram Alerts System - Core module for sending alerts
"""
import os
import sys
import json
import logging
import requests
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path
from enum import Enum

class AlertLevel(Enum):
    INFO = "ℹ️"
    SUCCESS = "✅"
    WARNING = "⚠️"
    ERROR = "❌"
    CRITICAL = "🚨"

class TelegramAlerts:
    def __init__(self, config_file: str = "/home/turbo/automation/config/telegram.yml"):
        self.config_file = config_file
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        # Setup logging
        log_dir = Path("/home/turbo/automation/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger("TelegramAlerts")
        handler = logging.FileHandler(log_dir / "telegram.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)
        
    def send_message(self, message: str, level: AlertLevel = AlertLevel.INFO,
                    parse_mode: str = "Markdown") -> bool:
        """Send a message to Telegram"""
        if not self.bot_token or not self.chat_id:
            self.logger.error("Telegram credentials not configured")
            return False
        
        try:
            emoji = level.value
            formatted_message = f"{emoji} {message}"
            
            payload = {
                "chat_id": self.chat_id,
                "text": formatted_message,
                "parse_mode": parse_mode,
                "disable_notification": level == AlertLevel.INFO
            }
            
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                self.logger.info(f"Message sent successfully: {message[:50]}...")
                return True
            else:
                self.logger.error(f"Failed to send message: {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending message: {str(e)}")
            return False
    
    def send_alert(self, title: str, message: str, level: AlertLevel = AlertLevel.WARNING,
                  metadata: Optional[Dict] = None) -> bool:
        """Send a formatted alert"""
        alert_text = f"*{title}*\n{message}"
        
        if metadata:
            alert_text += "\n\n_Details:_"
            for key, value in metadata.items():
                alert_text += f"\n• {key}: `{value}`"
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alert_text += f"\n\n`[{timestamp}]`"
        
        return self.send_message(alert_text, level)
    
    def send_monitoring_update(self, stats: Dict) -> bool:
        """Send system monitoring update"""
        message = "*📊 System Monitoring Update*\n"
        message += f"• CPU: `{stats.get('cpu', 'N/A')}%`\n"
        message += f"• RAM: `{stats.get('memory', 'N/A')}%`\n"
        message += f"• Disk: `{stats.get('disk', 'N/A')}%`\n"
        
        if stats.get('gpu'):
            message += f"• GPU: `{stats['gpu']}%`\n"
        
        return self.send_message(message, AlertLevel.INFO)

# Global instance
_alerts = None

def get_alerts():
    global _alerts
    if _alerts is None:
        _alerts = TelegramAlerts()
    return _alerts

if __name__ == "__main__":
    alerts = TelegramAlerts()
    
    # Test message
    test_message = "🧪 Test d'alerte Telegram - Système d'automation en cours de configuration"
    alerts.send_message(test_message, AlertLevel.INFO)
    print("✓ Test message sent")
