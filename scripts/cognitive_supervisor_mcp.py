import asyncio
import json
import os
import psutil
from mcp.server.fastmcp import FastMCP

# Configuration
CONFIG = {
    "thresholds": {
        "cpu_limit": 80,
        "mexc_priority": True
    }
}

mcp = FastMCP("CognitiveSupervisor")

class GeminiSupervisor:
    def __init__(self):
        # Support hybride Windows/Linux pour le chemin de DB
        if os.name == 'nt':
            self.state_db = "F:/BUREAU/jarvis.db"
        else:
            self.state_db = "/home/pamerys/jarvis/data/jarvis.db"
            
        self.lock = asyncio.Lock()
        self._cpu_cache = 0

    async def update_telemetry_loop(self):
        """Boucle de fond pour la télémétrie CPU (hybride Windows/Linux)."""
        while True:
            try:
                if os.name == 'nt':
                    # Windows
                    cmd = "powershell -Command \"(Get-CimInstance Win32_Processor).LoadPercentage\""
                    proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE)
                    stdout, _ = await proc.communicate()
                    self._cpu_cache = int(stdout.decode().strip() or 0)
                else:
                    # Linux
                    self._cpu_cache = int(psutil.cpu_percent(interval=None))
            except Exception as e:
                print(f"Erreur télémétrie: {e}")
            await asyncio.sleep(5)

    async def execute_task(self, prompt: str, context_paths: str = "", task_type: str = "archi") -> dict:
        cpu_load = self._cpu_cache 
        
        # Bascule automatique en mode eco si surcharge CPU
        if cpu_load > CONFIG["thresholds"]["cpu_limit"]:
            task_type = "eco"

        dermi_context = ""
        if CONFIG["thresholds"]["mexc_priority"]:
            dermi_context = "PRIORITÉ: Flux MEXC actif. Optimisation latence critique."
            
        full_prompt = (
            f"SYSTEM: JARVIS-TURBO Supervisor | 127.0.0.1 | CPU:{cpu_load}% | {dermi_context}\n"
            f"CONTEXTE: {context_paths}\n"
            f"TASK: {prompt}\n"
            f"OUTPUT: JSON ONLY"
        )
        
        async with self.lock: # Transaction atomique
            # Simulation d'appel : dans la version de prod, on remplacerait cela 
            # par asyncio.create_subprocess_exec("openclaw", ...) ou un appel API
            if task_type == "eco":
                result = {"status": "success", "mode": "eco", "model": "local-OL1", "details": full_prompt}
            else:
                result = {"status": "success", "mode": "archi", "model": "gemini-pro", "details": full_prompt}
            
            await asyncio.sleep(0.1) # Simule le temps d'exécution
            return result

supervisor = GeminiSupervisor()

@mcp.tool()
async def execute_cognitive_task(prompt: str, context_paths: str = "", task_type: str = "archi") -> str:
    """
    Exécute une tâche via le superviseur cognitif. 
    Effectue une bascule eco/archi selon le CPU et injecte la priorité MEXC.
    """
    res = await supervisor.execute_task(prompt, context_paths, task_type)
    return json.dumps(res)

if __name__ == "__main__":
    import threading
    
    # Lancement de la télémétrie dans un thread séparé avec sa propre boucle asynchrone
    # pour ne pas interférer avec la boucle mcp.run() (FastMCP gère sa propre loop)
    def start_telemetry():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(supervisor.update_telemetry_loop())

    t = threading.Thread(target=start_telemetry, daemon=True)
    t.start()
    
    # Démarrage du serveur MCP stdio
    mcp.run()
