#!/usr/bin/env python3
"""
System Monitoring Script
Continuous monitoring of CPU, RAM, GPU, Disk and services
"""
import os
import sys
import json
import logging
import time
import subprocess
import psutil
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import yaml

# Add parent directory to path
automation_dir = Path(__file__).parent.parent
sys.path.insert(0, str(automation_dir))

# Import telegram alerts
import importlib.util
spec = importlib.util.spec_from_file_location("telegram_alerts", str(automation_dir / "telegram-alerts.py"))
telegram_alerts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(telegram_alerts)
get_alerts = telegram_alerts.get_alerts
AlertLevel = telegram_alerts.AlertLevel

class SystemMonitor:
    def __init__(self, config_file: str = "/home/turbo/automation/config/monitoring.yml"):
        self.config = self.load_config(config_file)
        self.setup_logging()
        self.alerts = get_alerts()
        self.last_hourly_report = None
        
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
        
        self.logger = logging.getLogger("SystemMonitor")
        handler = logging.FileHandler(log_dir / "monitoring.log")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def get_cpu_stats(self) -> Dict:
        """Get CPU statistics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            per_cpu = psutil.cpu_percent(interval=1, percpu=True)
            
            return {
                "total": cpu_percent,
                "count": cpu_count,
                "per_cpu": per_cpu,
                "status": "critical" if cpu_percent > 80 else "warning" if cpu_percent > 70 else "ok"
            }
        except Exception as e:
            self.logger.error(f"Error getting CPU stats: {e}")
            return {}
    
    def get_memory_stats(self) -> Dict:
        """Get memory statistics"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                "total_gb": round(memory.total / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "percent": memory.percent,
                "swap_percent": swap.percent,
                "status": "critical" if memory.percent > 85 else "warning" if memory.percent > 75 else "ok"
            }
        except Exception as e:
            self.logger.error(f"Error getting memory stats: {e}")
            return {}
    
    def get_disk_stats(self) -> Dict:
        """Get disk statistics"""
        try:
            disk_stats = {}
            paths = self.config.get('monitoring', {}).get('disk', {}).get('paths_to_monitor', ['/'])
            
            for path in paths:
                try:
                    disk = psutil.disk_usage(path)
                    disk_stats[path] = {
                        "total_gb": round(disk.total / (1024**3), 2),
                        "used_gb": round(disk.used / (1024**3), 2),
                        "free_gb": round(disk.free / (1024**3), 2),
                        "percent": disk.percent,
                        "status": "critical" if disk.percent > 85 else "warning" if disk.percent > 75 else "ok"
                    }
                except Exception as e:
                    self.logger.error(f"Error getting disk stats for {path}: {e}")
            
            return disk_stats
        except Exception as e:
            self.logger.error(f"Error getting disk stats: {e}")
            return {}
    
    def get_gpu_stats(self) -> Dict:
        """Get GPU statistics"""
        try:
            gpu_stats = {}
            
            # Try to get NVIDIA GPU stats
            try:
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=index,name,utilization.gpu,memory.used,memory.total', 
                     '--format=csv,noheader,nounits'],
                    capture_output=True,
                    timeout=5,
                    text=True
                )
                
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            parts = [p.strip() for p in line.split(',')]
                            if len(parts) >= 5:
                                gpu_stats[f"GPU_{parts[0]}"] = {
                                    "name": parts[1],
                                    "utilization": int(parts[2]),
                                    "memory_used": int(parts[3]),
                                    "memory_total": int(parts[4]),
                                    "status": "critical" if int(parts[2]) > 90 else "warning" if int(parts[2]) > 80 else "ok"
                                }
            except (FileNotFoundError, subprocess.TimeoutExpired):
                self.logger.debug("NVIDIA GPU not found or nvidia-smi not available")
            
            return gpu_stats
        except Exception as e:
            self.logger.error(f"Error getting GPU stats: {e}")
            return {}
    
    def check_services(self) -> Dict:
        """Check service status"""
        try:
            services_status = {}
            services = self.config.get('monitoring', {}).get('services', {}).get('services_to_monitor', [])
            
            for service in services:
                service_name = service.get('name', '')
                service_type = service.get('type', 'systemd')
                
                try:
                    if service_type == 'systemd':
                        result = subprocess.run(
                            ['systemctl', 'is-active', service_name],
                            capture_output=True,
                            timeout=5,
                            text=True
                        )
                        status = result.stdout.strip()
                    else:  # process
                        # Check if process is running
                        running_processes = [p.info for p in psutil.process_iter(['name'])]
                        status = "active" if any(service_name in p['name'] for p in running_processes) else "inactive"
                    
                    services_status[service_name] = {
                        "status": status,
                        "type": service_type,
                        "critical": service.get('critical', False)
                    }
                except Exception as e:
                    self.logger.error(f"Error checking service {service_name}: {e}")
                    services_status[service_name] = {"status": "unknown", "type": service_type}
            
            return services_status
        except Exception as e:
            self.logger.error(f"Error checking services: {e}")
            return {}
    
    def get_process_stats(self) -> List[Dict]:
        """Get top processes by CPU usage"""
        try:
            processes = []
            top_n = self.config.get('monitoring', {}).get('processes', {}).get('track_top_n', 5)
            
            # Get all processes sorted by CPU usage
            proc_list = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    proc_list.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort by CPU and get top N
            proc_list.sort(key=lambda x: x['cpu_percent'], reverse=True)
            
            for proc in proc_list[:top_n]:
                processes.append({
                    "pid": proc['pid'],
                    "name": proc['name'],
                    "cpu_percent": round(proc['cpu_percent'], 2),
                    "memory_percent": round(proc['memory_percent'], 2)
                })
            
            return processes
        except Exception as e:
            self.logger.error(f"Error getting process stats: {e}")
            return []
    
    def check_alerts(self, stats: Dict):
        """Check thresholds and send alerts"""
        try:
            cpu = stats.get('cpu', {})
            memory = stats.get('memory', {})
            disk = stats.get('disk', {})
            gpu = stats.get('gpu', {})
            services = stats.get('services', {})
            
            # CPU alerts
            if cpu.get('status') == 'critical':
                self.alerts.send_alert(
                    "🚨 High CPU Usage",
                    f"CPU: {cpu['total']}%\nThreshold: > 80%",
                    AlertLevel.CRITICAL,
                    {"CPUs": cpu['count'], "Usage": f"{cpu['total']}%"}
                )
            elif cpu.get('status') == 'warning':
                self.alerts.send_alert(
                    "⚠️ Medium CPU Usage",
                    f"CPU: {cpu['total']}%",
                    AlertLevel.WARNING
                )
            
            # Memory alerts
            if memory.get('status') == 'critical':
                self.alerts.send_alert(
                    "🚨 High Memory Usage",
                    f"Memory: {memory['percent']}% ({memory['used_gb']}GB / {memory['total_gb']}GB)",
                    AlertLevel.CRITICAL
                )
            
            # Disk alerts
            for path, disk_info in disk.items():
                if disk_info.get('status') == 'critical':
                    self.alerts.send_alert(
                        "🚨 Disk Space Critical",
                        f"Path: {path}\nUsage: {disk_info['percent']}% ({disk_info['used_gb']}GB / {disk_info['total_gb']}GB)",
                        AlertLevel.CRITICAL
                    )
            
            # Services alerts
            for service_name, service_info in services.items():
                if service_info.get('status') != 'active' and service_info.get('critical'):
                    self.alerts.send_alert(
                        f"🚨 Critical Service Down",
                        f"Service: {service_name}\nStatus: {service_info['status']}",
                        AlertLevel.CRITICAL
                    )
        
        except Exception as e:
            self.logger.error(f"Error checking alerts: {e}")
    
    def send_hourly_report(self, stats: Dict):
        """Send hourly summary report"""
        try:
            cpu = stats.get('cpu', {})
            memory = stats.get('memory', {})
            disk = stats.get('disk', {})
            
            message = "*📊 Hourly System Report*\n"
            message += f"• CPU: `{cpu.get('total', 'N/A')}%`\n"
            message += f"• RAM: `{memory.get('percent', 'N/A')}%` ({memory.get('used_gb', 'N/A')}GB / {memory.get('total_gb', 'N/A')}GB)\n"
            
            for path, disk_info in disk.items():
                message += f"• Disk ({path}): `{disk_info.get('percent', 'N/A')}%`\n"
            
            self.alerts.send_message(message, AlertLevel.INFO)
            
        except Exception as e:
            self.logger.error(f"Error sending hourly report: {e}")
    
    def run(self):
        """Run monitoring"""
        try:
            self.logger.info("Running system monitor check...")
            
            stats = {
                "timestamp": datetime.now().isoformat(),
                "cpu": self.get_cpu_stats(),
                "memory": self.get_memory_stats(),
                "disk": self.get_disk_stats(),
                "gpu": self.get_gpu_stats(),
                "services": self.check_services(),
                "processes": self.get_process_stats()
            }
            
            # Check alerts
            self.check_alerts(stats)
            
            # Send hourly report
            now = datetime.now()
            if now.minute == 0 and self.last_hourly_report != now.hour:
                self.send_hourly_report(stats)
                self.last_hourly_report = now.hour
            
            self.logger.info(f"Monitor check complete: CPU={stats['cpu'].get('total')}%, RAM={stats['memory'].get('percent')}%")
            return True
            
        except Exception as e:
            self.logger.error(f"Monitor error: {e}")
            self.alerts.send_alert(
                "System Monitor Error",
                f"Error: {str(e)}",
                AlertLevel.ERROR
            )
            return False

if __name__ == "__main__":
    monitor = SystemMonitor()
    success = monitor.run()
    sys.exit(0 if success else 1)
