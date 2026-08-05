"""Tests for news script parsing module."""
import os
import sys

import pytest

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Add scripts dir to path
_SCRIPTS_DIR = os.path.join(_PROJECT_ROOT, "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from win_pipeline_parse import parse_script, build_tts_text, build_intro_text


class TestParseScript:
    """Test the parse_script function."""

    def test_parses_sample_script(self, sample_script_text):
        items = parse_script(sample_script_text)
        assert len(items) == 3

    def test_first_item_has_correct_number(self, sample_script_text):
        items = parse_script(sample_script_text)
        assert items[0]["num"] == 1

    def test_section_detection(self, sample_script_text):
        items = parse_script(sample_script_text)
        assert items[0]["section"] == "科技前沿"
        assert items[2]["section"] == "经济财经"

    def test_title_extraction(self, sample_script_text):
        items = parse_script(sample_script_text)
        assert "SpaceX" in items[0]["title"]

    def test_opinion_extraction(self, sample_script_text):
        items = parse_script(sample_script_text)
        assert items[0]["opinion"] == "这将彻底改变太空运输的成本结构。"
        assert items[2]["opinion"] == ""

    def test_empty_text_returns_empty_list(self):
        items = parse_script("")
        assert items == []

    def test_no_items_after_separator(self, sample_script_text):
        """Text after --- separator should not be parsed."""
        items = parse_script(sample_script_text)
        # The "以上就是..." line after --- should not be an item
        for item in items:
            assert "以上就是" not in item["title"]

    def test_full_body_is_cleaned(self, sample_script_text):
        items = parse_script(sample_script_text)
        for item in items:
            # full_body should not contain excessive whitespace
            assert "  " not in item.get("full_body", "")


class TestBuildTtsText:
    """Test the build_tts_text function."""

    def test_tts_text_has_intro(self, sample_parsed_items):
        text = build_tts_text(sample_parsed_items, "2026年1月1日", "星期四")
        assert "隔天信号弹" in text
        assert "2026年1月1日" in text

    def test_tts_text_has_all_items(self, sample_parsed_items):
        text = build_tts_text(sample_parsed_items, "2026年1月1日", "星期四")
        for item in sample_parsed_items:
            assert item["title"] in text

    def test_tts_text_has_outro(self, sample_parsed_items):
        text = build_tts_text(sample_parsed_items, "2026年1月1日", "星期四")
        assert "下期见" in text

    def test_tts_text_has_opinions(self, sample_parsed_items):
        text = build_tts_text(sample_parsed_items, "2026年1月1日", "星期四")
        assert "主播观点" in text


class TestBuildIntroText:
    """Test the build_intro_text function."""

    def test_intro_returns_tuple(self, sample_parsed_items):
        intro = build_intro_text(sample_parsed_items, "2026年1月1日", "星期四")
        assert isinstance(intro, tuple)
        assert len(intro) == 3

    def test_intro_contains_date(self, sample_parsed_items):
        intro = build_intro_text(sample_parsed_items, "2026年1月1日", "星期四")
        assert any("2026年1月1日" in line for line in intro)

    def test_intro_contains_item_count(self, sample_parsed_items):
        intro = build_intro_text(sample_parsed_items, "2026年1月1日", "星期四")
        assert any(str(len(sample_parsed_items)) in line for line in intro)
