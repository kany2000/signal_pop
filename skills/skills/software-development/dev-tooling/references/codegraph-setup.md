# CodeGraph Setup Reference

## What It Is
Pre-indexed code knowledge graph. Auto-syncs on code changes. For Claude Code, Codex, Gemini, Cursor, OpenCode, Hermes Agent, Antigravity, Kiro. 100% local.

## Install
```bash
npm i -g @colbymchenry/codegraph
```
No Node.js required — bundles own runtime.

## Wire to Agent
```bash
codegraph install
```
Detects and auto-configures supported agents. Only wires up the agent — does NOT index code.

## Initialize Project
```bash
cd your-project
codegraph init
```
Creates `.codegraph/` directory, builds full graph. Auto-sync enabled by default.

## Usage
```bash
codegraph explore "your query"   # semantic search
codegraph status                  # index stats
codegraph sync                    # incremental update
codegraph index                   # full rebuild
codegraph upgrade --check         # check for updates
codegraph upgrade                 # upgrade
codegraph uninstall               # remove from all agents
codegraph uninit                  # remove project index
```

## Index Stats (Hermes Agent repo example)
- Files: 2,493 | Nodes: 74,516 | Edges: 197,792
- DB: 174MB | Languages: Python, TS, YAML, TSX, JS
- Build time: ~5 min on 2493 files (Python heavy)

## Benefits (benchmark median)
- 58% fewer tool calls
- 22% faster
- ~0 file reads
- Works on TS/Python/Rust/Java/Go/Swift

## Pitfalls
- `codegraph init` on large repos takes minutes — don't timeout prematurely
- `codegraph install` is a separate step from CLI install — both needed
- New terminal may be needed after npm global install for PATH