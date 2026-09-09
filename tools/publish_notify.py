#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop — 发布结果通知（参考 Easel skill-publish-notify）

把一期发布结果推送到群机器人 webhook（飞书 / 钉钉 / Slack / 通用）。
未配置 webhook 时只打印摘要并退出 0（不阻塞发布）。

环境变量：
  PUBLISH_NOTIFY_WEBHOOK   webhook 完整 URL
  PUBLISH_NOTIFY_FORMAT    feishu | dingtalk | slack | generic（默认 generic）

用法：
  python tools/publish_notify.py --date 20260908 --dry
  python tools/publish_notify.py --date 20260908 --webhook <url> --format feishu
  python tools/publish_notify.py --message "手动发布提醒：小红书/知乎待发" --dry

说明：
  - 优先读取 output/<kind>/<date>/publish_status.json（由编排器写入）；
    不存在时回退解析 publish.log 的 ✅/❌ 行（best-effort）；
    都没有则用 --message。
"""
import os
import sys
import json
import argparse
import urllib.request
import urllib.error

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PLATFORMS = ["douyin", "kuaishou", "bilibili", "xiaohongshu", "zhihu",
             "channels", "facebook", "youtube", "twitter"]


def load_status(date, kind):
    """返回 (title, lines:list[str])"""
    base = os.path.join(PROJECT_ROOT, "output", kind, date)
    sj = os.path.join(base, "publish_status.json")
    if os.path.exists(sj):
        with open(sj, encoding="utf-8") as f:
            data = json.load(f)
        lines = [f"  {'✅' if v else '❌'} {k}" for k, v in data.get("results", {}).items()]
        return data.get("title", f"发布结果 · {date}"), lines
    # 回退：解析 publish.log
    log = os.path.join(base, "publish.log")
    if os.path.exists(log):
        with open(log, encoding="utf-8", errors="replace") as f:
            txt = f.read()
        lines = []
        for plat in PLATFORMS:
            if f"✅ {plat}" in txt:
                lines.append(f"  ✅ {plat}")
            elif f"❌ {plat}" in txt:
                lines.append(f"  ❌ {plat}")
        if lines:
            return f"发布结果 · {date}（来自 publish.log）", lines
    return None, []


def build_payload(fmt, title, text):
    if fmt == "feishu":
        return {"msg_type": "text", "content": {"text": f"{title}\n{text}"}}
    if fmt == "dingtalk":
        return {"msgtype": "text", "text": {"content": f"{title}\n{text}"}}
    if fmt == "slack":
        return {"text": f"{title}\n{text}"}
    # generic
    return {"title": title, "text": text, "markdown": f"# {title}\n{text}"}


def send(webhook, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(webhook, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.URLError as e:
        return None, f"网络错误: {e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date")
    ap.add_argument("--kind", default="daily", choices=["daily", "weekly"])
    ap.add_argument("--message", help="直接指定通知文本（覆盖自动解析）")
    ap.add_argument("--webhook", help="webhook URL（或走 PUBLISH_NOTIFY_WEBHOOK）")
    ap.add_argument("--format", default=os.environ.get("PUBLISH_NOTIFY_FORMAT", "generic"))
    ap.add_argument("--dry", action="store_true", help="只打印 payload，不发送")
    args = ap.parse_args()

    if args.message:
        title, lines = "Signal Pop 发布通知", args.message.splitlines() or [args.message]
    elif args.date:
        title, lines = load_status(args.date, args.kind)
        if not lines:
            title, lines = "Signal Pop 发布通知", [f"（{args.date} 无发布状态可解析）"]
    else:
        ap.error("需提供 --date 或 --message")

    text = "\n".join(lines)
    payload = build_payload(args.format, title, text)

    webhook = args.webhook or os.environ.get("PUBLISH_NOTIFY_WEBHOOK")
    if args.dry or not webhook:
        print("【通知 payload（dry-run）】")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        if not webhook:
            print("\n⚠️ 未配置 PUBLISH_NOTIFY_WEBHOOK，跳过实际发送（不影响发布）。")
        sys.exit(0)

    status, body = send(webhook, payload)
    print(f"通知已发送 → {args.format}  webhook 状态: {status}")
    print(body[:500])
    sys.exit(0 if status and 200 <= status < 300 else 1)


if __name__ == "__main__":
    main()
