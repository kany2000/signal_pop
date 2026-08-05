"""Tests for image generation prompt building."""
import os
import sys

import pytest

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

_SCRIPTS_DIR = os.path.join(_PROJECT_ROOT, "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from win_pipeline_images import make_prompt, SCENE_PROMPTS, DEFAULT_SCENE, NO_TEXT


class TestMakePrompt:
    """Test the make_prompt function."""

    def test_keyword_match_spaceX(self):
        prompt = make_prompt("SpaceX星舰首飞成功", "some body text")
        assert "SpaceX" in prompt

    def test_keyword_match_in_body(self):
        prompt = make_prompt("某条新闻", "涉及到超算相关内容")
        assert "supercomputer" in prompt

    def test_default_prompt_for_unknown_topic(self):
        prompt = make_prompt("某条普通新闻标题", "普通新闻内容")
        assert "news event scene" in prompt
        assert NO_TEXT in prompt

    def test_prompt_always_has_no_text_suffix(self):
        """All prompts should end with the no-text directive."""
        prompt = make_prompt("SpaceX", "")
        assert "no text" in prompt

    def test_deepseek_keyword(self):
        prompt = make_prompt("DeepSeek发布新模型", "")
        assert "DeepSeek" in prompt

    def test_a_stock_keyword(self):
        prompt = make_prompt("A股大涨", "")
        assert "stock market" in prompt or "A股" in prompt

    def test_opec_keyword(self):
        prompt = make_prompt("OPEC会议结果", "")
        assert "OPEC" in prompt


class TestScenePrompts:
    """Test the SCENE_PROMPTS dictionary."""

    def test_has_opening_and_ending_prompts(self):
        from win_pipeline_images import NEWS_PROMPTS

        assert "opening" in NEWS_PROMPTS
        assert "ending" in NEWS_PROMPTS

    def test_all_scene_prompts_have_no_text(self):
        for keyword, prompt in SCENE_PROMPTS.items():
            assert NO_TEXT in prompt, f"Prompt for '{keyword}' missing NO_TEXT suffix"

    def test_default_scene_has_no_text(self):
        assert NO_TEXT in DEFAULT_SCENE
