---
name: graphify-project-map
description: Turn any code/docs/SQL project into a queryable knowledge graph with graphify (Graphify-Labs/graphify). Use when a user hands you a new project to understand, onboard a bot to an unfamiliar repo, assess code-change impact, or wants a visual/agent-readable map of a codebase. Covers install, code-only (free) extraction, semantic layer via OpenAI-compatible backend (Sensenova glm-5.2 tested), and emitting agent-friendly flat-triples output. NOT for image/video-heavy projects unless a multimodal backend is provided.
---

# Graphify Project Map

Map any project into a knowledge graph you query instead of grepping. Skill distilled from a live run on the Signal Pop project (2026-07-09).

## When to use
- User drops a new repo/project and wants fast structure understanding
- Onboarding a subagent/bot to an unfamiliar codebase
- Pre-change impact check (`graphify affected X`)
- User explicitly asks for a "knowledge graph" / architecture map

## Hard rules
- **Code-only extraction is free, local, zero-LLM.** Always run it first — no key needed.
- **Never modify the target project's build/run scripts to integrate graphify.** Graph is a map, not part of the pipeline. Do NOT `graphify install` into the project unless user asks.
- **Isolate outputs.** Copy `graphify-out/` to a separate `graphify-demo/<project>-graph/` dir, never leave it inside the project's working tree (keeps production dirs clean; user rejected leaving it in signal_pop/).
- **Image/video projects**: graphify sends them as multimodal chunks. A text-only model (e.g. glm-5.2) REJECTS `image_url` → those nodes become empty shells, image edges are guessed (INFERRED, low conf). Flag this honestly; don't present guessed image relations as real. Requires a vision-capable OpenAI-compatible endpoint to do properly.

## Install (one time)
```bash
uv tool install graphifyy          # base CLI (command: graphify)
uv tool install "graphifyy[gemini]" --force   # if you'll use gemini backend — base lacks openai pkg
```
Note: gemini backend actually uses the `openai` SDK. Without the extra, you get "the 'openai' package is required".

## Workflow
```bash
# 1. clone / locate project on shared disk (e.g. /home/kan/shared/<proj>)
cd /home/kan/shared/<proj>

# 2. code-only graph (FREE, no key, ~seconds)
graphify extract . --code-only --out /home/kan/shared/<proj>
graphify cluster-only /home/kan/shared/<proj>

# 3a. if docs/papers/news need semantic layer, use OpenAI-compatible backend.
#     Tested working endpoint (Sensenova, text-only):
export OPENAI_BASE_URL="https://token.sensenova.cn/v1"
export OPENAI_API_KEY="sk-uYIUXv8NlePvFVJJisGjSPvQABMfg9Us"
export OPENAI_MODEL="glm-5.2"
graphify extract . --backend openai --out /home/kan/shared/<proj>   # GRAPHIFY_FORCE=1 to overwrite

# 3b. SQL schema directly:
graphify extract . --postgres "postgresql://user:pass@host:5432/db"

# 4. emit agent-friendly flat views (see build_graph_views.py reference)
python3 build_graph_views.py graph.json    # -> graph_triples.md + graph_simple.md

# 5. isolate outputs away from project tree
mkdir -p /home/kan/shared/graphify-demo/<proj>-graph
cp graphify-out/graph.html graphify-out/graph.json graph_triples.md graph_simple.md \
   /home/kan/shared/graphify-demo/<proj>-graph/

# 6. incremental upkeep after code changes (AST-only, FREE, no LLM)
graphify update . --out /home/kan/shared/<proj>   # re-extract code, keep curated edges
graphify cluster-only /home/kan/shared/<proj>      # refresh report + communities
#   use GRAPHIFY_FORCE=1 (or --force) after refactors that DELETE code
#   (a smaller rebuild is otherwise rejected to avoid clobbering curated edges)
```

## References
- `references/build_graph_views.py` — emit graph_triples.md (agent-readable) + graph_simple.md.
- `references/sensenova-backend.md` — OpenAI-compatible backend config + glm-5.2 text-only quirk (reproduction recipe).

## Query the graph (after extract)
```bash
graphify explain "generate_images"          # node + neighbors, edge confidence tags
graphify path "extract_titles" "build_prompt"   # shortest path
graphify query "how are news images generated"  # BFS subgraph for a question
graphify affected "X" --relation calls       # reverse traversal: who depends on X
```
Every edge carries `EXTRACTED` (in source) vs `INFERRED` (model-guessed) — tell them apart.

## Output files (3 + 2 derived)
- `graph.html` — interactive force-directed graph (browser)
- `GRAPH_REPORT.md` — god nodes, communities, surprising connections, suggested questions
- `graph.json` — full graph (query anytime, no re-read)
- `graph_triples.md` *(derived)* — flat `A --rel--> B` lines, EXTRACTED vs INFERRED split, agent-readable
- `graph_simple.md` *(derived)* — communities + god nodes + verify-needed, human skim

## Pitfalls (hit during live run)
1. **gemini backend needs `graphifyy[gemini]`** extra or it errors on missing `openai` pkg.
2. **Environment `GEMINI_API_KEY` was dead** (Google: API_KEY_INVALID). Don't trust it; prefer explicit `OPENAI_*` backend.
3. **Text-only model can't read images** — glm-5.2 returned `messages.content.type 参数非法，取值范围 ['text']`. Image edges become guessed/empty.
4. **`graphify-out/` left in project tree pollutes it** — user wanted it moved out. Always isolate.
5. **`GEMINI_API_KEY` auto-selected** when set, causing failures even when you meant to use openai. Export `OPENAI_*` AND pass `--backend openai` explicitly.
6. **graph.json shape**: top-level `nodes` + `links` (NOT `edges`); node id may be a hash while `links.source/target` reference that hash — build an id→label map for readable output.

## Coverage table
| Project type | Works? | Condition |
|---|---|---|
| Pure code repo (~40 langs, tree-sitter) | ✅ instant | none |
| Code + docs/papers/text | ✅ | OpenAI-compatible backend (Sensenova key available) |
| Code + PostgreSQL schema | ✅ | `--postgres` DSN |
| Image/video-heavy | ⚠️ | needs vision-capable multimodal endpoint |

## build_graph_views.py
Reference script (emit agent/human-readable views from graph.json). See `references/build_graph_views.py`. Copies `nodes`+`links`, maps hash ids→labels, splits EXTRACTED/INFERRED, prints god nodes by degree. Place next to graph.json and run `python3 build_graph_views.py`.
