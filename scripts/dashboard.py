#!/usr/bin/env python3
"""
JARVIS Dashboard — Affichage terminal rapide à chaque login
Affiche: compte à rebours MAMS, météo Toulouse, cluster M1/M2, GPU thermal, top 3 todos, citation pédagogique
Timeout total: 3s (threading parallèle)
"""

import subprocess
import threading
import json
import sqlite3
from datetime import datetime
from pathlib import Path
import time
import random

# ANSI colors
CYAN = "\033[96m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

# Citations pédagogiques requises
CITATIONS = [
    "\"La connaissance s'acquiert par l'expérience, tout le reste n'est que de l'information.\" — Einstein",
    '"Éduquer, c\'est allumer un feu, pas remplir un vase." — Plutarque',
    "\"Un enfant qui ne joue pas n'est pas un enfant, mais l'homme qui ne joue pas a perdu à jamais l'enfant qui était en lui.\" — Neruda",
    "\"L'éducation est l'arme la plus puissante que vous puissiez utiliser pour changer le monde.\" — Mandela",
    '"La première fonction de l\'éducation est de te donner les yeux pour voir." — Krishnamurti',
    '"Tout le monde est un génie. Mais si vous jugez un poisson sur ses capacités à grimper à un arbre..." — Einstein',
]

# Date oral MAMS
ORAL_MAMS_DATE = datetime(2026, 6, 2)


class Dashboard:
    def __init__(self):
        self.data = {}
        self.lock = threading.Lock()
        self.start_time = time.time()

    def days_until_mams(self):
        """Calcul J-X avant ORAL MAMS"""
        today = datetime.now().date()
        delta = (ORAL_MAMS_DATE.date() - today).days
        return delta

    def fetch_weather(self):
        """Météo Toulouse via wttr.in (timeout 3s)"""
        try:
            result = subprocess.run(
                ["curl", "-s", "--max-time", "3", "wttr.in/Toulouse?format=%C+%t"],
                capture_output=True,
                text=True,
                timeout=3.5,
            )
            if result.returncode == 0 and result.stdout.strip():
                self.data["weather"] = result.stdout.strip()
            else:
                self.data["weather"] = "indisponible"
        except Exception:
            self.data["weather"] = "indisponible"

    def fetch_cluster(self):
        """Ping cluster M1 et M2 avec latence (timeout 1s chacun)"""
        cluster_status = {}

        for name, ip in [("M1", "192.168.1.85"), ("M2", "192.168.1.26")]:
            try:
                start = time.time()
                result = subprocess.run(
                    ["curl", "-s", "--max-time", "1", f"http://{ip}:1234/v1/models"],
                    capture_output=True,
                    timeout=1.5,
                )
                elapsed_ms = int((time.time() - start) * 1000)
                if result.returncode == 0:
                    cluster_status[name] = f"✅ ({elapsed_ms}ms)"
                else:
                    cluster_status[name] = "❌"
            except Exception:
                cluster_status[name] = "❌"

        self.data["cluster"] = cluster_status

    def fetch_thermal(self):
        """GPU temp depuis thermal-status.json"""
        json_path = Path.home() / "jarvis" / "logs" / "thermal-status.json"

        try:
            if json_path.exists():
                with open(json_path) as f:
                    thermal = json.load(f)
                    temp = thermal.get("temp", "N/A")
                    state = thermal.get("state", "unknown")
                    self.data["thermal"] = {"temp": temp, "state": state}
            else:
                self.data["thermal"] = {"temp": "N/A", "state": "unknown"}
        except Exception:
            self.data["thermal"] = {"temp": "N/A", "state": "unknown"}

    def fetch_todos(self):
        """Top 3 todos depuis todo.db"""
        db_path = Path.home() / "jarvis" / "todo.db"

        try:
            if not db_path.exists():
                self.data["todos"] = []
                return

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT titre, deadline FROM todo
                WHERE statut='todo'
                ORDER BY CASE priorite
                    WHEN 'urgent' THEN 1
                    WHEN 'high' THEN 2
                    ELSE 3
                END, deadline
                LIMIT 3
                """
            )
            todos = cursor.fetchall()
            self.data["todos"] = todos if todos else []
            conn.close()
        except Exception:
            self.data["todos"] = []

    def run_async(self):
        """Exécute toutes les requêtes en parallèle (timeout global 3s)"""
        threads = [
            threading.Thread(target=self.fetch_weather, daemon=True),
            threading.Thread(target=self.fetch_cluster, daemon=True),
            threading.Thread(target=self.fetch_thermal, daemon=True),
            threading.Thread(target=self.fetch_todos, daemon=True),
        ]

        for t in threads:
            t.start()

        # Timeout global
        timeout = 3.0
        for t in threads:
            remaining = timeout - (time.time() - self.start_time)
            if remaining > 0:
                t.join(timeout=remaining)

    def render(self):
        """Affiche le dashboard en format boxé"""
        now = datetime.now()
        date_str = now.strftime("%A %d %B %Y").capitalize()
        time_str = now.strftime("%H:%M")
        days_mams = self.days_until_mams()
        mams_label = (
            f"J-{days_mams} avant ORAL MAMS 🎯"
            if days_mams > 0
            else "🎯 ORAL MAMS aujourd'hui!"
        )

        # Header boxé
        header_line = f"║  JARVIS PAMERYS M4 — {date_str}"
        padding = 46 - len(header_line)
        print(f"╔{'═' * 44}╗")
        print(f"║  JARVIS PAMERYS M4 — {date_str}{' ' * padding}║")
        print(f"║  {time_str} | 📅 {mams_label}{' ' * (30 - len(mams_label))}║")
        print(f"╚{'═' * 44}╝")

        # Météo + GPU
        weather = self.data.get("weather", "indisponible")
        thermal = self.data.get("thermal", {})
        temp = thermal.get("temp", "N/A")
        state = thermal.get("state", "unknown")
        state_icon = "🔴" if state == "HOT" else "🟡" if state == "warm" else "🟢"
        print(f"  🌡️  GPU: {temp}°C {state_icon} {state} | 🌤️  Toulouse: {weather}")

        # Cluster
        cluster = self.data.get("cluster", {})
        m1_status = cluster.get("M1", "❌")
        m2_status = cluster.get("M2", "❌")
        print(f"  💻 Cluster: M1 {m1_status} | M2 {m2_status}")

        # Citation
        citation = random.choice(CITATIONS)
        print(f"  💡 Citation: {citation}")

        # Top 3 urgences
        todos = self.data.get("todos", [])
        if todos:
            print("  \n  📋 Top 3 urgences:")
            for titre, deadline in todos:
                print(f"    🔴 [{deadline}] {titre}")
        else:
            print("  \n  📋 Aucune urgence en cours")

        print()  # Blank line at end


if __name__ == "__main__":
    dashboard = Dashboard()
    dashboard.run_async()
    dashboard.render()
