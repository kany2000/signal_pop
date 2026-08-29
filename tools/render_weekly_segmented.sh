#!/usr/bin/env bash
# =============================================================
# 周末版 · 应急分段渲染脚本（signal_pop）
# -------------------------------------------------------------
# 用途：标准管线 `tools/remotion_weekly_build.py`（单次 remotion render）
#       在本环境会被后台任务回收（长渲染静默被杀）时使用。
#       本脚本把整片切成若干短段分别渲染，最后拼接 + 整体重编码，
#       规避单次长渲染被回收的问题。
#
# 用法：
#   bash tools/render_weekly_segmented.sh <制作日> [CHUNK]
#     <制作日>  例如 20260828
#     CHUNK     每段帧数，默认 1000（≈33s @30fps）；单段够短以扛过回收
#
# 特性：
#   * 幂等 + 可续：已完成的段（part 文件存在且 render.log 标记 PART DONE）
#     自动跳过；后台任务被回收后重跑本脚本即从断点继续。
#   * 总帧数自动从 remotion_poc/src/weekly_segs.json 计算
#     （round(sum(seg.dur)*30)），与 Root.tsx 的 durationInFrames 完全一致，
#     不硬编码。可用环境变量 TOTAL_FRAMES 覆盖。
#   * 关键约束：拼接用 -c copy 保留各段 Remotion 编码，最后再用
#     libx264 CRF26 整体重编码一遍并合并 TTS 音频，确保接缝/关键帧被抹平、
#     码率统一（CRF 见下方 CRF 变量，锁定为 26）。
#
# 退出码：某段渲染失败 -> 1（检查 render.log 后重跑即可）；缺 TTS -> 1。
# =============================================================
set -u

DATE="${1:?用法: bash tools/render_weekly_segmented.sh <制作日> [CHUNK]}"
CHUNK="${2:-1000}"
CRF="${CRF:-26}"

ROOT="E:/projects/signal_pop"
POC="$ROOT/remotion_poc"
OUT="$ROOT/output/weekly/$DATE"
FF="$ROOT/bin/ffmpeg-9.0.1-essentials_build/bin/ffmpeg.exe"
CHROME="C:/Program Files/Google/Chrome/Application/chrome.exe"
REMIX="$POC/node_modules/.bin/remotion"
PY="C:/Users/Administrator/AppData/Local/Programs/Python/Python311/python.exe"
LOG="$OUT/render.log"

mkdir -p "$OUT"

# 1) 计算总帧数（与 Remotion Root.tsx 一致）
if [ -n "${TOTAL_FRAMES:-}" ]; then
  TOTAL="$TOTAL_FRAMES"
else
  TOTAL=$("$PY" -c "import json;d=json.load(open(r'$POC/src/weekly_segs.json'));print(int(round(sum(x['dur'] for x in d)*30)))")
fi
echo "[$(date +%H:%M:%S)] TOTAL_FRAMES=$TOTAL  CHUNK=$CHUNK  CRF=$CRF" | tee -a "$LOG"

NPARTS=$(( (TOTAL + CHUNK - 1) / CHUNK ))

# 2) 逐段渲染（幂等：跳过已完成段）
#    注意：Remotion --frames 接受闭区间 "start-end"（短横线），端点为帧索引，
#          最大有效帧 = TOTAL-1（durationInFrames=TOTAL，0-based）。
for ((i=0;i<NPARTS;i++)); do
  start=$((i*CHUNK))
  end=$(( start + CHUNK - 1 ))
  [ "$end" -ge "$TOTAL" ] && end=$((TOTAL - 1))
  part="$OUT/part$(printf '%02d' $i).mp4"
  if [ -f "$part" ] && grep -q "PART DONE $i " "$LOG" 2>/dev/null; then
    echo "[$(date +%H:%M:%S)] skip part $i (already done)" | tee -a "$LOG"
    continue
  fi
  echo "[$(date +%H:%M:%S)] render part $i  frames=$start-$end" | tee -a "$LOG"
  ( cd "$POC" && "$REMIX" render WeeklyTalk "$part" --frames="$start-$end" --concurrency=8 --browser-executable="$CHROME" ) >> "$LOG" 2>&1
  if [ -f "$part" ]; then
    echo "PART DONE $i $(date +%H:%M:%S)" >> "$LOG"
  else
    echo "PART FAILED $i $(date +%H:%M:%S)" >> "$LOG"
    echo "!! part $i 渲染失败，检查 $LOG 后重跑本脚本即可续渲染" >&2
    exit 1
  fi
done

# 若最终成片已存在且本片 FINAL DONE 已记录，则跳过拼接/重编码
if [ -f "$OUT/signal_pop_weekly_$DATE.mp4" ] && grep -q "FINAL DONE" "$LOG" 2>/dev/null; then
  echo "[$(date +%H:%M:%S)] 成片已存在，跳过拼接/重编码" | tee -a "$LOG"
  exit 0
fi

# 3) 拼接（copy）+ 整体 CRF26 重编码 + 合并 TTS
SILENT="$POC/out/WeeklyTalk_silent.mp4"
FINAL="$OUT/signal_pop_weekly_$DATE.mp4"
AUDIO="$OUT/audio/tts.wav"
LIST="$OUT/concat_list.txt"

: > "$LIST"
for ((i=0;i<NPARTS;i++)); do
  echo "file '$OUT/part$(printf '%02d' $i).mp4'" >> "$LIST"
done

echo "[$(date +%H:%M:%S)] concat parts (copy)" | tee -a "$LOG"
"$FF" -y -f concat -safe 0 -i "$LIST" -c copy "$SILENT" >> "$LOG" 2>&1

if [ ! -f "$AUDIO" ]; then
  echo "!! 缺少 TTS 音频 $AUDIO（请先跑 gen_dual_tts.py）" >&2
  exit 1
fi

echo "[$(date +%H:%M:%S)] re-encode CRF$CRF + merge audio" | tee -a "$LOG"
"$FF" -y -i "$SILENT" -i "$AUDIO" -c:v libx264 -preset fast -crf "$CRF" -pix_fmt yuv420p -c:a aac -b:a 192k -ar 24000 -ac 1 -map 0:v:0 -map 1:a:0 "$FINAL" >> "$LOG" 2>&1

echo "FINAL DONE $(date +%H:%M:%S)" >> "$LOG"
echo "[$(date +%H:%M:%S)] 完成: $FINAL" | tee -a "$LOG"
