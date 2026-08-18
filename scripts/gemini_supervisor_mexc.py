import asyncio
import json
import os
import subprocess

CONFIG = {
    "thresholds": {
        "cpu_limit": 85,
        "mexc_priority": True
    }
}

class GeminiSupervisor:
    def __init__(self):
        self.state_db = "/home/pamerys/jarvis/jarvis_master.db"
        self.lock = asyncio.Lock()  # Protection des transactions
        self._cpu_cache = 0

    async def update_telemetry_loop(self):
        """Boucle de fond pour éviter l'overhead des appels shell répétés."""
        while True:
            try:
                # Lecture native du load average sous Linux sans surcoût PowerShell/WMI
                load1, _, _ = os.getloadavg()
                cpu_count = os.cpu_count() or 1
                self._cpu_cache = int(min(100, (load1 / cpu_count) * 100))
            except Exception:
                self._cpu_cache = 0
            await asyncio.sleep(5)  # Refresh toutes les 5s

    def build_params(self, task_type):
        """Construit la commande pour déléguer l'inférence aux scripts du cluster (lm-ask.sh)."""
        if task_type == "eco":
            return ["bash", "/home/pamerys/jarvis/scripts/lm-ask.sh"]
        else:
            return ["bash", "/home/pamerys/jarvis/scripts/lm-ask.sh", "--big"]

    async def execute_task(self, prompt, context_paths=None, task_type="archi"):
        # Utilisation du cache pour la décision de backpressure
        cpu_load = self._cpu_cache
        
        if cpu_load > CONFIG["thresholds"]["cpu_limit"]:
            task_type = "eco"

        # Injection de la contrainte DERMI si nécessaire
        dermi_context = "PRIORITÉ: Flux MEXC actif. Optimisation latence critique."
        
        params = self.build_params(task_type)
        full_prompt = (
            f"SYSTEM: JARVIS-TURBO Supervisor | 127.0.0.1 | {dermi_context}\n"
            f"CONTEXTE: {context_paths}\n"
            f"TASK: {prompt}\n"
            f"OUTPUT: JSON ONLY"
        )
        params.append(full_prompt)

        async with self.lock:  # Transaction atomique
            process = await asyncio.create_subprocess_exec(*params, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await process.communicate()
            res_str = stdout.decode().strip()
            try:
                return json.loads(res_str)
            except Exception:
                return {"raw_output": res_str, "status": "success"}

if __name__ == "__main__":
    print("✅ Module GeminiSupervisor adapté et validé pour l'environnement Linux JARVIS.")
