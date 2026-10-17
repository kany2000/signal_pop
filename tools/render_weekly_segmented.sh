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
# 本机 Remotion 调用方式（三条铁律，都实测踩过）：
#   ① `node_modules/.bin/remotion` 是 **shell shim**，在 Git Bash 下会报
#      `SyntaxError: Invalid or unexpected token` —— 必须直调 CLI 的 JS 入口。
#   ② props 参数名是 `--props`（不是新版的 `--input-props`，后者被静默忽略）。
#   ③ 2026-10-16 根因定位（连踩 3 次才找到，17~19 秒即挂，报
#      `node ...: No such file or directory`）：
#      **`$NODE` 必须带 `.exe` 后缀**。Git Bash 里 `node`（无后缀）能解析到
#      PATH 里的 shim，但脚本内是 `( cd "$POC" && "$REMIX" ... )` 子 shell，
#      Windows 按字面找 `node` 这个文件 → 报 No such file or directory。
#      三个修复叠加才稳：① 绝对路径 ② 带 .exe ③ JS 入口也用绝对路径（不吃 cwd）。
NODE="C:/Users/Administrator/.workbuddy/binaries/node/versions/22.22.2-6/node.exe"
REMIX="$NODE $POC/node_modules/@remotion/cli/remotion-cli.js"
OPENING_OUT="$OUT/opening_anim.mp4"
PIANO="$ROOT/output/mp3/Romeo - Winds of Hope - Creative Cut - Piano.mp3"
OPEN_FRAMES=270
PY="C:/Users/Administrator/AppData/Local/Programs/Python/Python311/python.exe"
# 片头 Composition id + 片头配乐在钢琴曲里的起点（秒）
# 2026-10-12：MARK哥定版 V4「新闻联播式过场」为**每期标配**，替换原 OpeningAnimation（纸卡 3D）。
# V4 零人物/零 Logo，换成宋体 Noto Serif SC + 地球弧线 + 横向光带。
OPENING_ID="${OPENING_ID:-OpeningV4}"
PIANO_START="${PIANO_START:-34}"
# 片头文案（每期可覆盖，不改代码）
# ⚠️ 之前 title/date/weekday 是硬编码在 Root.tsx 的 defaultProps 里，
# 意味着每期都要手改 TSX 才会更新日期 —— 已改为可用环境变量注入。
# 日期留空时从制作日 $DATE 推导（20261002 → 2026年10月3日周六，按发布日算）。
OPENING_TITLE="${OPENING_TITLE:-AI语播·信号弹每周精选}"
OPENING_DATE="${OPENING_DATE-}"
OPENING_WEEKDAY="${OPENING_WEEKDAY-}"
if [ -z "$OPENING_DATE" ] || [ -z "$OPENING_WEEKDAY" ]; then
  read -r OPENING_DATE OPENING_WEEKDAY <<<"$("$PY" -c "
import datetime
d=datetime.datetime.strptime('$DATE','%Y%m%d')+datetime.timedelta(days=1)  # 周五制作→周六发布
wk=['星期一','星期二','星期三','星期四','星期五','星期六','星期日'][d.weekday()]
print(f'{d.year}年{d.month}月{d.day}日', wk)")"
fi
# 片头配乐淡入淡出（秒）
# 时长必须与 OpeningAnimationV4 的画面淡入淡出对齐，否则音画不同步：
#   画面 bgFade  = frame 0→36   （36 帧 = 1.2s 淡入）
#   画面 fadeOut = frame 240→269（30 帧 = 1.0s 淡出至黑）
# 淡出终点正好落在 9.0s = TTS 起点，配乐此时已归零，concat 处不会有咔哒声。
PIANO_FADE_IN="${PIANO_FADE_IN:-1.2}"
PIANO_FADE_OUT="${PIANO_FADE_OUT:-1.0}"
# 曲线：esin（指数正弦）比默认 tri（线性）更接近音乐录音的淡入淡出听感
PIANO_FADE_CURVE="${PIANO_FADE_CURVE:-esin}"
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

