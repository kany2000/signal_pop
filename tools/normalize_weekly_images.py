#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""周末版配图规格化：把用户提供的原图统一到 1920x1080（16:9）

策略（按优先级）：
  1) 等比缩放到能覆盖 1920x1080 -> 居中裁切（不丢主体，画面铺满）
  2) 等比缩放到刚好塞进 1920x1080 -> 剩余边用同图高斯模糊放大版补边
     （避免主体被裁掉，同时不留黑边）
  3) 原图已是 1920x1080 -> 跳过

原图请先备份到 images/_original_backup/。
"""
import os
import sys
from PIL import Image, ImageFilter

TARGET_W, TARGET_H = 1920, 1080
DEFAULT_QUALITY = 90


def fit_center_crop(im, tw=TARGET_W, th=TARGET_H):
    """覆盖缩放 + 居中裁切（画面铺满，不留边）"""
    ratio = max(tw / im.width, th / im.height)
    nw, nh = max(tw, int(round(im.width * ratio))), max(th, int(round(im.height * ratio)))
    im = im.resize((nw, nh), Image.LANCZOS)
    left, top = (nw - tw) // 2, (nh - th) // 2
    return im.crop((left, top, left + tw, top + th))


def fit_blur_pad(im, tw=TARGET_W, th=TARGET_H, blur_radius=28):
    """塞进缩放 + 同图模糊版补边（不裁主体）"""
    ratio = min(tw / im.width, th / im.height)
    nw, nh = max(1, int(round(im.width * ratio))), max(1, int(round(im.height * ratio)))
    fg = im.resize((nw, nh), Image.LANCZOS)

    # 背景：同图放大 + 强模糊 + 压暗，避免补边区域抢戏
    bg = im.resize((tw, th), Image.LANCZOS).filter(ImageFilter.GaussianBlur(blur_radius))
    bg = bg.point(lambda v: int(v * 0.55))

    left, top = (tw - nw) // 2, (th - nh) // 2
    bg.paste(fg, (left, top))
    return bg


def normalize(path, tw=TARGET_W, th=TARGET_H, quality=DEFAULT_QUALITY):
    im = Image.open(path)
    if im.mode != "RGB":
        im = im.convert("RGB")
    src_size = im.size

    if src_size == (tw, th):
        return False, src_size, "already"

    src_ratio = im.width / im.height
    tgt_ratio = tw / th
    # 比例接近（偏差 < 6%）-> 直接居中裁切，损失最小
    if abs(src_ratio - tgt_ratio) / tgt_ratio < 0.06:
        out, mode = fit_center_crop(im, tw, th), "crop"
    else:
        out, mode = fit_blur_pad(im, tw, th), "blur-pad"

    out.save(path, "JPEG", quality=quality, subsampling=0)
    return True, src_size, mode


def main():
    args = sys.argv[1:]
    if not args:
        print("用法: python normalize_weekly_images.py <img_dir> [file.jpg ...]")
        return 1
    img_dir = args[0]
    targets = args[1:] or [
        f"news_{i:02d}.jpg" for i in range(1, 10)
    ]
    for name in targets:
        p = os.path.join(img_dir, name)
        if not os.path.exists(p):
            print(f"  ⏭️  {name} 不存在，跳过")
            continue
        try:
            changed, src, mode = normalize(p)
        except Exception as e:
            print(f"  ❌ {name} 处理失败: {e}")
            continue
        if not changed:
            print(f"  ➖ {name} 已是 {TARGET_W}x{TARGET_H}，跳过")
        else:
            print(f"  ✅ {name} {src[0]}x{src[1]} -> {TARGET_W}x{TARGET_H}  [{mode}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
