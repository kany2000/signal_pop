#!/bin/bash
# =============================================================================
# Signal Pop — Audio-Only News Pipeline
# 每天 8:30 运行（周一/三/五 → daily），周六 9:00 运行（weekly）
# 语音：周一~周五+周六 → 女声，周六用 Owl Meeting 男声
# =============================================================================

set -e

# 项目目录
PROJECT_DIR="/home/kan/signal_pop"
SRC_DIR="$PROJECT_DIR/src"
OUTPUT_DIR="$PROJECT_DIR/output"
DATA_DIR="$PROJECT_DIR/data"
LOG_DIR="$PROJECT_DIR/logs"
TTS_SCRIPT="$SRC_DIR/tts_mimo.py"
PARSE_XIAOXIAOTU="$SRC_DIR/parse_xiaoxiaotu.py"

mkdir -p "$OUTPUT_DIR/daily" "$OUTPUT_DIR/weekly" "$DATA_DIR" "$LOG_DIR"

# Mode: daily 或 weekly
MODE="${1:-daily}"
TODAY=$(date +%Y%m%d)
WEEKDAY=$(date +%u)  # 1=周一 ... 6=周六 7=周日

# 日志
LOGFILE="$LOG_DIR/pipeline_${MODE}_${TODAY}.log"

echo "=========================================="
echo "Signal Pop Pipeline — $(date '+%Y-%m-%d %H:%M')"
echo "Mode: $MODE | Weekday: $WEEKDAY"
echo "=========================================="

# ---------------------------------------------
# 判断用男声还是女声
# daily (周一~周五) → 女声  |  weekly (周六) → 男声
if [ "$MODE" == "weekly" ]; then
    VOICE_GENDER="male"
    VOICE_LABEL="👨 男声（MiMo）"
else
    VOICE_GENDER="female"
    VOICE_LABEL="👩 女声（MiMo）"
fi
echo "[Voice] 使用: $VOICE_LABEL"

# 输出目录：daily/ 或 weekly/
OUT_SUBDIR="$OUTPUT_DIR/$MODE"

# ---------------------------------------------
# Step 1: 尝试读取「虾小图」新闻稿
# ---------------------------------------------
echo ""
echo ">>> Step 1: 读取虾小图新闻稿..."

SCRIPT_CONTENT=""
if [ -f "$PARSE_XIAOXIAOTU" ]; then
    # 尝试解析虾小图新闻稿
    SCRIPT_CONTENT=$(python3 "$PARSE_XIAOXIAOTU" "$TODAY" 2>/dev/null || true)
fi

