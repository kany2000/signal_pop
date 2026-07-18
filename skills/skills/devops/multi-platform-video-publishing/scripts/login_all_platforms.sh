#!/usr/bin/env bash
# 一键登录脚本 - 依次登录 4 个平台
# 用法: bash login_all_platforms.sh
# 依赖: sau 命令已在 PATH 中（通过 wrapper）

set -euo pipefail

ACCOUNT="her2home"
SAU="/home/kan/.local/bin/sau"

echo "=== 开始批量登录 (账号: $ACCOUNT) ==="

# B站 - 有头模式扫码更稳
echo "[1/4] 登录 B站..."
$SAU bilibili login --account "$ACCOUNT"

# 小红书 - 无头模式
echo "[2/4] 登录 小红书..."
$SAU xiaohongshu login --account "$ACCOUNT" --headless

# 快手 - 无头模式
echo "[3/4] 登录 快手..."
$SAU kuaishou login --account "$ACCOUNT" --headless

# 抖音 - 无头模式 + 固定二维码链接
echo "[4/4] 登录 抖音 (请在 4 分钟内扫码)..."
echo "固定二维码链接: http://100.84.133.58:8080/social-auto-upload/cookies/douyin_${ACCOUNT}_latest_qrcode.png"
$SAU douyin login --account "$ACCOUNT" --headless

echo "=== 批量登录完成 ==="
echo "验证 Cookie 状态:"
$SAU bilibili check --account "$ACCOUNT"
$SAU xiaohongshu check --account "$ACCOUNT"
$SAU kuaishou check --account "$ACCOUNT"
$SAU douyin check --account "$ACCOUNT"