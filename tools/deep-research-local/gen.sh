#!/usr/bin/env bash
# Deep-research 0-token : génération via Ollama Cloud (kimi) → fallback local lm-ask/ollama.
set -uo pipefail
OUT="$HOME/Downloads/research-social-publish-headless"; mkdir -p "$OUT/sources"
LM="$HOME/jarvis/scripts/lm-ask.sh"
log(){ echo "[$(date +%H:%M:%S)] $*"; }

ASK(){ # $1=prompt -> stdout (cascade: ollama cloud kimi -> ollama cloud gpt-oss -> lm-ask local)
  local p="$1" out=""
  out="$(printf '%s' "$p" | timeout 240 ollama run gpt-oss:120b-cloud 2>/dev/null)"
  [ -z "$out" ] && out="$(printf '%s' "$p" | timeout 240 ollama run gpt-oss:120b-cloud 2>/dev/null)"
  [ -z "$out" ] && [ -x "$LM" ] && out="$(timeout 200 bash "$LM" --big "$p" 2>/dev/null)"
  printf '%s' "$out"
}

declare -a K=(1-linkedin 2-meta-ig-threads 3-tiktok 4-browser-antibot 5-outils-tiers)
declare -a P=(
"Synthèse experte FR ~550 mots, factuelle, 2025-2026. Sujet: publier un CAROUSEL/document sur LinkedIn en AUTO depuis un serveur Linux headless. Couvre: (1) API officielle LinkedIn Posts/UGC, upload document, scopes (w_member_social), app/page entreprise requise, quotas; (2) cookie de session li_at: durée, ce qui l'invalide, réinjection Playwright, fiabilité headless; (3) détection anti-bot et risque de ban. Termine par VERDICT: voie la plus fiable. Style notes techniques, pas de blabla."
"Synthèse experte FR ~550 mots, 2025-2026. Sujet: publier sur INSTAGRAM et THREADS via API officielle Meta Graph depuis un backend headless. Couvre: IG Content Publishing API (image + carousel 10 medias, /media + /media_publish, compte Business lié Page FB, token long-lived ~60j refresh, 25 posts/24h, medias en URL publique obligatoire), Threads API (publication texte/image/carousel, auth), app review Meta + permission instagram_content_publish. VERDICT: faisabilité + étapes + blocages."
"Synthèse experte FR ~550 mots, 2025-2026. Sujet: publier un carousel photo/vidéo sur TIKTOK via Content Posting API depuis backend headless. Couvre: endpoints Direct Post vs Upload, support photo carousel, OAuth scopes (video.publish/upload), statut app unaudited => posts SELF_ONLY/privés tant que non audité, process audit, quotas/tokens. VERDICT: faisabilité + blocage principal (audit)."
"Synthèse experte FR ~550 mots, 2025-2026. Sujet: automatiser la publication réseaux via navigateur headless (Playwright/Puppeteer/CDP) sans se faire détecter, avec sessions persistantes. Couvre: persistance storageState/cookies + user-data-dir, ce qui casse une session (IP/fingerprint), détection bot (navigator.webdriver, fingerprint, headless), contournements (playwright-stealth, undetected, rebrowser), headful sous Xvfb vs headless=new. VERDICT: approche la plus robuste sans ban."
"Synthèse experte FR ~550 mots, 2025-2026. Sujet: outils self-host/API pour publier multi-reseaux (LinkedIn/IG/Threads/TikTok) en auto, alternative au code maison. Couvre: self-hosted OSS (Postiz, Mixpost) reseaux supportes + carousel + auth + Docker; API unifiees (Ayrshare, Buffer, Publer) prix + carousel; n8n noeuds sociaux + limites. VERDICT: solution la plus pragmatique et 0-cout pour un setup self-host."
)

for i in "${!K[@]}"; do
  log "angle ${K[$i]} ..."
  { echo "# ${K[$i]}"; echo; echo "_Généré via Ollama Cloud (kimi/gpt-oss) — connaissance modèle, à recouper._"; echo; echo "---"; echo; ASK "${P[$i]}"; } > "$OUT/sources/${K[$i]}.md"
  log "  -> $(wc -w < "$OUT/sources/${K[$i]}.md") mots"
done

log "assemblage findings.md"
{ echo "# Research Findings: Auto-publication réseaux headless (2026)"; echo; echo "**Date:** $(date +%F)  ·  **Backend:** Ollama Cloud (0 token Anthropic)  ·  **Sources:** 5 angles"; echo; for k in "${K[@]}"; do echo; echo "## ${k}"; sed '1,5d' "$OUT/sources/${k}.md"; echo; done; } > "$OUT/findings.md"

log "report.html (via LLM)"
ASK "Transforme ces notes en UN fichier report.html COMPLET et autonome (doctype, <style> inline, fond blanc, typo sans-serif, titres, sections, lisible mobile, footer 'JARVIS Deep Research $(date +%F)'). Rends UNIQUEMENT le HTML, rien d'autre. NOTES:
$(head -c 14000 "$OUT/findings.md")" > "$OUT/report.html"
# garde-fou: si pas de <html>, enrobe
grep -qi '<html' "$OUT/report.html" || { tmp=$(cat "$OUT/report.html"); printf '<!doctype html><meta charset=utf-8><title>Deep Research</title><body style="font-family:sans-serif;max-width:820px;margin:2rem auto;padding:0 1rem"><pre style="white-space:pre-wrap">%s</pre></body>' "$tmp" > "$OUT/report.html"; }

log "PDF (chrome headless)"
CH=$(command -v google-chrome || command -v chromium || echo /opt/google/chrome/chrome)
"$CH" --headless --no-sandbox --disable-gpu --print-to-pdf="$OUT/report.pdf" "file://$OUT/report.html" >/dev/null 2>&1 && log "PDF ok" || log "PDF skip"
log "TERMINÉ → $OUT"
ls -la "$OUT"
