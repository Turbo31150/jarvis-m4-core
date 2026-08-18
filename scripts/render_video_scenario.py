#!/usr/bin/env python3
"""
Rendu vidéo déterministe du scénario Table Ronde JARVIS OS.

Pipeline :
  1. Chrome headless pilote le canvas du studio HTML image par image
  2. edge-tts génère la voix off française de chaque scène
  3. ffmpeg assemble frames + audio en MP4 H.264

Zéro service cloud payant, tout local.
"""

import asyncio
import base64
import shutil
import subprocess
import sys
from pathlib import Path

STUDIO = Path("/home/pamerys/Bureau/JARVIS_OS_STUDIO_VIDEO_TABLE_RONDE.html")
OUTDIR = Path("/home/pamerys/Bureau/production_video_jarvis")
FRAMES = OUTDIR / "frames"
AUDIO = OUTDIR / "audio"
FPS = 25
VOICE = "fr-FR-DeniseNeural"


async def render_frames():
    from playwright.async_api import async_playwright

    FRAMES.mkdir(parents=True, exist_ok=True)
    for old in FRAMES.glob("*.png"):
        old.unlink()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path="/usr/bin/google-chrome",
            args=["--no-sandbox", "--disable-gpu", "--hide-scrollbars"],
        )
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        await page.goto(STUDIO.as_uri())
        await page.wait_for_function("typeof TIMELINE !== 'undefined'")

        # Couper la synthèse vocale du navigateur : la voix vient d'edge-tts
        await page.evaluate("voiceEnabled = false; isPlaying = false;")

        timeline = await page.evaluate("TIMELINE")
        total = await page.evaluate("TOTAL_DURATION")
        n_frames = int(total * FPS)

        for i in range(n_frames):
            t = i / FPS
            data_url = await page.evaluate(
                """(t) => {
                    currentTime = t;
                    updateUI();
                    renderCanvas(getCurrentScene());
                    return document.getElementById('videoCanvas').toDataURL('image/png');
                }""",
                t,
            )
            png = base64.b64decode(data_url.split(",", 1)[1])
            (FRAMES / f"f{i:05d}.png").write_bytes(png)
            if i % 100 == 0:
                print(f"  frame {i}/{n_frames}  (t={t:.1f}s)", flush=True)

        await browser.close()
    return timeline, total, n_frames


def render_voice(timeline):
    """Une piste par scène, décalée à son timecode de départ."""
    AUDIO.mkdir(parents=True, exist_ok=True)
    for old in AUDIO.glob("*"):
        old.unlink()

    tracks = []
    for idx, scene in enumerate(timeline):
        mp3 = AUDIO / f"s{idx:02d}.mp3"
        subprocess.run(
            [
                "edge-tts",
                "--voice",
                VOICE,
                "--text",
                scene["speech"],
                "--write-media",
                str(mp3),
            ],
            check=True,
            capture_output=True,
        )
        tracks.append((int(scene["start"] * 1000), mp3))
        print(
            f"  voix scène {idx + 1}/{len(timeline)} — {scene['speaker']}", flush=True
        )
    return tracks


def mux(tracks, total):
    out = OUTDIR / "JARVIS_OS_TABLE_RONDE.mp4"
    cmd = ["ffmpeg", "-y", "-framerate", str(FPS), "-i", str(FRAMES / "f%05d.png")]
    for _, mp3 in tracks:
        cmd += ["-i", str(mp3)]

    # Chaque voix est retardée à son timecode puis mixée sur une piste unique
    delays = "".join(
        f"[{i + 1}:a]adelay={ms}|{ms}[a{i}];" for i, (ms, _) in enumerate(tracks)
    )
    mixin = "".join(f"[a{i}]" for i in range(len(tracks)))
    filt = f"{delays}{mixin}amix=inputs={len(tracks)}:normalize=0[aout]"

    cmd += [
        "-filter_complex",
        filt,
        "-map",
        "0:v",
        "-map",
        "[aout]",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-t",
        str(total),
        str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return out


def main():
    if not STUDIO.exists():
        sys.exit(f"Studio introuvable : {STUDIO}")
    OUTDIR.mkdir(parents=True, exist_ok=True)

    print("[1/3] Rendu des images du scénario…", flush=True)
    timeline, total, n_frames = asyncio.run(render_frames())

    print("[2/3] Synthèse de la voix off…", flush=True)
    tracks = render_voice(timeline)

    print("[3/3] Assemblage ffmpeg…", flush=True)
    out = mux(tracks, total)

    size = out.stat().st_size / 1_000_000
    print(f"\nVidéo produite : {out}")
    print(f"  {n_frames} images · {total}s · {FPS} fps · {size:.1f} Mo")
    shutil.rmtree(FRAMES, ignore_errors=True)


if __name__ == "__main__":
    main()
