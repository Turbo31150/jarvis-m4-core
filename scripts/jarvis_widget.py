#!/usr/bin/env python3
"""
JARVIS BOARD WIDGET — Dashboard de bureau temps réel
Affiche : Cluster LLM (M1/M2/M4/OL1), tâches, moisson, Board OS, Skills Library
Fonctionne en terminal ou comme widget flottant via python3-tk
"""

import tkinter as tk
from tkinter import font as tkfont
import threading, time, json, urllib.request, ssl, sqlite3, subprocess, os
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────
NODES = {
    "OL1 Local":    {"base": "http://127.0.0.1:11434",    "type": "ollama",    "label": "🟢 LOCAL Ollama"},
    "LM Local":     {"base": "http://127.0.0.1:1234",     "type": "lmstudio", "label": "🟢 LOCAL LMStudio"},
    "M6 ⚡ TAMPON": {"base": "http://10.42.0.230:11434",  "type": "ollama",    "label": "🔗 M6 Câble Direct"},
    "M1 LMStudio":  {"base": "http://192.168.1.10:1234",  "type": "lmstudio", "label": "🖥  M1 Heavy GPU"},
    "M4 OpenAI":    {"base": "http://192.168.0.10:11235", "type": "lmstudio", "label": "🖥  M4 Inference"},
}
DB_SKILLS = "/home/pamerys/Workspaces/jarvis-linux/skills-library/skills_library.db"
DB_BOARD  = "/home/pamerys/jarvis/board/board.db"
HARVEST_LOG = "/home/pamerys/jarvis/logs/"
REFRESH_SEC = 15

# ── PALETTE ───────────────────────────────────────────────────────────
BG      = "#0d1117"
BG2     = "#161b22"
BG3     = "#21262d"
ACCENT  = "#58a6ff"
GREEN   = "#3fb950"
YELLOW  = "#d29922"
RED     = "#f85149"
PURPLE  = "#bc8cff"
CYAN    = "#79c0ff"
FG      = "#e6edf3"
FG2     = "#8b949e"
ORANGE  = "#ff7b22"

CTX = ssl.create_default_context()

def probe_node(name, cfg):
    base = cfg["base"]
    try:
        if cfg["type"] == "lmstudio":
            url = f"{base}/v1/models"
            req = urllib.request.Request(url, headers={"Accept":"application/json"})
            with urllib.request.urlopen(req, timeout=3, context=CTX) as r:
                d = json.loads(r.read())
            models = [m["id"].split("/")[-1][:22] for m in d.get("data",[])]
            return {"status":"UP","models":models[:6],"count":len(models)}
        else:
            url = f"{base}/api/tags"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=3) as r:
                d = json.loads(r.read())
            models = [m["name"][:22] for m in d.get("models",[])]
            return {"status":"UP","models":models[:6],"count":len(models)}
    except Exception as e:
        return {"status":"DOWN","models":[],"count":0,"error":str(e)[:40]}

def get_db_stats():
    stats = {}
    try:
        s = sqlite3.connect(DB_SKILLS)
        stats["skills"] = s.execute("SELECT COUNT(*) FROM skills").fetchone()[0]
        stats["cats"] = s.execute(
            "SELECT category, COUNT(*) c FROM skills GROUP BY category ORDER BY c DESC LIMIT 4"
        ).fetchall()
        s.close()
    except: stats["skills"]=0; stats["cats"]=[]
    try:
        b = sqlite3.connect(DB_BOARD)
        stats["board_src"] = b.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        stats["board_chk"] = b.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        b.close()
    except: stats["board_src"]=0; stats["board_chk"]=0
    return stats

def get_harvest_status():
    try:
        logs = sorted([f for f in os.listdir(HARVEST_LOG) if "harvest" in f], reverse=True)
        if not logs: return "Aucun log"
        last = open(os.path.join(HARVEST_LOG, logs[0])).readlines()
        for line in reversed(last[-30:]):
            line = line.strip()
            if line and not line.startswith("#"): return line[:80]
        return "En cours..."
    except: return "Inconnu"

