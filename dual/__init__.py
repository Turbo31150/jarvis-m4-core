"""JARVIS DUAL ORCHESTRATOR — couche d'orchestration à deux workers.

Modules :
  providers  adapters backends (LM Studio, Ollama) — seule couche qui connaît une URL
  config     découverte + configuration centralisée
  worker     unité d'exécution observable (heartbeat, retry classifié)
  dispatcher modes single/parallel/cascade/review/fallback/pipeline + agrégation
  checkpoint persistance des jobs et reprise
  journal    événements JSONL (board, replay, preuve de parallélisme)
  doctor     diagnostic global CAUSE/IMPACT/ACTION
  benchmark  mesures et verdict DUAL_PARALLEL
  board      vue d'état + replay
  watchdog   détection des jobs figés et workers silencieux
"""

__version__ = "0.1.0"
