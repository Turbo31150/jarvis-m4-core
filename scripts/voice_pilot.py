#!/usr/bin/env python3
"""
JARVIS Voice Pilot — full-duplex hands-free.
Loop: mic → openWakeWord("hey jarvis") → VAD record → Whisper → Ollama → Piper TTS → play.
"""

import io
import os
import subprocess
import sys
import time
import wave

import numpy as np
import requests
import sounddevice as sd
from openwakeword.model import Model as OWWModel

OWW_PATH = os.path.expanduser(
    "~/.local/lib/python3.12/site-packages/openwakeword/resources/models/hey_jarvis_v0.1.onnx"
)
WHISPER_URL = "http://127.0.0.1:9743/v1/audio/transcriptions"
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = os.environ.get("JARVIS_LLM", "deepseek-r1:7b")
PIPER_BIN = os.path.expanduser("~/.local/bin/piper")
PIPER_VOICE = "/home/pamerys/Workspaces/jarvis-linux/models/fr_FR-siwis-medium.onnx"
SAMPLE_RATE = 16000
FRAME_MS = 80
FRAME_SAMPLES = SAMPLE_RATE * FRAME_MS // 1000  # 1280
WAKE_THRESHOLD = 0.40
SILENCE_RMS = 180
SILENCE_HOLD = 1.6  # s of silence ends utterance
MAX_RECORD_S = 15
START_GRACE = 1.2  # s minimum recording before silence can end it
SYSTEM_PROMPT = "Tu es JARVIS. Réponds en français, en 1-2 phrases courtes, factuel."


def log(*a):
    print("[voice_pilot]", *a, flush=True)


def say(text: str):
    if not text.strip():
        return
    log("TTS:", text[:120])
    try:
        p1 = subprocess.Popen(
            [PIPER_BIN, "--model", PIPER_VOICE, "--output_raw"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        p2 = subprocess.Popen(
            ["aplay", "-q", "-r", "22050", "-c", "1", "-f", "S16_LE"],
            stdin=p1.stdout,
            stderr=subprocess.DEVNULL,
        )
        p1.stdin.write(text.encode("utf-8"))
        p1.stdin.close()
        p1.stdout.close()
        p2.wait(timeout=30)
    except Exception as e:
        log("TTS error:", e)


def transcribe(pcm16: bytes) -> str:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm16)
    buf.seek(0)
    try:
        r = requests.post(
            WHISPER_URL,
            files={"file": ("utt.wav", buf, "audio/wav")},
            data={"model": "base", "language": "fr"},
            timeout=30,
        )
        return (r.json().get("text") or "").strip()
    except Exception as e:
        log("STT error:", e)
        return ""


def _strip_think(s: str) -> str:
    import re

    return re.sub(r"<think>.*?</think>", "", s, flags=re.DOTALL).strip() or s


def _try_openai_lms(
    base_url: str, model: str, text: str, timeout: int = 90
) -> str | None:
    """LM Studio / OpenAI-compatible chat completion."""
    try:
        r = requests.post(
            f"{base_url}/v1/chat/completions",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT + " /no_think"},
                    {"role": "user", "content": text + " /no_think"},
                ],
                "temperature": 0.4,
                "max_tokens": 400,
                "stream": False,
            },
            timeout=timeout,
        )
        if r.status_code != 200:
            return None
        msg = r.json()["choices"][0]["message"]
        out = (msg.get("content") or "").strip()
        if not out:
            out = (msg.get("reasoning_content") or "").strip()
        return _strip_think(out) if out else None
    except Exception:
        return None


def _try_ollama(text: str) -> str | None:
    try:
        r = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                "stream": False,
                "options": {"temperature": 0.4, "num_predict": 200},
            },
            timeout=180,
        )
        if r.status_code != 200:
            return None
        return _strip_think((r.json().get("message", {}).get("content") or "").strip())
    except Exception:
        return None


def _try_gemini(text: str) -> str | None:
    try:
        out = subprocess.run(
            [
                os.path.expanduser("~/jarvis/scripts/gemini-ask.sh"),
                "--flash",
                f"{SYSTEM_PROMPT}\n\n{text}",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if out.returncode != 0:
            return None
        return (out.stdout or "").strip()
    except Exception:
        return None


def ask_llm(text: str) -> str:
    # Cible primaire = hub LLM unifié :18800 (cascade failover + log domino local)
    log("LLM: hub unifié :18800 (jarvis-auto)…")
    r = _try_openai_lms("http://127.0.0.1:18800", "jarvis-auto", text, timeout=90)
    if r:
        log("LLM via hub")
        return r
    # Fallback direct si le hub est down : M1 → M2 → Ollama OL1 → Gemini Flash
    log("LLM: hub KO → probing M1 (qwen/qwen3.5-9b)…")
    r = _try_openai_lms("http://127.0.0.1:1234", "qwen/qwen3.5-9b", text, timeout=30)
    if r:
        log("LLM via M1")
        return r
    log("LLM: probing M2 (qwen3.5-9b)…")
    r = _try_openai_lms("http://127.0.0.1:18800", "qwen3.5-9b", text, timeout=30)
    if r:
        log("LLM via M2")
        return r
    log("LLM: fallback Ollama OL1…")
    r = _try_ollama(text)
    if r:
        log("LLM via OL1")
        return r
    log("LLM: dernier recours Gemini…")
    r = _try_gemini(text)
    if r:
        log("LLM via Gemini")
        return r
    return "Aucun modèle ne répond."


def record_utterance(stream, max_seconds=MAX_RECORD_S) -> bytes:
    log("→ recording")
    frames = []
    silence_start = None
    start = time.time()
    while True:
        block, _ = stream.read(FRAME_SAMPLES)
        pcm = (
            (block[:, 0] * 32767).astype(np.int16)
            if block.dtype == np.float32
            else block[:, 0].astype(np.int16)
        )
        frames.append(pcm.tobytes())
        rms = float(np.sqrt(np.mean(pcm.astype(np.float32) ** 2)))
        now = time.time()
        if rms < SILENCE_RMS:
            if silence_start is None:
                silence_start = now
            elif now - silence_start > SILENCE_HOLD and now - start > START_GRACE:
                break
        else:
            silence_start = None
        if now - start > max_seconds:
            break
    log(f"← recorded {now - start:.1f}s")
    return b"".join(frames)


def warm_llm():
    try:
        requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": "", "keep_alive": "1h"},
            timeout=10,
        )
        log("LLM préchauffé:", OLLAMA_MODEL)
    except Exception as e:
        log("warm_llm err:", e)


def main():
    log("loading wake-word model…")
    oww = OWWModel(wakeword_model_paths=[OWW_PATH])
    warm_llm()
    log("ready — say 'Hey Jarvis'")
    say("Jarvis en ligne.")

    with sd.InputStream(
        samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=FRAME_SAMPLES
    ) as stream:
        while True:
            block, _ = stream.read(FRAME_SAMPLES)
            audio = block[:, 0].astype(np.int16)
            preds = oww.predict(audio)
            score = preds.get("hey_jarvis_v0.1", 0.0)
            if score > WAKE_THRESHOLD:
                log(f"WAKE score={score:.2f}")
                oww.reset()
                # short ack beep via piper
                say("Oui ?")
                pcm = record_utterance(stream)
                text = transcribe(pcm)
                if not text:
                    say("Je n'ai rien entendu.")
                    continue
                log("USER:", text)
                reply = ask_llm(text)
                log("JARVIS:", reply)
                say(reply)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
