#!/usr/bin/env python3
"""
Codeur.com Automation Script
Manages messages, proposals, and client interactions
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

class CodeurAutomation:
    def __init__(self, config_file: str = "/home/turbo/automation/config/codeur.yml"):
        self.config = self.load_config(config_file)
        self.setup_logging()
        self.alerts = get_alerts()
        self.data_file = Path("/home/turbo/automation/logs/codeur_data.json")
        
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
        
        self.logger = logging.getLogger("CodeurAutomation")
        handler = logging.FileHandler(log_dir / "codeur.log")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def check_messages(self) -> List[Dict]:
        """Check for new messages from clients"""
        try:
            self.logger.info("Checking for new messages...")
            
            # Simulate fetching messages
            messages = [
                {
                    "id": f"msg_{i}",
                    "from": f"client_{i}",
                    "subject": random.choice([
                        "Project Budget Question",
                        "Timeline Inquiry",
                        "Technical Requirements",
                        "Rate Negotiation",
                        "Reference Request"
                    ]),
                    "timestamp": datetime.now().isoformat(),
                    "unread": True
                }
                for i in range(random.randint(0, 3))
            ]
            
            if messages:
                self.logger.info(f"Found {len(messages)} new messages")
                for msg in messages:
                    self.logger.info(f"  - {msg['from']}: {msg['subject']}")
                    
                    # Alert on new messages
                    self.alerts.send_alert(
                        "New Codeur.com Message",
                        f"From: {msg['from']}\nSubject: {msg['subject']}",
                        AlertLevel.INFO
                    )
            
            return messages
            
        except Exception as e:
            self.logger.error(f"Error checking messages: {e}")
            return []
    
    def process_auto_replies(self, messages: List[Dict]) -> int:
        """Process auto-replies for known patterns"""
        try:
            self.logger.info("Processing auto-replies...")
            
            triggers = self.config.get('codeur', {}).get('auto_reply_triggers', [])
            replied_count = 0
            
            for message in messages:
                subject_lower = message.get('subject', '').lower()
                
                for trigger in triggers:
                    keywords = trigger.get('keyword', '').split('|')
                    if any(kw in subject_lower for kw in keywords):
                        template = trigger.get('template', '')
                        self.logger.info(f"Auto-replying to {message['id']} with template: {template}")
                        replied_count += 1
                        
                        self.alerts.send_alert(
                            "Auto-Reply Sent",
                            f"To: {message['from']}\nTemplate: {template}",
                            AlertLevel.SUCCESS
                        )
                        break
            
            return replied_count
            
        except Exception as e:
            self.logger.error(f"Error processing auto-replies: {e}")
            return 0
    
    def detect_opportunities(self) -> List[Dict]:
        """Detect high-value opportunities"""
        try:
            self.logger.info("Detecting new opportunities...")
            
            # Simulate opportunity detection
            opportunities = []
            
            if random.random() > 0.6:  # 40% chance
                opportunity = {
                    "id": f"opp_{datetime.now().timestamp()}",
                    "title": random.choice([
                        "AI Integration for E-commerce Platform",
                        "Python Backend Optimization Project",
                        "DevOps Pipeline Automation",
                        "Real-time Analytics Dashboard",
                        "Microservices Migration"
                    ]),
                    "budget": random.randint(1000, 10000),
                    "skill_match": random.uniform(0.7, 1.0),
                    "client": f"client_{random.randint(1, 100)}",
                    "timestamp": datetime.now().isoformat()
                }
                
                budget_threshold = self.config.get('codeur', {}).get('opportunity_detection', {}).get('budget_threshold', 500)
                skill_threshold = self.config.get('codeur', {}).get('opportunity_detection', {}).get('skill_match_threshold', 0.75)
                
                if opportunity['budget'] >= budget_threshold and opportunity['skill_match'] >= skill_threshold:
                    opportunities.append(opportunity)
                    self.logger.info(f"New opportunity detected: {opportunity['title']} (Budget: {opportunity['budget']})")
                    
                    self.alerts.send_alert(
                        "💰 High-Value Opportunity Detected!",
                        f"*{opportunity['title']}*\n"
                        f"Budget: €{opportunity['budget']}\n"
                        f"Skill Match: {opportunity['skill_match']:.0%}",
                        AlertLevel.WARNING,
                        {
                            "Client": opportunity['client'],
                            "Match Score": f"{opportunity['skill_match']:.0%}"
                        }
                    )
            
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Error detecting opportunities: {e}")
            return []
    
    def list_proposals(self) -> List[Dict]:
        """List proposals ready to send"""
        try:
            self.logger.info("Listing pending proposals...")
            
            proposals = [
                {
                    "id": f"prop_{i}",
                    "project": f"Project {chr(65+i)}",
                    "client": f"Client {i}",
                    "status": "ready",
                    "created_at": datetime.now().isoformat()
                }
                for i in range(random.randint(0, 2))
            ]
            
            if proposals:
                self.logger.info(f"Found {len(proposals)} pending proposals")
                for prop in proposals:
                    self.logger.info(f"  - {prop['project']}: {prop['status']}")
            
            return proposals
            
        except Exception as e:
            self.logger.error(f"Error listing proposals: {e}")
            return []
    
    def run(self):
        """Run the Codeur automation workflow"""
        try:
            self.logger.info("=" * 60)
            self.logger.info("Starting Codeur.com Automation Workflow")
            self.logger.info("=" * 60)
            
            # Check messages
            messages = self.check_messages()
            
            # Process auto-replies
            if messages:
                replied = self.process_auto_replies(messages)
                self.logger.info(f"Auto-replied to {replied} messages")
            
            # Detect opportunities
            opportunities = self.detect_opportunities()
            
            # List proposals
            proposals = self.list_proposals()
            
            self.logger.info("Codeur.com Automation Workflow Complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Workflow error: {e}")
            self.alerts.send_alert(
                "Codeur Automation Error",
                f"Workflow failed: {str(e)}",
                AlertLevel.CRITICAL
            )
            return False

if __name__ == "__main__":
    automation = CodeurAutomation()
    success = automation.run()
    sys.exit(0 if success else 1)
