#!/usr/bin/env python3
"""
JARVIS LM ROUTER — Routeur intelligent multi-modèles LM Studio
Branches immédiates :
  --tool / --function   → qwen/qwen3.5-9b  (Function Calling + Reasoning ✅)
  --reason / --deep     → deepseek/deepseek-r1-0528-qwen3-8b (Deep Reasoning)
  --big / --large       → qwen/qwen3.5-35b  (Long context, big tasks)
  --fast / --chat       → hermes-2-pro-mistral-7b  (Texte libre, rapide)
  --embed               → text-embedding-nomic-embed-text-v1.5
  --code                → qwen/qwen3.5-9b  (Code generation)
  (default)             → qwen/qwen3.5-9b
"""

import sys, os, json, urllib.request, urllib.error, argparse

LM_HOST = os.environ.get("LM_HOST", "http://127.0.0.1:1234")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")

# Branche → Modèle LM Studio
BRANCH_MAP = {
    "tool":    "qwen/qwen3.5-9b",
    "function":"qwen/qwen3.5-9b",
    "code":    "qwen/qwen3.5-9b",
    "default": "qwen/qwen3.5-9b",
    "reason":  "deepseek/deepseek-r1-0528-qwen3-8b",
    "deep":    "deepseek/deepseek-r1-0528-qwen3-8b",
    "big":     "qwen/qwen3.5-35b",
    "large":   "qwen/qwen3.5-35b",
    "fast":    "hermes-2-pro-mistral-7b",
    "chat":    "hermes-2-pro-mistral-7b",
    "gpt":     "openai/gpt-oss-20b",
    "embed":   "text-embedding-nomic-embed-text-v1.5",
    # M6 câble direct — tampon + délégation massive
    "m6":      "gemma3:4b",
    "buffer":  "gemma3:4b",
    "delegate":"qwen3:1.7b",
    "tiny":    "tinyllama:1.1b",
}

# IPs Cluster réelles (mises à jour 2026-08-08)
CLUSTER = {
    "local_lmstudio": "http://127.0.0.1:1234",
    "local_ollama":   "http://127.0.0.1:11434",
    "m6_cable":       "http://10.42.0.230:11434",   # câble direct — tampon massif
    "m1_lmstudio":    "http://192.168.1.10:1234",   # heavy GPU (si UP)
    "m4_openai":      "http://192.168.0.10:11235",  # inference secondaire
}

def build_chat_body(model, prompt, tools=None, tool_choice=None, temperature=0.2, max_tokens=1200):
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if tools:
        body["tools"] = tools
        body["tool_choice"] = tool_choice or "auto"
    return body


def build_completion_body(model, prompt, temperature=0.2, max_tokens=900):
    """Fallback /v1/completions — évite le reasoning-runaway sur qwen3.5-9b."""
    return {
        "model": model,
        "prompt": (f"<|im_start|>user\n{prompt}<|im_end|>\n"
                   "<|im_start|>assistant\n<think></think>\n\n"),
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stop": ["<|im_end|>"],
    }


