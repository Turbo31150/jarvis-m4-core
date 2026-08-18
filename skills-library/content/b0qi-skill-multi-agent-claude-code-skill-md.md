---
name: multi-agent
description: Use when coordinating multiple AI agents (Codex, Gemini) for parallel or collaborative tasks. Invoke with /multi-agent.
user-invocable: true
---

# Multi-Agent Orchestrator Skill

## Overview

This skill coordinates multiple AI agents (Claude Code, Codex, Gemini) for parallel or collaborative tasks. It sits on top of the `/codex` and `/gemini` adapter skills, providing CLI detection, task routing, 3-way parallel worktree management, and graceful degradation.

```
┌─────────────────────────────────────┐
│  multi-agent skill (orchestrator)   │  ← Claude Code reads this
│  - CLI detection & routing          │
│  - Task splitting & ownership       │
│  - 3-way worktree bootstrap         │
│  - Integration gate & merge         │
│  - Graceful degradation             │
├─────────────┬───────────────────────┤
│ codex skill │  gemini skill         │  ← Adapter skills
│ (/codex)    │  (/gemini)            │
└─────────────┴───────────────────────┘
```

## CLI Detection

On first invocation, probe for available agents and record results in `.coord/agents.yaml`:

```bash
# Detect available agents
echo "=== Agent Detection ==="
if codex --version 2>/dev/null; then
  echo "codex: available"
else
  echo "codex: not found"
fi

if gemini --version 2>/dev/null; then
  echo "gemini: available"
else
  echo "gemini: not found"
fi
```

Record results in `.coord/agents.yaml`:

```yaml
detected_at: "<ISO8601>"
agents:
  codex:
    available: true
    version: "<version string>"
  gemini:
    available: true
    version: "<version string>"
```

Re-detect if the user reports a newly installed agent or if a previously available agent fails.

## Agent Routing

Decision tree based on detected agents:

| Codex | Gemini | Routing |
| --- | --- | --- |
| available | available | User chooses or auto-assign based on task type (see Task Assignment Strategy) |
| available | unavailable | Route all external tasks to Codex |
| unavailable | available | Route all external tasks to Gemini |
| unavailable | unavailable | Claude Code works solo — no external agents |

When only one agent is available, inform the user and proceed with the available agent. When neither is available, inform the user that multi-agent mode requires at least one external CLI agent and offer to proceed with Claude Code alone.

## Task Assignment Strategy

Each subtask in `.coord/plan.yaml` gets a `preferred_agent` and `fallback_agent`:

```yaml
subtasks:
  - id: auth-module
    description: "Implement authentication module"
    preferred_agent: codex
    fallback_agent: gemini
    files: [src/auth.ts, src/auth.test.ts]

  - id: design-review
    description: "Review API design for consistency"
    preferred_agent: gemini
    fallback_agent: codex
    files: [docs/api-design.md]

  - id: architecture-decision
    description: "Evaluate caching strategy"
    preferred_agent: dual
    files: [docs/adr-caching.md]
```

### Agent Strengths

| Task Type | Preferred Agent | Rationale |
| --- | --- | --- |
| Large code changes, multi-file refactoring | codex | Strong at structured code generation |
| Test writing and fixing | codex | Good at test patterns |
| Design review, analysis | gemini | Strong at reasoning and constraint analysis |
| Second opinion, cross-validation | gemini | Independent perspective |
| Architecture decisions (high uncertainty) | dual | Both agents provide independent recommendations |

### Dual-Run Mode

For `preferred_agent: dual`, launch both agents with the same prompt independently. Compare their outputs and present both perspectives to the user for a decision. This is useful for high-uncertainty architecture decisions where a second opinion adds value.

## Parallel Worktree Mode (3-Way)

### Branch Naming

```
main ─┬─ cc/<task>  (Claude Code — main worktree, optional)
      ├─ cx/<task>  (Codex worktree)
      └─ gm/<task>  (Gemini worktree)
           ↓ 3-way overlap check
      int/<task> → main
```

