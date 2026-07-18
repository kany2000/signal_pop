# 微信视频号 Cookie 手动导出与格式转换

当 `sau tencent login` 自动扫码失败时（二维码提取超时 / 页面改版找不到选择器），手动导出 Cookie 是最稳的替代路径。

## 适用场景

- `sau tencent login --headed` 弹窗后二维码空白/加载中
- 报错 "未获取到视频号登录二维码地址"（页面 DOM 结构变化）
- 扫码后 300 秒超时（不是过期刷新问题，而是登录态不完整）

## 工具选择

| 工具 | 导出格式 | 转换难度 |
|------|---------|---------|
| **Get cookies.txt LOCALLY** | Netscape `.txt` | ❌ 需转换为 Playwright JSON |
| **EditThisCookie** | JSON array | ✅ 接近 Playwright，需字段映射 |
| **手动从 DevTools 复制** | 无 | 硬核，不推荐 |

推荐 **EditThisCookie** 扩展：
https://chromewebstore.google.com/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg

## 手动 Cookie 导出 + 转换流程

### Step 1: 浏览器登录 → 导出 Cookie

1. 手动开 Chrome，访问 `https://channels.weixin.qq.com`
2. 用微信扫码登录视频号创作者后台
3. 装 EditThisCookie 扩展
4. 点击扩展图标 → Export → 复制 JSON
5. 保存到 `cookies/tencent_uploader/<account_name>`（无后缀）

### Step 2: 格式转换

EditThisCookie 导出的 JSON 字段名与 Playwright `storage_state` 不完全兼容，转换脚本：

```python
import json

with open('cookies/tencent_uploader/signalpop', 'r') as f:
    cookies = json.loads(f.read())

pw_cookies = []
for c in cookies:
    ss = c.get("sameSite", "Lax").lower()
    if ss in ("unspecified", "no_restriction"):
        ss = "None" if c.get("secure") else "Lax"
    else:
        ss = ss.capitalize()
    pw = {
        "name": c["name"],
        "value": c["value"],
        "domain": c["domain"],
        "path": c.get("path", "/"),
        "expires": c.get("expirationDate", c.get("expires", -1)),
        "httpOnly": c.get("httpOnly", False),
        "secure": c.get("secure", False),
        "sameSite": ss,
    }
    pw_cookies.append(pw)

state = {"cookies": pw_cookies, "origins": []}
with open('cookies/tencent_uploader/signalpop', 'w') as f:
    json.dump(state, f, indent=2)
```

### Step 3: 验证

```bash
sau tencent check --account <name>
```

返回 `valid` 则成功，否则可能 Cookie 本身已过期。

## 关键字段映射

| EditThisCookie 字段 → Playwright 字段 | 处理 |
|---|---|
| `expirationDate` → `expires` | 同语义，改键名 |
| `sameSite: "unspecified"` → `"Lax"` | 不安全 cookie 默认 Lax |
| `sameSite: "no_restriction"` → `"None"` | 仅限 secure=true |
| 缺 `httpOnly` → `false` | 默认值 |

## 已知问题

- **Get cookies.txt LOCALLY** 导出 Netscape 格式（`# Netscape HTTP Cookie File` 开头），无法直接转为 Playwright storage_state。如需用该扩展，另用 `curl_cffi` 解析。推荐换 EditThisCookie。
- **sessionid 未过期但 check 仍 invalid** — 三种可能：
  1. 微信服务端 session 已失效（重导一次即可）
  2. `sameSite` 值不匹配 — Playwright 只认 `Lax`/`Strict`/`None`，EditThisCookie 导出 `"unspecified"` / `"no_restriction"` 会被无声拒绝。转换脚本以上已处理。
  3. `cookie_auth()` 中 `wait_for_url()` 超时 — 重定向到 `/platform/post/list` 而不是严格匹配 `/platform/post/create` 时抛异常，脚本认为是 cookie 失效。如果 check 报 `Timeout 15000ms exceeded` 但 cookie 确认有效（刚导出的），就是这个问题。修法见 `uploader/tencent_uploader/main.py` 中的 `wait_for_load_state` 替代方案。

