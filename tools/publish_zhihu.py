#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop — 知乎自动发布（参考 Easel skill-zhihu-publisher）

前提：先 `playwright install chromium`，再 `python publish_zhihu.py --date 20260908 --login` 抓登录态。
正常发布： `python publish_zhihu.py --date 20260908`

⚠️ SELECTORS 为占位实现，站点改版后需实测修正。知乎视频发布入口在创作者中心「视频」tab。
"""
from _platform_publisher import PlatformPublisher


class ZhihuPublisher(PlatformPublisher):
    PLATFORM = "zhihu"
    CREATOR_URL = "https://www.zhihu.com/creator#/content/video"

    SELECTORS = {
        "upload_input": "input[type=file]",          # 视频文件选择
        "title": "input[placeholder*='标题'], .VideoTitle input",  # 标题
        "desc": "textarea[placeholder*='简介'], .VideoDesc textarea",  # 简介
        "cover_add": "text=上传封面",                  # 封面（可选）
        "publish_btn": "text=发布, button:has-text('发布')",  # 发布按钮
    }

    def _fill_form(self, pg, md):
        pg.set_input_files(self.SELECTORS["upload_input"], self.video)
        pg.wait_for_selector("text=上传成功", timeout=180000)
        if self.cover:
            try:
                pg.set_input_files(self.SELECTORS["upload_input"], self.cover)
            except Exception:
                print("  ⚠️ 封面上传跳过")
        if md.get("标题"):
            pg.fill(self.SELECTORS["title"], md["标题"])
        body = md.get("正文") or md.get("简介") or md["raw"]
        if body:
            pg.fill(self.SELECTORS["desc"], body[:1000])

    def _submit(self, pg):
        pg.click(self.SELECTORS["publish_btn"], timeout=15000)
        pg.wait_for_timeout(3000)


if __name__ == "__main__":
    ZhihuPublisher.cli()
