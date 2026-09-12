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
FP="$ROOT/bin/ffmpeg-9.0.1-essentials_build/bin/ffprobe.exe"
CHROME="C:/Program Files/Google/Chrome/Application/chrome.exe"
REMIX="$POC/node_modules/.bin/remotion"
OPENING_OUT="$OUT/opening_anim.mp4"
PIANO="$ROOT/output/mp3/Romeo - Winds of Hope - Creative Cut - Piano.mp3"
OPEN_FRAMES=270
PY="C:/Users/Administrator/AppData/Local/Programs/Python/Python311/python.exe"
LOG="$OUT/render.log"

mkdir -p "$OUT"

# 1) 计算总帧数（与 Remotion Root.tsx 一致）
if [ -n "${TOTAL_FRAMES:-}" ]; then
  TOTAL="$TOTAL_FRAMES"
else
  TOTAL=$("$PY" -c "import json;d=json.load(open(r'$POC/src/weekly_segs.json'));print(int(round(sum(x['dur'] for x in d)*30)))")
fi
FULL_TOTAL=$(( OPEN_FRAMES + TOTAL ))
echo "[$(date +%H:%M:%S)] TOTAL_FRAMES=$TOTAL  OPEN_FRAMES=$OPEN_FRAMES  FULL_TOTAL=$FULL_TOTAL  CHUNK=$CHUNK  CRF=$CRF" | tee -a "$LOG"

NPARTS=$(( (TOTAL + CHUNK - 1) / CHUNK ))

# 校验单个 part 的视频帧数是否等于期望帧数（防"渲染被杀留下残缺文件被当成功"）
# 用 count_packets 而非 nb_frames：部分 mp4 不写 nb_frames 元数据
check_part_frames() {
  local part="$1" expected="$2"
  local nb
  nb=$("$FP" -v error -select_streams v:0 -count_packets \
       -show_entries stream=nb_read_packets -of default=noprint_wrappers=1:nokey=1 "$part" 2>/dev/null | tr -d '[:space:]\r')
  [ -n "$nb" ] && [ "$nb" -eq "$expected" ]
}

# 2) 渲染片头 OpeningAnimation（幂等）
if [ -f "$OPENING_OUT" ] && check_part_frames "$OPENING_OUT" "$OPEN_FRAMES"; then
  echo "[$(date +%H:%M:%S)] skip opening (already done, ${OPEN_FRAMES} frames ok)" | tee -a "$LOG"
else
  echo "[$(date +%H:%M:%S)] render OpeningAnimation ${OPEN_FRAMES} frames" | tee -a "$LOG"
  rm -f "$OPENING_OUT"
  ( cd "$POC" && "$REMIX" render OpeningAnimation "$OPENING_OUT" --concurrency=2 --browser-executable="$CHROME" --chrome-flags="--disable-accelerated-video-decode --disable-gpu" ) >> "$LOG" 2>&1
  if ! check_part_frames "$OPENING_OUT" "$OPEN_FRAMES"; then
    echo "!! OpeningAnimation 渲染失败或帧数不足（期望 ${OPEN_FRAMES}）" >&2
    exit 1
  fi
fi

# 3) 逐段渲染 WeeklyTalk（幂等：跳过已完成段）
#    注意：Remotion --frames 接受闭区间 "start-end"（短横线），端点为帧索引，
#          最大有效帧 = TOTAL-1（durationInFrames=TOTAL，0-based）。
for ((i=0;i<NPARTS;i++)); do
  start=$((i*CHUNK))
  end=$(( start + CHUNK - 1 ))
  [ "$end" -ge "$TOTAL" ] && end=$((TOTAL - 1))
  part="$OUT/part$(printf '%02d' $i).mp4"
  expected=$(( end - start + 1 ))
  if [ -f "$part" ] && grep -q "PART DONE $i " "$LOG" 2>/dev/null; then
    if check_part_frames "$part" "$expected"; then
      echo "[$(date +%H:%M:%S)] skip part $i (already done, frames ok)" | tee -a "$LOG"
      continue
    else
      # 已标记 DONE 但帧数不符（历史残缺段）-> 删掉重渲染
      echo "[$(date +%H:%M:%S)] part $i 已标记 DONE 但帧数不足（期望 $expected），删除重渲染" | tee -a "$LOG"
      rm -f "$part"
      sed -i "/PART DONE $i /d" "$LOG"
    fi
  fi
  echo "[$(date +%H:%M:%S)] render part $i  frames=$start-$end" | tee -a "$LOG"
  ( cd "$POC" && "$REMIX" render WeeklyTalk "$part" --frames="$start-$end" --concurrency=2 --browser-executable="$CHROME" --chrome-flags="--disable-accelerated-video-decode --disable-gpu" ) >> "$LOG" 2>&1
  if [ -f "$part" ] && check_part_frames "$part" "$expected"; then
    echo "PART DONE $i $(date +%H:%M:%S)" >> "$LOG"
  else
    echo "PART FAILED $i $(date +%H:%M:%S) (frames<${expected})" >> "$LOG"
    rm -f "$part"   # 清掉残缺文件，防止下次误判成功
    echo "!! part $i 渲染失败或帧数不足（期望 $expected），检查 $LOG 后重跑本脚本即可续渲染" >&2
    exit 1
  fi
