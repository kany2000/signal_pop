"""Tests for config module."""
import os
import sys

import pytest

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from config import (
    BASE_DIR,
    PREP_DATE_STR,
    PUB_DATE_STR,
    PUB_DATE_FMT,
    PUB_WEEKDAY,
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    VIDEO_FPS,
    STYLE_THEMES,
    FFMPEG_PATH,
    LOG_LEVEL,
    get_style_for_date,
)


class TestConfigBasics:
    """Test basic config module functionality."""

    def test_base_dir_exists(self):
        assert os.path.isdir(BASE_DIR)

    def test_prep_date_format(self):
        assert len(PREP_DATE_STR) == 8
        assert PREP_DATE_STR.isdigit()

    def test_pub_date_is_prep_plus_one(self):
        from datetime import datetime, timedelta

        prep = datetime.strptime(PREP_DATE_STR, "%Y%m%d")
        pub = datetime.strptime(PUB_DATE_STR, "%Y%m%d")
        assert pub == prep + timedelta(days=1)

    def test_pub_date_fmt_contains_chinese(self):
        assert "年" in PUB_DATE_FMT
        assert "月" in PUB_DATE_FMT
        assert "日" in PUB_DATE_FMT

    def test_pub_weekday_valid(self):
        assert PUB_WEEKDAY in ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


class TestVideoConfig:
    """Test video-related configuration."""

    def test_video_resolution(self):
        assert VIDEO_WIDTH == 1920
        assert VIDEO_HEIGHT == 1080

    def test_video_fps(self):
        assert VIDEO_FPS == 30

    def test_style_themes_exist(self):
        assert len(STYLE_THEMES) >= 1
        for theme in STYLE_THEMES:
            assert "bar" in theme
            assert "accent" in theme
            assert "sub" in theme

    def test_get_style_for_date_deterministic(self):
        """Same date should always return same style."""
        style1 = get_style_for_date("20260101")
        style2 = get_style_for_date("20260101")
        assert style1 == style2

    def test_get_style_for_date_different_dates(self):
        """Different dates may return different styles (not guaranteed but likely)."""
        styles = set()
        for d in range(1, 32):
            style = get_style_for_date(f"202601{d:02d}")
            styles.add(id(style))
        # At least 2 different styles across 31 days
        assert len(styles) >= 2


class TestEnvironmentConfig:
    """Test environment-dependent configuration."""

    def test_ffmpeg_path_is_string(self):
        assert isinstance(FFMPEG_PATH, str)
        assert len(FFMPEG_PATH) > 0

    def test_log_level_valid(self):
        assert LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
