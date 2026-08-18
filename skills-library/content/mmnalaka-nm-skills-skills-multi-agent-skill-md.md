---
name: multi-agent
description: Use when a task has independent parallel concerns — decomposes into subagents with a dispatch plan approved before execution.
---

# Multi-Agent

Decompose complex tasks into parallel subagent work. Use when multiple independent concerns need to be addressed simultaneously.

**Recommended model:** Opus (orchestration reasoning)

---

## When to Use

Use multi-agent dispatch when:
- 3+ independent files or modules need changes with no shared state
- Multiple concerns need investigation at the same time (security + performance + correctness)
- A task has clear subtask boundaries that can be verified independently

Do NOT dispatch agents when:
- Subtasks share files they will both write to (race condition on changes)
- One subtask's output is required as input for another (sequence instead)
- The task is simple enough for a single focused response

## Rules

### 1. Identify independent subtasks

Before dispatching, list subtasks and verify independence:
- No shared file writes
- No data dependency between subtasks
- Each subtask has a clear, verifiable output

### 2. Assign model per subtask

| Task type | Model |
|-----------|-------|
| Simple lookup, convention check, formatting | Haiku |
| Feature implementation, refactoring, test writing | Sonnet |
| Architecture review, complex orchestration, security audit | Opus |

### 3. Present dispatch plan and wait for approval

Show the plan before dispatching:

```
Parallel dispatch plan:
  Agent 1 [Sonnet]: Implement user authentication middleware — output: auth.ts
  Agent 2 [Sonnet]: Write integration tests for /v1/users — output: users.test.ts
  Agent 3 [Haiku]:  Review API design conventions in routes/v1/ — output: findings list

Proceed? [y / n / modify]
```

Wait for explicit `y` before dispatching.

### 4. After agents complete

- Show each agent's output summary
- Check for conflicting changes (same file edited by multiple agents)
- Run integration verification: tests, type check, lint
- If conflicts exist: resolve manually before declaring done

### 5. Never dispatch subtasks with shared write targets

If two agents need to edit the same file, sequence them — don't parallelize.

---

## Dispatch Format

When dispatching, give each agent:
- Clear scope (which files, which concern)
- Expected output format
- Constraints (follow `ts-api` / `go-api` standards, no scope creep)
- Model to use

---

## What NOT to do

- Do not dispatch more than 5 agents in one batch
- Do not dispatch without user approval
- Do not assume subtasks are independent without checking for shared state
- Do not merge agent outputs without verifying no conflicts
