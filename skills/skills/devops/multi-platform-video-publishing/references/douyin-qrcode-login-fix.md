# 抖音二维码登录 Bug 修复记录

## 问题现象
- `sau douyin login --account her2home` 显示二维码后 ~4 分钟超时
- 即使用户扫码也提示「二维码失效」或「登录失败: 等待抖音扫码登录超时」
- 错误日志：`NameError: name 'original_url' is not defined`

## 根因分析
文件：`uploader/douyin_uploader/main.py`
函数：`_wait_for_douyin_login()` (约第 160-202 行)

三个变量在使用前未初始化：
1. `original_url` - 第 173 行 `if page.url != original_url:` 但从未赋值
2. `saw_2fa` - 第 186 行 `if not saw_2fa:` 但从未赋值
3. `i` - 第 187 行 `({i}/{max_checks})` 但循环变量名为 `_`，未绑定 `i`

此外，二维码有效期极短（约 4 分钟），原有自动刷新逻辑仅在检测到「二维码失效」文本时触发，但该元素可能不出现或检测失败。

## 修复补丁
应用于 `/home/kan/shared/social-auto-upload/uploader/douyin_uploader/main.py`：

```python
# 第 160 行附近：初始化三个变量
original_url = page.url
saw_2fa = False
i = 0

# 在 while 循环内（约第 196 行后）：主动每 30 秒刷新二维码
# poll_interval=3s, 10*3=30s
if i > 0 and i % 10 == 0:
    try:
        refresh_btn = page.get_by_text("刷新", exact=True).first
        if await refresh_btn.count() and await refresh_btn.is_visible():
            await refresh_btn.click()
            await asyncio.sleep(1)
            qrcode_info = await _save_douyin_qrcode(page, account_file, qrcode_path, qrcode_callback=qrcode_callback)
            qrcode_path = Path(qrcode_info["image_path"]) if qrcode_info.get("image_path") else None
            douyin_logger.info(_msg("🔄", "主动刷新二维码"))
    except Exception:
        pass
```

## 操作建议
1. 登录前确保修复已应用
2. 运行 `sau douyin login --account <name>` 后，**立即打开 HTTP 链接扫码**：
   `http://10.10.10.30:8080/social-auto-upload/cookies/douyin_her2home_login_qrcode_<timestamp>.png`
3. 二维码每 30 秒自动刷新，以最新文件为准
4. 登录成功后会生成 `cookies/douyin_her2home.json`，后续复用

### 远程扫码最佳实践（本次会话新增）
**首选 Tailscale** — 已有节点 `100.84.133.58`，手机开 Tailscale 直接访问固定链接：
```
http://100.84.133.58:8080/social-auto-upload/cookies/douyin_her2home_latest_qrcode.png
```
- 固定链接指向最新二维码（软链自动更新），无需刷新浏览器
- 登录进程跑完自动生成 `cookies/douyin_her2home.json`

备选 ngrok — 需认证，临时隧道配置繁琐

## 验证命令
```bash
sau douyin check --account her2home  # 应返回 valid
```

## 关联文件
- `scripts/auto_publish.py` — 自动分发主脚本（依赖所有平台 cookie 有效）
- `scripts/login_all_platforms.sh` — 一键登录脚本（含抖音）