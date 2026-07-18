# YouTube 平台上传配置说明

## social-auto-upload 对 YouTube 的支持

项目已内置 `youtube_uploader/main.py`，CLI 入口 `sau youtube upload-video` 可用。

### 启用步骤

1. **登录 YouTube（需有头模式）**
   ```bash
   cd /home/kan/shared/social-auto-upload
   sau youtube login --account her2home
   ```
   - 浏览器打开 YouTube Studio，登录 Google 账号
   - 进入频道页后 Cookie 自动保存到 `cookies/youtube_her2home.json`

2. **验证 Cookie 有效**
   ```bash
   sau youtube check --account her2home
   ```

3. **同步 Cookie 到共享文件夹**（Linux 定时任务复用）
   - 登录成功后，把 `cookies/youtube_her2home.json` 复制到 `/home/kan/shared/her2home/` 或确保项目在共享文件夹下

4. **配置代理（国内必需）**
   - YouTube.com 国内直连超时，需在 `conf.py` 设置：
     ```python
     YT_PROXY = "http://127.0.0.1:7890"  # 本地代理端口
     ```
   - patchright 启动的 Chromium 不吃系统代理，必须显式指定

5. **在 auto_publish.py 中启用 YouTube**
   - 已在 PLATFORMS 列表中添加 youtube 配置
   - 支持 `--visibility public|unlisted|private`（默认 public）
   - 支持 `--thumbnail` 封面上传
   - 需 `--headless` 无头模式（已在配置中设置）

### 已知限制

- **国内服务器必须配置代理**，否则登录/上传会超时
- 上传过程需保持浏览器窗口开启直到 100% 完成（否则卡在 76% 等进度）
- 无官方 API 公开发布权限（未审核项目强制私密），只能用浏览器自动化

### Cookie 格式问题（2026-06-30 会话新增）

YouTube 登录会产生**两类 Cookie**，`storage_state` 需要 **YouTube 域名的 Cookie** 才能工作：

| 类型 | 域名 | 用途 |
|------|------|------|
| Google 账号级 | `accounts.google.com`、`.google.com`、`.google.co.jp` | 核心登录态（HSID、SSID、SAPISID、SID、`__Secure-*` 等） |
| YouTube Studio 级 | `.youtube.com`、`.studio.youtube.com` | 后台专用（`LOGIN_INFO`、`YSC`、`VISITOR_INFO1_LIVE`、`SID`、`HSID` 等） |

**本次会话发现**：Windows 本地登录导出的 Cookie（`youtube_her2home.json`）**同时包含两类**，可直接替换服务器端文件。若仅导出 Google 账号级 Cookie，**无法直接用于 YouTube Studio 上传**（会被重定向到登录页）。

**修复步骤**：
```bash
# 1. 本地 Windows 完成登录后，找到导出的完整 Cookie 文件
# 2. 替换服务器共享文件夹
cp /home/kan/shared/youtube_her2home.json /home/kan/shared/social-auto-upload/cookies/youtube_her2home.json
# 3. 验证包含 .youtube.com 域名
grep -c '\.youtube\.com' /home/kan/shared/social-auto-upload/cookies/youtube_her2home.json
# 应输出 > 5
```

**注意**：Playwright `storage_state` 包含 `cookies` + `origins`(localStorage)。YouTube 需 `studio.youtube.com` 的 `localStorage`（如 `yt-icons-last-purged`），导出时会自动带上。

---

# Facebook/Meta 平台不支持说明

## social-auto-upload 现状

- **无 `facebook_uploader` 目录**
- **CLI 无 `sau facebook` 子命令**

## 原因

1. **Graph API 限制**
   - 个人账号发视频需 `pages_show_list` + `pages_read_engagement` + `pages_manage_posts` 权限
   - 这些权限需 **App Review（应用审核）**，个人/小项目极难通过
   - 未审核应用只能发到测试账号，无法公开分发

2. **无官方公开上传接口**
   - Meta 官方未提供类似 YouTube Data API 的公开视频上传 API
   - 现有方案均为逆向/浏览器自动化，极不稳定

3. **社区项目不维护 Facebook**
   - social-auto-upload、biliup-rs、douyin-uploader 等主流开源项目均不含 Facebook
   - 抖音/B站/小红书/快手/视频号/百家号/TikTok/YouTube 都有维护者，唯独 Facebook 无

## 替代方案（如必须发 Facebook）

| 方案 | 可行性 | 维护成本 |
|------|--------|----------|
| Selenium/Playwright 手写浏览器自动化 | 低（反爬强、验证码多、选择器易失效） | 极高 |
| 第三方 SaaS（Buffer、Hootsuite、Later、Publer） | 高（官方合作伙伴，API 稳定） | 需付费订阅 |
| Zapier/Make (Integromat) + Facebook Pages | 中（免费额度有限，需配置 Webhook） | 中 |
| 手动发布 | 100% 成功 | 人力成本 |

## 建议

- **短期**：继续用 social-auto-upload 覆盖国内 4 平台 + YouTube，Facebook 人工发布
- **长期**：如需自动化，预算允许时接入 Buffer/Hootsuite API 或 Zapier
- **不建议**投入精力维护 Facebook 浏览器自动化（ROI 极低）

---

# 参考文件位置

- `scripts/auto_publish.py` — 已含 YouTube 的自动分发脚本（需部署到 /home/kan/shared/her2home/）
- `references/youtube-facebook-support.md` — 本文件