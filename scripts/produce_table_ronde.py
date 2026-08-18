#!/usr/bin/env python3
"""
Production complète de « JARVIS OS : DE LA MACHINE BRIDÉE À L'IA SOUVERAINE ».

Chaîne : casting vocal edge-tts (3 voix) → mesure des durées réelles →
rendu déterministe du canvas image par image → sous-titres SRT calés sur
l'audio réel → assemblage ffmpeg en MP4.

Tout est local. Aucun service payant.
"""

import asyncio
import base64
import shutil
import subprocess
from pathlib import Path

STUDIO = Path("/home/pamerys/jarvis/scripts/studio_v2_table_ronde.html")
OUT = Path("/home/pamerys/Bureau/production_video_jarvis")
FRAMES = OUT / "frames_v2"
AUDIO = OUT / "audio_v2"
FPS = 20

# Casting vocal : une voix distincte par personnage (voix, débit, hauteur)
VOICES = {
    "marc": ("fr-FR-HenriNeural", "-8%", "-3Hz"),  # fatigué, débit lent
    "turbo": ("fr-FR-RemyMultilingualNeural", "+0%", "+0Hz"),  # posé, chirurgical
    "board": ("fr-FR-VivienneMultilingualNeural", "-6%", "-8Hz"),  # synthétique, grave
}


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(out.stdout.strip())


def synth_voices(timeline: list) -> list:
    """Une piste par réplique, avec la voix du personnage."""
    AUDIO.mkdir(parents=True, exist_ok=True)
    for old in AUDIO.glob("*"):
        old.unlink()

    durations = []
    for i, cue in enumerate(timeline):
        voice, rate, pitch = VOICES[cue["voice"]]
        raw = AUDIO / f"c{i:02d}_raw.mp3"
        subprocess.run(
            [
                "edge-tts",
                "--voice",
                voice,
                # Forme --opt=valeur obligatoire : argparse prendrait « -8% » pour une option
                f"--rate={rate}",
                f"--pitch={pitch}",
                "--text",
                cue["text"],
                "--write-media",
                str(raw),
            ],
            check=True,
            capture_output=True,
        )

        final = AUDIO / f"c{i:02d}.mp3"
        if cue["voice"] == "board":
            # Traitement « entité IA » : chorus léger + réverbération de grande salle
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-v",
                    "error",
                    "-i",
                    str(raw),
                    "-af",
                    "chorus=0.6:0.9:50|60:0.4|0.32:0.25|0.4:2|1.3,"
                    "aecho=0.8:0.85:180|340:0.35|0.22",
                    str(final),
                ],
                check=True,
                capture_output=True,
            )
            raw.unlink()
        else:
            raw.rename(final)

        d = probe_duration(final)
        durations.append(d)
        print(
            f"  [{i + 1:2d}/{len(timeline)}] {cue['short']:<5} {d:5.1f}s  {voice}",
            flush=True,
        )
    return durations


def write_srt(timeline: list, durations: list) -> Path:
    """Sous-titres calés sur l'audio réel, 2 lignes de 42 caractères max."""

    def ts(sec: float) -> str:
        h = int(sec // 3600)
        m = int(sec % 3600 // 60)
        s = int(sec % 60)
        ms = int(round((sec - int(sec)) * 1000))
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    def wrap(txt: str, width: int = 42) -> list:
        lines, cur = [], ""
        for w in txt.split():
            if len(cur) + len(w) + 1 > width:
                lines.append(cur)
                cur = w
            else:
                cur = f"{cur} {w}".strip()
        lines.append(cur)
        return lines

    blocks, idx = [], 1
    for cue, dur in zip(timeline, durations):
        lines = wrap(cue["text"])
        groups = [lines[i : i + 2] for i in range(0, len(lines), 2)]
        total_chars = sum(len(" ".join(g)) for g in groups) or 1
        t = cue["start"]
        for g in groups:
            end = t + dur * (len(" ".join(g)) / total_chars)
            blocks.append(f"{idx}\n{ts(t)} --> {ts(end)}\n" + "\n".join(g) + "\n")
            idx += 1
            t = end

    srt = OUT / "sous_titres" / "JARVIS_OS_FR.srt"
    srt.parent.mkdir(parents=True, exist_ok=True)
    srt.write_text("\n".join(blocks), encoding="utf-8")
    return srt


def mux(timeline: list) -> Path:
    out = OUT / "JARVIS_OS_MACHINE_BRIDEE_VERS_IA_SOUVERAINE.mp4"
    tracks = [
        (int(c["start"] * 1000), AUDIO / f"c{i:02d}.mp3")
        for i, c in enumerate(timeline)
    ]

    cmd = [
        "ffmpeg",
        "-y",
        "-v",
        "error",
        "-framerate",
        str(FPS),
        "-i",
        str(FRAMES / "f%05d.png"),
    ]
    for _, mp3 in tracks:
        cmd += ["-i", str(mp3)]

    delays = "".join(
        f"[{i + 1}:a]adelay={ms}|{ms}[a{i}];" for i, (ms, _) in enumerate(tracks)
    )
    mixin = "".join(f"[a{i}]" for i in range(len(tracks)))
    filt = f"{delays}{mixin}amix=inputs={len(tracks)}:normalize=0,dynaudnorm[aout]"

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
        "-r",
        str(FPS),
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        str(out),
    ]
    subprocess.run(cmd, check=True)
    return out


async def run() -> None:
    from playwright.async_api import async_playwright

    OUT.mkdir(parents=True, exist_ok=True)
    FRAMES.mkdir(parents=True, exist_ok=True)
    for old in FRAMES.glob("*.png"):
        old.unlink()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path="/usr/bin/google-chrome",
            args=[
                "--no-sandbox",
                "--disable-gpu",
                "--hide-scrollbars",
                "--force-device-scale-factor=1",
            ],
        )
        page = await browser.new_page(viewport={"width": 1400, "height": 820})
        await page.goto(STUDIO.as_uri())
        await page.wait_for_function("typeof renderAt === 'function'")

        # Le studio est l'unique source de vérité du scénario
        timeline = await page.evaluate("TIMELINE")
        total = await page.evaluate("TOTAL_DURATION")
        print(f"Scénario : {len(timeline)} répliques · {total // 60:.0f} min\n")

        print("[1/4] Casting vocal (3 voix)…", flush=True)
        durations = await asyncio.to_thread(synth_voices, timeline)

        print("\n[2/4] Sous-titres synchronisés…", flush=True)
        print(f"  {write_srt(timeline, durations)}", flush=True)

        print("\n[3/4] Rendu des images…", flush=True)
        await page.evaluate("(d) => setDurations(d)", durations)
        n = int(total * FPS)
        for i in range(n):
            data_url = await page.evaluate(
                "(t) => { renderAt(t); "
                "return document.getElementById('videoCanvas').toDataURL('image/png'); }",
                i / FPS,
            )
            (FRAMES / f"f{i:05d}.png").write_bytes(
                base64.b64decode(data_url.split(",", 1)[1])
            )
            if i % 500 == 0:
                print(f"  image {i}/{n}  ({i / FPS:.0f}s / {total}s)", flush=True)
        await browser.close()

    print("\n[4/4] Assemblage ffmpeg…", flush=True)
    video = mux(timeline)
    print(f"\nVidéo : {video}")
    print(
        f"  {n} images · {total} s · {FPS} fps · "
        f"{video.stat().st_size / 1_000_000:.1f} Mo"
    )
    shutil.rmtree(FRAMES, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(run())
