"""Pytest fixtures for Signal Pop test suite."""
import os
import sys

import pytest

# Ensure project root is on sys.path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


# Reusable constants for tests
SAMPLE_SCRIPT_TEXT = """=== 📰 信号弹周末特别版 ===

【科技前沿】
1. **SpaceX星舰首飞成功**：SpaceX星舰在德克萨斯州博卡奇卡成功完成首次轨道飞行，标志着可重复使用火箭技术取得重大突破。
   👉 *[主播观点]*：这将彻底改变太空运输的成本结构。

2. **超算中心落地深圳**：国家超算深圳中心新一代系统正式启用，算力达到每秒百亿亿次。
   👉 *[主播观点]*：算力基础设施是AI时代的核心竞争力。

【经济财经】
3. **A股三大指数集体收涨**：沪指涨1.2%，深成指涨1.5%，创业板指涨1.8%，两市成交额突破万亿。

---
以上就是本期信号弹的全部内容。
"""

SAMPLE_PARSED_ITEMS = [
    {
        "num": 1,
        "section": "科技前沿",
        "title": "SpaceX星舰首飞成功",
        "body": "SpaceX星舰在德克萨斯州博卡奇卡成功完成首次轨道飞行，标志着可重复使用火箭技术取得重大突破。",
        "full_body": "SpaceX星舰在德克萨斯州博卡奇卡成功完成首次轨道飞行，标志着可重复使用火箭技术取得重大突破。",
        "opinion": "这将彻底改变太空运输的成本结构。",
    },
    {
        "num": 2,
        "section": "科技前沿",
        "title": "超算中心落地深圳",
        "body": "国家超算深圳中心新一代系统正式启用，算力达到每秒百亿亿次。",
        "full_body": "国家超算深圳中心新一代系统正式启用，算力达到每秒百亿亿次。",
        "opinion": "算力基础设施是AI时代的核心竞争力。",
    },
    {
        "num": 3,
        "section": "经济财经",
        "title": "A股三大指数集体收涨",
        "body": "沪指涨1.2%，深成指涨1.5%，创业板指涨1.8%，两市成交额突破万亿。",
        "full_body": "沪指涨1.2%，深成指涨1.5%，创业板指涨1.8%，两市成交额突破万亿。",
        "opinion": "",
    },
]


@pytest.fixture
def sample_script_text():
    """Provide sample news script text for parsing tests."""
    return SAMPLE_SCRIPT_TEXT


@pytest.fixture
def sample_parsed_items():
    """Provide pre-parsed news items for downstream tests."""
    return SAMPLE_PARSED_ITEMS
