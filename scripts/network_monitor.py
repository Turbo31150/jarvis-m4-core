#!/usr/bin/env python3
import json
import os
import re
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

LOG_FILE = "/var/log/nginx/access_json.log"
STATUS_URL = "http://loadbalancer:8420/nginx_status"

def get_nginx_status():
    """Queries Nginx stub_status and parses it."""
    try:
        req = urllib.request.Request(STATUS_URL)
        with urllib.request.urlopen(req, timeout=2) as response:
            data = response.read().decode('utf-8')
            # Format typical:
            # Active connections: 291 
            # server accepts handled requests
            #  16630948 16630948 31070465 
            # Reading: 6 Writing: 179 Waiting: 106
            lines = data.split('\n')
            active = int(re.search(r'Active connections:\s+(\d+)', lines[0]).group(1))
            reading = int(re.search(r'Reading:\s+(\d+)', lines[3]).group(1))
            writing = int(re.search(r'Writing:\s+(\d+)', lines[3]).group(1))
            waiting = int(re.search(r'Waiting:\s+(\d+)', lines[3]).group(1))
            return {
                "active_connections": active,
                "reading": reading,
                "writing": writing,
                "waiting": waiting
            }
    except Exception as e:
        return {
            "active_connections": 0,
            "reading": 0,
            "writing": 0,
            "waiting": 0,
            "error": str(e)
        }

def parse_logs(limit=500):
    """Reads and parses the last N lines of Nginx json log."""
    if not os.path.exists(LOG_FILE):
        return []

    parsed_lines = []
    try:
        # Read file backwards or just read the tail
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()
            tail = lines[-limit:]
            for line in tail:
                try:
                    parsed_lines.append(json.loads(line.strip()))
                except Exception:
                    continue
    except Exception as e:
        print(f"Error reading logs: {e}")
    return parsed_lines

def analyze_traffic():
    logs = parse_logs(500)
    nginx_stats = get_nginx_status()

    if not logs:
        return {
            "health_score": 100,
            "total_requests_analyzed": 0,
            "requests_per_second": 0.0,
            "error_rate": 0.0,
            "avg_latency": 0.0,
            "nginx": nginx_stats,
            "upstreams": {},
            "top_clients": {},
            "status": "idle"
        }

    total = len(logs)
    err_5xx = 0
    err_4xx = 0
    slow_reqs = 0
    total_latency = 0.0
    latency_count = 0
    upstreams = {}
    clients = {}

    # For RPS calculation (last 10 seconds)
    now_ts = datetime.utcnow()
    recent_requests = 0

    for log in logs:
        # HTTP Status
        status_str = log.get("status", "200").strip()
        status = 200
        try:
            status = int(status_str)
        except ValueError:
            pass

        if 500 <= status < 600:
            err_5xx += 1
        elif 400 <= status < 500:
            err_4xx += 1

        # Client IP
        ip = log.get("remote_addr", "unknown")
        clients[ip] = clients.get(ip, 0) + 1

        # Latency / Upstream
        req_time_str = log.get("request_time", "0")
        try:
            req_time = float(req_time_str)
        except ValueError:
            req_time = 0.0

        # Don't penalize long-lived WebSocket connections (status 101)
        is_websocket = (status == 101)
        if req_time > 1.5 and not is_websocket:
            slow_reqs += 1

        if not is_websocket:
            total_latency += req_time
            latency_count += 1

        # Upstream info
        req_str = log.get("request", "")
        # Extract upstream name from request URI or use path
        upstream_name = "unknown"
        for path_key, name in [
            ("/socket.io", "jarvis-ws"),
            ("/openclaw", "openclaw-node"),
            ("/api/network", "network-monitor"),
            ("/nginx_status", "nginx-status")
        ]:
            if path_key in req_str:
                upstream_name = name
                break
        
        # Or deduce from request port or headers if logged, but here we can check request pattern
        if upstream_name == "unknown":
            # Guessing based on upstream response time availability
            upstream_resp = log.get("upstream_response_time", "")
            if upstream_resp:
                upstream_name = "proxied-app"
            else:
                upstream_name = "static/direct"

        if upstream_name not in upstreams:
            upstreams[upstream_name] = {"requests": 0, "errors": 0, "total_latency": 0.0, "latency_count": 0}
        
        upstreams[upstream_name]["requests"] += 1
        if 500 <= status < 600:
            upstreams[upstream_name]["errors"] += 1
        if not is_websocket and req_time > 0:
            upstreams[upstream_name]["total_latency"] += req_time
            upstreams[upstream_name]["latency_count"] += 1

        # RPS timing parse
        # time_local format: "06/Jun/2026:12:39:32 +0000"
        time_local = log.get("time_local", "")
        if time_local:
            try:
                # Remove timezone offset for simple parsing
                time_clean = time_local.split(" ")[0]
                dt = datetime.strptime(time_clean, "%d/%b/%Y:%H:%M:%S")
                delta = (now_ts - dt).total_seconds()
                if 0 <= delta <= 10:
                    recent_requests += 1
            except Exception:
                pass

    # Scoring formulation
    ratio_5xx = err_5xx / total
    ratio_4xx = err_4xx / total
    ratio_slow = slow_reqs / total if total > 0 else 0

    score = 100 - (ratio_5xx * 150) - (ratio_4xx * 30) - (ratio_slow * 50)
    score = max(0, min(100, int(score)))

    avg_lat = total_latency / latency_count if latency_count > 0 else 0.0
    rps = recent_requests / 10.0

    # Format Upstreams data
    upstreams_formatted = {}
    for name, data in upstreams.items():
        avg_upstream_lat = data["total_latency"] / data["latency_count"] if data["latency_count"] > 0 else 0.0
        upstreams_formatted[name] = {
            "requests": data["requests"],
            "errors": data["errors"],
            "error_rate_pct": round((data["errors"] / data["requests"]) * 100, 2) if data["requests"] > 0 else 0.0,
            "avg_latency_sec": round(avg_upstream_lat, 3)
        }

    # Sort clients and take top 5
    top_clients = dict(sorted(clients.items(), key=lambda item: item[1], reverse=True)[:5])

    status = "healthy"
    if score < 70:
        status = "degraded"
    if score < 40:
        status = "critical"

    return {
        "health_score": score,
        "status": status,
        "total_requests_analyzed": total,
        "requests_per_second": round(rps, 2),
        "error_rate": round(ratio_5xx * 100, 2),
        "avg_latency": round(avg_lat, 3),
        "nginx": nginx_stats,
        "upstreams": upstreams_formatted,
        "top_clients": top_clients,
        "timestamp": datetime.now().isoformat()
    }

class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/stats":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            stats = analyze_traffic()
            self.wfile.write(json.dumps(stats).encode('utf-8'))
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "UP"}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

def run():
    server_address = ('', 8421)
    httpd = HTTPServer(server_address, MetricsHandler)
    print("Network monitor server running on port 8421...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()

if __name__ == '__main__':
    run()