if [ -n "$SCRIPT_CONTENT" ] && [ ${#SCRIPT_CONTENT} -gt 100 ]; then
    echo "[Step 1] ✅ 成功读取虾小图新闻稿 (${#SCRIPT_CONTENT} 字符)"
    USE_XIAOXIAOTU=1
else
    echo "[Step 1] ⚠️ 未找到今日虾小图新闻稿，回退到 RSS 抓取流程"
    USE_XIAOXIAOTU=0
    
    # ---------------------------------------------
    # 回退：抓取新闻
    # ---------------------------------------------
    echo ""
    echo ">>> Step 1 (fallback): 抓取 RSS 新闻..."
    if ! python3 "$SRC_DIR/fetch_news.py"; then
        echo "⚠️ 抓取新闻失败，使用缓存数据或退出"
    fi
    
    # ---------------------------------------------
    # Step 2: 过滤新闻
    # ---------------------------------------------
    echo ""
    echo ">>> Step 2: 过滤新闻 (daily=10条, weekly=12条)..."
    if [ "$MODE" == "weekly" ]; then
        python3 "$SRC_DIR/filter_news.py" --mode "$MODE" --top 12
    else
        python3 "$SRC_DIR/filter_news.py" --mode "$MODE" --top 10
    fi
    
    # ---------------------------------------------
    # Step 3: 生成脚本
    # ---------------------------------------------
    echo ""
    echo ">>> Step 3: 生成播报脚本..."
    python3 "$SRC_DIR/generate_script.py" "$TODAY" "$MODE"
    SCRIPT_TXT="$OUT_SUBDIR/signal_pop_${MODE}_latest.txt"
    
    if [ ! -f "$SCRIPT_TXT" ]; then
        echo "❌ 脚本文件不存在: $SCRIPT_TXT"
        exit 1
    fi
    
    SCRIPT_CONTENT=$(cat "$SCRIPT_TXT")
fi

# ---------------------------------------------
# Step 4: TTS 语音合成 + SRT 字幕生成
# ---------------------------------------------
echo ""
echo ">>> Step 4: TTS 语音合成 + SRT 字幕 ($VOICE_LABEL)..."

SCRIPT_TXT="$OUT_SUBDIR/signal_pop_${MODE}_latest.txt"
SRT_TXT="$OUT_SUBDIR/signal_pop_${MODE}_latest.srt"
# 保存脚本文本（无论来源）
echo "$SCRIPT_CONTENT" > "$SCRIPT_TXT"

TEMP_TTS_SCRIPT="/tmp/tts_mimo_run.py"

# 生成临时 TTS 调用脚本
cat > "$TEMP_TTS_SCRIPT" << 'TTSEOF'
import sys
sys.path.insert(0, '/home/kan/signal_pop/src')
from tts_mimo import synthesize_long_text, convert_to_mp3
import os

text = os.environ.get("SCRIPT_TEXT", "")
gender = os.environ.get("VOICE_GENDER", "female")
output_dir = os.environ.get("OUTPUT_DIR", "/home/kan/signal_pop/output/daily")
today = os.environ.get("TODAY", "20260101")
mode = os.environ.get("MODE", "daily")

wav_path = f"{output_dir}/signal_pop_{mode}_{today}_raw.wav"
mp3_path = f"{output_dir}/signal_pop_{mode}_{today}.mp3"
srt_path = f"{output_dir}/signal_pop_{mode}_{today}.srt"

wav, segments = synthesize_long_text(text, voice_gender=gender, output_path=wav_path, srt_path=srt_path)
mp3 = convert_to_mp3(wav)

# 同时更新 _latest
import shutil
latest_mp3 = f"{output_dir}/signal_pop_{mode}_latest.mp3"
latest_srt = f"{output_dir}/signal_pop_{mode}_latest.srt"
shutil.copy(mp3, latest_mp3)
shutil.copy(srt_path, latest_srt)
print(f"✅ 最终输出: {latest_mp3}")
print(f"✅ 字幕输出: {latest_srt}")
TTSEOF

export SCRIPT_TEXT="$SCRIPT_CONTENT"
export VOICE_GENDER="$VOICE_GENDER"
export OUTPUT_DIR="$OUT_SUBDIR"
export TODAY="$TODAY"
export MODE="$MODE"

python3 "$TEMP_TTS_SCRIPT"

# ---------------------------------------------
# Step 5: 视频生成 (仅 weekly 生成视频，daily 只做音频)
# ---------------------------------------------
echo ""
echo ">>> Step 5: 视频生成..."

VIDEO_SCRIPT="$SRC_DIR/generate_video.py"
if [ "$MODE" == "weekly" ] && [ -f "$VIDEO_SCRIPT" ]; then
    python3 "$VIDEO_SCRIPT" "$MODE" --date "$TODAY" 2>&1 | tail -10
elif [ "$MODE" == "daily" ]; then
    echo "[Step 5] ⏭️ daily 模式跳过视频生成（仅生成音频+字幕）"
else
    echo "⚠️ 视频生成脚本不存在，跳过: $VIDEO_SCRIPT"
fi

# ---------------------------------------------
# 完成
# ---------------------------------------------
echo ""
echo "=========================================="
echo "✅ Pipeline 完成！"
echo "=========================================="
echo "📄 文本脚本: $SCRIPT_TXT"
echo "📝 字幕文件: $SRT_TXT"
echo "🎵 音频文件: $OUT_SUBDIR/signal_pop_${MODE}_latest.mp3"
echo "🎬 视频文件: $OUT_SUBDIR/signal_pop_${MODE}_latest.mp4"
ls -lh "$OUT_SUBDIR"/signal_pop_${MODE}_${TODAY}.* 2>/dev/null
ls -lh "$OUT_SUBDIR"/signal_pop_${MODE}_latest.* 2>/dev/null