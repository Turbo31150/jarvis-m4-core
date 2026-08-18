[user] # Debug Skill

Help the user debug an issue they're encountering in this current Claude Code session.

## Debug Logging Just Enabled

Debug logging was OFF for this session until now. Nothing prior to this /debug invocation was captured.

Tell the user that debug logging is now active at `/home/turbo/.claude/debug/b6fcbba7-5bf3-431e-8275-05c04f451829.txt`, ask them to reproduce the issue, then re-read the log. If they can't reproduce, they can also restart with `claude --debug` to capture logs from startup.

## Session Debug Log

The debug log for the current session is at: `/home/turbo/.claude/debug/b6fcbba7-5bf3-431e-8275-05c04f451829.txt`

No log file exists yet.

For additional context, grep for [ERROR] and [WARN] lines across the full file.

## Daemon

The background daemon manages `& <prompt>` jobs and `claude agents`. If the issue involves background sessions, look here.

### daemon.lock
```json
{
  "pid": 31012,
  "version": "2.1.220",
  "jsonPath": "/home/turbo/.claude/daemon.json",
  "logPath": "/home/turbo/.claude/daemon.log",
  "startedAt": 1785789978872,
  "origin": "transient",
  "spawnedBy": {
    "label": "claude",
    "cwd": "/home/turbo/jarvis",
    "pid": 27569
  },
  "procStart": "8657",
  "launchTarget": "/home/turbo/.local/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe",
  "processWrapper": ""
}
```

### daemon.status.json
```json
{
  "supervisorPid": 31012,
  "supervisorProcStart": "8657",
  "writtenAt": 1785789978977,
  "workers": {}
}
```



[assistant] API Error: 400 {"error":"Engine protocol predict request returned 400: {\"error\":{\"code\":400,\"message\":\"request (15589 tokens) exceeds the available context size (4096 tokens), try increasing it\",\"type\":\"exceed_context_size_error\",\"n_prompt_tokens\":15589,\"n_ctx\":4096}}"}

[assistant] API Error: 400 {"error":"Engine protocol predict request returned 400: {\"error\":{\"code\":400,\"message\":\"request (15591 tokens) exceeds the available context size (4096 tokens), try increasing it\",\"type\":\"exceed_context_size_error\",\"n_prompt_tokens\":15591,\"n_ctx\":4096}}"}