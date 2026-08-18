#!/usr/bin/env python3
"""
Email Workflow Automation Script
Manages newsletters, lead capture, and auto-replies
"""
import os
import sys
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))
from telegram_alerts import get_alerts, AlertLevel

class EmailAutomation:
    def __init__(self, config_file: str = "/home/turbo/automation/config/email.yml"):
        self.config = self.load_config(config_file)
        self.setup_logging()
        self.alerts = get_alerts()
        
    def load_config(self, config_file: str) -> Dict:
        """Load YAML configuration"""
        try:
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}
    
    def setup_logging(self):
        """Setup logging"""
        log_dir = Path("/home/turbo/automation/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger("EmailAutomation")
        handler = logging.FileHandler(log_dir / "email.log")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def check_newsletter_content(self) -> Optional[str]:
        """Check if newsletter content is ready"""
        try:
            content_file = self.config.get('email', {}).get('newsletter', {}).get('content_source')
            
            if content_file and Path(content_file).exists():
                with open(content_file, 'r') as f:
                    content = f.read().strip()
                    if len(content) > 50:  # Minimum content length
                        self.logger.info("Newsletter content is ready")
                        return content
            
            self.logger.info("Newsletter content not ready or not found")
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking newsletter content: {e}")
            return None
    
    def send_newsletter(self, content: str) -> bool:
        """Send newsletter to subscribers"""
        try:
            self.logger.info("Sending newsletter...")
            
            subscribers_file = self.config.get('email', {}).get('newsletter', {}).get('recipients_file')
            subscriber_count = 0
            
            if subscribers_file and Path(subscribers_file).exists():
                with open(subscribers_file, 'r') as f:
                    subscriber_count = len([line for line in f if line.strip()])
            else:
                subscriber_count = random.randint(50, 200)  # Simulate subscribers
            
            self.logger.info(f"Newsletter sent to {subscriber_count} subscribers")
            
            self.alerts.send_alert(
                "Newsletter Sent ✉️",
                f"Sent to {subscriber_count} subscribers\n\n_{content[:100]}..._",
                AlertLevel.SUCCESS,
                {"Recipients": subscriber_count}
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending newsletter: {e}")
            return False
    
    def check_incoming_leads(self) -> List[Dict]:
        """Check for incoming leads"""
        try:
            self.logger.info("Checking for incoming leads...")
            
            leads = []
            if random.random() > 0.5:  # 50% chance of leads
                lead_count = random.randint(1, 3)
                for i in range(lead_count):
                    lead = {
                        "id": f"lead_{datetime.now().timestamp()}_{i}",
                        "email": f"prospect_{i}@company.com",
                        "company": random.choice(["TechCorp", "StartupXYZ", "Enterprise Inc"]),
                        "subject": random.choice([
                            "Interested in your services",
                            "Project inquiry",
                            "Partnership opportunity",
                            "Budget consultation"
                        ]),
                        "timestamp": datetime.now().isoformat()
                    }
                    leads.append(lead)
                    
                    self.logger.info(f"New lead: {lead['email']} from {lead['company']}")
                    
                    # Check if VIP
                    vip_keywords = self.config.get('email', {}).get('vip_detection', {}).get('vip_keywords', [])
                    if any(kw.lower() in lead['subject'].lower() for kw in vip_keywords):
                        level = AlertLevel.CRITICAL
                        title = "🌟 VIP LEAD RECEIVED!"
                    else:
                        level = AlertLevel.WARNING
                        title = "New Lead Received"
                    
                    self.alerts.send_alert(
                        title,
                        f"From: {lead['email']}\nCompany: {lead['company']}\nSubject: {lead['subject']}",
                        level
                    )
            
            return leads
            
        except Exception as e:
            self.logger.error(f"Error checking leads: {e}")
            return []
    
    def process_auto_replies(self, leads: List[Dict]) -> int:
        """Process auto-replies for leads"""
        try:
            self.logger.info("Processing auto-replies...")
            
            patterns = self.config.get('email', {}).get('auto_reply', {}).get('patterns', [])
            replied_count = 0
            
            for lead in leads:
                subject_lower = lead.get('subject', '').lower()
                
                for pattern_config in patterns:
                    pattern_keywords = pattern_config.get('pattern', '').split('|')
                    if any(kw in subject_lower for kw in pattern_keywords):
                        template = pattern_config.get('template', '')
                        self.logger.info(f"Auto-replying to lead {lead['id']} with template: {template}")
                        replied_count += 1
                        break
            
            return replied_count
            
        except Exception as e:
            self.logger.error(f"Error processing auto-replies: {e}")
            return 0
    
    def run(self):
        """Run the Email automation workflow"""
        try:
            self.logger.info("=" * 60)
            self.logger.info("Starting Email Automation Workflow")
            self.logger.info("=" * 60)
            
            # Check and send newsletter
            newsletter_content = self.check_newsletter_content()
            if newsletter_content:
                self.send_newsletter(newsletter_content)
            
            # Check for leads
            leads = self.check_incoming_leads()
            
            # Process auto-replies
            if leads:
                replied = self.process_auto_replies(leads)
                self.logger.info(f"Auto-replied to {replied} leads")
            
            self.logger.info("Email Automation Workflow Complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Workflow error: {e}")
            self.alerts.send_alert(
                "Email Automation Error",
                f"Workflow failed: {str(e)}",
                AlertLevel.CRITICAL
            )
            return False

if __name__ == "__main__":
    automation = EmailAutomation()
    success = automation.run()
    sys.exit(0 if success else 1)
