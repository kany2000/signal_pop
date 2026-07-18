# social-auto-upload CLI 参考 (来源: https://github.com/dreammis/social-auto-upload)

## 统一入口
`sau <platform> <subcommand> [options]`

支持平台：`douyin` | `kuaishou` | `xiaohongshu` | `bilibili` | `youtube` | `tiktok` | `baijiahao` | `tencent` (视频号)

## 通用参数
- `--account <name>`：账号名（对应一个 cookie 文件）
- `--headless` / `--headed`：无头/有头模式（默认 headless）
- `--debug`：调试模式，失败保留更多信息

## 视频上传参数
```
--file <path>              视频文件 (mp4/mov/mkv)
--title <str>              标题
--desc <str>               简介/描述
--tags <csv>               标签，逗号分隔
--thumbnail <path>         封面图（兼容参数，等同 3:4 竖版）
--thumbnail-landscape <path>  16:9 横版封面（B站/YouTube）
--thumbnail-portrait <path>   3:4 竖版封面（抖音/快手/小红书）
--schedule <datetime>      定时发布，格式 "YYYY-MM-DD HH:MM"
```

### 抖音额外
```
--product-link <url>       商品链接
--product-title <str>      商品标题
```

### B站额外
```
--tid <int>                分区 ID（必填，如 249=数码/科技）
--tags 映射到 biliup --tag
```

### YouTube 额外
```
--tags <csv>               标签
--playlist <str>           播放列表名
--visibility <enum>        public|unlisted|private
```
> YouTube 走浏览器自动化（Studio），非官方 API，避免未审核项目被锁私享。需等上传 100% 再点发布。被墙地区需在 `conf.py` 设 `YT_PROXY`。

## 图文上传参数
```
--images <paths...>        多张图片路径
--title <str>              标题
--note <str>               正文（小红书建议必填）
--tags <csv>               标签
--schedule <datetime>      定时发布
```

## 登录/检查
```
sau <platform> login --account <name>   扫码登录，生成 cookie
sau <platform> check --account <name>   校验 cookie 有效性
```

## 抖音/快手/小红书/B站 CLI 示例
```bash
# 登录
sau douyin login --account her2home
sau bilibili login --account her2home
sau xiaohongshu login --account her2home
sau kuaishou login --account her2home

# 视频发布（立即）
sau douyin upload-video --account her2home --file video.mp4 --title "标题" --desc "简介" --tags "科技,新闻"

# 视频发布（定时 + 双封面）
sau douyin upload-video --account her2home \
  --file video.mp4 --title "隔天信号弹" --desc "内容" \
  --thumbnail-portrait cover_3x4.png \
  --thumbnail-landscape cover_16x9.png \
  --schedule "2026-06-28 08:30"

# B站（需 tid）
sau bilibili upload-video --account her2home --file video.mp4 --title "标题" --desc "简介" --tid 249 --schedule "2026-06-28 08:30"
```

## 环境变量
- `SAU_XHS_CREATOR_BASE_URL`：小红书海外环境切换到 `https://creator.rednote.com`
- `YT_PROXY`：YouTube 代理（如 `http://127.0.0.1:7890`）

## 技能目录（供 Agent 调用）
- `skills/douyin-upload/SKILL.md`
- `skills/kuaishou-upload/SKILL.md`
- `skills/xiaohongshu-upload/SKILL.md`
- `skills/bilibili-upload/SKILL.md`

## 部署建议
1. 同一台机器跑马小v生产 + 发布，共享 `/home/kan/shared/her2home/`
2. 视频文件命名建议：`signal_pop_YYYYMMDD_daily.mp4` / `signal_pop_YYYYMMDD_weekly.mp4`
3. 同名 JSON 元数据：`{title, desc, tags, schedule, platforms: ["douyin","bilibili","xiaohongshu","kuaishou"]}`
4. 发布 cron 读取 JSON → 并行 `sau` 调用 → 记录发布结果日志