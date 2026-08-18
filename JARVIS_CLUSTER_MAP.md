# JARVIS OS — Carte Mentale du Cluster (17/08/2026)

```mermaid
mindmap
  root((JARVIS OS CLUSTER))
    M4_Local_Orchestrateur
      Role: Gestion, Decidion, Orchestration
      Statut: OK (Load 0.4)
      Hardware: RTX 3050 (4GB)
      Local_API: 127.0.0.1 (Ports 9761, 18800)
    M1_M6_Inference_Lourde
      Connection: USB-C ASIX (10.42.0.230)
      Statut: DEGRADE (Load 10-10, IO Wait 40%)
      Hardware: RTX 3080 (10GB), RTX 2060 (12GB)
      Role: LLM Qwen, LMStudio, Connecteurs Gitmore
      Problèmes_Persistants:
        - Xorg (PID 3433) persiste malgré kill -9 et redémarrage GDM.
        - llama-server redémarre automatiquement, consomme beaucoup de RAM/CPU.
        - Forte I/O Wait (40%), swapping actif (kswapd0).
        - Nécessite un diagnostic approfondi sur place ou une investigation de la configuration LM Studio/swapping.
    Remi_ASUS_Embeddings
      Statut: OK (SSH via Tailscale)
      Hardware: Ollama UP
      Modeles: gemma3:27b, Embeddings 768dim
    M3_Ollama_Fallback
      IP: 192.168.1.113
      Statut: UP
      Role: Fallback Ollama
    Infrastructure_Bridges
      Port_9742: Whisper Bridge (Proxy 9743)
      Port_18800: Chat Proxy (Telegram/LLM)
      Port_4173: Lumen Vite Dev
      Port_3001: Jarvis Lumen Token
    Moisson_Claude_Code
      Statut: En cours (lancée en arrière-plan avec agy)
      Source: /home/pamerys/jarvis/data/questions-claude-code.txt
      Destination: /home/pamerys/jarvis/data/moisson-claude-code/RAPPORT.md
```

## État des lieux et Recommandations
- **M1 (10.42.0.230)** est en souffrance I/O et les processus `Xorg` et `llama-server` (LM Studio) ne peuvent être contrôlés à distance via `kill -9` ou `systemctl restart gdm`. Le problème nécessite une investigation plus approfondie sur M1, potentiellement via accès physique ou en examinant les scripts de démarrage/surveillance qui relancent ces services.
- **Claude Code** est prêt dans `/home/pamerys/.local/bin/claude`.
- **Connectivité** : Le lien USB-C vers M1 est ultra-stable (1.4ms).
- La moisson de données sur Claude Code est en cours d'exécution en arrière-plan. Un rapport consolidé sera généré.
