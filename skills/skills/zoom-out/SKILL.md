---
name: zoom-out
description: "Zoom out from the current code to get broader context and higher-level perspective. Use when unfamiliar with a code section, need to understand how it fits into the bigger picture, or plan architectural changes. Adapted from mattpocock/skills."
related_skills: [writing-plans, spike]
---

# Zoom Out

我不熟悉这块代码。上升一层 abstraction，给我一张所有相关 modules 和 callers 的地图。

## 触发条件

用户说以下任一时自动加载本 skill：
- "帮我看看这个项目的架构"
- "这段代码在整个项目里的角色是什么"
- "我不熟悉这块代码"
- "zoom out"
- "大局分析"
- "这张图是什么"

## 产出

1. **模块地图** — 所有相关 modules 和它们的 caller/called-by 关系
2. **数据流** — 关键数据从创建到消费的路径
3. **架构模式** — 正在使用的架构风格（分层/DDD/clean/hexagonal 等）
4. **边界 & 接口** — 模块间的 contract 和 seam
5. **改进点** — 如果发现设计问题，记录但不主动修改

## 方法

1. 先从当前文件开始，向上追踪 caller chain
2. 向下看 callee chain（调用了哪些外部模块）
3. 找边界：输入来自哪，输出流向哪
4. 如果有测试文件，读测试理解预期的行为契约
5. 输出结构化的模块地图
