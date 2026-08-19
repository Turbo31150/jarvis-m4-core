[user] You are building ONE portfolio piece for a freelance profile on Upwork. The freelancer positions as an "AI Systems & Automation Engineer" specialising in production-grade retrieval systems.

## Your scope — ONLY this
Produce a **RAG pipeline with freshness gating** — the differentiator being that stale sources are detected, flagged and down-weighted at retrieval time instead of being silently served as fact. Also demonstrate hybrid search (lexical + semantic), per-datatype chunking, and metadata filtering.

Do NOT work on n8n workflows or multi-LLM routing/cost control — other agents own those. Do not touch any file outside your output directory.

## Ground it in real patterns first
This machine runs a real RAG system ("board") with genuine freshness controls. Before writing anything, study the real patterns:
- `~/jarvis/scripts/board/ask-board.py` — real retrieval with RRF re-ranking and a freshness gate
- `~/jarvis/scripts/board/freshness-watchdog.py` and `board-freshness-sweep.py` — real staleness detection with half-life logic
- `~/jarvis/scripts/board/chunk-source.py`, `embed-chunks.py`, `reembed-drift.py`
- `eval-retrieval.py` if present — retrieval evaluation

Pay attention to how staleness is actually computed (half-life ratios, STALE/FRESH classification) and how RRF re-ranking combines rankings. Then write something fresh and generic in **Python**. Do NOT copy real corpus content, real domain names, or real source material.

## HARD CONSTRAINT — anonymisation (non-n

[assistant] I'll start by studying the real patterns on this machine, then build the portfolio piece.

[assistant] ToolSearch found no context-mode tools; proceeding with standard tools. Let me study the real freshness logic.

[assistant] Now the core retrieval logic. Let me extract the algorithmic sections without pulling in corpus content.

[assistant] Environment checked: numpy and pytest available, `sentence_transformers` absent (good — the fallback path is the real one here). Now building.

[assistant] Found a real bug: with the gate disabled, blocks were labelled UNKNOWN and triggered a false stale warning. Fixing.

[assistant] Now the crafted-case test corpus. Let me probe empirically to build a genuinely hard case.

[assistant] The single-query "rank 2 in both arms" design is contrived. Let me probe the real corpus for a genuinely honest asymmetry instead.

[assistant] The probe was conflating retrieval rank with post-gate rank. Let me fix that and also improve compound-identifier tokenization.

[assistant] Found a real defect: RRF ties when the two arms swap the top two, and the tie was broken by chunk id — silently wrong. Fixing with a principled tie-break.

[assistant] The latent geometry is knife-edge at dim=8. Let me strengthen the bridge structure and sweep for a stable dimension.

[assistant] dim=8 sits mid-band with a strong margin. Now fixing the three remaining failures.

[assistant] All green across both runners and all three embedder configs. Cleaning up and capturing real output for the README.

[assistant] Everything verified and clean. Done.

## What I built

`~/upwork-portfolio/rag-freshness-gating/` — a self-contained, runnable retrieval pipeline whose differentiator is that stale sources are detected, flagged and down-weighted at retrieval time.

| File | Contents |
|---|---|
| `/home/rempc/upwork-portfolio/rag-freshness-gating/rag_pipeline.py` | Full pipeline + CLI, 1551 lines, type-hinted, zero required dependencies |
| `/home/rempc/upwork-portfolio/rag-freshness-gating/sample_corpus/` | 8 synthetic docs, 5 datatypes, relative ages so the demo never rots |
| `/home/rempc/upwork-portfolio/rag-freshness-gating/test_rag.py` | 54 tests |
| `/home/rempc/upwork-portfolio/rag-freshness-gating/README.md` | Client-facing, English |
| `/home/rempc/upwork-portfolio/rag-freshness-gating/architecture.md` | Mermaid + ASCII diagram, stage reference |

Six chunkers (prose / markdown / faq / code / tabular / transcript) selected by datatype; BM25 + embedding arms fused by RRF; metadata filtering with `$contains/$in/$gte/...` that fails closed; freshness gate on `ratio = age / half_life` with FRESH / AGING / STALE / EXPIRED / CANONICAL / UNKNOWN bands and `0.5 ** (ratio-1)` decay. Embedding backend is a protocol: corpus-fitted LSA (numpy) → stdlib hashing stub → sentence-transformers when explicitly selected.

## Proof it works

```
$ python3 -m pytest test_rag.py -q
......................................................                   [100%]
54 passed in 0.32s
```

Also green under `py