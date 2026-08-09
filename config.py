"""
Signal Pop - Centralized Configuration Module

All project-wide configuration is managed here.
Values can be overridden via environment variables.
"""

import os
import hashlib
from datetime import datetime, timedelta

# --- General Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_dotenv():
    """Load .env into os.environ (no third-party dependency)."""
    path = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            os.environ.setdefault(k, v)


_load_dotenv()

# Output base directory for generated files
OUTPUT_BASE = os.getenv("SIGNAL_POP_OUTPUT_BASE", os.path.join(BASE_DIR, "output"))

# Date for content preparation (YYYYMMDD). Defaults to yesterday.
PREP_DATE_STR = os.getenv("SIGNAL_POP_PREP_DATE", (datetime.now() - timedelta(days=1)).strftime("%Y%m%d"))
PREP_DATE_DT = datetime.strptime(PREP_DATE_STR, "%Y%m%d")

# Publication date (Prep date + 1 day)
PUB_DATE_DT = PREP_DATE_DT + timedelta(days=1)
PUB_DATE_STR = PUB_DATE_DT.strftime("%Y%m%d")
PUB_DATE_FMT = f"{PUB_DATE_STR[:4]}年{PUB_DATE_STR[4:6]}月{PUB_DATE_STR[6:8]}日"
PUB_DATE_SHORT = f"{PUB_DATE_STR[:4]}.{PUB_DATE_STR[4:6]}.{PUB_DATE_STR[6:8]}"
PUB_WEEKDAY = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][PUB_DATE_DT.weekday()]

# --- Paths Configuration ---
SCRIPT_FILE = os.getenv(
    "SIGNAL_POP_SCRIPT_FILE", os.path.join(BASE_DIR, "archive", f"signal_pop_daily_{PREP_DATE_STR}.txt")
)

OUT_DIR = os.path.join(OUTPUT_BASE, "daily", PREP_DATE_STR)
IMAGES_DIR = os.path.join(OUT_DIR, "images")
AUDIO_DIR = os.path.join(OUT_DIR, "audio")
FRAME_DIR = os.path.join(OUT_DIR, "frames")

AUDIO_PATH = os.path.join(AUDIO_DIR, "tts.wav")
AUDIO_SEGMENTS_PATH = os.path.join(AUDIO_DIR, "tts_segments.json")
PARSED_NEWS_PATH = os.path.join(OUT_DIR, "parsed_news.json")
OUTPUT_VIDEO_PATH = os.path.join(OUT_DIR, f"signal_pop_daily_{PREP_DATE_STR}.mp4")

# --- Video Configuration ---
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
VIDEO_FPS = 30

FONT_REGULAR = os.getenv("SIGNAL_POP_FONT_REGULAR", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
FONT_BOLD = os.getenv("SIGNAL_POP_FONT_BOLD", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")

# Style themes (rotated by date hash for visual variety)
STYLE_THEMES = [
    {"bar": (30, 85, 130), "accent": (255, 215, 0), "sub": (200, 200, 220)},  # 蓝白经典
    {"bar": (180, 70, 30), "accent": (255, 160, 40), "sub": (220, 200, 180)},  # 橙黑科技
    {"bar": (20, 100, 70), "accent": (0, 210, 150), "sub": (180, 220, 200)},  # 墨绿财经
    {"bar": (80, 40, 120), "accent": (200, 160, 255), "sub": (210, 200, 220)},  # 紫金国际
]


def get_style_for_date(date_str: str) -> dict:
    """Select a style theme based on the date string (deterministic)."""
    seed = int(hashlib.md5(date_str.encode()).hexdigest()[:8], 16)
    return STYLE_THEMES[seed % len(STYLE_THEMES)]


# --- FFmpeg Configuration ---
FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")

# --- API Keys (from environment variables only — never hardcode) ---
SENSENOVA_API_KEY = os.getenv("SENSENOVA_API_KEY", "")
UNSPLASH_API_KEY = os.getenv("UNSPLASH_API_KEY", "")

# --- Distribution Paths ---
HER2HOME_VIDEO_PATH = os.getenv("HER2HOME_VIDEO_PATH", os.path.join(BASE_DIR, "her2home", f"video_{PREP_DATE_STR}.mp4"))
HER2HOME_COVER_PATH = os.getenv("HER2HOME_COVER_PATH", os.path.join(BASE_DIR, "her2home", f"cover_{PREP_DATE_STR}.png"))

# --- Logging Configuration ---
LOG_LEVEL = os.getenv("SIGNAL_POP_LOG_LEVEL", "INFO").upper()
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, f"signal_pop_{PREP_DATE_STR}.log")
