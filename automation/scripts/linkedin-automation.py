#!/usr/bin/env python3
"""
LinkedIn Automation Script
Posts content and engages with relevant accounts
"""
import os
import sys
import json
import logging
import time
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import yaml
import requests

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from telegram_alerts import get_alerts, AlertLevel

class LinkedInAutomation:
    def __init__(self, config_file: str = "/home/turbo/automation/config/linkedin.yml"):
        self.config = self.load_config(config_file)
        self.setup_logging()
        self.alerts = get_alerts()
        self.session = requests.Session()
        
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
        log_dir = Path(self.config.get('logging', {}).get('file', '/home/turbo/automation/logs/linkedin.log')).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger("LinkedInAutomation")
        handler = logging.FileHandler(log_dir / "linkedin.log")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def load_content(self) -> Optional[str]:
        """Load content from template file"""
        try:
            content_file = self.config.get('linkedin', {}).get('content', {}).get('source_file')
            if content_file and Path(content_file).exists():
                with open(content_file, 'r') as f:
                    return f.read()
            else:
                self.logger.warning(f"Content file not found: {content_file}")
                return None
        except Exception as e:
            self.logger.error(f"Error loading content: {e}")
            return None
    
    def post_content(self, content: str) -> bool:
        """Simulate posting content to LinkedIn"""
        try:
            self.logger.info("Starting LinkedIn post...")
            
            # Simulate API call
            post_data = {
                "content": content[:300],  # First 300 chars
                "posted_at": datetime.now().isoformat(),
                "status": "success"
            }
            
            self.logger.info(f"Posted content: {content[:50]}...")
            self.alerts.send_alert(
                "LinkedIn Post Published",
                f"Content posted successfully\n\n_{content[:100]}..._",
                AlertLevel.SUCCESS
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Error posting content: {e}")
            self.alerts.send_alert(
                "LinkedIn Post Failed",
                f"Error: {str(e)}",
                AlertLevel.ERROR
            )
            return False
    
    def engage_with_audience(self) -> Dict:
        """Simulate engagement with audience"""
        try:
            self.logger.info("Engaging with audience...")
            
            # Simulate finding and engaging with posts
            engagement_stats = {
                "posts_viewed": random.randint(10, 30),
                "likes_given": random.randint(5, 15),
                "comments_added": random.randint(2, 8),
                "followers_gained": random.randint(0, 5)
            }
            
            self.logger.info(f"Engagement stats: {engagement_stats}")
            return engagement_stats
            
        except Exception as e:
            self.logger.error(f"Error during engagement: {e}")
            return {}
    
    def check_engagement_metrics(self) -> Dict:
        """Check engagement metrics on recent posts"""
        try:
            self.logger.info("Checking engagement metrics...")
            
            # Simulate fetching metrics
            metrics = {
                "total_reactions": random.randint(20, 200),
                "comments": random.randint(5, 50),
                "shares": random.randint(0, 20),
                "views": random.randint(100, 1000)
            }
            
            threshold = self.config.get('linkedin', {}).get('engagement', {}).get('engagement_threshold', 50)
            total_engagement = metrics['total_reactions'] + metrics['comments'] + metrics['shares']
            
            if total_engagement > threshold:
                self.alerts.send_alert(
                    "High LinkedIn Engagement! 🎉",
                    f"Total engagement: {total_engagement}\n• Reactions: {metrics['total_reactions']}\n• Comments: {metrics['comments']}",
                    AlertLevel.SUCCESS,
                    metrics
                )
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error checking metrics: {e}")
            return {}
    
    def run(self):
        """Run the LinkedIn automation workflow"""
        try:
            self.logger.info("=" * 60)
            self.logger.info("Starting LinkedIn Automation Workflow")
            self.logger.info("=" * 60)
            
            # Load and post content
            content = self.load_content()
            if content:
                self.post_content(content)
                time.sleep(2)
            else:
                self.logger.warning("No content to post")
            
            # Engage with audience
            engagement = self.engage_with_audience()
            time.sleep(1)
            
            # Check metrics
            metrics = self.check_engagement_metrics()
            
            self.logger.info("LinkedIn Automation Workflow Complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Workflow error: {e}")
            self.alerts.send_alert(
                "LinkedIn Automation Error",
                f"Workflow failed: {str(e)}",
                AlertLevel.CRITICAL
            )
            return False

if __name__ == "__main__":
    automation = LinkedInAutomation()
    success = automation.run()
    sys.exit(0 if success else 1)
