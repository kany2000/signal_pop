# 抖音二维码登录 Bug 精确补丁记录

## 问题背景
`social-auto-upload` 上游 `uploader/douyin_uploader/main.py` 的 `_wait_for_douyin_login()` 存在三个未定义变量导致崩溃：
- `original_url` - 第 175 行使用但未定义
- `saw_2fa` - 第 183 行使用但未定义
- `i` - 第 189 行 `if i % 10 == 0` 使用但未定义（循环变量被 `max_checks` 替代）

且二维码自动刷新机制失效，有效期仅 ~4 分钟。

## 补丁位置
文件: `/home/kan/shared/social-auto-upload/uploader/douyin_uploader/main.py`

### 补丁 1: 变量初始化 (约第 135-152 行后)
```python
# 在 _wait_for_douyin_login 开头添加
original_url = page.url
saw_2fa = False
i = 0  # 计数器，用于每 10 次轮询刷新二维码
```

### 补丁 2: 主动刷新二维码 (约第 197-210 行，替换原有轮询逻辑)
```python
for i in range(max_checks):
    # 页面导航检测
    if page.url != original_url and "creator.douyin.com" in page.url:
        logger.success("检测到页面跳转，登录成功")
        break

    # 2FA 检测
    if "2fa" in page.url.lower() or "verify" in page.url.lower():
        if not saw_2fa:
            logger.warning("检测到二次验证，请在手机上完成")
            saw_2fa = True

    # 每 30 秒主动点击刷新按钮强制换码 (poll_interval=3s, 10*3=30s)
    if i % 10 == 0:
        try:
            refresh_btn = page.locator('button:has-text("刷新"), .qrcode-refresh-btn, [class*="refresh"]').first
            if await refresh_btn.count() > 0:
                await refresh_btn.click()
                logger.info("已点击刷新二维码")
                await page.wait_for_timeout(2000)
        except Exception:
            pass

    await page.wait_for_timeout(poll_interval * 1000)
```

### 补丁 3: 固定链接软链创建 (在 _save_douyin_qrcode 中，约第 142-150 行)
```python
# 保存二维码后，创建/更新固定链接指向最新二维码
latest_link = qrcode_path.parent / f"douyin_{Path(account_file).stem}_latest_qrcode.png"
try:
    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    latest_link.symlink_to(qrcode_path.name)
except Exception:
    pass
```

### 补丁 4: 函数签名透传 qrcode_path (约第 238 行)
```python
# 修改前
await self._save_douyin_qrcode(page, account_name)

# 修改后
await self._save_douyin_qrcode(page, account_name, qrcode_path=latest_qrcode)
```

## 稳定访问链接
- 局域网: `http://10.10.10.30:8080/social-auto-upload/cookies/douyin_her2home_latest_qrcode.png`
- Tailscale: `http://100.84.133.58:8080/social-auto-upload/cookies/douyin_her2home_latest_qrcode.png`

手机开 Tailscale 直接访问固定链接，**无需刷新**，对着屏幕用抖音扫一扫即可。