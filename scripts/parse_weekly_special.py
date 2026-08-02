#!/usr/bin/env python3
"""Parse weekly special format → structured JSON for pipeline"""
import sys, os, re, json

INPUT = "E:/projects/signal_pop/archive/signal_pop_weekly_special_20260731.txt"
OUTPUT = "E:/projects/signal_pop/output/parsed_weekly_20260731.json"

SECTION_MAP = {
    "科技与产业": "科技前沿",
    "国内与社会": "国内民生",
    "国际与金融": "国际综合",
}

def parse_weekly(text):
    items = []
    current_section = "综合"
    lines = text.split('\n')

    # State machine
    current_item = None
    state = "idle"  # idle | in_title | in_body | in_opinion

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Section header: **【科技与产业】**
        sec_m = re.match(r'\*{0,2}【(.+?)】\*{0,2}', line_stripped)
        if sec_m:
            sn = sec_m.group(1)
            current_section = SECTION_MAP.get(sn, sn)
            continue

        # Skip === header lines, 🎙️, ✨, etc.
        if line_stripped.startswith('===') or line_stripped.startswith('🎙') or line_stripped.startswith('✨'):
            continue

        # Check for item number: "N. **标题**：body" or "第N条。标题：body"
        # Format: "1. **中国机器人大军如何改变英国零售业？**：英国生产力增长乏力..."
        num_m = re.match(r'(\d+)\.\s*\*\*(.+?)\*\*[：:]\s*(.*)', line_stripped)
        if num_m:
            # Save previous item
            if current_item:
                items.append(current_item)

            num = int(num_m.group(1))
            title = num_m.group(2).strip()
            body = num_m.group(3).strip()
            current_item = {
                "num": num,
                "section": current_section,
                "title": title,
                "body": body,
                "opinion": "",
                "visual_prompt": "",
                "category": current_section,
            }
            continue

        # Check for item number without bold: "N. text"
        num_m2 = re.match(r'(\d+)\.\s+(.+?)[：:]\s*(.*)', line_stripped)
        if num_m2 and not current_item:
            num = int(num_m2.group(1))
            title = num_m2.group(2).strip()
            body = num_m2.group(3).strip()
            current_item = {
                "num": num,
                "section": current_section,
                "title": title,
                "body": body,
                "opinion": "",
                "visual_prompt": "",
                "category": current_section,
            }
            continue

        # 👉 [主播观点]：opinion
        op_m = re.search(r'👉\s*\[主播观点\]\s*[：:]\s*(.*)', line_stripped)
        if op_m and current_item:
            current_item["opinion"] = op_m.group(1).strip()
            continue

        # Continuation of body if we're in an item
        if current_item is not None:
            # Check if this line starts a new section or item
            if re.match(r'^\d+\.\s', line_stripped):
                continue  # handled above
            # Append to body
            if current_item["body"]:
                current_item["body"] += line_stripped
            else:
                current_item["body"] = line_stripped

    # Save last item
    if current_item:
        items.append(current_item)

    # Re-number
    for i, item in enumerate(items, 1):
        item["num"] = i

    return items

def main():
    with open(INPUT, 'r', encoding='utf-8') as f:
        text = f.read()

    items = parse_weekly(text)
    print(f"Parsed {len(items)} items")

    for item in items:
        has_op = bool(item["opinion"])
        blen = len(item["body"])
        print(f"  #{item['num']:2d} [{item['section']}] title={item['title'][:40]} body={blen}c op={has_op}")

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {OUTPUT}")
    return items

if __name__ == "__main__":
    main()