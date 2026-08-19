[assistant] API Error: 400 Error from provider(m6-direct,qwen/qwen3.5-9b: 400): {
    "error": {
        "message": "Failed to load model \"qwen/qwen3.5-9b\". Error: Engine protocol runtime llama-server for 3pq3PD6vBsidy7Tj0lY3vqnG exited before becoming healthy. exitCode=1, signal=null",
        "type": "invalid_request_error",
        "param": "model",
        "code": null
    }
}Error: Error from provider(m6-direct,qwen/qwen3.5-9b: 400): {
    "error": {
        "message": "Failed to load model \"qwen/qwen3.5-9b\". Error: Engine protocol runtime llama-server for 3pq3PD6vBsidy7Tj0lY3vqnG exited before becoming healthy. exitCode=1, signal=null",
        "type": "invalid_request_error",
        "param": "model",
        "code": null
    }
}
    at qn (/home/pamerys/.local/lib/node_modules/@musistudio/claude-code-router/dist/cli.js:582:7451)
    at fD (/home/pamerys/.local/lib/node_modules/@musistudio/claude-code-router/dist/cli.js:582:11338)
    at process.processTicksAndRejections (node:internal/process/task_queues:103:5)
    at async cN (/home/pamerys/.local/lib/node_modules/@musistudio/claude-code-router/dist/cli.js:582:8659)

[user] export OPENAI_BASE_URL=http://10.42.0.1:1234/v1 && export LM_STUDIO_HOST=http://10.42.0.1:1234export OPENAI_BASE_URL=http://127.0.0.1:11434/v1 && export OLLAMA_HOST=http://127.0.0.1:11434echo '[JARVIS-OMEGA] Systems fully connected'

[assistant] ```bash
export OPENAI_BASE_URL=http://10.42.0.1:1234/v1 && export LM_STUDIO_HOST=http://10.42.0.1:1234
export OPENAI_BASE_URL=http://127.0.0.1:11434/v1 && export OLLAMA_HOST=http://127.0.0.1:11434
echo '[JARVIS-OMEGA] Systems fully connected'
```