---
name: codebase-knowledge-graph
description: Turn any folder of code (and optionally docs/images/PDFs/video) into a queryable knowledge graph with graphify. Use when the user wants to understand a codebase's structure, find god nodes / communities / cross-file call paths, trace how two concepts connect, or explore a repo instead of grepping. Also covers the install gotchas (double-y package name, Gemini backend needs the [gemini] extra) and the zero-cost code-only AST mode.
triggers:
  - map this codebase / understand this repo / what is the structure of X
  - knowledge graph / code graph / graphify
  - how does A connect to B in this code / find god nodes / communities
  - user shares a graphify GitHub link as a learning or tooling project
---

# Codebase Knowledge Graph (graphify)

graphify builds a **real traversable graph** (not embeddings/vector store) from a
codebase. Code is parsed locally with tree-sitter (deterministic, no LLM, nothing
leaves the machine). Docs/images/PDF/video optionally get a semantic pass via a
configured LLM backend. Every edge is tagged `EXTRACTED` (explicit in source) or
`INFERRED` (resolved by graphify) so you can tell read-directly from inferred.

Deliverables: `graphify-out/{graph.html, GRAPH_REPORT.md, graph.json}`.
- `graph.html` — clickable force-directed graph, open in any browser.
- `GRAPH_REPORT.md` — god nodes, communities, surprising connections, suggested questions.
- `graph.json` — full graph, query anytime without re-reading files.

## Install

Package is **`graphifyy`** (double-y) on PyPI; the CLI command is `graphify`.

```bash
uv tool install graphifyy          # recommended (isolated env)
# or: pipx install graphifyy
```

The `/graphify` assistant skill maps to `graphify extract .`.

## Run

```bash
cd <repo>
graphify extract .                 # full: AST + semantic LLM pass
graphify extract . --code-only     # AST only, NO API key, 0 token cost
graphify extract . --out <dir>     # write graphify-out/ under <dir>
```

`--code-only` is the safe default for a first pass or when no LLM key is available.
Semantic (docs/media) extraction needs a backend API key.

## Semantic backend: any OpenAI-compatible endpoint

graphify's `openai` backend reads `OPENAI_BASE_URL` / `OPENAI_API_KEY` /
`OPENAI_MODEL` and reaches ANY OpenAI-compatible server (Sensenova, MiMo,
DeepSeek, a local llama.cpp/vLLM, etc.). It does NOT have to be OpenAI proper.

```bash
export OPENAI_BASE_URL="https://token.sensenova.cn/v1"
export OPENAI_API_KEY="<key>"
export OPENAI_MODEL="glm-5.2"
graphify extract . --backend openai --out <dir>   # --backend openai optional;
                                                  # OPENAI_* env is auto-detected
```

This is the way to run when `GEMINI_API_KEY` is dead or you have another
provider. Confirm the endpoint first with a raw chat call:
`curl -s $OPENAI_BASE_URL/chat/completions -H "Authorization: Bearer $OPENAI_API_KEY" -d '{"model":"'$OPENAI_MODEL'","messages":[{"role":"user","content":"hi"}]}'`.

## Query the graph

```bash
graphify explain "SomeSymbol"       # node + neighbors, edge types, community, degree
graphify path "A" "B"               # shortest path between two nodes
graphify query "plain language Q"   # BFS/DFS scoped subgraph (--dfs, --budget N)
graphify affected "X"               # reverse traversal: what breaks if X changes
# point at a specific graph:  --graph <path>/graph.json
```

After editing code (no LLM needed): `graphify update .` keeps the graph current.

## Pitfalls (learned the hard way)

1. **Gemini backend requires the `[gemini]` extra.** Plain `uv tool install graphifyy`
   lacks the `openai` package the gemini backend calls. Symptom:
   `the 'openai' package is required for this backend but is not installed`.
   Fix: `uv tool install "graphifyy[gemini]" --force`. (Other backends: openai/deepseek
   also pull the openai SDK; claude needs the anthropic SDK; ollama needs neither.)
2. **Invalid API key still "succeeds" the install but fails all semantic chunks.**
   A `GEMINI_API_KEY` with the correct `AIzaSy...` shape can still be rejected by
   Google with `400 INVALID_ARGUMENT / Please pass a valid API key`. The run reports
   "3/3 semantic chunk(s) failed" and returns partial (AST-only) results — it does NOT
   crash. Fall back to `--code-only` for the structure, and flag the key as the issue.
   Prefer the OpenAI-compatible endpoint path (see "Semantic backend" above) instead of
   Gemini when the Gemini key is dead — a working provider beats fighting a revoked key.
3. **Empty files are not cached.** graphify warns about zero-node source files but
   retries them on re-run (no permanent cache of empties). Ignore the warning unless
   it persists across re-runs.
4. **Community labeling needs the LLM too.** `graphify cluster-only <dir>` will use
   `Community N` placeholders if the key is invalid — the graph + report still generate,
   just without human-readable community names.
5. **A TEXT-ONLY model silently drops the image layer.** graphify sends each image as a
   multimodal `image_url` content block. A text-only model (e.g. Sensenova `glm-5.2`)
   rejects it with `400 messages.content.type 参数非法，取值范围 ['text']`, so image chunks
   fail while the text/docs chunks succeed. Symptom: graph has image nodes (filenames only)
   but 0 image understanding, and image↔image edges are pure INFERRED guesses from paths.
   To actually parse images you need a MULTIMODAL-compatible endpoint; otherwise use
   `--code-only` or accept that only docs/text get semantically mapped.
6. **graph.json shape:** edges live under the `links` key (NOT `edges`); nodes under
   `nodes`; the raw `graph` key is nested metadata. When scripting, read
   `d['links']` / `d['nodes']`, not `d['edges']`.

## Verification

A clean run prints e.g. `wrote graphify-out/graph.json: 6 nodes, 16 edges (N communities)`.
Confirm `graphify-out/graph.html` exists, then exercise one query command to prove the
graph is queryable. For Signal Pop (docs + 2 .py scripts) the code-only pass produced
6 nodes / 6 edges / 3 communities, 0 tokens, and `graphify explain "generate_images"`
correctly surfaced god nodes and `calls`/`contains` EXTRACTED edges.

The full semantic pass via Sensenova `glm-5.2` (OpenAI-compatible) produced 12 nodes /
11 edges / 4 communities (~$0.0028, 37s) but ONLY the text docs were understood — the
46 images were dropped because glm-5.2 is text-only (see Pitfall 5).

See `references/graphify-quickstart.md` for a copy-paste reproduction recipe with real
error transcripts, and `references/openai-compatible-backends.md` for non-Gemini backend
configs (Sensenova confirmed working).