# 2) 渲染片头（幂等）
#    ⚠️ 幂等键必须含 OPENING_ID **和文案**：换片头版本后旧的 opening_anim.mp4
#    帧数也是 270，只看帧数会误判"已完成"而跳过渲染，导致成片里仍是旧片头；
#    同理改了日期/标题但帧数不变，也会错误跳过 → 日期永远更新不了。
#    故把「版本 id + 标题 + 日期」一起写进 render.log 作为幂等键。
OPEN_SIG="$OPENING_ID|$OPENING_TITLE|$OPENING_DATE|$OPENING_WEEKDAY"
if [ -f "$OPENING_OUT" ] && check_part_frames "$OPENING_OUT" "$OPEN_FRAMES" \
   && grep -qF "OPENING DONE $OPEN_SIG " "$LOG" 2>/dev/null; then
  echo "[$(date +%H:%M:%S)] skip opening (same version+text, ${OPEN_FRAMES} frames ok)" | tee -a "$LOG"
else
  if [ -f "$OPENING_OUT" ] && check_part_frames "$OPENING_OUT" "$OPEN_FRAMES"; then
    echo "[$(date +%H:%M:%S)] 片头帧数虽完整但日志无匹配 OPENING DONE（版本或文案已变），强制重渲" | tee -a "$LOG"
  fi
  echo "[$(date +%H:%M:%S)] render $OPENING_ID ${OPEN_FRAMES} frames  [title=$OPENING_TITLE | $OPENING_DATE $OPENING_WEEKDAY]" | tee -a "$LOG"
  rm -f "$OPENING_OUT"
  # 片头文案用 --props 注入（Remotion 读 JSON 文件）。
  # 这是「每期标配」的前提：日期/标题变了不用改 TSX，只改环境变量。
  # ⚠️ 本机 Remotion 版本的参数名是 `--props`，**不是** `--input-props`
  # （新版本文档写的是 --input-props，但本机 --input-props 会被静默忽略，
  #  渲染照常成功但文案仍是 defaultProps 的硬编码值 —— 不报错，极难发现。
  #  实测判定法：传一个可辨识标题（如 ZZTEST），渲一帧看画面上有没有出现。）
  PROPS="$OUT/opening_props.json"
  "$PY" -c "
import json, io
json.dump({'title': '''$OPENING_TITLE''', 'date': '''$OPENING_DATE''', 'weekday': '''$OPENING_WEEKDAY'''},
          io.open(r'$PROPS','w',encoding='utf-8'), ensure_ascii=False, indent=2)"
  # ⑤ 2026-10-16：`( cd "$POC" && ... )` 子 shell 包装在 set -u 下会让
  #    Windows 侧执行失败（报 No such file or directory，而同样命令手动前台跑完全正常）。
  #    改用 `pushd`/`popd` 或直接 pushd 到 POC 后原地执行，避免子 shell。
  pushd "$POC" >/dev/null
  "$REMIX" render "$OPENING_ID" "$OPENING_OUT" --props="$PROPS" --concurrency=2 --browser-executable="$CHROME" --chrome-flags="--disable-accelerated-video-decode --disable-gpu" >> "$LOG" 2>&1
  popd >/dev/null
  if ! check_part_frames "$OPENING_OUT" "$OPEN_FRAMES"; then
    echo "!! $OPENING_ID 渲染失败或帧数不足（期望 ${OPEN_FRAMES}）" >&2
    exit 1
  fi
  echo "OPENING DONE $OPEN_SIG $(date +%H:%M:%S)" >> "$LOG"
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
  pushd "$POC" >/dev/null
  "$REMIX" render WeeklyTalk "$part" --frames="$start-$end" --concurrency=2 --browser-executable="$CHROME" --chrome-flags="--disable-accelerated-video-decode --disable-gpu" >> "$LOG" 2>&1
  popd >/dev/null
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
# ⚠️ 换片头版本后必须强制重建：成片总帧数不变（都是 270+16491），
# 只看 "FINAL DONE" 会跳过重建 → 成片里仍是旧片头。
# 故把 OPENING_ID 记进 FINAL DONE 行，版本不同则重建。
if [ -f "$OUT/signal_pop_weekly_$DATE.mp4" ] && grep -qF "FINAL DONE $OPEN_SIG " "$LOG" 2>/dev/null; then
  if check_part_frames "$OUT/signal_pop_weekly_$DATE.mp4" "$FULL_TOTAL"; then
    echo "[$(date +%H:%M:%S)] 成片已存在且帧数完整（片头 $OPENING_ID），跳过拼接/重编码" | tee -a "$LOG"
    exit 0
  fi
  echo "[$(date +%H:%M:%S)] 警告：成片已存在但帧数不完整，强制重建" | tee -a "$LOG"
