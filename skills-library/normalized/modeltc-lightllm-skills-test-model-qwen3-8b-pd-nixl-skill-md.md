---
id: modeltc-lightllm-skills-test-model-qwen3-8b-pd-nixl-skill-md
name: "test-model-qwen3-8b-pd-nixl"
author: "ModelTC"
repository: "https://github.com/ModelTC/LightLLM/tree/main/skills/test_model/qwen3-8b-pd-nixl"
skill_url: "https://skillsmp.com/creators/modeltc/lightllm/skills-test-model-qwen3-8b-pd-nixl"
stars: 4207
verified: false
quality_score: 100
security_score: 20
status: "DANGEROUS"
collected_at: "2026-08-07T17:30:15.182680"
---

# Résumé
LightLLM Qwen3-8b PD disaggregation gsm8k: pd_master on 8089, prefill on 8001, decode on 8002, tp 2 each. Assign four GPUs via nvidia-smi then export PREFILL_CUDA_DEVICES / DECODE_CUDA_DEVICES (no fixed card IDs; no complex shell automation). UCX_NET_DEVICES and TLS for RDMA per cluster. lm_eval hits pd_master URL. HOST vs PD_MASTER_IP when co-located. Before lm_eval, must POST one completion via curl to pd_master for warmup verification. Requires LOG_DIR, MODEL_DIR, proxy cleared, no_proxy, summary.txt. Same-GPU model_infer + pd_*_trans need NVIDIA MPS for best KV copy perf; record MPS on/off in summary. Run check_nvidia_peermem.sh in this skill dir; record in summary.txt. Use for PD separation tests with either NIXL transport or the default NCCL transport.

# Objectif
Skill d'automatisation/intégration pour test-model-qwen3-8b-pd-nixl.

# Déclencheurs d’utilisation
Mots-clés associés: test-model-qwen3-8b-pd-nixl, ModelTC

# Procédure
Consulter le dépôt source: https://github.com/ModelTC/LightLLM/tree/main/skills/test_model/qwen3-8b-pd-nixl

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
