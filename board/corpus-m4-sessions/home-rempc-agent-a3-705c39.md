[user] You are building ONE portfolio piece for a freelance profile on Upwork. The freelancer positions as an "AI Systems & Automation Engineer" specialising in production-grade n8n workflows.

## Your scope — ONLY this
Produce a **resilient, self-hosted n8n workflow** that demonstrates production engineering: error branches, automatic retries with backoff, dead-letter handling, and failure alerting.

Do NOT work on RAG, vector search, or multi-LLM routing — other agents own those. Do not touch any file outside your output directory.

## Ground it in real patterns first
This machine runs a real JARVIS automation stack. Before writing anything, spend a little time looking for existing n8n workflows and automation patterns to anchor on, e.g.:
- `ls ~/jarvis/` and look for n8n-related directories, scripts, or workflow JSON exports
- `grep -ril "n8n" ~/jarvis/scripts/ ~/jarvis/docs/ 2>/dev/null | head -20`
- any n8n backup scripts (there is reportedly a `jarvis-n8n-backup` routine)

Use them to learn the *patterns actually used* (how errors are branched, how alerts are sent). Then write something fresh and generic. Do NOT copy real workflow content.

## HARD CONSTRAINT — anonymisation (non-negotiable)
The output is PUBLIC. It must contain **zero** trace of the owner's real activity:
- no company names, client names, personal names, employee names
- no private IPs (no 192.168.x, 100.x, 10.x), no internal hostnames
- no personal domains or email addresses
- no credentials, tokens, API key

[assistant] I'll start by grounding in the real patterns on this machine, then build the deliverable.

[assistant] Good, plenty of real material. Let me examine the actual workflow exports and backup routine.

[assistant] Now let me extract the *schema patterns* (node types, versions, error settings) from the real workflows without pulling in their content.

[assistant] Let me look at how errors are branched and alerts are sent in the real patterns, plus the retry/backoff conventions.

[assistant] Let me verify current schema details for error-branch and retry constructs against local authoritative references.

[assistant] Found an authoritative n8n node schema DB. Let me query it for exact type versions.

[assistant] Now let me validate the export — JSON structure, n8n schema invariants, and the embedded JavaScript.

[assistant] Graph is clean. Now let me syntax-check the embedded JavaScript and unit-test the failure-classification logic.

[assistant] All Code nodes parse. Now let me behaviourally test the classification and validation logic against real failure scenarios.

[assistant] Escaping issue in my test harness. Let me fix it by separating the code map from the harness.

[assistant] Both hits are benign (the required `example.com` address, and one checkmark glyph). Let me remove the glyph and check for an offline n8n validator.

[assistant] Zero structural errors from n8n's own validator. Let me also run parameter-level validation against the node property schemas.

[assistant] Most are false positives from a validator that doesn't evaluate `displayOptions`. But one claim is load-bearing — let me verify expressions are actually allowed on the Wait node's `amount` field.

[assistant] `noDataExpression` is absent on `amount`, so expressions are permitted — the design holds. Let me check one more webhook detail and harden the expression.

[assistant] Confirmed correct (`multipleMethods` defaults false, so the string form applies). Let me harden the backoff expression defensively.

[assistant] Let me correct two numeric claims in the README so they match the actual configuration exactly.

[assistant] Done. All three deliverables are in `/home/rempc/upwork-portfolio/n8n-resilient-workflow/`.

## What I built

A 21-node n8n workflow, **"Resilient Order Sync"**, with three entry points (webhook, hourly schedule, Error Trigger) and a genuinely modelled failure path:

- **Two-tier retry.** Tier 1 is n8n-native (`retryOnFail`, 3 tries @1s) for blips. Tier 2 is an explicit loop: `onError: continueErrorOutput` → classify → Switch → budget check → `Wait` → back into the HTTP node. 15s→30s→60s with ±20% jitter, 900s ceiling, 4-round budget.
- **Failure classification** that probes `httpCode`/`status`/`response.status`/`cause.*` then falls back to message parsing, because n8n's error shape varies by version. 429 honours `Retry-After` (seconds *and* HTTP-date forms) instead of guessing; permanent 4xx fails fast rather than burning retries.
- **Dead-letter handling with replay.** Three reasons (`schema_validation_failed` / `upstream_rejected` / `retry_budget_exhausted`) with a `replayable` flag, plus an hourly sweep that re-injects records through the same path — a DLQ that is only written to is a logbook, not a queue.
- **Alerting that can't be suppressed.** The DLQ persist node uses `continueRegularOutput` + `alwaysOutputData`, so if the dead-letter store is down the alert still fires *with the payload inlined*. Both the dead-letter path and the crash path emit an identical envelope into one shared notify node.

Two design choices worth flagging: the loop counter is `$runIndex`, not