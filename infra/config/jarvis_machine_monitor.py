#!/usr/bin/env python3
"""JARVIS Machine Monitor — log personnalisé adaptatif par machine.
Usage: python3 jarvis_machine_monitor.py --machine M1 --interval 30
"""
import argparse, json, time, subprocess, os, sqlite3
from datetime import datetime
from pathlib import Path

MATRIX = json.load(open('/home/pamerys/jarvis/infra/config/jarvis_adaptive_matrix.json'))

ALERT_ACTIONS = {
    'M1': lambda m: _stabilize_m1(m),
    'M3': lambda m: _alert_m3(m),
}

def collect_m1():
    load = float(open('/proc/loadavg').read().split()[0])
    mem = open('/proc/meminfo').read()
    ram_free = int([l for l in mem.split('\n') if 'MemAvailable' in l][0].split()[1])//1024
    npm_count = int(subprocess.check_output(['pgrep','-c','npm'], stderr=subprocess.DEVNULL).decode().strip() or '0')
    node_count = int(subprocess.check_output(['pgrep','-c','node'], stderr=subprocess.DEVNULL).decode().strip() or '0')
    try:
        gpu_raw = subprocess.check_output(['nvidia-smi','--query-gpu=utilization.gpu,temperature.gpu','--format=csv,noheader'], timeout=3).decode()
        gpus = [{'util':int(l.split(',')[0].strip().rstrip(' %')),'temp':int(l.split(',')[1].strip().rstrip(' °C'))} for l in gpu_raw.strip().split('\n')]
        max_temp = max(g['temp'] for g in gpus)
        max_util = max(g['util'] for g in gpus)
    except: max_temp=0; max_util=0; gpus=[]
    return {'machine':'M1','ts':datetime.now().isoformat(),'load_1m':load,'ram_free_mb':ram_free,
            'npm_count':npm_count,'node_count':node_count,'gpu_max_temp':max_temp,'gpu_max_util':max_util}

def collect_m3():
    import urllib.request
    try:
        r = urllib.request.urlopen('http://192.168.1.113:8080/health', timeout=3)
        return json.loads(r.read())
    except: return {'machine':'M3','ts':datetime.now().isoformat(),'status':'ssh_only'}

def _stabilize_m1(metrics):
    actions = []
    alerts = MATRIX['log_templates']['M1']['alerts']
    if metrics['load_1m'] > alerts['load_gt']:
        actions.append('HIGH_LOAD')
    if metrics['ram_free_mb'] < alerts['ram_free_lt']:
        subprocess.run(['sh','-c','echo 1 > /proc/sys/vm/drop_caches'], capture_output=True)
        actions.append('DROP_CACHE')
    if metrics['npm_count'] > alerts.get('npm_count_gt', 20):
        # Tuer les npm en surplus (garder 8 max)
        pids = subprocess.check_output(['pgrep','-n','npm']).decode().strip().split('\n')
        for pid in pids[8:]:
            subprocess.run(['kill','-15', pid.strip()], capture_output=True)
        actions.append(f'KILLED_NPM_SURPLUS:{len(pids)-8}')
    return actions

def _alert_m3(metrics):
    return ['M3_OVERLOAD'] if metrics.get('load_1m',0) > 8 else []

def run(machine='M1', interval=30, log_dir='/var/log/jarvis'):
    os.makedirs(log_dir, exist_ok=True)
    log_file = f"{log_dir}/{machine}_profile.jsonl"
    collectors = {'M1': collect_m1, 'M3': collect_m3}
    collect = collectors.get(machine, collect_m1)
    print(f"[MONITOR] Machine={machine} interval={interval}s log={log_file}")
    while True:
        try:
            m = collect()
            alerts = ALERT_ACTIONS.get(machine, lambda x:[])(m)
            m['alerts_triggered'] = alerts
            with open(log_file, 'a') as f:
                f.write(json.dumps(m) + '\n')
            if alerts:
                print(f"[ALERT] {datetime.now().strftime('%H:%M:%S')} {alerts}")
            else:
                print(f"[OK] {datetime.now().strftime('%H:%M:%S')} load={m.get('load_1m','?')} ram={m.get('ram_free_mb','?')}MB npm={m.get('npm_count','?')}")
        except Exception as e:
            print(f"[ERR] {e}")
        time.sleep(interval)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='JARVIS Machine Monitor')
    ap.add_argument('--machine', default='M1')
    ap.add_argument('--interval', type=int, default=30)
    ap.add_argument('--once', action='store_true')
    args = ap.parse_args()
    if args.once:
        c = {'M1':collect_m1,'M3':collect_m3}.get(args.machine, collect_m1)()
        print(json.dumps(c, indent=2))
    else:
        run(args.machine, args.interval)