### Bootstrap Commands

```bash
# From the project root (main worktree)
BASE_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@')
git switch "$BASE_BRANCH" && git pull

# Create branches (use -f to reset if they already exist from a previous attempt)
git branch -f cc/<task>
git branch -f cx/<task>
git branch -f gm/<task>

# Create worktrees
git worktree add ../<project>-codex cx/<task> 2>/dev/null || \
  echo "Worktree already exists; reusing ../<project>-codex"
git worktree add ../<project>-gemini gm/<task> 2>/dev/null || \
  echo "Worktree already exists; reusing ../<project>-gemini"

# Claude Code stays in the main worktree
git switch cc/<task>

# Ensure .coord/ is gitignored
mkdir -p .coord
grep -qxF '.coord/' .git/info/exclude 2>/dev/null || echo '.coord/' >> .git/info/exclude
```

Only create worktrees for agents that are available and assigned subtasks. If only Codex is available, skip the Gemini worktree (and vice versa).

### Launching Agents

After bootstrap, launch each agent in its worktree using the appropriate adapter skill:

```bash
# Codex (has -C flag)
codex exec -C ../<project>-codex --skip-git-repo-check \
  -m gpt-5.3-codex --config model_reasoning_effort="high" \
  --sandbox workspace-write --full-auto \
  "<task package prompt>" 2>/dev/null

# Gemini (no -C flag, use subshell cd)
(cd ../<project>-gemini && gemini -m gemini-3-pro-preview \
  --approval-mode auto_edit -y \
  -p "<task package prompt>" 2>/dev/null)
```

### Integration Gate (3-Way Overlap Check)

Before merging, check all three pairs for file overlap:

```bash
BASE_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@')

echo "=== cc/cx overlap ==="
comm -12 \
  <(git diff --name-only "$BASE_BRANCH"...cc/<task> | sort) \
  <(git diff --name-only "$BASE_BRANCH"...cx/<task> | sort)

echo "=== cc/gm overlap ==="
comm -12 \
  <(git diff --name-only "$BASE_BRANCH"...cc/<task> | sort) \
  <(git diff --name-only "$BASE_BRANCH"...gm/<task> | sort)

echo "=== cx/gm overlap ==="
comm -12 \
  <(git diff --name-only "$BASE_BRANCH"...cx/<task> | sort) \
  <(git diff --name-only "$BASE_BRANCH"...gm/<task> | sort)
```

If **any** overlap is found, stop and resolve ownership before proceeding.

### Integration Merge

```bash
# Create integration branch
git switch -c int/<task> "$BASE_BRANCH"

# Merge in order: Claude Code first, then Codex, then Gemini
git merge --no-ff cc/<task>
git merge --no-ff cx/<task>
git merge --no-ff gm/<task>

# Run tests, resolve conflicts if any
# If clean: merge int/<task> into $BASE_BRANCH
```

Skip the merge step for any agent that was not assigned work or is unavailable.

### Cleanup

After successful integration:

```bash
git worktree remove ../<project>-codex 2>/dev/null
git worktree remove ../<project>-gemini 2>/dev/null
git branch -d cc/<task> cx/<task> gm/<task> int/<task>
rm -rf .coord/
```

## Unified Task Package Dispatch

The multi-agent skill uses the same Task Package format as the adapter skills, with an added `Agent` field:

```
[Task Package]
Agent: codex | gemini
Goal:
- <single-sentence goal>

Mode: parallel
Branch: <cx/<task> or gm/<task>>
Worktree: <worktree path>

Files:
- <explicit file list>

Ownership:
- <agent>: <file globs this agent may edit>
- DO NOT TOUCH: <file globs reserved for other agents>

Constraints:
- <non-functional requirements, style rules, time limits, deps>

Acceptance Criteria:
- <observable outcomes>
- <tests to run or checks to pass>

Notes:
- <assumptions, risk areas, or context snapshots>
```

