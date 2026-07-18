#!/usr/bin/env python3
"""Emit agent-readable + human-readable views of a graphify graph.json.

Run from a dir containing graph.json (or pass path as argv[1]).
Writes graph_triples.md (flat triples, agent-friendly) and graph_simple.md
(human overview: communities, god nodes, verify-needed items).

Why this exists (ponytail: ceiling = full graph.html interactive viz; this is
the LLM-readable fallback for agents that can't render a browser).
"""
import json, sys, collections, os

SRC = sys.argv[1] if len(sys.argv) > 1 else "graph.json"
OUT_DIR = os.path.dirname(os.path.abspath(SRC))

d = json.load(open(SRC, encoding="utf-8"))
nodes = d.get("nodes", [])
links = d.get("links", [])
# Build id->label map robustly: some nodes keyed by 'id', some by 'label'
id2label = {}
label2label = {}
for n in nodes:
    lid = n.get("id") or n.get("label")
    lab = n.get("label") or lid
    if lid:
        id2label[lid] = lab
    label2label[lab] = lab

def lbl(x):
    return id2label.get(x) or label2label.get(x) or x

# Community map
coms = collections.defaultdict(list)
for n in nodes:
    coms[n.get("community")].append(n.get("label") or n.get("id"))

# God nodes by degree
deg = collections.Counter()
for l in links:
    deg[l.get("source")] += 1
    deg[l.get("target")] += 1
god = sorted(deg.items(), key=lambda x: -x[1])

ext, inf = [], []
for l in links:
    s, t, r, c = lbl(l.get("source")), lbl(l.get("target")), l.get("relation"), l.get("confidence")
    line = f"{s} --{r}--> {t}"
    (ext if c == "EXTRACTED" else inf).append((line, c, l.get("confidence_score")))

# ---- graph_triples.md (agent-readable) ----
lines = []
lines.append("# Graph Triples (agent-readable)")
lines.append("")
lines.append(f"- nodes: {len(nodes)}  edges: {len(links)}  communities: {len(coms)}")
lines.append(f"- EXTRACTED (read from source): {len(ext)}  INFERRED (model-guessed): {len(inf)}")
lines.append("")
lines.append("## Legend")
lines.append("- `EXTRACTED`: edge explicitly present in source code/docs (trustworthy)")
lines.append("- `INFERRED`: model-reasoned connection (verify before relying on it)")
lines.append("")
lines.append("## EXTRACTED edges")
for line, c, sc in ext:
    lines.append(f"- {line}")
if inf:
    lines.append("")
    lines.append("## INFERRED edges (verify)")
    for line, c, sc in inf:
        lines.append(f"- {line}  [conf {sc}]")
open(os.path.join(OUT_DIR, "graph_triples.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")

# ---- graph_simple.md (human overview) ----
h = []
h.append("# Project Knowledge Graph — Overview")
h.append("")
h.append(f"**{len(nodes)} nodes · {len(links)} edges · {len(coms)} communities**")
h.append("")
h.append("## God Nodes (most connected — core abstractions)")
for nid, c in god[:10]:
    h.append(f"- `{lbl(nid)}` — {c} edges")
h.append("")
h.append("## Communities")
for c, ns in sorted(coms.items(), key=lambda x: -len(x[1])):
    sample = ", ".join(ns[:8])
    if len(ns) > 8:
        sample += f" … (+{len(ns)-8})"
    h.append(f"- **C{c}** ({len(ns)}): {sample}")
if inf:
    h.append("")
    h.append("## ⚠️ Verify-needed (INFERRED edges)")
    for line, c, sc in inf:
        h.append(f"- {line} [conf {sc}]")
h.append("")
h.append("## Full interactive view")
h.append("Open `graph.html` in a browser for the clickable force-directed graph.")
open(os.path.join(OUT_DIR, "graph_simple.md"), "w", encoding="utf-8").write("\n".join(h) + "\n")
print(f"wrote graph_triples.md ({len(ext)} ext, {len(inf)} inf) + graph_simple.md ({len(coms)} communities)")
