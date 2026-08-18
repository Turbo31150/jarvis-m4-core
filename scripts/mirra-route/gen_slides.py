#!/usr/bin/env python3
"""Génère 6 slides 4:5 Instagram pour réponse critique LinkedIn JARVIS.
Sortie: /tmp/mirra-slides/slide_{1..6}.jpg
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

W, H = 1080, 1350  # 4:5 Instagram
BG = (12, 16, 28)  # near-black tech
ACCENT = (50, 220, 200)  # cyan
WHITE = (240, 240, 245)
DIM = (140, 145, 160)
RED = (255, 90, 90)

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_MONO = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Regular.ttf"

OUT = Path("/tmp/mirra-slides")
OUT.mkdir(parents=True, exist_ok=True)


def f(path, size):
    return ImageFont.truetype(path, size)


def wrap(text, font, max_w, draw):
    """Wrap text to fit max_w pixels."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=font) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def base_slide(num):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # top bar
    d.rectangle([0, 0, W, 8], fill=ACCENT)
    # footer brand
    d.text(
        (60, H - 80), "JARVIS OS · 127.0.0.1 > Cloud", fill=DIM, font=f(FONT_MONO, 22)
    )
    d.text((W - 180, H - 80), f"{num}/6", fill=ACCENT, font=f(FONT_BOLD, 28))
    return img, d


# --- SLIDE 1 — HOOK ---
img, d = base_slide(1)
d.text((60, 120), "Hier sur LinkedIn:", fill=DIM, font=f(FONT_REG, 36))
# quote box
d.rectangle([60, 220, W - 60, 820], outline=RED, width=3)
d.rectangle([60, 220, 70, 820], fill=RED)
quote = "« Python pour les LLM ? Code en bazar. JARVIS tient combien de temps ? 24h ? 72h avant le crash ? »"
lines = wrap(quote, f(FONT_REG, 44), W - 200, d)
y = 280
for ln in lines:
    d.text((100, y), ln, fill=WHITE, font=f(FONT_REG, 44))
    y += 64
d.text((60, 920), "Réponse honnête.", fill=ACCENT, font=f(FONT_BOLD, 56))
d.text((60, 1000), "Pas démo-day.", fill=ACCENT, font=f(FONT_BOLD, 56))
d.text((60, 1100), "Build in public. ↓", fill=DIM, font=f(FONT_REG, 36))
img.save(OUT / "slide_1.jpg", quality=92)

# --- SLIDE 2 — PYTHON ---
img, d = base_slide(2)
d.text((60, 120), "01", fill=ACCENT, font=f(FONT_BOLD, 120))
d.text((280, 160), "Python = bazar ?", fill=WHITE, font=f(FONT_BOLD, 64))
d.text((60, 360), "Faux procès.", fill=ACCENT, font=f(FONT_BOLD, 52))
body = "Python = tissu conjonctif. Pas hot path. L'inférence tourne sur llama.cpp, Whisper.cpp, Ollama, LM Studio. Du C++/CUDA bien tassé."
y = 470
for ln in wrap(body, f(FONT_REG, 40), W - 120, d):
    d.text((60, y), ln, fill=WHITE, font=f(FONT_REG, 40))
    y += 58
d.text((60, 880), "Python orchestre du I/O-bound.", fill=DIM, font=f(FONT_REG, 36))
d.text((60, 940), "C'est un choix d'archi.", fill=DIM, font=f(FONT_REG, 36))
d.rectangle([60, 1030, W - 60, 1130], outline=ACCENT, width=2)
d.text(
    (80, 1050),
    "→ github.com/Turbo31150/jarvis-cowork",
    fill=ACCENT,
    font=f(FONT_MONO, 28),
)
d.text((80, 1090), "  249 agents · 570+ scripts QA", fill=DIM, font=f(FONT_MONO, 24))
img.save(OUT / "slide_2.jpg", quality=92)

# --- SLIDE 3 — CONTEXT WINDOW ---
img, d = base_slide(3)
d.text((60, 120), "02", fill=ACCENT, font=f(FONT_BOLD, 120))
d.text((280, 160), "Contexte ?", fill=WHITE, font=f(FONT_BOLD, 64))
d.text((60, 360), "Pas de context-window XXL.", fill=ACCENT, font=f(FONT_BOLD, 44))
body = "MCP (Model Context Protocol Anthropic) + RAG vectoriel. Chaque agent ne reçoit que les tokens utiles à sa micro-tâche."
y = 480
for ln in wrap(body, f(FONT_REG, 40), W - 120, d):
    d.text((60, y), ln, fill=WHITE, font=f(FONT_REG, 40))
    y += 58
