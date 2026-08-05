"""Tests for style management module."""
import os
import sys

import pytest

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from styles import get_style_for_date, get_video_resolution, get_style_metadata
from config import STYLE_THEMES


class TestStyleSelection:
    """Test style selection by date."""

    def test_returns_dict(self):
        style = get_style_for_date("20260101")
        assert isinstance(style, dict)

    def test_contains_required_keys(self):
        style = get_style_for_date("20260101")
        assert "bar" in style
        assert "accent" in style
        assert "sub" in style

    def test_colors_are_tuples(self):
        style = get_style_for_date("20260101")
        assert isinstance(style["bar"], tuple)
        assert len(style["bar"]) == 3

    def test_deterministic(self):
        s1 = get_style_for_date("20260101")
        s2 = get_style_for_date("20260101")
        assert s1 == s2

    def test_different_dates_different_styles(self):
        """At least some dates should produce different styles."""
        styles = set()
        for month in range(1, 13):
            for day in range(1, 29):
                style = get_style_for_date(f"2026{month:02d}{day:02d}")
                styles.add(str(style))
        assert len(styles) >= 2

    def test_style_from_themes_list(self):
        """Selected style must be from the STYLE_THEMES list."""
        style = get_style_for_date("20260101")
        assert style in STYLE_THEMES


class TestVideoResolution:
    """Test video resolution helper."""

    def test_returns_tuple(self):
        res = get_video_resolution()
        assert isinstance(res, tuple)
        assert len(res) == 3

    def test_resolution_values(self):
        w, h, fps = get_video_resolution()
        assert w == 1920
        assert h == 1080
        assert fps == 30


class TestStyleMetadata:
    """Test style metadata generation."""

    def test_returns_dict(self):
        meta = get_style_metadata("20260101")
        assert isinstance(meta, dict)

    def test_contains_expected_keys(self):
        meta = get_style_metadata("20260101")
        assert "bar_color" in meta
        assert "accent_color" in meta
        assert "resolution" in meta
