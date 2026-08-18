#!/usr/bin/env python3
"""
biblio_infinite_expansion.py — Générateur 1,000,000 cycles pour la Bibliothèque Vivante.
Génère et injecte des milliers de sujets ultra-spécifiques dans biblio_topics.
"""

import sqlite3
import os
import sys
import time

DB_PATH = os.path.expanduser("~/jarvis/jarvis_master.db")

DOMAINS_INFINITE = {
    "LLM Architecture & Training 2026": [
        "LLaMA 3.2 11B & 90B Vision Architecture",
        "Mistral Large 2 & NeMo Inference",
        "Qwen 2.5 Coder 32B Benchmark & Fine-tuning",
        "DeepSeek V3 Multi-Head Latent Attention",
        "FlashAttention v3 Triton Assembly",
        "KV Cache Quantization FP8 & INT4",
        "Rotary Position Embeddings (YaRN & Dynamic RoPE)",
        "BitNet 1.58-bit Ternary LLMs",
        "RLHF vs DPO vs KTO Alignment Tradeoffs",
        "Direct Preference Optimization at Scale",
        "Grouped Query Attention (GQA) Optimization",
        "Mixture-of-Experts (MoE) Token Routing",
    ],
    "Agentic AI, Swarms & Tool Use": [
        "OpenClaw Engine Multi-Agent Protocol",
        "AutoGPT v2 Multi-Agent Swarm Orchestration",
        "LangGraph Async State Machine Agents",
        "CrewAI Hierarchical Agent Delegations",
        "Function Calling JSON Schema Strict Validation",
        "Tool Use Error Recovery & Retry Loops",
        "Agentic RAG with Self-Correction Loops",
        "Multi-Agent Consensus & Voting Mechanisms",
    ],
    "RAG, Vector DBs & Graph Knowledge": [
        "Nomic Embeddings v1.5 Matryoshka Layer Compression",
        "BGE-M3 Multi-Function Retrieval",
        "Cohere Rerank v3 Precision Rescoring",
        "GraphRAG Entity & Relation Extraction",
        "Qdrant HNSW Vector Index Tuning",
        "Milvus Distributed Cluster Sharding",
        "ChromaDB Persistent SQLite Backend",
        "pgvector Indexing (HNSW vs IVFFlat)",
    ],
    "Linux Systems, High Performance & eBPF": [
        "eBPF Network Packet Filtering & XDP",
        "io_uring Async File I/O Engine",
        "Linux Memory Cgroups v2 OOM Killer Tuning",
        "Btrfs Transparent Compression & Snapshots",
        "Systemd Hardening & PrivateTmp Sandboxing",
        "CPU Affinity & NUMA Node Binding",
        "ZFS ZPOOL RAIDZ2 Performance Tuning",
        "nftables Custom Packet Inspection",
    ],
    "GPU Hardware, CUDA & Acceleration": [
        "NVIDIA TensorRT 10.x FP8 Inference",
        "CUDA C++ Shared Memory & Warp Shuffles",
        "Triton GPU Kernel Programming for MatMul",
        "vLLM PagedAttention v2 Mechanics",
        "BitsAndBytes INT8/INT4 Quantization",
        "NVIDIA SMI GPU Thermal Throttling Control",
        "Multi-GPU NVLink Interconnect Scaling",
        "AMD ROCm 6.x PyTorch Integration",
    ],
    "Cloud Native, Kubernetes & DevOps": [
        "Docker Swarm Service Rolling Updates",
        "K3s Kubernetes High Availability Control Plane",
        "Cilium CNI eBPF Service Mesh",
        "ArgoCD GitOps Continuous Delivery",
        "Prometheus & Grafana AlertManager Integration",
        "Helm v3 Custom Chart Packaging",
        "Podman Rootless Multi-Stage Builds",
        "Terraform Infrastructure as Code Patterns",
    ],
    "Voix, Audio & Realtime STT/TTS": [
        "Whisper Large-v3 Turbo Realtime Streaming",
        "Piper TTS Neural Voice Cloning",
        "Silero VAD v4 Voice Activity Detection",
        "PyAnnote 3.1 Speaker Diarization",
        "Faster-Whisper CTranslate2 FP16 Engine",
        "WebRTC Low-Latency Audio Transports",
    ],
    "Sécurité, Cryptographie & Zero Trust": [
        "OAuth2.1 & OIDC Token Introspection",
        "HashiCorp Vault Dynamic Secrets",
        "Post-Quantum Cryptography (Kyber/Dilithium)",
        "Zero Trust Network Access (ZTNA)",
        "Fail2ban Custom Log Parsers",
        "TLS 1.3 Handshake Optimization",
    ],
    "Automatisation B2B & Prospection": [
        "Cold Email Deliverability (SPF/DKIM/DMARC/BIMI)",
        "Dropcontact & Hunter API Lead Enrichment",
        "n8n Custom Node Building",
        "Notion API Two-Way Sync Engine",
        "LinkedIn Automation Limits & Safety",
        "Mailgun / SendGrid Transactional Ingestion",
    ],
    "PassCerfa, MDPH & Admin FR": [
        "Cerfa 14018*04 Vehicle Registration",
        "Cerfa 15695*01 MDPH Form Processing",
        "FranceConnect v2 OAuth Integration",
        "Chorus Pro PDP Electronic Invoicing",
        "INPI Guichet Unique Business API",
        "URSSAF Auto-Entrepreneur Declaration API",
    ],
}

