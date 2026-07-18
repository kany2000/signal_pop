---
name: handoff
description: Compact the current conversation into a handoff document for another agent to pick up.
argument-hint: "What will the next session be used for?"
---

写一份 handoff document，总结当前对话，让 fresh agent 可以继续工作。保存到由 `mktemp -t handoff-XXXXXX.md` 生成的路径（写入前先读取该文件）。

建议下一次 session 应使用的 skills（如果有）。

不要重复已经捕获在其他 artifacts（PRDs、plans、ADRs、issues、commits、diffs）中的内容。改用 path 或 URL 引用它们。

如果用户传入了 arguments，把它们视为下一次 session 重点的描述，并据此调整文档。
