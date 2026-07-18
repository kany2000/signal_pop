# NotebookLM 新闻播客集成

## 安装

```bash
uv tool install "notebooklm-py[browser]"
```

## 认证方式（无头服务器）

EditThisCookie 导出 → 转 Playwright storage_state:

```python
import json, os

with open("cookies.json") as f:
    etc_cookies = json.load(f)

ss_map = {"unspecified": "None", "no_restriction": "None", "lax": "Lax", "strict": "Strict"}
pw_cookies = []
for c in etc_cookies:
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

storage_state = {"cookies": pw_cookies, "origins": []}
os.makedirs(os.path.expanduser("~/.notebooklm/profiles/default"), exist_ok=True)
with open(os.path.expanduser("~/.notebooklm/profiles/default/storage_state.json"), "w") as f:
    json.dump(storage_state, f)
```

验证: `notebooklm auth check --test --json`

## ⚠️ 关键坑：storage_state.json 双份存在

**profile 目录**和**项目目录**各有一份 storage_state.json，用户可能只更新了项目目录的，但 notebooklm CLI 读的是 profile 目录的。

| 文件 | 用途 | 位置 |
|------|------|------|
| Profile | notebooklm CLI 实际读取 | `~/.notebooklm/profiles/default/storage_state.json` |
| Project | 项目共享/备份 | `/home/kan/shared/notebooklm-py/storage_state.json` |

**症状**：`notebooklm auth check` 通过（它读 profile 目录→但可能读的是旧版本），而 `notebooklm list` 或 `notebooklm generate audio` 报 `Authentication expired`。

**原因**：`auth check` 只检查 cookie 存在性和格式，不测 token 有效性。`--test` 标志才实际发请求验证。

**修复**：用户重新认证后，必须把新 storage_state.json **复制到 profile 目录**：
```bash
cp /home/kan/shared/notebooklm-py/storage_state.json ~/.notebooklm/profiles/default/storage_state.json
```

验证真实有效性：
```bash
notebooklm list           # 应列出所有 notebook（不报 auth 错误）
```

## 正确命令 vs 错误命令

| 意图 | 正确命令 | 错误命令（不存在） |
|------|---------|-----------------|
| 列出 notebook | `notebooklm list` | `notebooklm note list` |
| 设置当前 notebook | `notebooklm use <id>` | — |
| 查看当前上下文 | `notebooklm status` | — |
| 生成播客 | `notebooklm generate audio "描述" --format deep-dive --language zh_Hans --wait --json` | — |

## 中文播客生成

```bash
notebooklm generate audio "你的播客描述" --format deep-dive --language zh_Hans --wait --timeout 600
```

- `--language zh_Hans`（不是 `zh`）
- `--length long` 可能超时（>10min），默认长度即可
- 长耗时任务必须在后台跑: `terminal(background=true, notify_on_complete=true)`
- `--wait --timeout 1200`：最长等 20 分钟
- `--json`：机器可读输出

## 已知问题

- Source add 经常 RPC TransportServerError（超时），但 idempotency retry 会自动恢复，最终 ready
- 每个 source 约 35s 处理时间
- NotebookLM 播客不能控制主播声音/语调/内容结构
- 播客标题由 Google 自动生成、不可控
- **Google 播客生成有日配额**（~2-3 次/天），超限报错需等次日重置
- **认证过期无声失败**：`auth check` 通过但实际操作仍可能失败，必须用 `notebooklm list` 或 `generate audio` 实测才能确认