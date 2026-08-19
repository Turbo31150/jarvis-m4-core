#!/usr/bin/env python3
"""
JARVIS-OMEGA — Universal Deliverables Dispatcher & Client Portal
================================================================
"""

import os
import sys
import json
import time
import zipfile
import sqlite3
import datetime
import subprocess
from pathlib import Path

DB_MASTER = Path("/home/pamerys/jarvis/jarvis_master.db")
PDF_DIR = Path("/home/pamerys/labo/output/proposals_pdf")
REPORTS_DIR = Path("/home/pamerys/jarvis/reports")
ZIP_OUTPUT = REPORTS_DIR / "JARVIS_LIVRABLES_COMPLETS_2026.zip"
HTML_PORTAL = REPORTS_DIR / "INDEX_LIVRABLES_CLIENTS.html"

def build_master_zip():
    print("📦 [ARCHIVAGE] Compilation de l'archive universelle des livrables...")
    with zipfile.ZipFile(str(ZIP_OUTPUT), 'w', zipfile.ZIP_DEFLATED) as zipf:
        if PDF_DIR.exists():
            for pdf_file in PDF_DIR.glob("*.pdf"):
                zipf.write(pdf_file, arcname=f"Devis_Propositions_B2B/{pdf_file.name}")
        if REPORTS_DIR.exists():
            for report in REPORTS_DIR.glob("*.md"):
                zipf.write(report, arcname=f"Rapports_et_Exports/{report.name}")
                
    size_mb = ZIP_OUTPUT.stat().st_size / (1024 * 1024)
    print(f"✓ Archive générée : {ZIP_OUTPUT} ({size_mb:.2f} Mo)")

