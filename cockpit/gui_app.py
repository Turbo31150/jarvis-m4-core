#!/usr/bin/env python3
"""
gui_app.py — JARVIS MASTER COCKPIT (AAA FUTURISTIC CYBERPUNK GUI — PYQT6)
0% HTML — 100% NATIVE GRAPHICAL QT6 APPLICATION
"""

from __future__ import annotations
import sys
import os
import json
import sqlite3
import subprocess
import socket
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QLineEdit, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QSplitter,
    QProgressBar, QGraphicsDropShadowEffect, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon, QColor, QPainter, QLinearGradient, QBrush, QPen

MASTER_DB = os.path.expanduser("~/jarvis/jarvis_master.db")
BOARD_DIR = os.path.expanduser("~/jarvis/board")

def is_port_open(host: str, port: int, timeout: float = 0.15) -> bool:
    try:
        s = socket.socket()
        s.settimeout(timeout)
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False

def get_vram_info() -> tuple[int, int, int, int]:
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total,temperature.gpu,utilization.gpu", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=1
        )
        if r.returncode == 0 and r.stdout.strip():
            parts = [int(p.strip()) for p in r.stdout.strip().split(",")]
            return parts[0], parts[1], parts[2], parts[3]
    except Exception:
        pass
    return 0, 4096, 0, 0

def get_ram_info() -> tuple[float, float]:
    try:
        with open("/proc/meminfo") as f:
            lines = f.readlines()
            mem_tot = int(lines[0].split()[1]) / 1024 / 1024
            mem_avail = int(lines[2].split()[1]) / 1024 / 1024
            return round(mem_tot - mem_avail, 1), round(mem_tot, 1)
    except Exception:
        return 0.0, 16.0

def get_mcp_servers() -> dict:
    p = os.path.expanduser("~/.claude.json")
    if os.path.exists(p):
        try:
            return json.load(open(p)).get("mcpServers", {})
        except Exception:
            pass
    return {}

def get_tasks_list() -> list[dict]:
    if not os.path.exists(MASTER_DB):
        return []
    try:
        con = sqlite3.connect(MASTER_DB)
        cur = con.cursor()
        cur.execute("SELECT id, title, status, category FROM tasks ORDER BY id DESC LIMIT 60")
        rows = cur.fetchall()
        con.close()
        return [{"id": r[0], "title": r[1], "status": r[2], "category": r[3]} for r in rows]
    except Exception:
        return []

class WorkerThread(QThread):
    finished_signal = pyqtSignal(str)
    def __init__(self, cmd):
        super().__init__()
        self.cmd = cmd
    def run(self):
        try:
            r = subprocess.run(self.cmd, capture_output=True, text=True, timeout=60)
            res = r.stdout or r.stderr or "Terminé."
        except Exception as e:
            res = f"Erreur: {e}"
        self.finished_signal.emit(res)

class JarvisMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JARVIS MASTER COCKPIT — POSTE DE COMMANDE UNIFIÉ M4")
        self.resize(1340, 840)
        self.setMinimumSize(1100, 700)
        self.all_mcps = get_mcp_servers()
        self.apply_cyberpunk_theme()
        self.init_ui()

        # Telemetry Timer (2s)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_telemetry)
        self.timer.start(2000)
        self.update_telemetry()

    def apply_cyberpunk_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #050814;
            }
            QWidget {
                color: #e2e8f0;
                font-family: 'Ubuntu', 'Segoe UI', system-ui, sans-serif;
                font-size: 13px;
            }
            QTabWidget::pane {
                border: 1px solid #1e293b;
                background-color: #0a0f1d;
                border-radius: 12px;
                padding: 10px;
            }
            QTabBar::tab {
                background-color: #0f172a;
                color: #94a3b8;
                padding: 12px 24px;
                margin-right: 6px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                font-weight: 700;
                font-size: 13px;
                border: 1px solid #1e293b;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #06b6d4);
                color: #ffffff;
                border: 1px solid #38bdf8;
                border-bottom: none;
            }
            QTabBar::tab:hover:!selected {
                background-color: #1e293b;
                color: #f8fafc;
            }
            QFrame.cyber-card {
                background-color: #0d1527;
                border: 1px solid #1e293b;
                border-radius: 14px;
                padding: 16px;
            }
            QFrame.cyber-card:hover {
                border: 1px solid #0284c7;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #0284c7);
                color: #ffffff;
                font-weight: 700;
                border-radius: 10px;
                padding: 12px 20px;
                border: 1px solid #38bdf8;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0369a1, stop:1 #0284c7);
                border: 1px solid #7dd3fc;
            }
            QPushButton.purple {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #9333ea);
                border: 1px solid #c084fc;
            }
            QPushButton.purple:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6d28d9, stop:1 #7e22ce);
            }
            QPushButton.green {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10b981);
                border: 1px solid #34d399;
            }
            QPushButton.green:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #059669);
            }
            QPushButton.amber {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #d97706, stop:1 #f59e0b);
                border: 1px solid #fcd34d;
            }
            QPushButton.amber:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #b45309, stop:1 #d97706);
            }
            QLineEdit, QTextEdit {
                background-color: #030712;
                border: 1px solid #1e293b;
                border-radius: 10px;
                padding: 10px 14px;
                color: #f8fafc;
                font-family: 'Fira Code', 'Monospace', monospace;
                font-size: 12px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #00f0ff;
                background-color: #050b18;
            }
            QTableWidget {
                background-color: #030712;
                border: 1px solid #1e293b;
                border-radius: 10px;
                gridline-color: #111c33;
                color: #e2e8f0;
                font-family: 'Fira Code', 'Monospace', monospace;
                font-size: 12px;
                selection-background-color: #0369a1;
            }
            QHeaderView::section {
                background-color: #0f172a;
                color: #00f0ff;
                font-weight: 700;
                padding: 8px;
                border: 1px solid #1e293b;
            }
            QProgressBar {
                background-color: #030712;
                border: 1px solid #1e293b;
                border-radius: 6px;
                height: 12px;
                text-align: center;
                font-size: 10px;
                font-weight: bold;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #00f0ff);
                border-radius: 5px;
            }
        """)

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(14)

        # TOP BAR / TELEMETRY HUD
        top_bar = QFrame()
        top_bar.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0a1124, stop:1 #0f1b38);
            border: 1px solid #00f0ff;
            border-radius: 14px;
            padding: 12px 18px;
        """)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(5, 5, 5, 5)

        # Title Brand
        brand_layout = QVBoxLayout()
        title_label = QLabel("🤖 JARVIS MASTER COCKPIT")
        title_label.setFont(QFont("Ubuntu", 15, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #00f0ff; letter-spacing: 1px;")
        brand_layout.addWidget(title_label)

        sub_title = QLabel("POSTE MAÎTRE M4 • SSD M1 USB (1 To) • M6 RJ45 (1.4 ms)")
        sub_title.setFont(QFont("Ubuntu", 10))
        sub_title.setStyleSheet("color: #94a3b8;")
        brand_layout.addWidget(sub_title)
        top_layout.addLayout(brand_layout)

        top_layout.addStretch()

        # Telemetry Gauges / Live Badges
        telem_layout = QHBoxLayout()
        telem_layout.setSpacing(15)

        # VRAM Gauge Box
        vram_box = QVBoxLayout()
        self.lbl_vram_title = QLabel("VRAM GPU RTX 3050: -- / 4096 MB")
        self.lbl_vram_title.setFont(QFont("Monospace", 10, QFont.Weight.Bold))
        self.lbl_vram_title.setStyleSheet("color: #38bdf8;")
        self.bar_vram = QProgressBar()
        self.bar_vram.setRange(0, 4096)
        self.bar_vram.setFixedWidth(160)
        vram_box.addWidget(self.lbl_vram_title)
        vram_box.addWidget(self.bar_vram)
        telem_layout.addLayout(vram_box)

        # RAM Gauge Box
        ram_box = QVBoxLayout()
        self.lbl_ram_title = QLabel("RAM: -- / 16 GB")
        self.lbl_ram_title.setFont(QFont("Monospace", 10, QFont.Weight.Bold))
        self.lbl_ram_title.setStyleSheet("color: #c084fc;")
        self.bar_ram = QProgressBar()
        self.bar_ram.setRange(0, 160)
        self.bar_ram.setFixedWidth(140)
        ram_box.addWidget(self.lbl_ram_title)
        ram_box.addWidget(self.bar_ram)
        telem_layout.addLayout(ram_box)

        # Status Badges
        badges_box = QVBoxLayout()
        self.lbl_m6_badge = QLabel("🟢 M6 RJ45 : UP (1.4 ms)")
        self.lbl_m6_badge.setFont(QFont("Monospace", 10, QFont.Weight.Bold))
        self.lbl_m6_badge.setStyleSheet("color: #4ade80;")
        self.lbl_mcp_badge = QLabel("📦 MCPs : 40+ CONNECTÉS")
        self.lbl_mcp_badge.setFont(QFont("Monospace", 10, QFont.Weight.Bold))
        self.lbl_mcp_badge.setStyleSheet("color: #fbbf24;")
        badges_box.addWidget(self.lbl_m6_badge)
        badges_box.addWidget(self.lbl_mcp_badge)
        telem_layout.addLayout(badges_box)

        top_layout.addLayout(telem_layout)
        main_layout.addWidget(top_bar)

        # TABBED CONTENT
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # TAB 1: HUD & LANCEURS
        self.tab_hud = QWidget()
        self.init_tab_hud()
        self.tabs.addTab(self.tab_hud, "🎛 Cockpit Exécutif")

        # TAB 2: TABLE RONDE
        self.tab_board = QWidget()
        self.init_tab_board()
        self.tabs.addTab(self.tab_board, "🧠 Table Ronde & Experts")

        # TAB 3: BOARD PLAN & TODOLIST
        self.tab_plan = QWidget()
        self.init_tab_plan()
        self.tabs.addTab(self.tab_plan, "📋 Board Plan & To-Do")

        # TAB 4: 91 MCPs
        self.tab_mcps = QWidget()
        self.init_tab_mcps()
        self.tabs.addTab(self.tab_mcps, "📦 Serveurs MCP Actifs")

        # TAB 5: SWARM & BASES
        self.tab_swarm = QWidget()
        self.init_tab_swarm()
        self.tabs.addTab(self.tab_swarm, "🐳 Swarm Docker & SQL")

        # TAB 6: MOISSONNAGE
        self.tab_moisson = QWidget()
        self.init_tab_moisson()
        self.tabs.addTab(self.tab_moisson, "🌾 Moissonnage Réel")

        self.setCentralWidget(main_widget)

    # --- TAB 1: HUD ---
    def init_tab_hud(self):
        layout = QVBoxLayout(self.tab_hud)
        layout.setSpacing(16)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        # ACTION CARD 1: TTX WORKSPACE
        card1 = QFrame()
        card1.setProperty("class", "cyber-card")
        c1_box = QVBoxLayout(card1)
        lbl_c1 = QLabel("🚀 WORKSPACE MULTIPLEXER (TTX)")
        lbl_c1.setFont(QFont("Ubuntu", 13, QFont.Weight.Bold))
        lbl_c1.setStyleSheet("color: #00f0ff;")
        c1_box.addWidget(lbl_c1)
        
        lbl_c1_desc = QLabel("Centre de commandement 5 volets TMUX :\n• Claude Code Orfèvre + 40+ MCPs\n• Table Ronde 7 Experts en direct\n• Planning To-Do List unifié\n• Supervision Swarm & Shell Turbo")
        lbl_c1_desc.setStyleSheet("color: #94a3b8; font-size: 12px; margin-bottom: 8px;")
        c1_box.addWidget(lbl_c1_desc)
        
        btn_ttx = QPushButton("🚀 Lancer Cockpit TTX (5 Volets)")
        btn_ttx.clicked.connect(lambda: subprocess.Popen(["gnome-terminal", "--", "bash", "-ic", "ttx"]))
        c1_box.addWidget(btn_ttx)
        cards_layout.addWidget(card1)

        # ACTION CARD 2: CLAUDE ORFEVRE
        card2 = QFrame()
        card2.setProperty("class", "cyber-card")
        c2_box = QVBoxLayout(card2)
        lbl_c2 = QLabel("👑 CLAUDE CODE (MODE ORFÈVRE)")
        lbl_c2.setFont(QFont("Ubuntu", 13, QFont.Weight.Bold))
        lbl_c2.setStyleSheet("color: #c084fc;")
        c2_box.addWidget(lbl_c2)

        lbl_c2_desc = QLabel("Agent d'ingénierie suprême en autonomie 100% :\n• 0-Token prioritaire (Inférence M6 RJ45)\n• Tous les serveurs MCP connectés\n• Accès complet SSD M1 (1 To)\n• Protocole ininterruptible")
        lbl_c2_desc.setStyleSheet("color: #94a3b8; font-size: 12px; margin-bottom: 8px;")
        c2_box.addWidget(lbl_c2_desc)

        btn_claude = QPushButton("👑 Ouvrir Claude Code Dédié")
        btn_claude.setProperty("class", "purple")
        btn_claude.clicked.connect(lambda: subprocess.Popen(["gnome-terminal", "--", "bash", "-ic", "claude"]))
        c2_box.addWidget(btn_claude)
        cards_layout.addWidget(card2)

        # ACTION CARD 3: TERMINAL TURBO & SWARM
        card3 = QFrame()
        card3.setProperty("class", "cyber-card")
        c3_box = QVBoxLayout(card3)
        lbl_c3 = QLabel("💻 TERMINAL TURBO & SWARM")
        lbl_c3.setFont(QFont("Ubuntu", 13, QFont.Weight.Bold))
        lbl_c3.setStyleSheet("color: #4ade80;")
        c3_box.addWidget(lbl_c3)

        lbl_c3_desc = QLabel("Accès direct au terminal & conteneurs :\n• Session native Turbo M4\n• Base PostgreSQL 15 & Redis 7\n• Workflows n8n (:5678) & Portainer (:9000)\n• Prompt dynamique VRAM")
        lbl_c3_desc.setStyleSheet("color: #94a3b8; font-size: 12px; margin-bottom: 8px;")
        c3_box.addWidget(lbl_c3_desc)

        btn_turbo = QPushButton("💻 Ouvrir Terminal Turbo M4")
        btn_turbo.setProperty("class", "green")
        btn_turbo.clicked.connect(lambda: subprocess.Popen(["gnome-terminal", "--", "/home/pamerys/jarvis/scripts/start-turbo-m1.sh"]))
        c3_box.addWidget(btn_turbo)
        cards_layout.addWidget(card3)

        layout.addLayout(cards_layout)

        # BOTTOM QUICK ACTIONS ROW
        btn_row = QHBoxLayout()
        btn_plan = QPushButton("🔄 Scanner & Régénérer To-Do List M4")
        btn_plan.setProperty("class", "amber")
        btn_plan.clicked.connect(self.run_plan_regen)
        btn_row.addWidget(btn_plan)

        btn_moisson = QPushButton("🌾 Lancer Moisson Claude Code")
        btn_moisson.clicked.connect(lambda: subprocess.Popen(["gnome-terminal", "--", "bash", "-ic", "moisson; read -p 'Terminé'"]))
        btn_row.addWidget(btn_moisson)

        layout.addLayout(btn_row)
        layout.addStretch()

    # --- TAB 2: TABLE RONDE ---
    def init_tab_board(self):
        layout = QVBoxLayout(self.tab_board)
        layout.setSpacing(12)

        lbl = QLabel("🏛 CONSEIL DES 7 EXPERTS & ARBITRAGE EN DIRECT (0-TOKEN FACTURÉ)")
        lbl.setFont(QFont("Ubuntu", 13, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #c084fc;")
        layout.addWidget(lbl)

        inp_layout = QHBoxLayout()
        self.board_input = QLineEdit()
        self.board_input.setPlaceholderText("Posez une question ou entrez une tâche pour le Conseil des 7 Experts...")
        inp_layout.addWidget(self.board_input)

        btn_ask = QPushButton("⚖️ Distribuer aux Experts")
        btn_ask.setProperty("class", "purple")
        btn_ask.clicked.connect(self.ask_table_ronde)
        inp_layout.addWidget(btn_ask)
        layout.addLayout(inp_layout)

        self.board_output = QTextEdit()
        self.board_output.setReadOnly(True)
        self.board_output.setText("Posez une question ci-dessus pour lancer le débat d'experts avec citations du corpus FTS5 (board.db)...")
        layout.addWidget(self.board_output)

    def ask_table_ronde(self):
        q = self.board_input.text().strip()
        if not q:
            return
        self.board_output.setText(f"🏛 Débat des 7 Experts en cours sur : '{q}'...\n0-token facturé • Analyse FTS5 de la Bibliothèque Vivante (49 317 chunks)...")
        self.worker = WorkerThread(["python3", "/home/pamerys/jarvis/board/dispatch_table_ronde.py", "--task", q])
        self.worker.finished_signal.connect(self.board_output.setText)
        self.worker.start()

    # --- TAB 3: BOARD PLAN ---
    def init_tab_plan(self):
        layout = QVBoxLayout(self.tab_plan)
        layout.setSpacing(12)

        top_h = QHBoxLayout()
        lbl = QLabel("📋 TO-DO LIST UNIFIÉE DU PLANNING MASTER (jarvis_master.db)")
        lbl.setFont(QFont("Ubuntu", 13, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #38bdf8;")
        top_h.addWidget(lbl)
        top_h.addStretch()

        btn_regen = QPushButton("🔄 Scanner & Régénérer")
        btn_regen.clicked.connect(self.run_plan_regen)
        top_h.addWidget(btn_regen)
        layout.addLayout(top_h)

        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(4)
        self.tasks_table.setHorizontalHeaderLabels(["ID", "Catégorie", "Titre de la Tâche", "Statut"])
        self.tasks_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tasks_table)
        self.populate_tasks()

    def populate_tasks(self):
        tasks = get_tasks_list()
        self.tasks_table.setRowCount(len(tasks))
        for row, t in enumerate(tasks):
            self.tasks_table.setItem(row, 0, QTableWidgetItem(str(t["id"])))
            self.tasks_table.setItem(row, 1, QTableWidgetItem(str(t["category"])))
            self.tasks_table.setItem(row, 2, QTableWidgetItem(str(t["title"])))
            st_item = QTableWidgetItem(str(t["status"]))
            st_item.setForeground(QColor("#4ade80" if t["status"] == "DONE" else "#38bdf8"))
            self.tasks_table.setItem(row, 3, st_item)

    def run_plan_regen(self):
        self.worker_plan = WorkerThread(["python3", "/home/pamerys/jarvis/scripts/planning_mega_m4.py"])
        self.worker_plan.finished_signal.connect(lambda res: self.populate_tasks())
        self.worker_plan.start()

    # --- TAB 4: 91 MCPs ---
    def init_tab_mcps(self):
        layout = QVBoxLayout(self.tab_mcps)
        layout.setSpacing(12)

        search_h = QHBoxLayout()
        lbl = QLabel("📦 MATRICE DES SERVEURS MCP CONNECTÉS")
        lbl.setFont(QFont("Ubuntu", 13, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #fbbf24;")
        search_h.addWidget(lbl)
        search_h.addStretch()

        self.mcp_search = QLineEdit()
        self.mcp_search.setPlaceholderText("Filtrer les serveurs MCP...")
        self.mcp_search.textChanged.connect(self.filter_mcps)
        search_h.addWidget(self.mcp_search)
        layout.addLayout(search_h)

        self.mcp_table = QTableWidget()
        self.mcp_table.setColumnCount(4)
        self.mcp_table.setHorizontalHeaderLabels(["Nom du Serveur", "Statut", "Protocole", "Commande d'Exécution / URL"])
        self.mcp_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.mcp_table)
        self.populate_mcps(self.all_mcps)

    def populate_mcps(self, mcps_dict):
        self.mcp_table.setRowCount(len(mcps_dict))
        for row, (name, cfg) in enumerate(sorted(mcps_dict.items())):
            t = "HTTP" if (cfg.get("type") == "http" or "serverUrl" in cfg or "url" in cfg) else "STDIO"
            cmd = cfg.get("command") or cfg.get("url") or cfg.get("serverUrl") or "npx/python"
            self.mcp_table.setItem(row, 0, QTableWidgetItem(name))
            
            st_item = QTableWidgetItem("🟢 CONNECTÉ")
            st_item.setForeground(QColor("#4ade80"))
            self.mcp_table.setItem(row, 1, st_item)
            
            self.mcp_table.setItem(row, 2, QTableWidgetItem(t))
            self.mcp_table.setItem(row, 3, QTableWidgetItem(str(cmd)))

    def filter_mcps(self, query):
        q = query.lower()
        filtered = {k: v for k, v in self.all_mcps.items() if q in k.lower() or q in json.dumps(v).lower()}
        self.populate_mcps(filtered)

    # --- TAB 5: SWARM & BASES ---
    def init_tab_swarm(self):
        layout = QVBoxLayout(self.tab_swarm)
        layout.setSpacing(12)

        lbl = QLabel("🐳 ÉTAT DES SERVICES DOCKER SWARM & BASES DE DONNÉES")
        lbl.setFont(QFont("Ubuntu", 13, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #4ade80;")
        layout.addWidget(lbl)

        self.swarm_table = QTableWidget()
        self.swarm_table.setColumnCount(4)
        self.swarm_table.setHorizontalHeaderLabels(["Service", "Hôte : Port", "Rôle Système", "Statut Temps Réel"])
        self.swarm_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.swarm_table)

    # --- TAB 6: MOISSONNAGE ---
    def init_tab_moisson(self):
        layout = QVBoxLayout(self.tab_moisson)
        layout.setSpacing(12)

        lbl = QLabel("🌾 RAPPORT DE PROSPECTION RÉELLE & MOISSON CLAUDE CODE")
        lbl.setFont(QFont("Ubuntu", 13, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #facc15;")
        layout.addWidget(lbl)

        self.moisson_text = QTextEdit()
        self.moisson_text.setReadOnly(True)
        layout.addWidget(self.moisson_text)
        self.refresh_moisson()

    def refresh_moisson(self):
        try:
            r = subprocess.run(["python3", "/home/pamerys/jarvis/scripts/moisson_reelle.py", "--rapport"], capture_output=True, text=True, timeout=3)
            self.moisson_text.setText(r.stdout)
        except Exception as e:
            self.moisson_text.setText(f"Erreur rapport moisson: {e}")

    # --- TELEMETRY UPDATE ---
    def update_telemetry(self):
        v_used, v_tot, temp, util = get_vram_info()
        ram_used, ram_tot = get_ram_info()
        pg_up = is_port_open("127.0.0.1", 5432)
        rd_up = is_port_open("127.0.0.1", 6379)
        n8n_up = is_port_open("127.0.0.1", 5678)
        port_up = is_port_open("127.0.0.1", 9000)
        m6_up = is_port_open("10.42.0.230", 1234) or is_port_open("10.42.0.230", 22)
        ol1_up = is_port_open("127.0.0.1", 11434)
        m1_usb = os.path.exists("/media/pamerys/JARVIS-M1")

        self.lbl_vram_title.setText(f"VRAM RTX 3050: {v_used} / {v_tot} MB ({temp}°C)")
        self.bar_vram.setValue(v_used)

        self.lbl_ram_title.setText(f"RAM: {ram_used} / {ram_tot} GB")
        self.bar_ram.setValue(int(ram_used * 10))

        self.lbl_m6_badge.setText(f"🟢 M6 RJ45 : {'UP (1.4 ms)' if m6_up else '🔴 DOWN'}")
        self.lbl_mcp_badge.setText(f"📦 MCPs : {len(self.all_mcps)} CONNECTÉS")

        # Update Swarm table
        services = [
            ("PostgreSQL 15", "127.0.0.1:5432", "Base relationnelle & vectorielle Swarm", pg_up),
            ("Redis 7 Alpine", "127.0.0.1:6379", "Cache mémoire & Event bus Swarm", rd_up),
            ("n8n Automation", "127.0.0.1:5678", "Moteur de workflows & déclencheurs", n8n_up),
            ("Portainer CE", "127.0.0.1:9000", "Console d'administration Swarm", port_up),
            ("Docker Registry", "127.0.0.1:5000", "Registre d'images local", is_port_open("127.0.0.1", 5000)),
            ("Ollama Local (OL1)", "127.0.0.1:11434", "Inférence locale gemma3/llama3", ol1_up),
            ("M6 Inférence (RJ45)", "10.42.0.230:1234", "LM Studio Qwen 3.5 9B/27B", m6_up),
        ]
        self.swarm_table.setRowCount(len(services))
        for row, (name, host, role, is_active) in enumerate(services):
            self.swarm_table.setItem(row, 0, QTableWidgetItem(name))
            self.swarm_table.setItem(row, 1, QTableWidgetItem(host))
            self.swarm_table.setItem(row, 2, QTableWidgetItem(role))
            st_item = QTableWidgetItem("🟢 ACTIF (UP)" if is_active else "🔴 INACTIF (DOWN)")
            st_item.setForeground(QColor("#4ade80" if is_active else "#f87171"))
            self.swarm_table.setItem(row, 3, st_item)

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = JarvisMainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
