#!/usr/bin/env python3
"""
Signal Pop 视频合成工具
将 HeyGen 透明主播视频 + 背景图序列 → 合成最终成品

用法:
  python3 composite_video.py <heygen_video> <timeline.json> [--images-dir images/] [--output output.mp4]

timeline.json 格式:
  [
    {"id": "anchor_bg", "title": "主播背景", "duration": 10},
    {"index": 1, "title": "新闻标题1", "duration": 17},
    {"index": 2, "title": "新闻标题2", "duration": 14},
    ...
  ]
"""
import json, sys, os, subprocess, tempfile, shutil, textwrap
from pathlib import Path

def create_text_bg(text, output_path, width=1290, height=720, fontsize=36):
    """用 ffmpeg drawtext 生成文字背景图（占位用，无图时 fallback）"""
    # 中文字体路径
    font = find_chinese_font()
    # 多行文字处理
    lines = textwrap.wrap(text, width=30)
    text_draw = "\\n".join(lines[:4])

    cmd = [
        "ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=#1a1a2e:s={width}x{height}:d=1",
        "-vf", (
            f"drawtext=text='{text_draw}':"
            f"fontfile={font}:fontsize={fontsize}:"
            f"fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2-40:"
            f"line_spacing=10,"
            f"drawtext=text='Signal Pop':"
            f"fontfile={font}:fontsize=18:"
            f"fontcolor=gray@0.6:x=(w-text_w)/2:y=h-60"
        ),
        "-frames:v", "1", output_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)

def find_chinese_font():
    """找系统可用的中文字体"""
    candidates = [
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/wqy-microhei.ttc",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    # 随便拿个字体
    for root, dirs, files in os.walk("/usr/share/fonts"):
        for f in files:
            if f.endswith((".ttf", ".ttc")):
                return os.path.join(root, f)
    return ""

def build_timeline_from_script(script_path, visual_prompts_path):
    """从播报脚本和 visual_prompts 自动构建时间线（估算时长）"""
    with open(visual_prompts_path) as f:
        prompts = json.load(f)
    with open(script_path) as f:
        content = f.read()

    import re
    # 按编号分段
    segments = re.split(r'\n(?=\d+\.)', content.strip())
    timeline = []

    # intro
    intro_chars = len(segments[0].replace('\n','')) if segments else 0
    timeline.append({
        "id": "anchor_bg", "title": "开场",
        "duration": max(8, intro_chars // 5)
    })

    for i, seg in enumerate(segments[1:] if segments else []):
        # 找对应 prompt
        match = re.match(r'(\d+)\.\s*(.*?)(?:。|$)', seg)
        idx = int(match.group(1)) if match else i+1
        title = match.group(2)[:60] if match else f"新闻{idx}"

        chars = len(seg.replace('\n',''))
        duration = max(12, chars // 5)
        timeline.append({
            "index": idx, "title": title,
            "duration": duration
        })

    # outro
    timeline.append({
        "id": "outro", "title": "收播",
        "duration": 5
    })
    return timeline

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    heygen_video = sys.argv[1]
    timeline_file = sys.argv[2]
    images_dir = Path(os.getenv("IMAGES_DIR", "images"))
    output = os.getenv("OUTPUT", "signal_pop_final.mp4")

    with open(timeline_file) as f:
        timeline = json.load(f)

    workdir = Path(tempfile.mkdtemp(prefix="signal_pop_"))
    concat_file = workdir / "concat.txt"

    total_dur = 0
    with open(concat_file, "w") as cf:
        for i, seg in enumerate(timeline):
            seg_id = seg.get("id", seg.get("index", f"seg_{i}"))
            dur = seg["duration"]
            # 检查是否已有背景图
            img_path = images_dir / f"{seg_id}.png"
            if not img_path.exists():
                img_path = images_dir / f"{seg_id}.jpg"
            if not img_path.exists():
                # 生成带文字的占位背景
                bg_file = workdir / f"bg_{i:02d}.png"
                title = seg.get("title", "")
                create_text_bg(title, str(bg_file))
                print(f"[占位] 段{i}: {title} ({dur}s)")
            else:
                bg_file = img_path
                print(f"[图片] 段{i}: {img_path.name} ({dur}s)")

            # 生成对应时长的背景视频片段
            clip = workdir / f"clip_{i:02d}.mp4"
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", str(bg_file),
                "-c:v", "libx264",
                "-t", str(dur),
                "-pix_fmt", "yuv420p",
                "-vf", f"scale={1290}:{720}:force_original_aspect_ratio=decrease,pad={1290}:{720}:(ow-iw)/2:(oh-ih)/2",
                "-r", "25",
                str(clip)
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            cf.write(f"file '{clip}'\n")
            total_dur += dur

    print(f"[时间线] 总时长: {total_dur}s")

    # 合成背景视频
    bg_video = workdir / "background.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264", "-r", "25",
        "-pix_fmt", "yuv420p",
        str(bg_video)
    ], check=True, capture_output=True)

    # 裁切主播视频到同样长度（stream copy 快速）
    avatar_trimmed = workdir / "avatar_trimmed.mkv"
    cmd_trim = [
        "ffmpeg", "-y",
        "-c:v", "libvpx-vp9",  # 保持 VP9 alpha 解码
        "-i", heygen_video,
        "-t", str(total_dur),
        "-c", "copy",
        "-map", "0:v:0", "-map", "0:a:0",
        str(avatar_trimmed)
    ]
    result = subprocess.run(cmd_trim, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[WARN] 裁切失败: {result.stderr[:300]}, 尝试重编码...")
        cmd_trim = [
            "ffmpeg", "-y",
            "-i", heygen_video,
            "-t", str(total_dur),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-map", "0:v:0", "-map", "0:a:0",
            str(avatar_trimmed)
        ]
        subprocess.run(cmd_trim, check=True, capture_output=True)
    print(f"[裁切] {total_dur}s")

    # 合成：背景 + 透明主播叠层
    output_path = workdir / "final.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(bg_video),
        "-c:v", "libvpx-vp9",  # 确保 VP9 alpha 被识别
        "-i", str(avatar_trimmed),
        "-filter_complex", "[0:v][1:v]overlay=0:0[out]",
        "-map", "[out]", "-map", "1:a",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        str(output_path)
    ], check=True, capture_output=True)

    # 复制到最终输出
    shutil.copy2(output_path, output)
    print(f"✅ 完成: {output}")
    print(f"📁 临时文件: {workdir}")

if __name__ == "__main__":
    main()
