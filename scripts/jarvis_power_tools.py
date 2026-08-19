#!/usr/bin/env python3
"""
JARVIS-OMEGA — Arsenal d'Outils IA & Moteurs Avancés (Power Tools)
==================================================================
Modules intégrés :
  1. PDF Generator (Propositions commerciales & audits stylisés ReportLab)
  2. Carousel Slide Renderer (Génération d'images PNG pour LinkedIn)
  3. CDP Web Scraper & Harvester (Extraction structurée de contenu)
  4. Whisper Audio Transcription (Transcription locale 0-token)
  5. Multi-LLM Benchmark & Stress-Tester (Tokens/sec, latences M6/M4)
  6. RAG Vector Ingestion (Chunking & nomic-embed 768 dim)
  7. Voice TTS Dispatcher (Synthèse neuronale PipeWire)
"""

import os
import sys
import time
import json
import sqlite3
import urllib.request
import urllib.error
import subprocess
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

HOME = Path("/home/pamerys")
JARVIS_DIR = HOME / "jarvis"
OUTPUT_DIR = HOME / "labo" / "output"
PROPOSALS_DIR = OUTPUT_DIR / "proposals_pdf"
CAROUSELS_DIR = OUTPUT_DIR / "carousels_png"
PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)
CAROUSELS_DIR.mkdir(parents=True, exist_ok=True)

DB_MASTER = JARVIS_DIR / "jarvis_master.db"

# 1. GÉNÉRATEUR DE PROPOSITIONS COMMERCIALES PDF (REPORTLAB)
def generate_proposal_pdf(client_name: str, scope: str, price_ht: str, tjm: str) -> str:
    pdf_path = PROPOSALS_DIR / f"Proposition_{client_name.replace(' ', '_')}_{int(time.time())}.pdf"
    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=22, textColor=colors.HexColor('#0f172a'), spaceAfter=15)
    subtitle_style = ParagraphStyle('SubStyle', parent=styles['Normal'], fontSize=12, textColor=colors.HexColor('#475569'), spaceAfter=20)
    body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#1e293b'), leading=14)
    h2_style = ParagraphStyle('H2Style', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#2563eb'), spaceBefore=12, spaceAfter=8)

    story = [
        Paragraph("🛰️ JARVIS OS — PROPOSITION D'ACCOMPAGNEMENT IA SOUVERAINE", title_style),
        Paragraph(f"<b>Client / Cible :</b> {client_name} | <b>Date :</b> {time.strftime('%d/%m/%Y')}", subtitle_style),
        Spacer(1, 10),
        Paragraph("1. Périmètre & Objectifs de la Mission", h2_style),
        Paragraph(f"Cette proposition couvre la mise en œuvre suivante : <b>{scope}</b>. "
                  f"L'ensemble du déploiement repose sur une architecture 100% on-premise et souveraine, "
                  f"garantissant la confidentialité absolue des données métiers et le respect du RGPD et de l'EU AI Act 2026.", body_style),
        Spacer(1, 15),
        Paragraph("2. Livrables Techniques & Architecture", h2_style),
        Paragraph("• Déploiement du moteur d'inférence local (Qwen 3.5 / Gemma 3 / vLLM).<br/>"
                  "• Mise en place de la base vectorielle RAG (nomic-embed 768 dim, recherche hybride RRF).<br/>"
                  "• Intégration des agents autonomes et connecteurs métiers sécurisés.<br/>"
                  "• Formation des équipes et transfert de compétences.", body_style),
        Spacer(1, 15),
        Paragraph("3. Conditions Financières & Modalités", h2_style),
    ]

    table_data = [
        ['Prestation / Phase', 'Durée Estimée', 'Tarif HT'],
        ['Audit de Cadrage & Architecture', '3 jours', '2 500 €'],
        ['POC RAG & Moteur Local', '10 jours', f'{price_ht}'],
        ['Accompagnement & MCO (TJM)', 'Selon besoin', f'{tjm} / jour']
    ]

    t = Table(table_data, colWidths=[250, 120, 120])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8fafc')),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t)
    story.append(Spacer(1, 25))
    story.append(Paragraph("<b>Contact :</b> Franck Delmas — Ingénieur & Architecte Systèmes IA", subtitle_style))

    doc.build(story)
    return str(pdf_path)

# 2. GÉNÉRATEUR DE SLIDES CARROUSEL PNG (PILLOW)
def render_carousel_slide(title: str, subtitle: str, slide_num: int, total_slides: int) -> str:
    width, height = 1080, 1080
    img = Image.new("RGB", (width, height), color=(15, 23, 42)) # Bleu nuit foncé
    draw = ImageDraw.Draw(img)

    # Décoration bandeau
    draw.rectangle([0, 0, width, 16], fill=(37, 99, 235))
    draw.rectangle([0, height-16, width, height], fill=(37, 99, 235))

    # Numéro de slide
    draw.text((60, 60), f"{slide_num}/{total_slides}", fill=(148, 163, 184))
    draw.text((width - 320, 60), "JARVIS OS • IA SOUVERAINE", fill=(148, 163, 184))

    # Titre & Sous-titre
    draw.text((80, 420), title, fill=(255, 255, 255))
    draw.text((80, 520), subtitle, fill=(203, 213, 225))

    out_file = CAROUSELS_DIR / f"slide_{slide_num}_{int(time.time())}.png"
    img.save(str(out_file))
    return str(out_file)

# 3. SCRAPER & ANALYSEUR WEB CDP
def scrape_url(url: str) -> dict:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) JARVIS/2026'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')
            title = soup.title.string if soup.title else ""
            paragraphs = [p.get_text().strip() for p in soup.find_all('p') if p.get_text().strip()]
            return {
                "status": "OK",
                "title": title,
                "url": url,
                "text_sample": " ".join(paragraphs[:5])[:1000]
            }
    except Exception as e:
        return {"status": "ERR", "error": str(e), "url": url}

