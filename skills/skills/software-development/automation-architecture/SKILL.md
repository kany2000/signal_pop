---
name: automation-architecture
description: Three-layer automation architecture (RPA → Workflow → Agent) for systematic task decomposition and AI-augmented work design.
platforms: [linux, macos, windows]
---

# Automation Architecture

## Core Framework

Every task should be analyzed through three layers before implementation:

```
Layer 1: RPA (Robotic Process Automation)
Layer 2: Workflow (Process Orchestration)  
Layer 3: Agent (Intelligent Decision-Making)
```

**Trigger rule**: Always evaluate which layer(s) a task belongs to. Prefer the simplest layer that solves the problem. Only escalate to higher layers when the lower layer cannot handle the task's requirements.

---

## Layer 1: RPA — Rules-Based Automation

**When to use**: Task is fully specified, repetitive, and has deterministic outcomes.

**Characteristics**:
- Clear trigger conditions
- Fixed execution path
- No decision-making required
- Repeatable with identical results

**Examples**:
- Cron jobs for scheduled data fetching
- Regex-based text extraction
- File format conversions
- Monitoring and alerting on thresholds
- Web scraping with fixed selectors

**Tool examples**: cron, bash scripts, simple scrapers, IFTTT, Zapier (no AI)

---

## Layer 2: Workflow — Process Orchestration

**When to use**: Task has multiple steps, requires tool chaining, or needs conditional branches.

**Characteristics**:
- Defined start and end states
-串联 multiple services/tools
- Error handling and retry logic
- Human-defined flow path

**Examples**:
- RSS → Filter → Translate → Generate → Publish pipeline
- CI/CD pipelines
- Multi-step data processing pipelines
- Approval workflows with gates
- Signal Pop daily news generation

**Tool examples**: pipelines, Make.com, n8n, GitHub Actions, cron + scripts chains

---

## Layer 3: Agent — Intelligent Decision-Making

**When to use**: Open-ended goals, requires judgment, or needs dynamic adaptation.

**Characteristics**:
- Ambiguous or evolving objectives
- Requires reasoning and planning
- Dynamic tool selection
- Self-correcting based on feedback

**Examples**:
- Autonomous code review and improvement
- Research tasks requiring synthesis across sources
- Complex debugging with hypothesis formation
- Creative content generation with iterative refinement
- Multi-step projects with emergent subgoals

**Tool examples**: Claude Code, Codex, Manus, DSPy, custom LLM agents

---

## Decision Matrix

| Question | Layer 1 (RPA) | Layer 2 (Workflow) | Layer 3 (Agent) |
|----------|---------------|-------------------|-----------------|
| Is the process deterministic? | ✅ Yes | ❌ No | ❌ No |
| Are steps known upfront? | ✅ Yes | ✅ Mostly | ❌ No |
| Need AI/LLM reasoning? | ❌ No | ❌ No | ✅ Yes |
| Examples | cron, scrape | pipelines | agents |

---

## Application Examples

### Signal Pop Pipeline

| Layer | Task | Implementation |
|-------|------|----------------|
| 1 (RPA) |定时抓取 RSS feed | cron job |
| 1 (RPA) | 过滤重复内容 | dedup script |
| 2 (Workflow) | 筛选 → 翻译 → 生成脚本 | pipeline orchestration |
| 3 (Agent) | 判断新闻价值、选择配图 | LLM-based judgment |

### Chrome Extension Development

| Layer | Task | Implementation |
|-------|------|----------------|
| 1 (RPA) | 模板生成、文件打包 | script |
| 2 (Workflow) | 构建 → 测试 → 上传 | CI/CD pipeline |
| 3 (Agent) | 调试报错、修复违规 | debugging agent |

---

## Anti-Patterns

❌ **Over-engineering**: Using Agent for tasks solvable by RPA
❌ **Premature optimization**: Building workflow for one-off tasks
❌ **Rigid workflows**: Forcing Agent into fixed paths where flexibility is needed
❌ **Layer confusion**: Calling scripts "agents" when they're just automation

---

## When in Doubt

Start with Layer 1 (RPA). If you find yourself writing complex conditionals, escalate to Layer 2. Only reach for Layer 3 when the task genuinely requires judgment that cannot be encoded as rules or flows.

---

## Related Skills

- `signal-pop-news-pipeline`: Signal Pop specific workflow implementation
- `autonomous-ai-agents`: Layer 3 agent implementation patterns
- `kanban-orchestrator`: Task decomposition using this framework
