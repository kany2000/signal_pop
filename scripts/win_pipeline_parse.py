#!/usr/bin/env python3
"""Step 1: Parse Signal Pop weekly special news script -> structured JSON"""

import sys
import os
import json
import re

# Ensure project root is on sys.path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from logger import logger  # noqa: E402


def parse_script(text):
    """Parse weekly special format into structured news items.

    Format:
    === 📰 Header ===

    【Section Name】
    1. **Title**: Body text...
       👉 *[主播观点]*：...
    """
    try:
        items = []
        current_section = "综合"

        for line_num, line in enumerate(text.split("\n"), 1):
            line_stripped = line.strip()

            # Skip empty lines
            if not line_stripped:
                continue

            # Detect section header
            section_match = re.search(r"【(.+?)】", line_stripped)
            if section_match:
                current_section = section_match.group(1)
                logger.debug(f"Line {line_num}: Detected section '{current_section}'")
                continue

            # Detect news item: "1. **Title**" or "1. **Title**: body"
            item_match = re.match(r"^(\d+)\.\s+\*\*(.+?)\*\*[：:]\s*(.+)?$", line_stripped)
            if item_match:
                num = int(item_match.group(1))
                title = item_match.group(2).strip()
                body_start = item_match.group(3)
                items.append(
                    {
                        "num": num,
                        "section": current_section,
                        "title": title,
                        "body": body_start.strip() if body_start else "",
                        "lines": [],  # additional body lines
                        "opinion": "",
                    }
                )
                logger.debug(f"Line {line_num}: Found news item #{num}: '{title}'")
                continue

            # Check for anchor opinion
            opinion_match = re.search(r"\[主播观点\]", line_stripped)
            if opinion_match and items:
                opinion_text = line_stripped.split("]", 1)[-1].strip()
                opinion_text = opinion_text.lstrip("*：: ")
                items[-1]["opinion"] = opinion_text
                logger.debug(f"Line {line_num}: Added opinion to item #{len(items)}")
                continue

            # Stop at --- separator (footer starts)
            if line_stripped == "---" or line_stripped.startswith("---"):
                logger.debug(f"Line {line_num}: Found separator, stopping parsing")
                break

            # Continuation of current item's body
            if items and line_stripped and not line_stripped.startswith("==="):
                # Check if it looks like an item continuation (no number pattern)
                if not re.match(r"^\d+\.\s+\*\*", line_stripped):
                    items[-1]["lines"].append(line_stripped)
                    logger.debug(f"Line {line_num}: Added continuation line to item #{len(items)}")

        # Merge lines into body
        for item in items:
            if item["lines"]:
                full_body = item["body"]
                if full_body:
                    full_body += " "
                full_body += " ".join(item["lines"])
                item["full_body"] = full_body
            else:
                item["full_body"] = item["body"]
            # Clean whitespace
            item["full_body"] = re.sub(r"\s+", "", item["full_body"])
            del item["lines"]

        logger.info(f"Successfully parsed {len(items)} news items")
        return items

    except Exception as e:
        logger.error(f"Error parsing script: {e}", exc_info=True)
        raise


def build_tts_text(items, pub_date, pub_weekday):
    """Build the full TTS narration text with intro + items + outro."""
    try:
        parts = [
            f"这里是隔天信号弹，今天是{pub_date}，{pub_weekday}。",
            f"欢迎收看本期周末特别版，以下是本周精选的{len(items)}条核心新闻。",
        ]

        for i, item in enumerate(items, 1):
            parts.append(f"第{i}条，{item['section']}。{item['title']}。{item['full_body']}")
            if item["opinion"]:
                parts.append(f"主播观点：{item['opinion']}")

        parts.append("以上就是本周信号弹周末特别版的全部内容。感谢您的关注，我们下期见。")
        return "\n\n".join(parts)
    except Exception as e:
        logger.error(f"Error building TTS text: {e}", exc_info=True)
        raise


def build_intro_text(items, pub_date_fmt, pub_weekday):
    """Short intro text for the opening card overlay."""
    try:
        return (
            "这里是隔天信号弹，",
            f"今天是{pub_date_fmt}，{pub_weekday}。",
            f"欢迎收看本期周末特别版，以下是本周精选的{len(items)}条核心新闻。",
        )
    except Exception as e:
        logger.error(f"Error building intro text: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    import sys, io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    script_path = (
        sys.argv[1] if len(sys.argv) > 1 else "E:/projects/signal_pop/archive/signal_pop_weekly_special_20260717.txt"
    )

    try:
        with open(script_path, "r", encoding="utf-8") as f:
            text = f.read()

        items = parse_script(text)
        print(json.dumps(items, ensure_ascii=False, indent=2))
    except FileNotFoundError:
        logger.error(f"Script file not found: {script_path}")
        print(f"Error: Script file not found: {script_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error processing script file: {e}", exc_info=True)
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
