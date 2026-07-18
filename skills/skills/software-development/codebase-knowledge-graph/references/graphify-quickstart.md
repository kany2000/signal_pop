# graphify quickstart + reproduction recipe

Reproduced 2026-07-09 against the Graphify-Labs/graphify repo (v8) and the
`/home/kan/shared/signal_pop` project.

## Prereqs
- Python 3.10+, `uv` installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- For semantic layer: a valid LLM backend key (Gemini/OpenAI/DeepSeek/Claude/Ollama)

## Clone + install
```bash
git clone --branch v8 --depth 1 https://github.com/Graphify-Labs/graphify.git
uv tool install graphifyy                 # base
uv tool install "graphifyy[gemini]" --force   # + openai SDK for gemini backend
which graphify                            # -> ~/.local/bin/graphify
```

## Run on a target project
```bash
cd /home/kan/shared/signal_pop
PATH="$HOME/.local/bin:$PATH"
graphify extract . --code-only --out /home/kan/shared/signal_pop   # AST only, no key
graphify cluster-only /home/kan/shared/signal_pop                  # gen graph.html + report
```

## Query
```bash
graphify explain "generate_images"  --graph /home/kan/shared/signal_pop/graphify-out/graph.json
graphify path "extract_titles" "build_prompt" --graph .../graph.json
graphify query "how are news images generated" --graph .../graph.json
```

## Real error transcripts (for diagnosis)

### Missing openai SDK (gemini backend)
```
[graphify] chunk 1/3 failed: the 'openai' package is required for this backend
but is not installed. Install it with: uv tool install "graphifyy[gemini]" --force
Fix: uv tool install "graphifyy[gemini]" --force
```

### Invalid Gemini key (correct AIzaSy... shape, still rejected)
```
[graphify] chunk 3/3 failed: Error code: 400 -
  [{'error': {'code': 400, 'message': 'Please pass a valid API key',
   'status': 'INVALID_ARGUMENT'}}]
[graphify] WARNING: 3/3 semantic chunk(s) failed ... Partial results returned.
```
Run does NOT crash; returns AST-only partial. Fall back to `--code-only`.

### Empty source files (non-fatal, auto-retried)
```
warning: 4 source file(s) produced zero nodes and are absent from the graph:
  filtered_news_20260620_153642.json ...
A re-run will retry them (empties are no longer cached)
```

## Code-only output (signal_pop)
```
[graphify extract] found 6 code, 8 docs, 0 papers, 46 images
[graphify extract] AST extraction on 6 code files...
[graphify extract] wrote graphify-out/graph.json: 6 nodes, 16 edges (no clustering)
# cluster-only -> 3 communities. GRAPH_REPORT.md, graph.json, graph.html updated.
```
GRAPH_REPORT.md correctly flagged `generate_images()` as god node (3 edges) and
`extract_titles()`/`build_prompt()` as cross-community bridges via EXTRACTED `calls`
edges. Token cost: 0 input / 0 output.
