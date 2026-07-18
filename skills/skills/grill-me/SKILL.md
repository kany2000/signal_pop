---
name: grill-me
description: "Socratic questioning to stress-test plans, designs, and decisions. Use when user wants to refine a plan, get grilled on a design, validate assumptions, or says 'grill me'. Adapted from mattpocock/skills."
related_skills: [plan, writing-plans]
---

# Grill Me

围绕计划或设计的每个方面持续追问用户，直到达成共同理解。沿着 decision tree 的每个分支走下去，一次解决一个决策依赖。

## Rules

- **一次只问一个问题。** 不要一次抛出多个问题。
- 每个问题都附带你的推荐答案（根据项目上下文判断）。
- 如果某个问题可以通过探索 codebase 回答，先去探索，不要问用户。
- 把 grill 期间已经解决的问题捕获到 "established so far" 下，避免重复。
- 问题必须具体且可执行，而不是模糊的 "please provide more info"。

## Flow

1. 用户给出一个计划/设计/方案
2. 逐一追问：沿着决策树分支，从根到叶
3. 每轮：问一个问题 → 用户回答 → 更新 "established so far" → 下一个问题
4. 当所有分支都走到尽头，输出最终的 shared understanding 摘要

## 触发词

用户说"来 grill 我"、"帮我打磨方案"、"stress test this"、"挑刺" 时自动加载本 skill。
