import os
import subprocess
import argparse
import json

def run_remote_command(host, command):
    """
    Executes a command on a remote host via SSH and returns its output.
    """
    full_command = ["ssh", f"turbo@{host}", command]
    try:
        result = subprocess.run(full_command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing command on {host}: {e}")
        print(f"Stderr: {e.stderr.strip()}")
        return None
    except FileNotFoundError:
        print("SSH command not found. Ensure SSH client is installed and in PATH.")
        return None

def get_node_metrics(node_ip):
    """
    Collects GPU/RAM/CPU metrics from a given node.
    This is a placeholder and needs actual implementation for metric collection.
    """
    metrics = {
        "gpu_usage": "N/A",
        "gpu_memory": "N/A",
        "cpu_usage": "N/A",
        "ram_usage": "N/A"
    }
    print(f"Collecting metrics from {node_ip} (placeholder)...")
    
    # Placeholder for actual commands to collect metrics
    # Example for NVIDIA GPU: run_remote_command(node_ip, "nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader,nounits")
    # Example for CPU/RAM: run_remote_command(node_ip, "top -bn1 | grep 'Cpu(s)' | sed 's/.*, *\([0-9.]*\)%* id.*/\1/' | awk '{print 100 - $1}'")
    # Example for RAM: run_remote_command(node_ip, "free -m | grep Mem | awk '{print $3/$2 * 100.0}'")

    if node_ip == "192.168.0.10": # M1
        gpu_info = run_remote_command(node_ip, "nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader,nounits")
        if gpu_info:
            try:
                gpu_util, gpu_mem = gpu_info.split(', ')
                metrics["gpu_usage"] = f"{gpu_util.strip()}%"
                metrics["gpu_memory"] = f"{gpu_mem.strip()}MiB"
            except ValueError:
                pass # Handle parsing error
    
    cpu_usage = run_remote_command(node_ip, "top -bn1 | grep 'Cpu(s)' | sed 's/.*, *\([0-9.]*\)%* id.*/\1/' | awk '{print 100 - $1}'")
    if cpu_usage:
        metrics["cpu_usage"] = f"{float(cpu_usage):.1f}%"

    ram_usage = run_remote_command(node_ip, "free -m | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}'")
    if ram_usage:
        metrics["ram_usage"] = f"{float(ram_usage):.1f}%"

    return metrics

def distribute_task(task_description):
    """
    Distributes a heavy task to the most suitable node based on perceived load.
    This is a simplified logic.
    """
    print(f"Attempting to distribute task: {task_description}")
    
    # Node IPs (M6 câble direct 10.42.0.230 comme zone tampon / délestage)
    nodes = {
        "M6": "10.42.0.230", # Nœud Tampon dédié (Câble direct 10GB/s)
        "M1": "192.168.0.10", # 6 GPUs
        "M3": "127.0.0.1" # Ollama
    }
    
    # Tout délestage / démarrage M1 passe par M6 en premier (tampon d'inférence)
    target_node_name = "M6"
    target_ip = nodes.get(target_node_name)
    
    if target_ip:
        print(f"Task '{task_description}' délestée vers la machine tampon {target_node_name} ({target_ip}).")
        return f"Task '{task_description}' attribuée au tampon {target_node_name} ({target_ip})."
    else:
        return "Nœud tampon M6 non disponible."


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-machine navigator for JARVIS cluster.")
    parser.add_argument("--command", help="Command to execute on a remote machine.")
    parser.add_argument("--host", help="Host IP to execute the command on (e.g., 192.168.0.10).")
    parser.add_argument("--metrics", action="store_true", help="Collect metrics from specified host or all known hosts.")
    parser.add_argument("--distribute", help="Description of a heavy task to distribute.")

    args = parser.parse_args()

    if args.command and args.host:
        output = run_remote_command(args.host, args.command)
        if output:
            print(f"Output from {args.host}:
{output}")
    elif args.metrics:
        nodes = ["192.168.0.10", "127.0.0.1"] # M1 and M3
        all_metrics = {}
        for node in nodes:
            all_metrics[node] = get_node_metrics(node)
        print(json.dumps(all_metrics, indent=2))
    elif args.distribute:
        result = distribute_task(args.distribute)
        print(result)
    else:
        parser.print_help()