DIMENSIONS = [
    "Architecture & Conception 2026",
    "Guide d'implémentation pas à pas",
    "Résolution des bogues & pièges critiques",
    "Optimisation extrême & benchmarks",
    "Sécurité & conformité réglementaire",
    "Cas d'usage haute échelle en production",
]

LOT = 2000
SQL_INSERT = (
    "INSERT OR IGNORE INTO biblio_topics "
    "(kind, domain, topic, status, priority, source, created_at) "
    "VALUES ('knowledge', ?, ?, 'pending', 5, 'expansion_infinite_1M', datetime('now'))"
)


def _ecrire_lot(conn, c, lot, essais=6):
    """jarvis_master.db est écrite en continu par le filler, le widget et les
    aspirateurs. En WAL un seul écrivain passe : laisser remonter
    `database is locked` ferait échouer tout le service (c'est ce qui arrivait
    toutes les 2 minutes). On réessaie, et on ne perd au pire que ce lot."""
    for tentative in range(essais):
        try:
            c.executemany(SQL_INSERT, lot)
            conn.commit()
            return max(c.rowcount, 0)
        except sqlite3.OperationalError as e:
            if "locked" not in str(e).lower() and "busy" not in str(e).lower():
                raise
            time.sleep(2.0 * (tentative + 1))
    print("⚠️  lot abandonné : base verrouillée trop longtemps", file=sys.stderr)
    return 0


def run_expansion():
    conn = sqlite3.connect(DB_PATH, timeout=120)
    c = conn.cursor()
    c.execute("PRAGMA busy_timeout=120000")

    # Produit cartésien construit en mémoire : aucune I/O pendant le calcul, donc
    # aucun verrou tenu inutilement. On écrit ensuite par lots courts, ce qui
    # laisse des fenêtres aux autres écrivains — une transaction unique de
    # plusieurs milliers d'INSERT les affamerait.
    sujets = [
        (dom, f"{t} — {dim}")
        for dom, topics in DOMAINS_INFINITE.items()
        for t in topics
        for dim in DIMENSIONS
    ]

    inserted = 0
    for i in range(0, len(sujets), LOT):
        inserted += _ecrire_lot(conn, c, sujets[i : i + LOT])
    skipped = len(sujets) - inserted

    pending_count = c.execute(
        "SELECT count(*) FROM biblio_topics WHERE status='pending'"
    ).fetchone()[0]
    total_count = c.execute("SELECT count(*) FROM biblio_topics").fetchone()[0]
    conn.close()

    print(
        f"🔥 {inserted} nouveaux sujets 1,000,000 cycles ajoutés à la Bibliothèque Vivante."
    )
    print(f"ℹ️  {skipped} sujets existants conservés.")
    print(f"📊 Total sujets en attente ('pending') : {pending_count}")
    print(f"📚 Total sujets dans la base          : {total_count}")


if __name__ == "__main__":
    run_expansion()
