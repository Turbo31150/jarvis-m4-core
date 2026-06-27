import subprocess
import json
import sys
import re

# Define target machines and their SSH commands
MACHINES = {
    "M1": {
        "ssh_command": "ssh turbo@192.168.1.85",
        "metrics": {
            "gpu": "nvidia-smi --query-gpu=index,name,utilization.gpu,memory.total,memory.used,memory.free --format=csv,noheader,nounits",
            "ram": "free -m | awk 'NR==2{printf "%.0f", $3+$4}'", # Free RAM in MB
            "cpu": "nproc", # Number of CPU cores
        }
    },
    "M3": {
        "ssh_command": "ssh turbo@192.168.1.113",
        "metrics": {
            # M3 might have different nvidia-smi output, adjust if necessary.
            # Example: index,name,utilization.gpu,memory.total,memory.free
            "gpu": "nvidia-smi --query-gpu=index,name,utilization.gpu,memory.total,memory.free --format=csv,noheader,nounits", 
            "ram": "free -m | awk 'NR==2{printf "%.0f", $3+$4}'", # Free RAM in MB
            "cpu": "nproc",
        }
    }
}

def run_remote_command(machine_name, command):
    """Executes a command on a remote machine via SSH and returns its output."""
    ssh_cmd = MACHINES[machine_name]["ssh_command"]
    # Escape potential special characters in command if necessary, but for simplicity here we assume simple commands.
    # For complex commands, consider using a more robust method than shell=True or manual escaping.
    full_command = f"{ssh_cmd} "{command}""
    try:
        result = subprocess.run(
            full_command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            executable='/bin/bash'
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command on {machine_name}: {e.cmd}
Stderr: {e.stderr}", file=sys.stderr)
        return None
    except FileNotFoundError:
        print("Error: ssh command not found. Ensure SSH client is installed.", file=sys.stderr)
        return None

def parse_gpu_output(output, machine_name):
    """Parses the output of nvidia-smi for GPU metrics."""
    gpu_data = []
    lines = output.splitlines()
    
    # Heuristic to detect if header is present or not. 
    # If first line contains expected header fields, skip it. Otherwise, parse all lines.
    header_present = False
    if lines and "index,name" in lines[0]: # Common header part
        header_present = True
        lines = lines[1:] # Skip header line
        
    if not lines:
        print(f"Warning: No GPU data found or parsed for {machine_name}.", file=sys.stderr)
        return gpu_data

    for line in lines:
        line = line.strip()
        if not line: continue
        
        # Split by comma, but be careful if GPU names contain commas (unlikely with --format=csv,noheader)
        # A more robust split might be needed if names had commas.
        parts = [p.strip() for p in line.split(',')]
        
        # Expected fields based on nvidia-smi format string:
        # index,name,utilization.gpu,memory.total,memory.used,memory.free
        # M3 might have fewer fields, adjust parsing.
        
        expected_fields_count = 6 # For M1 (index, name, util, total, used, free)
        
        # Adjust expected fields for M3 if 'used' is not provided by its query string
        if machine_name == "M3" and "memory.used" not in MACHINES[machine_name]["metrics"]["gpu"]:
            expected_fields_count = 5 # index, name, util, total, free

        if len(parts) < 2: # Must have at least index and name
            print(f"Warning: Skipping malformed GPU line for {machine_name}: {line}", file=sys.stderr)
            continue

        try:
            gpu_info = {}
            gpu_info["index"] = int(parts[0])
            # GPU name can have spaces, so join all parts after index until the last known fields
            # This assumes name is always before util, total, free/used.
            name_parts = parts[1:- (expected_fields_count - 2)] if expected_fields_count > 2 else parts[1:] # Handle cases with only index/name
            gpu_info["name"] = " ".join(name_parts)

            # Parse specific metrics based on expected count and known indices
            if expected_fields_count > 2:
                gpu_info["utilization_gpu"] = parts[- (expected_fields_count - 2)]
            if expected_fields_count > 3:
                gpu_info["memory_total"] = parts[- (expected_fields_count - 3)]
            if expected_fields_count > 4: # M1 has memory.used
                gpu_info["memory_used"] = parts[- (expected_fields_count - 4)]
            if expected_fields_count > 5: # M1 has memory.free
                gpu_info["memory_free"] = parts[- (expected_fields_count - 5)]
            elif expected_fields_count == 5: # M3 might only have memory.free as the last field
                 gpu_info["memory_free"] = parts[-1] # Assuming last is free if only 5 fields

            gpu_data.append(gpu_info)

        except ValueError:
            print(f"Warning: Could not parse numerical values for GPU line on {machine_name}: {line}", file=sys.stderr)
        except IndexError:
            print(f"Warning: Not enough fields parsed for GPU line on {machine_name}: {line}", file=sys.stderr)
            
    return gpu_data

def collect_metrics():
    """Collects system metrics from all configured machines."""
    all_metrics = {}
    for machine_name, config in MACHINES.items():
        machine_metrics = {}
        print(f"Collecting metrics for {machine_name}...")
        for metric_name, cmd in config["metrics"].items():
            output = run_remote_command(machine_name, cmd)
            if output is not None:
                if metric_name == "gpu":
                    machine_metrics[metric_name] = parse_gpu_output(output, machine_name)
                elif metric_name == "cpu":
                    try:
                        machine_metrics[metric_name] = int(output)
                    except ValueError:
                        print(f"Warning: Could not parse CPU output for {machine_name}: {output}", file=sys.stderr)
                        machine_metrics[metric_name] = "N/A"
                elif metric_name == "ram":
                    try:
                        machine_metrics[metric_name] = int(output) # Output is already in MB as per awk
                    except ValueError:
                        print(f"Warning: Could not parse RAM output for {machine_name}: {output}", file=sys.stderr)
                        machine_metrics[metric_name] = "N/A"
                else:
                    # Fallback for any other metrics not specifically parsed
                    machine_metrics[metric_name] = output 
            else:
                print(f"Failed to collect {metric_name} for {machine_name}", file=sys.stderr)
        all_metrics[machine_name] = machine_metrics
    return all_metrics

def main():
    """Main function to collect and display metrics."""
    print("Starting cluster navigation and metrics collection...")
    
    metrics_data = collect_metrics()
    
    # Print the collected metrics in a structured format (e.g., JSON)
    # This could later be extended to include logic for task distribution.
    print("
--- Cluster Metrics ---")
    print(json.dumps(metrics_data, indent=4))
    print("-----------------------
")
    
    # Placeholder for task distribution logic
    # This would involve analyzing metrics_data to decide where to run tasks.
    print("Task distribution logic can be added here based on collected metrics.")
    # Example: Find the machine with most free GPU memory for heavy tasks.
    # This is a simplified example and would need robust memory parsing.
    best_machine_for_gpu = None
    max_free_gpu_mem_mb = -1
    
    for machine_name, metrics in metrics_data.items():
        if 'gpu' in metrics and isinstance(metrics['gpu'], list):
            for gpu_info in metrics['gpu']:
                mem_str = gpu_info.get("memory_free", "0MiB")
                try:
                    # Attempt to parse memory string like "14336MiB"
                    mem_val_mb = int(mem_str.replace("MiB", "").strip())
                    if mem_val_mb > max_free_gpu_mem_mb:
                        max_free_gpu_mem_mb = mem_val_mb
                        best_machine_for_gpu = {
                            "machine": machine_name,
                            "gpu_index": gpu_info.get("index"),
                            "memory_free_mb": mem_val_mb
                        }
                except ValueError:
                    print(f"Warning: Could not parse GPU free memory string '{mem_str}' for {machine_name} GPU {gpu_info.get('index')}.", file=sys.stderr)
    
    if best_machine_for_gpu:
        print(f"Identified best machine for GPU tasks: {best_machine_for_gpu['machine']} (GPU {best_machine_for_gpu['gpu_index']}) with {best_machine_for_gpu['memory_free_mb']}MiB free GPU memory.")
    else:
        print("Could not determine a machine with significant free GPU memory.")

if __name__ == "__main__":
    main()
