#!/usr/bin/env python3
"""gemini-interactions.py — CLI Interactions API Google Gemini pour JARVIS.

Usage:
    python3 gemini-interactions.py "Quelle est la situation météo ?"
    python3 gemini-interactions.py --stream "Explique l'informatique quantique"
    python3 gemini-interactions.py --prev-id <id> "Et ensuite ?"
    python3 gemini-interactions.py --agent antigravity-preview-05-2026 "Génère un script de benchmark"
    python3 gemini-interactions.py --agent deep-research-preview-04-2026 "Fais une veille sur les LLMs 2026"
    echo "Mon texte" | python3 gemini-interactions.py
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Ajouter le workspace au PYTHONPATH
workspace_dir = Path(__file__).resolve().parent.parent / "Workspaces" / "jarvis-linux"
if workspace_dir.exists():
    sys.path.insert(0, str(workspace_dir))
sys.path.insert(0, "/home/pamerys/Workspaces/jarvis-linux")

try:
    from google import genai
    GENAI_SDK = True
except ImportError:
    GENAI_SDK = False

try:
    from src.gemini_provider import get_gemini
    PROVIDER = True
except ImportError:
    PROVIDER = False


def main():
    parser = argparse.ArgumentParser(description="JARVIS Gemini Interactions API Bridge")
    parser.add_argument("prompt", nargs="*", help="Prompt ou question")
    parser.add_argument("--model", "-m", default="gemini-3.7-flash", help="Modèle (gemini-3.7-flash, gemini-3.5-flash-lite, gemini-3.1-pro-preview)")
    parser.add_argument("--agent", "-a", default=None, help="Agent managé (antigravity-preview-05-2026, deep-research-preview-04-2026)")
    parser.add_argument("--prev-id", "--previous-id", default=None, help="ID de l'interaction précédente (session multi-tours)")
    parser.add_argument("--system", "-s", default=None, help="Instruction système")
    parser.add_argument("--stream", action="store_true", help="Activer le streaming SSE")
    parser.add_argument("--json", action="store_true", help="Sortie JSON structurée avec métadonnées")
    parser.add_argument("--env", default="remote", help="Environnement agent managé")
    parser.add_argument("--background", action="store_true", help="Exécution en arrière-plan")

    args = parser.parse_args()

    # Lecture du prompt (args ou stdin)
    prompt = " ".join(args.prompt).strip()
    if not prompt and not sys.stdin.isatty():
        prompt = sys.stdin.read().strip()

    if not prompt:
        print("Erreur: prompt vide", file=sys.stderr)
        sys.exit(1)

    api_key = os.getenv("GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY_TURBO", "")
    client = genai.Client(api_key=api_key) if (GENAI_SDK and api_key) else (genai.Client() if GENAI_SDK else None)

    if not client or not hasattr(client, "interactions"):
        # Fallback via gemini_provider
        if PROVIDER:
            import asyncio
            gp = get_gemini()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            res = loop.run_until_complete(gp.chat(prompt, model=args.model, system=args.system))
            if args.json:
                print(json.dumps(res, indent=2, ensure_ascii=False))
            else:
                print(res.get("text", ""))
            return
        else:
            print("Erreur: google-genai SDK Interactions API non disponible.", file=sys.stderr)
            sys.exit(1)

    t0 = time.time()

    # Gestion Streaming
    if args.stream and not args.agent:
        try:
            stream = client.interactions.create(
                model=args.model,
                input=prompt,
                previous_interaction_id=args.prev_id,
                system_instruction=args.system,
                stream=True,
            )
            for event in stream:
                if getattr(event, "event_type", "") == "step.delta":
                    delta = getattr(event, "delta", None)
                    if delta and getattr(delta, "type", "") == "text":
                        sys.stdout.write(getattr(delta, "text", ""))
                        sys.stdout.flush()
            print()
            return
        except Exception as e:
            print(f"Erreur streaming: {e}", file=sys.stderr)
            sys.exit(1)

    # Gestion Interaction standard / Agent
    params = {"input": prompt}
    if args.agent:
        params["agent"] = args.agent
        if args.env:
            params["environment"] = args.env
        if "deep-research" in args.agent:
            params["background"] = True
    else:
        params["model"] = args.model

    if args.prev_id:
        params["previous_interaction_id"] = args.prev_id

    if args.system:
        params["system_instruction"] = args.system

    if args.background:
        params["background"] = True

    try:
        interaction = client.interactions.create(**params)

        # Si Deep Research en background → polling
        if args.agent and "deep-research" in args.agent and getattr(interaction, "status", "") != "completed":
            inter_id = interaction.id
            if not args.json:
                print(f"[DEEP-RESEARCH] Analyse lancée (ID: {inter_id}). En attente...", file=sys.stderr)
            while True:
                time.sleep(10)
                interaction = client.interactions.get(inter_id)
                if interaction.status == "completed":
                    break
                elif interaction.status in ("failed", "cancelled"):
                    print(f"Erreur Deep Research ({interaction.status}): {getattr(interaction, 'error', '')}", file=sys.stderr)
                    sys.exit(1)

        dur_ms = round((time.time() - t0) * 1000, 1)

        out_text = getattr(interaction, "output_text", "") or ""
        usage = getattr(interaction, "usage", None)
        tokens_in = getattr(usage, "prompt_tokens", 0) or 0 if usage else 0
        tokens_out = getattr(usage, "completion_tokens", 0) or getattr(usage, "total_tokens", 0) or 0 if usage else 0

        if args.json:
            data = {
                "interaction_id": getattr(interaction, "id", ""),
                "status": getattr(interaction, "status", "completed"),
                "model": args.model if not args.agent else None,
                "agent": args.agent,
                "output_text": out_text,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "duration_ms": dur_ms,
            }
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(out_text)

    except Exception as e:
        print(f"Erreur Interactions API: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
