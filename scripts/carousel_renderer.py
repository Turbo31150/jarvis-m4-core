#!/usr/bin/env python3
"""
carousel_renderer.py — Générateur de visuels HTML/SVG/PNG pour carrousels réseaux sociaux Board JARVIS
Transforme les slides issues du Board OS en rendu visuel haute fidélité (Dark Tech & Minimalist).
"""

import sys
import json
import os
from pathlib import Path

def render_html_carousel(slides: list, topic: str, output_path: str):
    slides_html = ""
    for idx, slide in enumerate(slides, 1):
        title = slide.get("title", f"Slide {idx}") if isinstance(slide, dict) else f"Slide {idx}"
        content = slide.get("content", slide) if isinstance(slide, dict) else str(slide)
        
        slides_html += f"""
        <div class="carousel-card" id="slide-{idx}">
            <div class="card-header">
                <span class="badge">JARVIS BOARD OS</span>
                <span class="slide-num">{idx} / {len(slides)}</span>
            </div>
            <div class="card-body">
                <h2>{title}</h2>
                <p>{content}</p>
            </div>
            <div class="card-footer">
                <span class="author">Franc Delmas · JARVIS Architecture</span>
                <span class="tag">0 Cloud · Souverain</span>
            </div>
        </div>
        """

    full_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>{topic} — Carrousel JARVIS</title>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@400;700&display=swap');
    
    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }}
    
    body {{
        background: #090d16;
        color: #f1f5f9;
        font-family: 'Inter', sans-serif;
        padding: 40px 20px;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 30px;
    }}
    
    h1.main-title {{
        font-size: 24px;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #38bdf8;
        margin-bottom: 10px;
        text-align: center;
    }}

    .carousel-container {{
        display: flex;
        flex-wrap: wrap;
        gap: 25px;
        justify-content: center;
        max-width: 1200px;
    }}

    .carousel-card {{
        width: 360px;
        height: 460px;
        background: linear-gradient(145deg, #111827, #1f2937);
        border: 1px solid #374151;
        border-radius: 16px;
        padding: 28px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }}

    .carousel-card:hover {{
        transform: translateY(-4px);
        border-color: #38bdf8;
    }}

    .card-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}

    .badge {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        font-weight: 700;
        background: rgba(56, 189, 248, 0.15);
        color: #38bdf8;
        padding: 4px 10px;
        border-radius: 9999px;
        border: 1px solid rgba(56, 189, 248, 0.3);
    }}

    .slide-num {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        color: #94a3b8;
    }}

    .card-body h2 {{
        font-size: 20px;
        font-weight: 700;
        line-height: 1.3;
        color: #ffffff;
        margin-bottom: 14px;
    }}

    .card-body p {{
        font-size: 14px;
        line-height: 1.6;
        color: #cbd5e1;
    }}

    .card-footer {{
        border-top: 1px solid #374151;
        padding-top: 14px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 11px;
        color: #94a3b8;
    }}

    .card-footer .tag {{
        font-family: 'JetBrains Mono', monospace;
        color: #10b981;
    }}
</style>
</head>
<body>
    <h1 class="main-title">📊 {topic} — Board OS Insights</h1>
    <div class="carousel-container">
        {slides_html}
    </div>
</body>
</html>
"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_html)
    print(f"🎨 Rendu visuel HTML du carrousel généré : {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 carousel_renderer.py <social_json_path>")
        sys.exit(1)
        
    p = Path(sys.argv[1])
    if not p.exists():
        print(f"Fichier {p} introuvable.")
        sys.exit(1)
        
    data = json.loads(p.read_text(encoding='utf-8'))
    topic = data.get("topic", "Sujet JARVIS")
    slides = data.get("pack", {}).get("carousel_slides", [])
    
    out_html = p.with_suffix(".html")
    render_html_carousel(slides, topic, str(out_html))