elif [ -f "$OUT/signal_pop_weekly_$DATE.mp4" ] && grep -q "FINAL DONE" "$LOG" 2>/dev/null; then
  echo "[$(date +%H:%M:%S)] 成片已存在但片头版本已变（$OPENING_ID），强制重建" | tee -a "$LOG"
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
echo "[$(date +%H:%M:%S)] build full audio (piano ${PIANO_START}s +9s fade ${PIANO_FADE_IN}/${PIANO_FADE_OUT}s, + tts delayed ${OPEN_FRAMES} frames)" | tee -a "$LOG"
# 片头钢琴必须淡入淡出：现版是硬切进，与 V4 画面的淡入淡出不同步。
# afade 的 st/d 作用在该滤镜**输入流**的时间轴上 —— 钢琴已被 -ss 截成 9s 独立流，
# 所以 st=0/d=$PIANO_FADE_IN 和 st=(9-$PIANO_FADE_OUT)/d=$PIANO_FADE_OUT 才是对的。
# ⚠️ 踩过的坑：若把 afade 放在 concat **之后**（作用在整条 558s 音频上），
# st=8 会落在 TTS 段落里，淡出的是人声而不是配乐 —— 位置必须在这条链里、
# 且在 concat 之前。
"$FF" -y -ss "$PIANO_START" -t 9 -i "$PIANO" -i "$AUDIO" -filter_complex "[0:a]aformat=sample_fmts=fltp:sample_rates=24000:channel_layouts=mono,afade=t=in:st=0:d=${PIANO_FADE_IN}:curve=${PIANO_FADE_CURVE},afade=t=out:st=$(awk "BEGIN{print 9-$PIANO_FADE_OUT}"):d=${PIANO_FADE_OUT}:curve=${PIANO_FADE_CURVE}[head];[1:a]aformat=sample_fmts=fltp:sample_rates=24000:channel_layouts=mono[tail];[head][tail]concat=n=2:v=0:a=1[out]" -map "[out]" -ar 24000 -ac 1 -c:a pcm_s16le "$AUDIO_FULL" >> "$LOG" 2>&1

echo "[$(date +%H:%M:%S)] re-encode CRF$CRF + merge audio" | tee -a "$LOG"
"$FF" -y -i "$SILENT" -i "$AUDIO_FULL" -c:v libx264 -preset fast -crf "$CRF" -pix_fmt yuv420p -c:a aac -b:a 192k -ar 24000 -ac 1 -map 0:v:0 -map 1:a:0 "$FINAL" >> "$LOG" 2>&1

# 成片帧数校验
if ! check_part_frames "$FINAL" "$FULL_TOTAL"; then
  nb=$("$FP" -v error -select_streams v:0 -count_packets -show_entries stream=nb_read_packets -of default=noprint_wrappers=1:nokey=1 "$FINAL" 2>/dev/null | tr -d '[:space:]\r')
  echo "!! 成片帧数 $nb != 期望 $FULL_TOTAL，合成异常。" >&2
  exit 1
fi

echo "FINAL DONE $OPEN_SIG $(date +%H:%M:%S)" >> "$LOG"
echo "[$(date +%H:%M:%S)] 完成: $FINAL" | tee -a "$LOG"