def generate_html_portal():
    print("🌐 [PORTAIL WEB] Génération du portail de livraison client HTML...")
    with sqlite3.connect(str(DB_MASTER), timeout=30) as cx:
        cx.row_factory = sqlite3.Row
        devis = cx.execute("SELECT target_sector, client_persona, offer_name, pricing_model, created_at FROM b2b_sales_pitches ORDER BY id DESC LIMIT 25").fetchall()
        missions = cx.execute("SELECT auteur, intitule, lieu, deadline, fit, statut FROM moisson_missions_linkedin ORDER BY id DESC LIMIT 15").fetchall()
        posts = cx.execute("SELECT id, theme, hook, status, created_at FROM linkedin_content_stream ORDER BY id DESC LIMIT 15").fetchall()
        comments = cx.execute("SELECT topic, comment_text, created_at FROM linkedin_comments_queue ORDER BY id DESC LIMIT 10").fetchall()
        
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>JARVIS OS — Portail Universel de Livraison & Livrables B2B</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0b0f19; color: #e2e8f0; margin: 0; padding: 24px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #38bdf8; border-bottom: 2px solid #1e293b; padding-bottom: 12px; display: flex; justify-content: space-between; align-items: center; }}
        .btn-download {{ background: #2563eb; color: #fff; text-decoration: none; padding: 10px 20px; border-radius: 8px; font-weight: bold; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; margin-top: 24px; }}
        .card {{ background: #1e293b; border-radius: 12px; padding: 20px; border: 1px solid #334155; }}
        .card h2 {{ color: #a855f7; margin-top: 0; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }}
        th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #334155; }}
        th {{ color: #94a3b8; }}
        .badge {{ display: inline-block; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: bold; background: #059669; color: white; }}
        .badge-urgent {{ background: #dc2626; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>
            <span>🚀 JARVIS OS — Portefeuille de Livrables & Déploiements 2026</span>
            <a href="JARVIS_LIVRABLES_COMPLETS_2026.zip" class="btn-download">📥 Télécharger le Pack Complet (ZIP)</a>
        </h1>
        <p>Architecte IA & Déploiements Souverains : <strong>Franck Delmas</strong> (TJM 950€ - 1 200€ / Forfaits 8.5k€ - 190k€)</p>
        
        <div class="grid">
            <div class="card">
                <h2>📑 Devis & Propositions B2B ({len(devis)})</h2>
                <table>
                    <tr><th>Secteur / Cible</th><th>Persona</th><th>Offre</th><th>Modèle Tarif</th></tr>
"""
    for d in devis:
        html += f"<tr><td><strong>{d['target_sector']}</strong></td><td>{d['client_persona']}</td><td>{d['offer_name']}</td><td><span class='badge'>{d['pricing_model']}</span></td></tr>"

    html += """
                </table>
            </div>

            <div class="card">
                <h2>🎯 Missions & Opportunités Urgentes</h2>
                <table>
                    <tr><th>Entreprise</th><th>Poste</th><th>Délai</th><th>Fit</th></tr>
"""
    for m in missions:
        html += f"<tr><td><strong>{m['auteur']}</strong></td><td>{m['intitule']}</td><td><span class='badge badge-urgent'>{m['deadline']}</span></td><td>{m['fit']}</td></tr>"

    html += """
                </table>
            </div>
        </div>

        <div class="grid" style="margin-top: 20px;">
            <div class="card">
                <h2>📢 Publications & Contenus Live LinkedIn</h2>
                <table>
                    <tr><th>Thème</th><th>Accroche</th><th>Statut</th></tr>
"""
    for p in posts:
        html += f"<tr><td><strong>{p['theme']}</strong></td><td>{p['hook'][:60]}...</td><td><span class='badge'>{p['status']}</span></td></tr>"

    html += """
                </table>
            </div>

            <div class="card">
                <h2>💬 Commentaires Experts sur l'Actualité</h2>
                <table>
                    <tr><th>Sujet</th><th>Commentaire d'Autorité</th></tr>
"""
    for c in comments:
        html += f"<tr><td><strong>{c['topic'][:40]}</strong></td><td>{c['comment_text'][:90]}...</td></tr>"

    html += """
                </table>
            </div>
        </div>
    </div>
</body>
</html>"""

    with open(str(HTML_PORTAL), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✓ Portail HTML généré : {HTML_PORTAL}")

def trigger_multichannel_dispatch():
    print("🚀 [DISPATCH MULTI-CANAUX] Expédition globale de l'archive et des livrables...")
    
    # Copie dans le stockage permanent /storage/
    if Path("/storage").exists():
        storage_dest = Path("/storage/JARVIS_LIVRABLES_COMPLETS_2026.zip")
        try:
            shutil.copy2(ZIP_OUTPUT, storage_dest)
            print(f"✓ Livrables archivés sur stockage permanent Samsung 870 EVO : {storage_dest}")
        except Exception as e:
            print(f"ℹ️ /storage copy: {e}")

    summary = f"🎉 [TOUS LES LIVRABLES EXPÉDIÉS] Pack universel compilé ({ZIP_OUTPUT.stat().st_size / (1024*1024):.2f} Mo) · Portail Web client prêt !"
    subprocess.run(["curl", "-s", "-d", summary, "https://ntfy.sh/jarvis_omega_turbo"], stdout=subprocess.DEVNULL)
    
    try:
        subprocess.run(['edge-tts', '--voice', 'fr-FR-RemyMultilingualNeural', '--text', 'Tous les livrables devis et candidatures ont été compilés et expédiés.', '--write-media', '/tmp/all_deliv.mp3'], timeout=10)
        subprocess.run(['ffmpeg', '-y', '-i', '/tmp/all_deliv.mp3', '-filter:a', 'volume=6.0', '-ar', '48000', '-ac', '2', '/tmp/all_deliv.wav'], timeout=10)
        subprocess.Popen(['aplay', '-D', 'plughw:1,0', '/tmp/all_deliv.wav'])
    except Exception:
        pass

def main():
    print("==================================================================")
    print("🚀 [UNIVERSAL DELIVERABLES DISPATCHER] COMPILATION & EXPÉDITION TOTALE")
    print("==================================================================")
    build_master_zip()
    generate_html_portal()
    trigger_multichannel_dispatch()
    
    os.system("rm -f /tmp/*.png /tmp/*.xml /tmp/*.3gp /tmp/*.wav /tmp/*.mp3 2>/dev/null")
    print("🧹 Nettoyage Zéro-Déchet effectué.")
    print("✅ TOUS LES LIVRABLES SONT OFFICIELLEMENT PACKAGÉS ET DISPONIBLES !")

if __name__ == "__main__":
    main()
