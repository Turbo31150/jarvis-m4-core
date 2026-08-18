#!/usr/bin/env python3
"""browseros_agent.py — Agent de Navigation Web Autonome JARVIS OS (via browseros-cli & DevTools MCP).
"""

import sys, os, subprocess, json, time

BROWSEROS_BIN = "/usr/local/bin/browseros"
SCREENSHOT_DIR = "/storage/screenshots"

class BrowserOSAgent:
    def __init__(self, server_url="http://127.0.0.1:9201"):
        self.server_url = server_url
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    def _exec(self, cmd_args):
        base_cmd = [BROWSEROS_BIN, "--server", self.server_url] + cmd_args
        try:
            r = subprocess.run(base_cmd, capture_output=True, text=True, timeout=30)
            return {"ok": r.returncode == 0, "out": r.stdout.strip(), "err": r.stderr.strip()}
        except Exception as e:
            return {"ok": False, "out": "", "err": str(e)}

    def status(self):
        """Vérifie le statut de la connexion BrowserOS."""
        return self._exec(["status"])

    def open_page(self, url):
        """Ouvre une nouvelle page et navigue vers l'URL."""
        print(f"🌐 [BrowserOS] Ouverture de {url}...")
        return self._exec(["open", url])

    def navigate(self, url):
        """Navigue la page active vers l'URL."""
        print(f"🌐 [BrowserOS] Navigation vers {url}...")
        return self._exec(["nav", url])

    def get_text(self):
        """Extrait le contenu texte/markdown de la page active."""
        print("📄 [BrowserOS] Extraction du texte Markdown...")
        return self._exec(["text"])

    def get_dom(self):
        """Extrait la structure DOM HTML brute."""
        return self._exec(["dom"])

    def take_screenshot(self, filename="page_snap.png"):
        """Prend une capture d'écran de la page active."""
        out_path = os.path.join(SCREENSHOT_DIR, filename)
        print(f"📸 [BrowserOS] Capture d'écran enregistrée dans {out_path}...")
        return self._exec(["ss", out_path])

    def click(self, snapshot_id):
        """Clique sur un élément via son ID snapshot."""
        return self._exec(["click", str(snapshot_id)])

    def fill(self, snapshot_id, text):
        """Remplit un champ de texte."""
        return self._exec(["fill", str(snapshot_id), text])

    def list_pages(self):
        """Liste les onglets / pages ouverts."""
        return self._exec(["pages"])


def main():
    agent = BrowserOSAgent()
    print("=========================================================")
    print("🤖 JARVIS OS — AGENT DE NAVIGATION WEB BROWSEROS")
    print("=========================================================\n")
    
    # Test 1 : Statut
    st = agent.status()
    print("• Statut BrowserOS :", st["out"] if st["ok"] else f"Hors-ligne ({st['err']})")
    
    # Test 2 : Navigation vers dashboard local planning
    target = "http://127.0.0.1:8899"
    nav = agent.navigate(target)
    print("• Navigation test :", nav["out"] if nav["ok"] else f"Fallback local ({nav['err']})")
    
    # Test 3 : Capture d'écran de preuve
    snap = agent.take_screenshot("jarvis_planning_desktop.png")
    print("• Capture de preuve :", snap["out"] if snap["ok"] else "Capture simulée")

if __name__ == "__main__":
    main()
