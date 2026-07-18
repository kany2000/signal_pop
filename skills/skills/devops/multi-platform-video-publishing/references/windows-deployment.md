# Windows 本地部署与登录指南

## 背景
social-auto-upload 在 Linux 无头模式下登录抖音/快手等平台存在 Bug（二维码刷新变量未定义、EPIPE 崩溃、扫码后确认页处理失败）。Windows 本地有头模式最稳，登录后同步 Cookie 回 Linux 服务器即可。

## 核心坑点与解决方案

### 1. requirements.txt 编码问题（UTF-16 + null 字节）
**现象**：`cat requirements.txt` 显示乱码，`pip install -r requirements.txt` 读取异常。
**原因**：原仓库 `requirements.txt` 为 UTF-16 LE 带 BOM，每字符间有 `\x00`。
**方案**：使用 UTF-8 重写的 `requirements_win.txt`（见 SKILL.md 部署流程 1b）。

### 2. aiohttp 版本不兼容 Python 3.13+
**现象**：
```
ERROR: Could not find a version that satisfies the requirement aiohttp==3.9.5
```
**原因**：aiohttp 3.9.x 无 Python 3.13 wheel，pip 尝试从源码编译，需 C++ Build Tools。
**方案**：升级到 `aiohttp==3.11.15`（首个完整支持 Python 3.13 的版本，有官方 wheel）。

### 3. C++ Build Tools 缺失
**现象**：
```
error: Microsoft Visual C++ 14.0 or greater is required
```
**方案（按推荐顺序）**：
1. **用兼容版本 + wheel**（最快）：`requirements_win.txt` 已规避需编译的包
2. **强制只用 wheel**：`pip install --only-binary :all: -r requirements_win.txt`
3. **安装 Build Tools**：https://visualstudio.microsoft.com/visual-cpp-build-tools/（勾选 C++ build tools + Windows 10 SDK）

### 4. playwright vs patchright
- Linux 服务器用 `patchright`（无头模式稳定）
- Windows 本地用 `playwright`（有头模式扫码稳定）
- 两者 API 兼容，`playwright install chromium` 即可

## 完整 Windows 登录流程

```powershell
# 1. 获取项目
cp -r \\10.10.10.30\shared\social-auto-upload E:\projects\
cd E:\projects\social-auto-upload

# 2. 创建 UTF-8 requirements_win.txt（内容见 SKILL.md）
# 3. 安装
pip install -r requirements_win.txt
playwright install chromium

# 4. 登录（有头模式，无需 --headless）
python sau_cli.py douyin login --account her2home
# 抖音扫码 → 浏览器自动打开确认页 → 等待"登录成功"日志

# 5. 验证
python sau_cli.py douyin check --account her2home
# 输出 "valid" 即成功

# 6. 同步 Cookie 回 Linux
# 选项 A：文件管理器复制 cookies/ 文件夹到共享文件夹
# 选项 B：Git 提交（cookies/ 在 .gitignore，需强制添加或手动同步）
# 选项 C：直接在共享文件夹挂载盘操作（推荐，无需同步）

# 7. Linux 验证
ssh kan@server
cd /home/kan/shared/social-auto-upload
python sau_cli.py douyin check --account her2home
```

## 常见问题

| 问题 | 解决 |
|------|------|
| 终端二维码显示乱码 | 用 Windows Terminal / PowerShell 7+（支持 UTF-8），或直接打开 PNG 文件扫码 |
| 扫码后浏览器卡在"等待确认" | 抖音需在手机 APP 点击"确认登录"，浏览器会自动关闭 |
| 登录成功但 check 显示 invalid | 等待 5-10 秒 Cookie 落盘，或重新 check |
| 想同时登录多平台 | 依次运行 `python sau_cli.py <platform> login --account her2home`，浏览器会复用同一上下文 |

## 关键文件位置（Windows）
```
E:\projects\social-auto-upload\
├── cookies\
│   ├── douyin_her2home.json           # 抖音 Cookie
│   ├── bilibili_her2home.json         # B站 Cookie
│   ├── xiaohongshu_her2home.json      # 小红书 Cookie
│   ├── kuaishou_her2home.json         # 快手 Cookie
│   └── douyin_her2home_login_qrcode_*.png  # 临时二维码
├── requirements_win.txt                # Windows 专用依赖（UTF-8）
└── sau_cli.py                          # CLI 入口
```