#!/usr/bin/env python3
"""
Signal Pop — 解析「虾小图」新闻稿格式
输入格式示例：
📡 隔天信号弹 · 新闻播报
🗓 2026年6月24日 星期三

1️⃣ 抖音商城618数据亮眼
...

输出：适合 TTS 的纯文本

用法: python3 parse_xiaoxiaotu.py [制作日期YYYYMMDD]
  制作日期: cron 运行的当天（如 20260709）
  发布日期 = 制作日期 + 1 天（视频开头播报用发布日期）
"""
import os
import re
import sys
from datetime import datetime, timedelta

WEEKDAYS = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

# 虾小图新闻稿可能的位置
POSSIBLE_PATHS = [
    "/home/kan/shared/xiaxiaotu/daily_news_latest.txt",
    "/home/kan/shared/xiaxiaotu/daily_news_{today}.txt",
    "/home/kan/shared/signal_pop/xiaoxiaotu_daily_latest.txt",
    "/home/kan/shared/signal_pop/xiaoxiaotu_daily_{today}.txt",
]

# 表情数字映射
EMOJI_NUMS = {
    '1️⃣': '1', '2️⃣': '2', '3️⃣': '3', '4️⃣': '4', '5️⃣': '5',
    '6️⃣': '6', '7️⃣': '7', '8️⃣': '8', '9️⃣': '9', '🔟': '10',
    '①': '1', '②': '2', '③': '3', '④': '4', '⑤': '5',
    '⑥': '6', '⑦': '7', '⑧': '8', '⑨': '9', '⑩': '10',
}

def clean_text(text: str) -> str:
    """移除表情符号、修复重复标点"""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002700-\U000027BF"
        "\U0001F900-\U0001F9FF"
        "\U00002600-\U000026FF"
        "\U0000FE00-\U0000FE0F"
        "]+", flags=re.UNICODE
    )
    text = emoji_pattern.sub('', text)
    text = re.sub(r'。+', '。', text)
    text = re.sub(r'\.+', '.', text)
    return text.strip()

def clean_ready_format(content: str) -> str:
    """清理已就绪格式（第1条、第2条...）"""
    return clean_text(content)

def adjust_date_to_publication(text: str, prod_date_str: str) -> str:
    """
    将日期行从制作日改为发布日（制作日+1）。
    处理格式：🗓 2026年7月9日 星期三 → 🗓 2026年7月10日 星期四
    以及：今天是2026年7月9日 → 今天是2026年7月10日
    """
    if not prod_date_str:
        return text
    try:
        prod_dt = datetime.strptime(prod_date_str, "%Y%m%d")
    except ValueError:
        return text  # invalid format, skip
    pub_dt = prod_dt + timedelta(days=1)
    pub_str = pub_dt.strftime("%Y年%m月%d日")
    pub_wd = WEEKDAYS[pub_dt.weekday()]

    # 匹配 "2026年7月9日" 格式的日期
    # 把日期替换为发布日
    date_pattern = re.compile(r'(\d{4})年(\d{1,2})月(\d{1,2})日')
    new_text = date_pattern.sub(pub_str, text)

    # 匹配星期（位于日期之后，第一个出现的星期词汇）
    # 替换为发布日的星期
    wd_pattern = re.compile(r'(' + '|'.join(WEEKDAYS) + r')')
    # 只替换第一个出现的星期（通常是日期行里的）
    new_text = wd_pattern.sub(pub_wd, new_text, count=1)

    return new_text

def find_latest_news_file(prod_date_str: str = None):
    """查找最新的虾小图新闻稿"""
    if prod_date_str is None:
        today = datetime.now().strftime("%Y%m%d")
    else:
        today = prod_date_str
    for pattern in POSSIBLE_PATHS:
        path = pattern.replace("{today}", today)
        if os.path.exists(path):
            mtime = datetime.fromtimestamp(os.path.getmtime(path))
            if mtime.date() == datetime.now().date():
                return path
    return None

def parse_xiaoxiaotu_script(content: str, prod_date_str: str = None) -> str:
    """解析虾小图格式，生成 TTS 友好文本"""
    content = content.strip()

    # 检测是否已经是就绪格式
    if '第1条' in content and '第2条' in content:
        return clean_ready_format(content)

    lines = content.split('\n')

    # 提取日期行
    date_line = ""
    for line in lines[:5]:
        if '年' in line and '月' in line and '日' in line:
            date_line = line.strip()
            date_line = re.sub(r'[📡🗓]', '', date_line).strip()
            date_line = date_line.replace('·', '').strip()
            break

    if not date_line:
        # 用发布日期作为 fallback
        if prod_date_str:
            dt = datetime.strptime(prod_date_str, "%Y%m%d") + timedelta(days=1)
        else:
            dt = datetime.now()
        date_line = f"{dt.strftime('%Y年%m月%d日')}，{WEEKDAYS[dt.weekday()]}。"

    # 如果提供了制作日，把日期行改为发布日
    if prod_date_str:
        date_line = adjust_date_to_publication(date_line, prod_date_str)

    # 提取新闻条目
    news_items = []
    current_title = ""
    current_content = []
    in_news = False

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('━') or line.startswith('---'):
            continue
        if line.startswith('📰') or '明天见' in line or '来源' in line:
            continue

        emoji_match = None
        for emoji, num in EMOJI_NUMS.items():
            if line.startswith(emoji):
                emoji_match = num
                break

        if emoji_match:
            if current_title:
                full_text = current_title
                if current_content:
                    full_text += "。" + "。".join(current_content)
                news_items.append(full_text)
            for emoji, num in EMOJI_NUMS.items():
                if line.startswith(emoji):
                    current_title = line[len(emoji):].strip()
                    break
            current_content = []
            in_news = True
        elif in_news and current_title:
            current_content.append(line)

    if current_title:
        full_text = current_title
        if current_content:
            full_text += "。" + "。".join(current_content)
        news_items.append(full_text)

    if not news_items:
        return None

    output_lines = []
    output_lines.append(f"这里是隔天信号弹，{clean_text(date_line)}。")
    output_lines.append("以下是今天的主要新闻。")
    output_lines.append("")

    for i, item in enumerate(news_items, 1):
        clean_item = clean_text(item)
        clean_item = clean_item.rstrip('。.').strip()
        output_lines.append(f"第{i}条，{clean_item}。")
        output_lines.append("")

    output_lines.append("以上是今天的隔天信号弹，我们明天见。")
    return "\n".join(output_lines)

def main():
    prod_date = sys.argv[1] if len(sys.argv) > 1 else None
    news_file = find_latest_news_file(prod_date)
    if not news_file:
        print("[parse_xiaoxiaotu] ❌ 未找到今日虾小图新闻稿", file=sys.stderr)
        sys.exit(1)

    print(f"[parse_xiaoxiaotu] 📄 读取: {news_file}", file=sys.stderr)
    with open(news_file, encoding='utf-8') as f:
        content = f.read()

    script = parse_xiaoxiaotu_script(content, prod_date)
    if not script:
        print("[parse_xiaoxiaotu] ❌ 解析失败，内容为空", file=sys.stderr)
        sys.exit(1)

    print(script)
    return 0

if __name__ == "__main__":
    main()