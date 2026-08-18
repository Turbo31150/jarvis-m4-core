#!/usr/bin/env bash
# Complète les angles vides (gpt-oss:120b-cloud, 0-token) + réassemble findings/report/pdf.
set -uo pipefail
O="$HOME/Downloads/research-social-publish-headless"
declare -A P=(
[1-linkedin]="Synthèse experte FR ~550 mots, factuelle, 2025-2026. Sujet: publier un CAROUSEL/document sur LinkedIn en AUTO depuis un serveur Linux headless. Couvre: (1) API officielle LinkedIn Posts/UGC, upload document, scopes (w_member_social), app/page entreprise requise, quotas; (2) cookie de session li_at: durée, ce qui l'invalide, réinjection Playwright, fiabilité headless; (3) détection anti-bot et risque de ban. Termine par VERDICT: voie la plus fiable. Notes techniques, pas de blabla."
[5-outils-tiers]="Synthèse experte FR ~550 mots, 2025-2026. Sujet: outils self-host/API pour publier multi-reseaux (LinkedIn/IG/Threads/TikTok) en auto. Couvre: self-hosted OSS (Postiz, Mixpost) reseaux + carousel + auth + Docker; API unifiees (Ayrshare, Buffer, Publer) prix + carousel; n8n noeuds sociaux + limites. VERDICT: solution la plus pragmatique 0-cout pour un setup self-host JARVIS."
)
for k in "${!P[@]}"; do
  f="$O/sources/$k.md"
  if [ "$(wc -w <"$f" 2>/dev/null || echo 0)" -gt 50 ]; then echo "skip $k"; continue; fi
  echo "[$(date +%H:%M:%S)] gen $k"
  { echo "# $k"; echo; echo "_Généré via Ollama Cloud gpt-oss:120b — à recouper._"; echo; echo "---"; echo
    printf '%s' "${P[$k]}" | timeout 300 ollama run gpt-oss:120b-cloud 2>/dev/null; } > "$f"
  echo "  -> $(wc -w <"$f") mots"
done
# réassemblage déterministe (bash/python pur, 0 LLM)
{ echo "# Research Findings — Auto-publication réseaux headless (2026)"; echo
  echo "**Date:** $(date +%F) · **Backend:** Ollama Cloud gpt-oss:120b (0 token Anthropic) · **Sujet:** publier carousels sur LinkedIn/IG/Threads/TikTok depuis serveur headless"; echo
  for f in "$O"/sources/*.md; do [ "$(wc -w <"$f")" -gt 50 ] && { echo; echo "## $(basename "$f" .md)"; sed '1,5d' "$f"; echo; }; done; } > "$O/findings.md"
python3 - "$O" <<'PY'
import sys,html,pathlib,datetime
o=pathlib.Path(sys.argv[1]); md=(o/"findings.md").read_text("utf-8","replace")
h=f'''<!doctype html><html lang=fr><meta charset=utf-8><title>Deep Research — Publication réseaux headless</title>
<style>body{{font-family:system-ui,sans-serif;max-width:860px;margin:2rem auto;padding:0 1rem;background:#fff;color:#1a1a1a;line-height:1.6}}h1{{border-bottom:3px solid #2d6cdf;padding-bottom:.3rem}}h2{{color:#2d6cdf;margin-top:2rem}}pre{{white-space:pre-wrap;font-family:inherit}}footer{{margin-top:3rem;border-top:1px solid #ddd;padding-top:1rem;color:#888;font-size:.85rem}}</style>
<pre>{html.escape(md)}</pre><footer>JARVIS Deep Research — {datetime.date.today()} — 0-token (Ollama Cloud gpt-oss)</footer></html>'''
(o/"report.html").write_text(h,"utf-8"); print("report.html",len(h),"o")
PY
CH=$(command -v google-chrome||command -v chromium||echo /opt/google/chrome/chrome)
"$CH" --headless --no-sandbox --disable-gpu --print-to-pdf="$O/report.pdf" "file://$O/report.html" >/dev/null 2>&1 && echo "PDF ok" || echo "PDF skip"
echo "[$(date +%H:%M:%S)] DONE"; for f in "$O"/sources/*.md; do echo "$(wc -w <"$f") $(basename "$f")"; done