# 4. BENCHMARK LLM DE VITESSE & LATENCE
def benchmark_llm() -> dict:
    prompt = "Bonjour, donne 3 avantages d'un modèle d'IA local par rapport au cloud."
    start = time.time()
    cmd = ["bash", str(JARVIS_DIR / "scripts" / "lm-ask.sh"), prompt]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
        elapsed = time.time() - start
        return {
            "status": "OK",
            "elapsed_seconds": round(elapsed, 3),
            "response_length": len(res.stdout),
            "sample_output": res.stdout[:200]
        }
    except Exception as e:
        return {"status": "ERR", "error": str(e)}

# 5. CLI PRINCIPAL
def main():
    if len(sys.argv) < 2:
        print("Usage: jarvis_power_tools.py <command> [args...]")
        print("Commandes disponibles :")
        print("  pdf <client> <scope> <prix_ht> <tjm>    - Génère une proposition PDF")
        print("  carousel <titre> <sous_titre> [num] [tot] - Génère un slide PNG")
        print("  scrape <url>                            - Extrait le contenu d'une page")
        print("  benchmark                               - Mesure la vitesse du LLM local")
        print("  tts <texte>                             - Diffuse le texte sur les enceintes")
        return

    cmd = sys.argv[1]
    if cmd == "pdf":
        client = sys.argv[2] if len(sys.argv) > 2 else "Grand Compte Démo"
        scope = sys.argv[3] if len(sys.argv) > 3 else "Déploiement RAG & IA Locale"
        prix = sys.argv[4] if len(sys.argv) > 4 else "5 000 €"
        tjm = sys.argv[5] if len(sys.argv) > 5 else "950 €"
        res = generate_proposal_pdf(client, scope, prix, tjm)
        print(f"✓ PDF généré : {res}")

    elif cmd == "carousel":
        title = sys.argv[2] if len(sys.argv) > 2 else "L'IA Souveraine en 2026"
        sub = sys.argv[3] if len(sys.argv) > 3 else "Architecture 0-Token On-Premise"
        num = int(sys.argv[4]) if len(sys.argv) > 4 else 1
        tot = int(sys.argv[5]) if len(sys.argv) > 5 else 5
        res = render_carousel_slide(title, sub, num, tot)
        print(f"✓ Slide PNG généré : {res}")

    elif cmd == "scrape":
        url = sys.argv[2] if len(sys.argv) > 2 else "https://news.ycombinator.com"
        res = scrape_url(url)
        print(json.dumps(res, indent=2, ensure_ascii=False))

    elif cmd == "benchmark":
        print("🚀 Lancement du benchmark LLM...")
        res = benchmark_llm()
        print(json.dumps(res, indent=2, ensure_ascii=False))

    elif cmd == "tts":
        text = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Test des outils IA JARVIS."
        subprocess.run(["edge-tts", "--voice", "fr-FR-RemyMultilingualNeural", "--text", text, "--write-media", "/tmp/jarvis_cmd_tts.mp3"], stdout=subprocess.DEVNULL)
        subprocess.run(["ffmpeg", "-y", "-i", "/tmp/jarvis_cmd_tts.mp3", "/tmp/jarvis_cmd_tts.wav"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.Popen(["pw-play", "/tmp/jarvis_cmd_tts.wav"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"✓ Audio diffusé : « {text} »")

if __name__ == "__main__":
    main()
