#!/usr/bin/env bash
# =============================================================
# 周末版 · 竖版 9:16 衍生生成（signal_pop）
# -------------------------------------------------------------
# reframe 能力迁移自 ZJU-REAL/Easel（Apache 2.0），迁移说明见
# E:/projects/Easel/outputs/reframe_migration_package/迁移说明.md
#
# 用法：
#   bash tools/reframe_weekly_vertical.sh <制作日> [MODE] [FORCE]
#     <制作日>  例如 20261002
#     MODE      blur（默认，2026-09-26 用户选定：完整画面+模糊延展，字幕无损）| smart | crop
#     FORCE     1 = 已有竖版也强制重做（默认跳过幂等）
#
# 输入（只读，不改动）：output/weekly/<日期>/signal_pop_weekly_<日期>.mp4
# 输出（新子目录）：    output/weekly/<日期>/vertical/signal_pop_weekly_<日期>_9x16.mp4
#
# 解释器说明：走 WorkBuddy 隔离 venv（cv2 4.14，smart 人脸检测可用）。
# 项目 Python311 的 opencv 是 5.0（已移除 CascadeClassifier），不动它；
# 即使误用 5.0，reframe.py 也会优雅降级为居中裁切，不会崩。
#
# 退出码：0 成功/幂等跳过；1 成片缺失或转换/校验失败。
# =============================================================
set -u

DATE="${1:?用法: bash tools/reframe_weekly_vertical.sh <制作日> [smart|blur|crop] [FORCE]}"
MODE="${2:-blur}"
FORCE="${3:-0}"

ROOT="E:/projects/signal_pop"
OUT="$ROOT/output/weekly/$DATE"
SRC="$OUT/signal_pop_weekly_$DATE.mp4"
VDIR="$OUT/vertical"
DST="$VDIR/signal_pop_weekly_${DATE}_9x16.mp4"
FFBIN="$ROOT/bin/ffmpeg-9.0.1-essentials_build/bin"
FP="$FFBIN/ffprobe.exe"
REFRAME_PY="C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe"
REFRAME_PP="C:/Users/Administrator/.workbuddy/binaries/python/envs/default/Lib/site-packages"
SCRIPT="$ROOT/tools/reframe.py"

[ -f "$SRC" ] || { echo "!! 成片不存在: $SRC（先跑 render_weekly_segmented.sh）"; exit 1; }
[ -f "$SCRIPT" ] || { echo "!! 缺少脚本: $SCRIPT"; exit 1; }

probe_wh() {
  # 注意：ffmpeg 9.0.1 的 csv=s=x 输出带尾部分隔符（如 1080x1920x），cut 只取前两段
  "$FP" -v error -select_streams v:0 -show_entries stream=width,height \
       -of csv=s=x:p=0 "$1" 2>/dev/null | tr -d '[:space:]\r' | cut -d'x' -f1-2
}
has_audio() {
  [ -n "$("$FP" -v error -select_streams a -show_entries stream=index -of csv=p=0 "$1" 2>/dev/null | tr -d '[:space:]\r')" ]
}

mkdir -p "$VDIR"

# 幂等：已存在且 1080x1920 + 有音轨则跳过（FORCE=1 强制重做）
if [ "$FORCE" != "1" ] && [ -f "$DST" ]; then
  wh="$(probe_wh "$DST")"
  if [ "$wh" = "1080x1920" ] && has_audio "$DST"; then
    echo "[$(date +%H:%M:%S)] 竖版已存在且校验通过，跳过（FORCE=1 可重做）: $DST"
    exit 0
  fi
  echo "[$(date +%H:%M:%S)] 已有竖版但校验不通过（wh=$wh），重做"
fi

echo "[$(date +%H:%M:%S)] reframe $MODE: $SRC -> $DST"
PATH="$FFBIN:$PATH" PYTHONPATH="$REFRAME_PP" "$REFRAME_PY" "$SCRIPT" reframe \
  -i "$SRC" -o "$DST" --ratio 9:16 --mode "$MODE" --size 1080x1920 || {
  echo "!! reframe 执行失败"; exit 1; }

# 产物校验：尺寸 + 音轨（拦截静默失败）
wh="$(probe_wh "$DST")"
if [ "$wh" != "1080x1920" ]; then
  echo "!! 竖版尺寸异常：期望 1080x1920，实得 $wh"; exit 1
fi
if ! has_audio "$DST"; then
  echo "!! 竖版音轨丢失"; exit 1
fi

echo "[$(date +%H:%M:%S)] 完成: $DST（1080x1920，音轨保留，模式 $MODE）"
