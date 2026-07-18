---
name: handoff
description: "Compact the current conversation into a handoff document for another agent to pick up. Use when switching context, ending a session, or when the next phase needs a fresh agent. Adapted from mattpocock/skills."
related_skills: [plan, writing-plans]
---

# Handoff

将当前对话浓缩为一份 handoff document，让下一个 agent 可以无缝继续。

## Output

- 保存到临时目录（OS temp dir），**不是**当前工作区
- 包含 "suggested skills" 章节，建议下个 agent 加载哪些 skills
- 不要重复已在 artifacts（PRDs、plans、ADRs、issues、commits、diffs）中捕获的内容——用路径或 URL 引用它们
- 脱敏：删除 API keys、passwords、PII

## 模板

```
# Handoff: [会话主题]

## 当前状态
[已完成/进行中的工作概述]

## 关键决策
- [决策1及其理由]
- [决策2及其理由]

## 待处理
- [ ] [待办1]
- [ ] [待办2]

## 已发现但未解决的问题
[已知风险/阻碍/疑问]

## Suggested Skills
- skill1 — 为什么需要
- skill2 — 为什么需要

## 引用
- PRD: path/to/prd.md
- ADR: path/to/adr.md

## 敏感信息已脱敏
[如有，列出脱敏项]
```

## 参数

如果用户传入了 arguments，视为下一次 session 的重点描述，据此调整文档侧重。