def get_processes():
    try:
        out = subprocess.check_output(
            ["ps", "aux"], text=True, timeout=3
        ).splitlines()
        procs = []
        kw = ["harvest", "lm-router", "board", "jarvis", "ollama", "lmstudio"]
        for line in out:
            if any(k in line.lower() for k in kw) and "grep" not in line and "widget" not in line:
                parts = line.split()
                cpu = parts[2]; mem = parts[3]
                cmd = " ".join(parts[10:])[:50]
                procs.append(f"  CPU:{cpu}% MEM:{mem}% — {cmd}")
        return procs[:6]
    except: return ["ps indisponible"]


class JarvisWidget(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("JARVIS BOARD OS — Cluster Monitor")
        self.configure(bg=BG)
        self.attributes("-topmost", True)
        self.geometry("780x900+50+50")
        self.resizable(True, True)

        # Fonts
        self.fn_title  = tkfont.Font(family="JetBrains Mono", size=13, weight="bold")
        self.fn_head   = tkfont.Font(family="JetBrains Mono", size=10, weight="bold")
        self.fn_body   = tkfont.Font(family="JetBrains Mono", size=9)
        self.fn_small  = tkfont.Font(family="JetBrains Mono", size=8)
        self.fn_status = tkfont.Font(family="JetBrains Mono", size=11, weight="bold")

        # Fallback fonts
        for f in [self.fn_title, self.fn_head, self.fn_body, self.fn_small, self.fn_status]:
            try: f.actual()
            except: f.configure(family="Monospace")

        self._build_ui()
        self._state = {}
        self._start_refresh()

    def _build_ui(self):
        # ── HEADER
        hdr = tk.Frame(self, bg=BG, pady=6)
        hdr.pack(fill="x", padx=12)
        tk.Label(hdr, text="⬡  JARVIS BOARD OS", font=self.fn_title,
                 bg=BG, fg=ACCENT).pack(side="left")
        self.lbl_time = tk.Label(hdr, text="", font=self.fn_small, bg=BG, fg=FG2)
        self.lbl_time.pack(side="right")

        sep = tk.Frame(self, bg=ACCENT, height=1)
        sep.pack(fill="x", padx=12)

        # ── CLUSTER NODES
        sec = self._section("🖥  CLUSTER LLM")
        self.nodes_frame = tk.Frame(sec, bg=BG2)
        self.nodes_frame.pack(fill="x", padx=4, pady=4)

        # ── BOARD OS + SKILLS
        sec2 = self._section("📚  BIBLIOTHÈQUE VIVANTE")
        self.board_frame = tk.Frame(sec2, bg=BG2)
        self.board_frame.pack(fill="x", padx=4, pady=4)

        # ── MOISSON
        sec3 = self._section("🌊  MOISSON EN COURS")
        self.harvest_lbl = tk.Label(sec3, text="...", font=self.fn_small,
                                    bg=BG2, fg=YELLOW, wraplength=720, justify="left")
        self.harvest_lbl.pack(anchor="w", padx=8, pady=4)

        # ── PROCESSUS
        sec4 = self._section("⚙  PROCESSUS JARVIS ACTIFS")
        self.proc_frame = tk.Frame(sec4, bg=BG2)
        self.proc_frame.pack(fill="x", padx=4, pady=4)

        # ── FOOTER
        foot = tk.Frame(self, bg=BG, pady=4)
        foot.pack(fill="x", padx=12, side="bottom")
        tk.Label(foot, text="↻ Auto-refresh 15s  |  JARVIS OMEGA 2026",
                 font=self.fn_small, bg=BG, fg=FG2).pack(side="left")
        tk.Button(foot, text="⟳ REFRESH", font=self.fn_small,
                  bg=BG3, fg=ACCENT, bd=0, padx=8, pady=2,
                  command=self._refresh_now).pack(side="right")

    def _section(self, title):
        outer = tk.Frame(self, bg=BG, padx=8, pady=4)
        outer.pack(fill="x", padx=8, pady=2)
        tk.Label(outer, text=title, font=self.fn_head,
                 bg=BG, fg=CYAN).pack(anchor="w")
        inner = tk.Frame(outer, bg=BG2, bd=0, highlightthickness=1,
                         highlightbackground=BG3)
        inner.pack(fill="x")
        return inner

    def _clear(self, frame):
        for w in frame.winfo_children(): w.destroy()

    def _update_nodes(self, results):
        self._clear(self.nodes_frame)
        for name, info in results.items():
            row = tk.Frame(self.nodes_frame, bg=BG2)
            row.pack(fill="x", padx=6, pady=2)
            st = info["status"]
            dot_col = GREEN if st == "UP" else RED
            tk.Label(row, text="●", font=self.fn_body,
                     bg=BG2, fg=dot_col).pack(side="left")
            tk.Label(row, text=f" {name:<14}", font=self.fn_body,
                     bg=BG2, fg=FG).pack(side="left")
            if st == "UP":
                tk.Label(row, text=f"UP  {info['count']} modèles",
                         font=self.fn_body, bg=BG2, fg=GREEN).pack(side="left")
                mlist = "  │  ".join(info["models"][:4])
                tk.Label(row, text=f"   {mlist}", font=self.fn_small,
                         bg=BG2, fg=FG2).pack(side="left")
            else:
                tk.Label(row, text="DOWN", font=self.fn_body,
                         bg=BG2, fg=RED).pack(side="left")
                tk.Label(row, text=f"  {info.get('error','')}",
                         font=self.fn_small, bg=BG2, fg=FG2).pack(side="left")

    def _update_board(self, stats):
        self._clear(self.board_frame)
        row1 = tk.Frame(self.board_frame, bg=BG2)
        row1.pack(fill="x", padx=6, pady=3)
        tk.Label(row1, text=f"🧠 Board OS   {stats['board_src']:,} sources  |  {stats['board_chk']:,} chunks FTS5",
                 font=self.fn_body, bg=BG2, fg=PURPLE).pack(side="left")
        row2 = tk.Frame(self.board_frame, bg=BG2)
        row2.pack(fill="x", padx=6, pady=2)
        tk.Label(row2, text=f"📦 Skills Lib  {stats['skills']:,} compétences",
                 font=self.fn_body, bg=BG2, fg=ACCENT).pack(side="left")
        row3 = tk.Frame(self.board_frame, bg=BG2)
        row3.pack(fill="x", padx=6, pady=2)
        cats_str = "  ".join([f"{cat}:{cnt}" for cat,cnt in stats.get("cats",[])])
        tk.Label(row3, text=f"   {cats_str}", font=self.fn_small,
                 bg=BG2, fg=FG2).pack(side="left")

    def _update_procs(self, procs):
        self._clear(self.proc_frame)
        if not procs:
            tk.Label(self.proc_frame, text="  Aucun processus JARVIS détecté",
                     font=self.fn_small, bg=BG2, fg=FG2).pack(anchor="w", padx=6)
            return
        for p in procs:
            tk.Label(self.proc_frame, text=p, font=self.fn_small,
                     bg=BG2, fg=ORANGE, justify="left").pack(anchor="w", padx=6)

    def _do_refresh(self):
        # Nodes
        node_results = {}
        threads = []
        def probe(n, c):
            node_results[n] = probe_node(n, c)
        for n, c in NODES.items():
            t = threading.Thread(target=probe, args=(n, c), daemon=True)
            threads.append(t); t.start()
        for t in threads: t.join(timeout=5)

        stats = get_db_stats()
        harvest = get_harvest_status()
        procs = get_processes()

        def upd():
            self._update_nodes(node_results)
            self._update_board(stats)
            self.harvest_lbl.config(text=harvest[:120])
            self._update_procs(procs)
            self.lbl_time.config(text=datetime.now().strftime("🕐 %H:%M:%S"))

        self.after(0, upd)

    def _refresh_now(self):
        threading.Thread(target=self._do_refresh, daemon=True).start()

    def _start_refresh(self):
        self._refresh_now()
        def loop():
            while True:
                time.sleep(REFRESH_SEC)
                self._refresh_now()
        threading.Thread(target=loop, daemon=True).start()


if __name__ == "__main__":
    app = JarvisWidget()
    app.mainloop()
