#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop — 微信视频号自动发布（参考 Easel skill-channels-upload）

⚠️ 注意事项：视频号登录依赖「微信扫码」，Playwright 自动化最麻烦，需人工在 --login 时扫码。
正常发布： `python publish_channels.py --date 20260908`（默认用竖版 _9x16.mp4）

SELECTORS 为占位实现，站点改版后需实测修正。
"""
from _platform_publisher import PlatformPublisher


class ChannelsPublisher(PlatformPublisher):
    PLATFORM = "channels"
    CREATOR_URL = "https://channels.weixin.qq.com/web/pages/login"

    SELECTORS = {
        "upload_input": "input[type=file]",
        "title": "textarea[placeholder*='标题'], .title-input",     # 标题
        "desc": "textarea[placeholder*='描述'], .desc-input",        # 描述
        "publish_btn": "text=发表, button:has-text('发表')",          # 发表按钮
    }

    def _fill_form(self, pg, md):
        pg.set_input_files(self.SELECTORS["upload_input"], self.video)
        pg.wait_for_selector("text=上传成功", timeout=180000)
        if md.get("标题"):
            pg.fill(self.SELECTORS["title"], md["标题"])
        body = md.get("正文") or md.get("简介") or md["raw"]
        if body:
            pg.fill(self.SELECTORS["desc"], body[:1000])

    def _submit(self, pg):
        pg.click(self.SELECTORS["publish_btn"], timeout=15000)
        pg.wait_for_timeout(3000)


if __name__ == "__main__":
    ChannelsPublisher.cli()
