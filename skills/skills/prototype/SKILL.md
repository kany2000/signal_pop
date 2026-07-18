---
name: prototype
description: "Build a throwaway prototype to flesh out a design before committing to it. Two branches: terminal app for logic/state questions, or UI variations toggled from one route. Use when user wants to prototype, sanity-check a data model, mock up a UI, explore design options. Adapted from mattpocock/skills."
related_skills: [spike]
---

# Prototype

Prototype 是**用来回答一个问题的 throwaway code**。问题决定形状。

## 选分支

先识别问题类型（从用户 prompt 或项目上下文推断，必要时直接问）：

### Logic 分支
**"这个逻辑/状态模型对吗？"**
→ 构建一个很小的交互式 terminal app，推动 state machine 跑过纸面上难以推理的 cases

### UI 分支
**"这个应该长什么样？"**
→ 在单一路由上生成几种差异很大的 UI variations，通过 URL search param 和浮动底栏切换

选错分支会浪费整个 prototype。如果模糊且用户不可达，默认选择更匹配周围代码的分支（backend → logic；page/component → UI）。

## 通用规则

1. **从第一天就是 throwaway，并明确标记。** 放在被 prototype 的 module/page 旁边，命名让别人一眼看出是 prototype。
2. **一个命令即可运行。** 使用项目现有 task runner（`pnpm <name>`、`python <path>` 等）。
3. **默认不持久化。** State 在内存中。Persistence 要检查的东西，不该成为依赖。
4. **跳过 polish。** 不写 tests，不做超过"能跑起来"所需的 error handling。
5. **暴露 state。** 每次 action 或 variant switch 后，打印完整 state。
6. **完成后删除或吸收。** 删掉它，或把验证过的决策折进真实代码。不要让它在 repo 里腐烂。

## 完成后

Prototype 里唯一值得保留的是**答案**。把它和所回答的问题一起记录到持久位置（commit message、ADR、issue，或 prototype 旁边的 NOTES.md）。

## 与 spike 的区别

| 方面 | spike | prototype |
|------|-------|-----------|
| 目的 | 验证一个技术可行性 | 打磨设计/交互/状态模型 |
| 产出 | 是/否结论 | 可交互的 demo |
| 受众 | 自己 | 自己或团队 |
| 去留 | 通常直接删除 | 答案吸收到代码中 |