def call_lmstudio_chat(model, prompt, tools=None, tool_choice=None):
    body = build_chat_body(model, prompt, tools=tools, tool_choice=tool_choice)
    req = urllib.request.Request(
        f"{LM_HOST}/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    msg = data["choices"][0]["message"]
    if msg.get("tool_calls"):
        return {"type": "tool_call", "tool_calls": msg["tool_calls"],
                "reasoning": msg.get("reasoning_content", "")}
    return {"type": "text", "content": msg.get("content", ""),
            "reasoning": msg.get("reasoning_content", "")}


def call_lmstudio_completion(model, prompt):
    body = build_completion_body(model, prompt)
    req = urllib.request.Request(
        f"{LM_HOST}/v1/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return {"type": "text", "content": data["choices"][0].get("text", "").strip()}


def call_ollama(model, prompt):
    body = {"model": model, "prompt": prompt, "stream": False, "keep_alive": -1}
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return {"type": "text", "content": data.get("response", "").strip()}


def route_and_call(branch, prompt, tools=None, tool_choice=None, verbose=False):
    model = BRANCH_MAP.get(branch, BRANCH_MAP["default"])

    if verbose:
        print(f"[ROUTER] Branche='{branch}' → Modèle='{model}'", file=sys.stderr)

    try:
        if branch in ("tool", "function", "code") or tools:
            # Function calling via /v1/chat/completions
            result = call_lmstudio_chat(model, prompt, tools=tools, tool_choice=tool_choice)
        elif branch in ("fast", "chat"):
            # Hermes — pas de function calling, réponse directe
            result = call_lmstudio_chat(model, prompt)
        else:
            # Completion mode — évite reasoning-runaway sur qwen
            result = call_lmstudio_completion(model, prompt)
        return model, result

    except urllib.error.URLError as e:
        if verbose:
            print(f"[ROUTER] LM Studio injoignable ({e}) → Fallback Ollama gemma3:4b", file=sys.stderr)
        try:
            result = call_ollama("gemma3:4b", prompt)
            return "gemma3:4b (ollama-fallback)", result
        except Exception as e2:
            return "error", {"type": "error", "content": str(e2)}


def main():
    parser = argparse.ArgumentParser(
        description="JARVIS LM Router — Routeur intelligent multi-modèles LM Studio"
    )
    parser.add_argument("prompt", nargs="?", help="Prompt à envoyer")
    parser.add_argument("--branch", "-b", default="default",
                        choices=list(BRANCH_MAP.keys()),
                        help="Branche de routage (défaut: default → qwen3.5-9b)")
    parser.add_argument("--tool", action="store_true",
                        help="Activer le mode Function Calling (qwen3.5-9b)")
    parser.add_argument("--function", action="store_true",
                        help="Alias --tool")
    parser.add_argument("--reason", action="store_true",
                        help="Mode raisonnement profond (deepseek-r1)")
    parser.add_argument("--big", action="store_true",
                        help="Modèle large (qwen3.5-35b)")
    parser.add_argument("--fast", action="store_true",
                        help="Réponse rapide texte libre (hermes-2-pro)")
    parser.add_argument("--gpt", action="store_true",
                        help="GPT-OSS-20B")
    parser.add_argument("--tools-json", "-T",
                        help="JSON des tools pour function calling (chemin fichier ou string)")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--json-out", "-j", action="store_true",
                        help="Sortie JSON structurée complète")

    args = parser.parse_args()

    # Résoudre la branche
    branch = args.branch
    if args.tool or args.function: branch = "tool"
    elif args.reason: branch = "reason"
    elif args.big: branch = "big"
    elif args.fast: branch = "fast"
    elif args.gpt: branch = "gpt"

    # Lire le prompt
    prompt = args.prompt
    if not prompt and not sys.stdin.isatty():
        prompt = sys.stdin.read().strip()
    if not prompt:
        parser.print_help()
        sys.exit(2)

    # Charger les tools
    tools = None
    if args.tools_json:
        try:
            if os.path.isfile(args.tools_json):
                tools = json.loads(open(args.tools_json).read())
            else:
                tools = json.loads(args.tools_json)
        except Exception as e:
            print(f"[ERROR] tools-json invalide: {e}", file=sys.stderr)
            sys.exit(1)

    model, result = route_and_call(branch, prompt, tools=tools, verbose=args.verbose)

    if args.json_out:
        print(json.dumps({"model": model, "branch": branch, "result": result},
                         ensure_ascii=False, indent=2))
    elif result["type"] == "tool_call":
        calls = result["tool_calls"]
        print(f"[FUNCTION CALL] {model}")
        for tc in calls:
            fn = tc.get("function", tc)
            print(f"  → {fn.get('name', '?')}({fn.get('arguments', '{}')})")
        if result.get("reasoning"):
            print(f"\n[REASONING]\n{result['reasoning'][:300]}...")
    else:
        print(result.get("content", ""))


if __name__ == "__main__":
    main()
