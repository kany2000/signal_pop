#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop — 小红书自动发布（参考 Easel skill-xhs-publisher）

前提：先 `playwright install chromium`，再 `python publish_xhs.py --date 20260908 --login` 抓登录态。
正常发布： `python publish_xhs.py --date 20260908`

⚠️ SELECTORS 为基于创作者后台「当前已知结构」的占位实现，站点改版后需实测修正。
"""
from _platform_publisher import PlatformPublisher


class XhsPublisher(PlatformPublisher):
    PLATFORM = "xiaohongshu"
    CREATOR_URL = "https://creator.xiaohongshu.com/publisher/publish?from=creator"

    # ===== 选择器（站点改版后在此集中修正）=====
    SELECTORS = {
        "video_tab": "text=视频",                       # 切到视频发布
        "upload_input": "input[type=file]",             # 视频/封面文件选择
        "title": "textarea[placeholder*='填写标题']",    # 标题
        "content": "div[data-test] textarea, .content-textarea",  # 正文
        "cover_add": "text=添加封面",                    # 封面（可选）
        "publish_btn": "text=发布",                      # 发布按钮
    }

    def _fill_form(self, pg, md):
        pg.click(self.SELECTORS["video_tab"], timeout=15000)
        pg.wait_for_timeout(1500)
        # 上传视频（隐藏 file input）
        pg.set_input_files(self.SELECTORS["upload_input"], self.video)
        pg.wait_for_selector("text=上传成功", timeout=120000)
        if self.cover:
            try:
                pg.set_input_files(self.SELECTORS["upload_input"], self.cover)
            except Exception:
                print("  ⚠️ 封面上传跳过（可能需手动选）")
        if md.get("标题"):
            pg.fill(self.SELECTORS["title"], md["标题"][:20])  # 小红书标题≤20字
        if md.get("正文"):
            pg.fill(self.SELECTORS["content"], md["正文"])
        else:
            pg.fill(self.SELECTORS["content"], md["raw"])
        # 标签：用 # 触发话题
        for t in (md.get("tags") or "").split(",")[:10]:
            if t:
                pg.keyboard.type(f"#{t} ")
                pg.wait_for_timeout(200)

    def _submit(self, pg):
        pg.click(self.SELECTORS["publish_btn"], timeout=15000)
        pg.wait_for_timeout(3000)


if __name__ == "__main__":
    XhsPublisher.cli()
