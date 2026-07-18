---
name: diagnose
description: "Disciplined diagnosis loop for tricky bugs and performance regressions. Reproduce → minimise → hypothesise → instrument → fix → regression-test. Use when user says 'diagnose this', reports a bug, or describes a performance regression. Adapted from mattpocock/skills."
related_skills: [systematic-debugging, test-driven-development]
---

# Diagnose

处理困难 bug 的纪律化流程。只有在理由明确时才跳过阶段。

## Phase 1 — Build a feedback loop

**这是这个 skill 的核心。** 如果你有一个快速、确定、agent 可运行的 pass/fail 信号来覆盖这个 bug，你就能找到原因。没有它，盯着代码看再久也救不了你。

### 构造反馈环的方式（按顺序尝试）

1. **Failing test** — 放在能触达 bug 的 seam 上（unit/integration/e2e）
2. **Curl / HTTP script** — 针对运行中 dev server
3. **CLI invocation** — fixture input + diff 已知正确 snapshot
4. **Headless browser** — Playwright/Puppeteer 驱动 UI，断言 DOM/console/network
5. **Replay captured trace** — 真实 request/payload/event log 存到磁盘，隔离重放
6. **Throwaway harness** — 系统最小子集 + mocked deps，触发 bug code path
7. **Property / fuzz loop** — 1000 个随机输入寻找失败模式
8. **Bisection harness** — 自动化"在状态 X 启动、检查、重复"，配合 `git bisect run`
9. **Differential loop** — 对同一输入运行 old vs new version，diff 输出
10. **HITL bash script** — 最后手段，必须有真人参与

构建正确的反馈环，bug 就已经修好 90%。

## Phase 2 — Minimise the reproduction

把反馈环修剪到最少步骤/最少代码。目标：在消除所有噪音后，bug 是否还在？

- 删除无关的 UI 步骤、无关的 mock 数据、无关的 module
- 直接调用怀疑的函数，不走整个流程
- 如果最小化后 bug 消失 → 你学到了关键信息（bug 在交互中）
- 如果最小化后 bug 还在 → 你有了一个超快的反馈环

## Phase 3 — Hypothesise

列出所有可能的 root cause（至少 3 个）。对每个假设：
- 如果这是 root cause，预期什么 observable signal？
- 如何用你的反馈环验证这个 signal？
- 优先级：最容易验证的排最前面

## Phase 4 — Instrument

不猜，不盯着代码看。加 instrumentation：

- `console.log` / `console.trace`
- debugger statement
- 性能计时：`performance.mark()` / `performance.measure()`
- 网络请求拦截
- 状态快照 dump

一次只验证一个假设。如果假设被推翻，删除对应 instrumentation。

## Phase 5 — Fix

找到 root cause 后：
1. 写 failing test 锁定它
2. 修复
3. 测试通过
4. 运行 regression suite

## Phase 6 — Cleanup

- [ ] 所有 `[DEBUG-...]` instrumentation 已删除
- [ ] Throwaway 代码已删除或移到标记位置
- [ ] 在 commit/PR message 中记录最终正确的 hypothesis

## 复盘

**问：什么本可以防止这个 bug？**
如果答案涉及 architecture change（没有好的 test seam、callers 缠绕、隐藏 coupling），带着具体信息交给 improve-codebase-architecture 或 zoom-out skill。