The orchestrator translates the `Agent` field to the correct CLI invocation by delegating to the appropriate adapter skill (`/codex` or `/gemini`).

## Graceful Degradation

### Detection

Agent availability is recorded in `.coord/agents.yaml` during CLI Detection. If an agent becomes unavailable mid-task (e.g., crashes, auth expires), the orchestrator detects this via non-zero exit codes.

### Reassignment

When a preferred agent is unavailable:

1. Check the subtask's `fallback_agent` in `.coord/plan.yaml`.
2. If the fallback is available, reassign the subtask to it.
3. If no external agent is available, Claude Code handles the subtask directly.
4. Log the degradation event in `.coord/events.jsonl`:

```json
{"ts":"<ISO8601>","from":"multi-agent","type":"degradation","subtask":"<id>","original_agent":"gemini","reassigned_to":"codex","reason":"gemini not found"}
```

### Degradation Modes

| Scenario | Behavior |
| --- | --- |
| One agent missing at bootstrap | Skip its worktree, reassign subtasks |
| Agent fails mid-task | Reassign remaining work to fallback |
| Both agents missing | Claude Code works solo, inform user |
| Agent returns after failure | User can re-invoke `/multi-agent` to re-detect |

## Coordination Protocol (`.coord/`)

The multi-agent skill extends the existing `.coord/` coordination directory:

| File | Purpose |
| --- | --- |
| `.coord/plan.yaml` | Task split, subtask assignments (with `preferred_agent` and `fallback_agent`), file ownership |
| `.coord/agents.yaml` | Detected agent availability and versions |
| `.coord/claims.yaml` | Active file/module claims per agent |
| `.coord/sessions.jsonl` | Session registry (shared across all agents, uses `agent` field) |
| `.coord/events.jsonl` | Append-only event log (handoff, blocked, done, degradation) |

### Event Types

All existing event types apply (`started`, `done`, `blocked`, `handoff`, `claim`, `release`), plus:

- `degradation` — agent unavailable, subtask reassigned
- `detection` — agent CLI detection result

## File Ownership Rules

- Each file/directory is assigned to **exactly one agent** during the Plan phase.
- Shared files (e.g., routes, schemas, lockfiles, config) must be flagged as **"serial handoff"** — only one agent may edit them at a time, with an explicit handoff.
- If an agent discovers it needs to modify a file owned by another agent, it must **stop and signal** rather than edit directly.
- In 3-way parallel mode, ownership is tracked across all three agents (Claude Code, Codex, Gemini).

## Cross-References

- For Codex execution details, CLI flags, and sandbox modes, see the `/codex` skill.
- For Gemini execution details, approval modes, and session management, see the `/gemini` skill.
- Session registry schema is documented in the `/codex` skill under "Session Registry".

## Error Handling

- If CLI detection fails for all agents, inform the user and offer to proceed with Claude Code alone.
- If worktree creation fails, fall back to serial mode with available agents.
- If integration merge has conflicts, stop and present the conflicts to the user for resolution.
- Log all errors and degradation events in `.coord/events.jsonl`.
- **Timeout recovery**: check `.coord/sessions.jsonl` for `status: running` entries across all agents. Resume each using the appropriate adapter skill's Resume Protocol.

## Workflow Summary

```
1. Detect       Run CLI detection for codex and gemini.
                Record in .coord/agents.yaml.

2. Plan         Analyze task, split into subtasks,
                assign preferred_agent + fallback per subtask,
                assign file ownership.

3. Bootstrap    Create branches and worktrees for available agents:
                cc/<task>, cx/<task>, gm/<task>

4. Dispatch     Send Task Packages to each agent via adapter skills.
                Claude Code works in main worktree.
                Codex works in ../<project>-codex.
                Gemini works in ../<project>-gemini.

5. Monitor      Check .coord/events.jsonl for completion/blockers.
                Handle degradation if an agent fails.

6. Integrate    3-way overlap check, then sequential merge into int/<task>.
                Run tests on integration branch.

7. Accept       Review integrated result, merge to main, cleanup.
```
