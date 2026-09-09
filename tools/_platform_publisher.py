#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop — 多平台 Playwright 发布基类（参考 Easel skill-*-upload）

⚠️ 重要前提（强依赖你的平台登录态）：
  1. 本机需安装 Playwright chromium： `playwright install chromium`
  2. 首次使用需先登录抓状态： `python publish_xhs.py --date 20260908 --login`
     会在浏览器里打开创作者后台，你手动扫码/登录后，状态存到 cookies/<平台>_state.json
     （该目录已在 .gitignore，不会入库）
  3. 之后正常发布即可自动读取登录态。

  选择器（CSS/XPath）是基于各平台创作者后台「当前已知结构」写的占位实现，
  站点改版后需实测修正——每个子类里 SELECTORS 常量集中标注，便于一处修改。

用法（在子类脚本内调用）：
  pub = XhsPublisher(date="20260908")
  pub.run()            # 读 xiaohongshu.md，登录态发布
  pub.capture_login()  # --login 模式：仅抓登录态
"""
import os
import sys
import time
import argparse

from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COOKIE_DIR = os.path.join(PROJECT_ROOT, "cookies")
os.makedirs(COOKIE_DIR, exist_ok=True)


class PlatformPublisher:
    # ===== 子类必须覆盖 =====
    PLATFORM = "base"
    CREATOR_URL = ""                       # 创作者后台地址
    STATE_FILE = None                      # 登录态文件（自动设）
    SELECTORS = {}                        # 表单字段选择器

    def __init__(self, date, kind="daily", headed=True, account=None):
        self.date = date
        self.kind = kind
        self.headed = headed
        self.account = account
        self.base = os.path.join(PROJECT_ROOT, "output", kind, date)
        self.STATE_FILE = os.path.join(COOKIE_DIR, f"{self.PLATFORM}_state.json")
        self.plat_md = os.path.join(self.base, f"{self.PLATFORM}.md")
        # 微信视频号等竖屏平台优先用竖版视频
        self.video = os.path.join(self.base, f"signal_pop_{kind}_{date}_9x16.mp4")
        if not os.path.exists(self.video):
            self.video = os.path.join(self.base, f"signal_pop_{kind}_{date}.mp4")
        self.cover = self._find_cover()

    # ---------- 文案读取（与 check_publish_ready / 发布脚本一致） ----------
    def _read_md(self):
        if not os.path.exists(self.plat_md):
            raise SystemExit(f"缺少文案文件: {self.plat_md}")
        txt = open(self.plat_md, encoding="utf-8").read()
        md = {"raw": txt}
        for key in ("标题", "简介", "正文"):
            import re
            m = re.search(rf"^{key}[：:]\s*(.+?)(?:\n\n|\Z)", txt, re.S | re.M)
            m = m or re.search(rf"^{key}[：:]\s*(.+)$", txt, re.S | re.M)
            md[key] = m.group(1).strip() if m else ""
        # 标签：取末尾 # 行
        tags = [l.strip("#") for l in txt.splitlines() if l.startswith("#")]
        md["tags"] = ",".join(tags) if tags else ""
        # 无「标题」字段的平台用首行
        if not md.get("标题"):
            md["标题"] = txt.strip().splitlines()[0].strip() if txt.strip() else ""
        return md

    def _find_cover(self):
        cands = [
            os.path.join(self.base, f"cover_{self.date}_3x4.png"),
            os.path.join(self.base, f"cover_{self.date}_9x16.png"),
            os.path.join(self.base, f"cover_{self.date}_16x9.png"),
        ]
        for c in cands:
            if os.path.exists(c):
                return c
        return None

    # ---------- 登录态捕获 ----------
    def capture_login(self):
        print(f"[{self.PLATFORM}] 打开 {self.CREATOR_URL}，请手动登录…")
        with sync_playwright() as p:
            b = p.chromium.launch(headless=False)
            ctx = b.new_context()
            pg = ctx.new_page()
            pg.goto(self.CREATOR_URL)
            input("登录完成后按回车（确保已进入创作者后台）…")
            ctx.storage_state(path=self.STATE_FILE)
            print(f"✅ 登录态已保存: {self.STATE_FILE}")
            b.close()

    # ---------- 发布主流程（子类实现 _fill_form） ----------
    def run(self):
        if not os.path.exists(self.STATE_FILE):
            raise SystemExit(
                f"[{self.PLATFORM}] 尚未登录。请先： python publish_{self.PLATFORM}.py "
                f"--date {self.date} --login")
        md = self._read_md()
        with sync_playwright() as p:
            b = p.chromium.launch(headless=not self.headed)
            ctx = b.new_context(storage_state=self.STATE_FILE)
            pg = ctx.new_page()
            pg.goto(self.CREATOR_URL)
            time.sleep(3)
            self._fill_form(pg, md)
            self._submit(pg)
            print(f"✅ [{self.PLATFORM}] 发布已提交")
            b.close()
        return True

    # 子类实现
    def _fill_form(self, pg, md):
        raise NotImplementedError

    def _submit(self, pg):
        raise NotImplementedError

    # ---------- CLI 入口（子类复用） ----------
    @classmethod
    def cli(cls):
        ap = argparse.ArgumentParser(description=f"{cls.PLATFORM} 发布")
        ap.add_argument("--date", required=True)
        ap.add_argument("--kind", default="daily")
        ap.add_argument("--headed", action="store_true", default=True)
        ap.add_argument("--no-headed", dest="headed", action="store_false")
        ap.add_argument("--login", action="store_true", help="仅抓取登录态")
        ap.add_argument("--account")
        args = ap.parse_args()
        inst = cls(date=args.date, kind=args.kind, headed=args.headed, account=args.account)
        if args.login:
            inst.capture_login()
        else:
            inst.run()
