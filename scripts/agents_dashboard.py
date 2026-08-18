#!/usr/bin/env python3
import subprocess
import time
import os
import sys

# Conteneurs critiques dont l'absence ou le crash déclenche une alerte
CRITICAL_CONTAINERS = [
    "jv-infra-redis",
    "jv-infra-omega-bridge",
    "jv-ia-browseros",
    "jarvis-lumen-token",
    "jv-infra-biblio-db",
    "jv-front-n8n"
]

# Couleurs ANSI
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"
BLINK = "\033[5m"

def get_containers():
    try:
        # Récupère tous les conteneurs, y compris arrêtés
        cmd = ["docker", "ps", "-a", "--format", "{{.Names}}\t{{.Status}}"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        containers = []
        for line in res.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) == 2:
                containers.append({"name": parts[0], "status": parts[1]})
        return containers
    except Exception as e:
        print(f"{RED}Erreur lors de la lecture de Docker : {e}{RESET}")
        return []

def categorize(name):
    if name.startswith("jv-infra"):
        return "Infrastructure & Base de données"
    elif name.startswith("jv-studio"):
        return "Studio & Agents IA"
    elif name.startswith("jv-front") or name.startswith("jarvis-lumen"):
        return "Interface & Frontends"
    elif name.startswith("jv-log"):
        return "Logging, Audit & Valise"
    elif name.startswith("jv-finance"):
        return "Finance & Trading"
    else:
        return "Autres conteneurs"

def main():
    try:
        while True:
            # Efface l'écran
            os.system("clear")
            
            print(f"{BOLD}{CYAN}============================================================{RESET}")
            print(f"{BOLD}{CYAN}             JARVIS OS — TABLEAU DE BORD DES AGENTS         {RESET}")
            print(f"{BOLD}{CYAN}============================================================{RESET}")
            print(f"Mise à jour : {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

            containers = get_containers()
            if not containers:
                print(f"{RED}Aucun conteneur trouvé ou Docker indisponible.{RESET}")
                time.sleep(5)
                continue

            # Indexation rapide
            status_map = {c["name"]: c["status"] for c in containers}

            # Vérification des conteneurs critiques
            alerts = []
            for crit in CRITICAL_CONTAINERS:
                if crit not in status_map:
                    alerts.append(f"MANQUANT : {crit}")
                elif "Up" not in status_map[crit]:
                    alerts.append(f"DOWN ({status_map[crit]}) : {crit}")

            if alerts:
                print(f"{BOLD}{RED}{BLINK}⚠️  ALERTE SERVICE CRITIQUE DOWN ⚠️{RESET}")
                for alert in alerts:
                    print(f"  {RED}- {alert}{RESET}")
                print()
            else:
                print(f"{BOLD}{GREEN}✓ Tous les services critiques sont opérationnels{RESET}\n")

            # Regroupement par catégorie
            groups = {}
            for c in containers:
                cat = categorize(c["name"])
                groups.setdefault(cat, []).append(c)

            # Affichage par catégorie
            for cat, items in sorted(groups.items()):
                print(f"{BOLD}{BLUE}📂 {cat} ({len(items)}) :{RESET}")
                for item in sorted(items, key=lambda x: x["name"]):
                    name = item["name"]
                    status = item["status"]
                    
                    # Détermine la couleur du statut
                    if "Up" in status:
                        if "healthy" in status:
                            status_str = f"{GREEN}Up (healthy){RESET}"
                        else:
                            status_str = f"{GREEN}Up{RESET}"
                    elif "Exited (0)" in status:
                        status_str = f"{YELLOW}Arrêté (Exit 0){RESET}"
                    else:
                        status_str = f"{RED}{status}{RESET}"
                        
                    print(f"  • {name:<35} → {status_str}")
                print()

            time.sleep(5)
    except KeyboardInterrupt:
        print("\nArrêt du tableau de bord.")
        sys.exit(0)

if __name__ == "__main__":
    main()
