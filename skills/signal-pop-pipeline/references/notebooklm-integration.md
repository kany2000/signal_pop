# NotebookLM-py 与 Signal Pop 集成参考

> 2026-07-11 实战验证: v0.7.3, cookie 登录, 中文播客生成

## 安装

```bash
uv tool install "notebooklm-py[browser]"
# → ~/.local/bin/notebooklm
# 独立 venv，不污染项目依赖
```

## 登录方式（无头VPS）

VPS 无 GUI 不能交互登录。EditThisCookie JSON → Playwright storage_state 转换：

```python
# EditThisCookie export → ~/.notebooklm/profiles/default/storage_state.json
import json, os

ss_map = {"unspecified": "None", "no_restriction": "None", "lax": "Lax", "strict": "Strict"}
pw_cookies = []
for c in json.load(open("etc_export.json")):
    pw_cookies.append({
        "name": c["name"],
        "value": c["value"],
        "domain": c["domain"],
        "path": c["path"],
        "expires": c.get("expirationDate", -1),
        "httpOnly": c.get("httpOnly", False),
        "secure": c.get("secure", False),
        "sameSite": ss_map.get(c.get("sameSite", "unspecified"), "None"),
    })

os.makedirs(os.path.expanduser("~/.notebooklm/profiles/default"), exist_ok=True)
json.dump({"cookies": pw_cookies, "origins": []},
          open(os.path.expanduser("~/.notebooklm/profiles/default/storage_state.json"), "w"))
```

验证: `notebooklm auth check --test --json` → `"status": "ok"`

## 中文播客生成

```bash
# 语言代码是 zh_Hans (不是 zh)
notebooklm generate audio "用中文解读" --format deep-dive --language zh_Hans --wait --timeout 600

# 下载
notebooklm download audio --latest --force /path/to/output.mp3
```

### 播客格式

| 格式 | 适合 Signal Pop 场景 |
|------|---------------------|
| deep-dive | 深度新闻分析（15分钟） |
| brief | 短新闻摘要（5分钟） |
| critique | 观点评论 |
| debate | 正反辩论 |

### 语言支持

`notebooklm language list` — 81种语言。zh_Hans (简体中文) 已验证可用。

## 对 Signal Pop 的评估

| 维度 | 评价 |
|------|------|
| 中文自然度 | ✅ 双人对话，远优于单声 TTS |
| 来源引用 | ✅ 自动引用来源，有 citation 标注 |
| 可控性 | ❌ 不能控制主播声音、语调、话题比重 |
| 组织结构 | ❌ 不能强制70%时事30%AI的分配 |
| 覆盖范围 | ❌ 只能基于 notebook 内 sources 的内容 |
| 与现有管线 | ⚠️ 需先导入新闻 URLs 到 notebook |

**结论**：可用作播客备选方案，但不建议替代现有 TTS（小米魔搭+xiaoxiao 女声）。更适合独立栏目或 BGM 补充内容。

## CLI 常用命令速查

```bash
notebooklm create "标题"                          # 创建 notebook
notebooklm use <id>                              # 设为当前
notebooklm source add <url>                      # 导入来源
notebooklm source add "./file.pdf"               # 导入本地文件
notebooklm ask "问题"                             # 问答
notebooklm generate audio "指令" --language zh_Hans --wait
notebooklm download audio --latest --force ./输出.mp3
notebooklm list --json                           # 列出所有 notebook
notebooklm delete -n <id> -y                     # 删除
notebooklm auth refresh --quiet                  # cookie 保活 (适合 cron)
```

## Cookie 有效期

2026-07-11 实测: expirationDate ~2027年中到2028年初。短期不需刷新。