done

# 若最终成片已存在、FINAL DONE 已记录且帧数校验通过，则跳过拼接/重编码
if [ -f "$OUT/signal_pop_weekly_$DATE.mp4" ] && grep -q "FINAL DONE" "$LOG" 2>/dev/null; then
  if check_part_frames "$OUT/signal_pop_weekly_$DATE.mp4" "$FULL_TOTAL"; then
    echo "[$(date +%H:%M:%S)] 成片已存在且帧数完整，跳过拼接/重编码" | tee -a "$LOG"
    exit 0
  fi
  echo "[$(date +%H:%M:%S)] 警告：成片已存在但帧数不完整，强制重建" | tee -a "$LOG"
fi

# 4) 拼接：片头 + WeeklyTalk 各段（copy），再整体 CRF26 重编码 + 合并完整音频
SILENT="$POC/out/WeeklyTalk_silent.mp4"
FINAL="$OUT/signal_pop_weekly_$DATE.mp4"
AUDIO="$OUT/audio/tts.wav"
AUDIO_FULL="$OUT/audio/full_audio.wav"
LIST="$OUT/concat_list.txt"

: > "$LIST"
echo "file '$OPENING_OUT'" >> "$LIST"
for ((i=0;i<NPARTS;i++)); do
  echo "file '$OUT/part$(printf '%02d' $i).mp4'" >> "$LIST"
done

echo "[$(date +%H:%M:%S)] concat opening + parts (copy)" | tee -a "$LOG"
"$FF" -y -f concat -safe 0 -i "$LIST" -c copy "$SILENT" >> "$LOG" 2>&1

# 拼接结果校验：总帧数必须等于 FULL_TOTAL，否则禁止进入成片阶段（拦截残缺成片）
if ! check_part_frames "$SILENT" "$FULL_TOTAL"; then
  nb=$("$FP" -v error -select_streams v:0 -count_packets -show_entries stream=nb_read_packets -of default=noprint_wrappers=1:nokey=1 "$SILENT" 2>/dev/null | tr -d '[:space:]\r')
  echo "!! 拼接后帧数 $nb != 期望 $FULL_TOTAL，某段残缺，已阻止生成成片。删除对应 part 后重跑本脚本。" >&2
  exit 1
fi

if [ ! -f "$AUDIO" ]; then
  echo "!! 缺少 TTS 音频 $AUDIO（请先跑 gen_dual_tts.py）" >&2
  exit 1
fi
if [ ! -f "$PIANO" ]; then
  echo "!! 缺少片头钢琴配乐 $PIANO" >&2
  exit 1
fi

# 组装完整音频：前 9s 钢琴配乐 + TTS 整体延后 OPEN_FRAMES 帧
mkdir -p "$OUT/audio"
echo "[$(date +%H:%M:%S)] build full audio (piano 9s + tts delayed ${OPEN_FRAMES} frames)" | tee -a "$LOG"
"$FF" -y -ss 0 -t 9 -i "$PIANO" -i "$AUDIO" -filter_complex "[0:a]aformat=sample_fmts=fltp:sample_rates=24000:channel_layouts=mono[head];[1:a]aformat=sample_fmts=fltp:sample_rates=24000:channel_layouts=mono[tail];[head][tail]concat=n=2:v=0:a=1[out]" -map "[out]" -ar 24000 -ac 1 -c:a pcm_s16le "$AUDIO_FULL" >> "$LOG" 2>&1

echo "[$(date +%H:%M:%S)] re-encode CRF$CRF + merge audio" | tee -a "$LOG"
"$FF" -y -i "$SILENT" -i "$AUDIO_FULL" -c:v libx264 -preset fast -crf "$CRF" -pix_fmt yuv420p -c:a aac -b:a 192k -ar 24000 -ac 1 -map 0:v:0 -map 1:a:0 "$FINAL" >> "$LOG" 2>&1

# 成片帧数校验
if ! check_part_frames "$FINAL" "$FULL_TOTAL"; then
  nb=$("$FP" -v error -select_streams v:0 -count_packets -show_entries stream=nb_read_packets -of default=noprint_wrappers=1:nokey=1 "$FINAL" 2>/dev/null | tr -d '[:space:]\r')
  echo "!! 成片帧数 $nb != 期望 $FULL_TOTAL，合成异常。" >&2
  exit 1
fi

echo "FINAL DONE $(date +%H:%M:%S)" >> "$LOG"
echo "[$(date +%H:%M:%S)] 完成: $FINAL" | tee -a "$LOG"