d.text((60, 880), "P95 bas sans modèle 200K.", fill=DIM, font=f(FONT_REG, 36))
d.rectangle([60, 1030, W - 60, 1130], outline=ACCENT, width=2)
d.text((80, 1050), "→ modelcontextprotocol.io", fill=ACCENT, font=f(FONT_MONO, 28))
d.text((80, 1090), "→ jarvis-mcp-toolkit", fill=ACCENT, font=f(FONT_MONO, 28))
img.save(OUT / "slide_3.jpg", quality=92)

# --- SLIDE 4 — CRASH ---
img, d = base_slide(4)
d.text((60, 120), "03", fill=ACCENT, font=f(FONT_BOLD, 120))
d.text((280, 160), "Crash 24-72h ?", fill=WHITE, font=f(FONT_BOLD, 60))
d.text((60, 360), "Oui. Ça plante.", fill=RED, font=f(FONT_BOLD, 56))
d.text((60, 440), "Et c'est OK.", fill=ACCENT, font=f(FONT_BOLD, 56))
body = "Build in public = montrer les incidents. La résilience c'est pas « ça tombe jamais »."
y = 560
for ln in wrap(body, f(FONT_REG, 38), W - 120, d):
    d.text((60, y), ln, fill=WHITE, font=f(FONT_REG, 38))
    y += 54
# checklist
y += 30
items = [
    "systemd watchdog",
    "Docker restart policies",
    "auto-repair pipeline",
    "failover LM Studio ↔ Ollama",
]
for it in items:
    d.text((60, y), "✓", fill=ACCENT, font=f(FONT_BOLD, 32))
    d.text((110, y), it, fill=WHITE, font=f(FONT_REG, 32))
    y += 50
img.save(OUT / "slide_4.jpg", quality=92)

# --- SLIDE 5 — COÛT ---
img, d = base_slide(5)
d.text((60, 120), "04", fill=ACCENT, font=f(FONT_BOLD, 120))
d.text((280, 160), "Le vrai sujet", fill=WHITE, font=f(FONT_BOLD, 64))
d.text((60, 360), "Pas « est-ce que Python est laid ».", fill=DIM, font=f(FONT_REG, 36))
d.text((60, 410), "Mais :", fill=DIM, font=f(FONT_REG, 36))
d.text((60, 490), "« Ça encaisse 24/7 ?", fill=ACCENT, font=f(FONT_BOLD, 48))
d.text((60, 560), "  Combien ça coûte ? »", fill=ACCENT, font=f(FONT_BOLD, 48))
# specs box
d.rectangle([60, 680, W - 60, 1080], outline=ACCENT, width=2)
d.text((80, 700), "Cluster on-prem", fill=ACCENT, font=f(FONT_BOLD, 32))
specs = [
    "6 machines · GPUs mixés",
    "RTX 2060 · RTX 3080 · GTX 1660S",
    "Quadro P4000 · ~40 GB VRAM agrégés",
    "",
    "Coût marginal LLM = électricité.",
    "Pas de facture API à 3000€.",
]
y = 760
for s in specs:
    d.text((80, y), s, fill=WHITE if s else DIM, font=f(FONT_REG, 30))
    y += 48
d.text((60, 1130), "127.0.0.1 > Cloud.", fill=ACCENT, font=f(FONT_BOLD, 44))
img.save(OUT / "slide_5.jpg", quality=92)

# --- SLIDE 6 — CTA ---
img, d = base_slide(6)
d.text((60, 200), "Vrai bug dans une", fill=WHITE, font=f(FONT_BOLD, 56))
d.text((60, 280), "fonction nommée ?", fill=WHITE, font=f(FONT_BOLD, 56))
d.text((60, 420), "→ Issue GitHub.", fill=ACCENT, font=f(FONT_BOLD, 48))
d.text((60, 490), "→ Tag-moi le commit.", fill=ACCENT, font=f(FONT_BOLD, 48))
d.text((60, 560), "→ Je réponds.", fill=ACCENT, font=f(FONT_BOLD, 48))
d.text((60, 720), "Code MIT, ouvert,", fill=DIM, font=f(FONT_REG, 36))
d.text((60, 770), "perfectible.", fill=DIM, font=f(FONT_REG, 36))
# QR/link box
d.rectangle([60, 880, W - 60, 1180], outline=ACCENT, width=3)
d.text((80, 910), "Liens publics :", fill=ACCENT, font=f(FONT_BOLD, 32))
links = [
    "github.com/Turbo31150",
    "  jarvis-cowork · jarvis-cluster",
    "  jarvis-mcp-toolkit · jarvis-whisper-flow",
    "",
    "jarvis-delmas.netlify.app",
]
y = 970
for ln in links:
    d.text((80, y), ln, fill=WHITE if ln else DIM, font=f(FONT_MONO, 26))
    y += 42
img.save(OUT / "slide_6.jpg", quality=92)

print(f"✓ 6 slides générées dans {OUT}")
for p in sorted(OUT.glob("slide_*.jpg")):
    print(f"  {p.name}  {p.stat().st_size // 1024} KB")
