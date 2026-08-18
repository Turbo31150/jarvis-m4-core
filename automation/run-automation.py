#!/usr/bin/env python3
"""
Main Automation Runner - Execute all automation tasks
"""
import os
import sys
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List

class AutomationRunner:
    def __init__(self):
        self.setup_logging()
        self.script_dir = Path("/home/turbo/automation/scripts")
        self.results = {}
        
    def setup_logging(self):
        """Setup logging"""
        log_dir = Path("/home/turbo/automation/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger("AutomationRunner")
        handler = logging.FileHandler(log_dir / "runner.log")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def run_script(self, script_name: str) -> bool:
        """Run a single automation script"""
        try:
            script_path = self.script_dir / script_name
            
            if not script_path.exists():
                self.logger.error(f"Script not found: {script_path}")
                return False
            
            self.logger.info(f"Running {script_name}...")
            
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                timeout=300,  # 5 minutes timeout
                text=True
            )
            
            if result.returncode == 0:
                self.logger.info(f"✓ {script_name} completed successfully")
                self.results[script_name] = "SUCCESS"
                return True
            else:
                self.logger.error(f"✗ {script_name} failed with code {result.returncode}")
                if result.stderr:
                    self.logger.error(f"Error output: {result.stderr}")
                self.results[script_name] = "FAILED"
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"✗ {script_name} timed out")
            self.results[script_name] = "TIMEOUT"
            return False
        except Exception as e:
            self.logger.error(f"✗ Error running {script_name}: {str(e)}")
            self.results[script_name] = "ERROR"
            return False
    
    def run_all(self, only_script: str = None):
        """Run all or specific automation scripts"""
        scripts = [
            'linkedin-automation.py',
            'codeur-automation.py',
            'email-automation.py',
            'system-monitor.py'
        ]
        
        if only_script:
            scripts = [s for s in scripts if only_script in s]
        
        self.logger.info("=" * 70)
        self.logger.info(f"Starting Automation Runner - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("=" * 70)
        
        print("\n" + "="*70)
        print("🤖 JARVIS Automation Runner")
        print("="*70 + "\n")
        
        for script in scripts:
            print(f"Running: {script}...", end=" ", flush=True)
            success = self.run_script(script)
            print("✓" if success else "✗")
        
        self.print_summary()
        
        return all(v == "SUCCESS" for v in self.results.values())
    
    def print_summary(self):
        """Print execution summary"""
        print("\n" + "="*70)
        print("📊 Execution Summary")
        print("="*70)
        
        for script, status in self.results.items():
            emoji = "✓" if status == "SUCCESS" else "✗"
            print(f"{emoji} {script:30} {status}")
        
        success_count = sum(1 for v in self.results.values() if v == "SUCCESS")
        total_count = len(self.results)
        
        print("\n" + "-"*70)
        print(f"Completed: {success_count}/{total_count}")
        print("="*70 + "\n")
        
        self.logger.info("Automation Run Complete")
        self.logger.info(f"Results: {success_count}/{total_count} succeeded")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run JARVIS Automation Tasks")
    parser.add_argument(
        '--script',
        type=str,
        help='Run only a specific script (e.g., "linkedin", "codeur", "email", "monitoring")',
        default=None
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Run all automation scripts'
    )
    
    args = parser.parse_args()
    
    runner = AutomationRunner()
    success = runner.run_all(args.script)
    
    sys.exit(0 if success else 1)