## 登录成功后的 Cookie 文件名规则

不同平台 sau 期望的 cookie 文件名不同——放错路径 check 报 invalid：

| 平台 | Cookie 目录 | 文件名（无后缀） | 导出/来源 |
|------|-----------|----------------|----------|
| 视频号 | `cookies/tencent_uploader/` | `signalpop`（按 `--account` 值） | Playwright `storage_state` JSON |
| B站 | `cookies/bilibili_her2home.json`（在项目根） | 固定名 `bilibili_<account>.json` | biliup CLI 专有格式（`cookie_info.cookies[]` + `token_info`），**不是 Playwright 格式，不能互用** |
| 快手 | `cookies/ks_uploader/` | `her2home`（按 `--account` 值） | Playwright `storage_state` JSON |
| 抖音 | `cookies/douyin_uploader/` | `her2home`（按 `--account` 值） | Playwright `storage_state` JSON |

**B站 cookie 格式特别说明**：biliup 的 JSON 结构是 `{cookie_info: {cookies: [...], domains: [...]}, token_info: {access_token, ...}}`，自动被 biliup 子进程识别。**不要**改成 Playwright storage_state 格式——biliup 不认。这个 JSON 文件在项目根（不是 `cookies/` 子目录），sau CLI 的 B站 login 命令自动生成。

如果你先把共享盘上的 cookie 下载到 Windows 本地，然后用 **EditThisCookie** 重新导出覆盖也是一样的（共享盘文件只是方便跨机器同步起点，具体平台上传时用的是本地的那份）。

## 登录代码修复记录（2026-07-11）

视频号 `uploader/tencent_uploader/main.py` 遭遇三个崩溃点，来自新版页面（2026年7月）：

| # | 问题 | 报错信息 | 根因 | 修法 |
|---|------|----------|------|------|
| 1 | `cookie_auth` 误判失效 | `Timeout 15000ms exceeded` / "load" event fired | `wait_for_url()` 期望严格 URL 匹配，但重定向后的页面 URL 不同 | 改 `page.goto(wait_until="domcontentloaded")` + `wait_for_load_state("networkidle", timeout=15000)` 替代 `wait_for_url` |
| 2 | QR 码提取失败直接崩溃 | `RuntimeError: 未获取到视频号登录二维码地址` | 新版页面 DOM 结构变化，CSS 选择器不匹配，`_extract_tencent_qrcode_src()` 抛出异常 | 在 `tencent_cookie_gen()` 中将 `_save_tencent_qrcode()` 包在 try/except 中，提取失败改为 warning 不致命，继续等待扫码 |
| 3 | QR 码提取失败后 KeyError | `KeyError: 'image_path'` | `except` 分支设 `qrcode_info={}`，但 `_wait_for_tencent_login()` 入口硬读 `qrcode_info["image_path"]` | 全路径判空：`qrcode_path = Path(qrcode_info["image_path"]) if qrcode_info.get("image_path") else None`，后续所有 `qrcode_path` 引用加 None 保护 |

**核心设计思想**：当 QR 码提取失败时（headless 模式会受影响），`--headed` 模式下的用户**肉眼可见浏览器窗口里的二维码**，扫码后登录流程的轮询逻辑 (`_wait_for_tencent_login`) 照常工作。不要因为提取失败就 abort 整个流程。

**三类登录方式 vs 代码鲁棒性需求**：

| 平台 | 登录机制 | 页面改版风险 | 修法模式 |
|------|---------|-------------|---------|
| 视频号 (tencent) | Playwright 弹窗 + CSS 选择器提取 QR | **高** — 微信频繁改版 | 提取失败降级为非致命 + headed 模式保底 |
| B站 (bilibili) | biliup CLI 终端打印 QR (无 Playwright) | 无 — 不依赖 DOM | 不需要修 |
| 快手 (kuaishou) | Playwright 弹窗 + CSS 选择器提取 QR | **中** — 偶有改版 | 同视频号修法，改 `uploader/ks_uploader/main.py` |
| 抖音 (douyin) | Playwright 弹窗 + 选择器 | **中** | 参见独立 fix 参考 |