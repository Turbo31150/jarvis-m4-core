#!/usr/bin/env python3
"""
JARVIS Cluster Optimizer — Production Mode
Configure tous les 114 agents OpenClaw avec routing optimal
M2 porteur → M1 fallback → OL1 rapide → kimi cloud overflow
"""
import json, os, subprocess, sys
from pathlib import Path

AGENTS_DIR = Path.home() / ".openclaw/agents"
OPENCLAW_JSON = Path.home() / ".openclaw/openclaw.json"

# Matrice routing par type d'agent
ROUTING = {
    # Reasoning / debug / security → M2 deepseek-r1
    "reasoning": {
        "provider": "lmstudio-m2",
        "model": "deepseek/deepseek-r1-0528-qwen3-8b",
        "agents": [
            "architect-guardian", "omega-security-agent", "jarvis-auditor",
            "code-reviewer", "code-guardian", "jarvis-code-reviewer",
            "pr-review-toolkit:silent-failure-hunter", "pr-review-toolkit:code-reviewer",
            "feature-dev:code-reviewer", "security-reviewer",
            "incident-responder", "jarvis-network-agent",
        ]
    },
    # Dev / implem / refactor → M2 qwen3.5-9b (chargé, rapide)
    "dev": {
        "provider": "lmstudio-m2",
        "model": "qwen/qwen3.5-9b",
        "agents": [
            "omega-dev-agent", "jarvis-auto-improver", "feature-dev:code-architect",
            "feature-dev:code-explorer", "code-simplifier:code-simplifier",
            "pr-review-toolkit:code-simplifier", "omega-analysis-agent",
            "omega-docs-agent", "omega-trading-agent", "omega-voice-agent",
            "plugin-dev:agent-creator", "plugin-dev:plugin-validator",
            "plugin-dev:skill-reviewer", "task-decomposer-prime",
            "jarvis-system-agent", "cowork-dev", "cowork-ai",
            "trading-engine", "ai-engine", "services-data",
        ]
    },
    # Heavy analysis → M1 27b-opus-distilled
    "heavy": {
        "provider": "lmstudio-m1",
        "model": "qwen3.5-27b-claude-4.6-opus-reasoning-distilled-v2",
        "agents": [
            "main", "openclaw-master", "coordinator",
        ]
    },
    # Ops rapides → OL1 qwen3:1.7b (< 1s)
    "fast": {
        "provider": "ollama",
        "model": "qwen3:1.7b",
        "agents": [
            "boot-layer", "cli-tools", "cluster-mgr", "cowork-cluster",
            "cowork-core", "dispatch", "monitoring", "maintenance",
            "system-health-monitor", "cowork-monitoring", "disk-cleaner",
            "service-auditor", "domino-optimizer", "cowork-comms",
            "jarvis-cluster-health", "jarvis-zombie-cleaner", "jarvis-monitor-live",
            "comms", "automation", "cowork-automation",
        ]
    },
    # Cloud overflow → kimi via OL1
    "cloud": {
        "provider": "ollama",
        "model": "kimi-k2.5:cloud",
        "agents": [
            "omega-voice-agent", "social-growth", "business-ops",
            "cowork-comms", "jarvis-browser",
        ]
    },
}

def get_default_model(agent_name):
    """Retourne (provider, model) optimal pour un agent."""
    for tier, cfg in ROUTING.items():
        if agent_name in cfg["agents"]:
            return cfg["provider"], cfg["model"]
    # Default: M2 qwen3.5-9b
    return "lmstudio-m2", "qwen/qwen3.5-9b"

def patch_agent_session(agent_dir, provider, model):
    """Patch sessions.json d'un agent."""
    sessions_file = agent_dir / "sessions" / "sessions.json"
    if not sessions_file.exists():
        return False
    try:
        with open(sessions_file) as f:
            data = json.load(f)
        changed = False
        for key in data:
            s = data[key]
            old_provider = s.get("modelProvider", "")
            old_model = s.get("modelId", "")
            if old_provider != provider or old_model != model:
                s["modelProvider"] = provider
                s["modelId"] = model
                changed = True
        if changed:
            with open(sessions_file, "w") as f:
                json.dump(data, f, indent=2)
        return changed
    except Exception as e:
        return False

def update_openclaw_defaults():
    """Met à jour openclaw.json avec les defaults optimaux."""
    with open(OPENCLAW_JSON) as f:
        config = json.load(f)
    
    # Default model: M2 primary, M1 fallback, OL1 ultra-fast
    config.setdefault("agents", {})
    config["agents"]["defaults"] = {
        "model": {
            "primary": "lmstudio-m2/qwen/qwen3.5-9b",
            "fallbacks": [
                "lmstudio-m1/qwen/qwen3.5-9b",
                "ollama/qwen3:1.7b",
                "ollama/kimi-k2.5:cloud"
            ]
        },
        "contextWindow": 16384,
        "maxTokens": 4096,
        "timeout": 45000,
        "bootstrapMaxChars": 4000,
    }
    
    # Modèles M2 explicites
    config["agents"]["list"] = [
        {"id": "main", "model": "lmstudio-m1/qwen3.5-27b-claude-4.6-opus-reasoning-distilled-v2"},
        {"id": "openclaw-master", "model": "lmstudio-m2/qwen/qwen3.5-9b"},
    ]
    
    # Ensure M2 provider is correctly defined
    config.setdefault("models", {}).setdefault("providers", {})
    config["models"]["providers"]["lmstudio-m2"] = {
        "baseUrl": "http://192.168.1.26:1234/v1",
        "apiKey": "lmstudio",
        "api": "openai",
        "name": "M2 LMStudio — Porteur Central"
    }
    config["models"]["providers"]["lmstudio-m1"] = {
        "baseUrl": "http://127.0.0.1:1234/v1",
        "apiKey": "lmstudio",
        "api": "openai",
        "name": "M1 LMStudio — GPU Power"
    }
    
    with open(OPENCLAW_JSON, "w") as f:
        json.dump(config, f, indent=2)
    print("✅ openclaw.json defaults mis à jour")

def main():
    update_openclaw_defaults()
    
    agents = [d for d in AGENTS_DIR.iterdir() if d.is_dir()]
    patched = 0
    skipped = 0
    
    for agent_dir in agents:
        name = agent_dir.name
        provider, model = get_default_model(name)
        changed = patch_agent_session(agent_dir, provider, model)
        if changed:
            patched += 1
        else:
            skipped += 1
    
    print(f"✅ {patched} agents patchés | {skipped} sans session (nouveau)")
    print()
    
    # Résumé par tier
    print("=== Routing Matrix ===")
    for tier, cfg in ROUTING.items():
        print(f"  [{tier:10}] {cfg['provider']:15} {cfg['model'][:40]:40} → {len(cfg['agents'])} agents")
    
    print(f"\n  [default   ] lmstudio-m2     qwen/qwen3.5-9b → {len(agents)-sum(len(c['agents']) for c in ROUTING.values())} agents restants")

if __name__ == "__main__":
    main()
