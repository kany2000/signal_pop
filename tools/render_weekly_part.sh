#!/usr/bin/env bash
# =============================================================
# 周末版 · 单段渲染驱动（signal_pop）
# 用途：本环境后台任务进程树会被回收（nohup/非沙箱均被杀），
#       只能前台跑。本脚本每次只渲染一个 part，配合外部循环调用。
# 用法：bash tools/render_weekly_part.sh <制作日> <part序号> [CHUNK]
# 幂等：part 已完成（文件存在 + render.log 有 PART DONE + 帧数吻合）直接跳过。
# =============================================================
set -u
DATE="${1:?用法: bash tools/render_weekly_part.sh <制作日> <part序号> [CHUNK]}"
IDX="${2:?need part index}"
CHUNK="${3:-1000}"
CRF="${CRF:-26}"

ROOT="E:/projects/signal_pop"
POC="$ROOT/remotion_poc"
OUT="$ROOT/output/weekly/$DATE"
FF="$ROOT/bin/ffmpeg-9.0.1-essentials_build/bin/ffmpeg.exe"
FP="$ROOT/bin/ffmpeg-9.0.1-essentials_build/bin/ffprobe.exe"
CHROME="C:/Program Files/Google/Chrome/Application/chrome.exe"
REMIX="$POC/node_modules/.bin/remotion"
PY="C:/Users/Administrator/AppData/Local/Programs/Python/Python311/python.exe"
LOG="$OUT/render.log"

mkdir -p "$OUT"

TOTAL=$("$PY" -c "import json;d=json.load(open(r'$POC/src/weekly_segs.json'));print(int(round(sum(x['dur'] for x in d)*30)))")
NPARTS=$(( (TOTAL + CHUNK - 1) / CHUNK ))
if [ "$IDX" -ge "$NPARTS" ]; then echo "IDX $IDX >= NPARTS $NPARTS"; exit 2; fi

check_part_frames() {
  local part="$1" expected="$2" nb
  nb=$("$FP" -v error -select_streams v:0 -count_packets \
       -show_entries stream=nb_read_packets -of default=noprint_wrappers=1:nokey=1 "$part" 2>/dev/null | tr -d '[:space:]\r')
  [ -n "$nb" ] && [ "$nb" -eq "$expected" ]
}

start=$((IDX*CHUNK)); end=$(( start + CHUNK - 1 ))
[ "$end" -ge "$TOTAL" ] && end=$((TOTAL - 1))
part="$OUT/part$(printf '%02d' $IDX).mp4"
expected=$(( end - start + 1 ))

if [ -f "$part" ] && grep -q "PART DONE $IDX " "$LOG" 2>/dev/null; then
  if check_part_frames "$part" "$expected"; then
    echo "[$(date +%H:%M:%S)] skip part $IDX (done, frames ok)"; exit 0
  fi
  rm -f "$part"; sed -i "/PART DONE $IDX /d" "$LOG"
fi

echo "[$(date +%H:%M:%S)] render part $IDX  frames=$start-$end (expected $expected)" | tee -a "$LOG"
( cd "$POC" && "$REMIX" render WeeklyTalk "$part" --frames="$start-$end" --concurrency=2 --browser-executable="$CHROME" --chrome-flags="--disable-accelerated-video-decode --disable-gpu" ) >> "$LOG" 2>&1
if [ -f "$part" ] && check_part_frames "$part" "$expected"; then
  echo "PART DONE $IDX $(date +%H:%M:%S)" >> "$LOG"
  echo "[$(date +%H:%M:%S)] PART DONE $IDX"
else
  echo "PART FAILED $IDX $(date +%H:%M:%S)" >> "$LOG"
  rm -f "$part"
  echo "!! part $IDX FAILED"; exit 1
fi
