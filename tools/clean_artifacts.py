#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Signal Pop 项目缓存与制作残留安全清理脚本
执行规则：
1. 清理根目录下临时抽帧与探针目录 (_all32, _test_st 等)
2. 清理 Remotion 可再生编译缓存 (node_modules/.cache, remotion_poc/out)
3. 清理 output 根目录下遗留调试音频与对比目录
4. 清理 output/daily 与 output/weekly 下各期分段切片中间件 (split_build, frames_exact, part*.mp4)
5. 严格白名单保护：成片mp4、封面图、8平台md、srt、json账本、used_*_styles.json指纹、channel_art
"""

import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def fmt_size(sz):
    for u in ['B', 'KB', 'MB', 'GB']:
        if sz < 1024:
            return f'{sz:.2f} {u}'
        sz /= 1024
    return f'{sz:.2f} TB'

def remove_path(path):
    """安全移除文件或目录，返回 (文件数, 字节数)"""
    if not os.path.exists(path):
        return 0, 0
    cnt = 0
    sz = 0
    try:
        if os.path.isfile(path):
            sz = os.path.getsize(path)
            cnt = 1
            os.remove(path)
        elif os.path.isdir(path):
            for r, dirs, files in os.walk(path):
                for f in files:
                    try:
                        sz += os.path.getsize(os.path.join(r, f))
                        cnt += 1
                    except OSError:
                        pass
            shutil.rmtree(path, ignore_errors=True)
    except Exception as e:
        print(f"  [跳过/警告] 无法清理 {path}: {e}")
        return 0, 0
    return cnt, sz

def main():
    print(f"=== 开始执行 Signal Pop 项目清理 [{ROOT}] ===")
    
    total_cnt = 0
    total_sz = 0
    
    # 1. 根目录临时/测试/探针目录与文件
    print("\n[1/5] 清理根目录临时测试目录与废弃脚本...")
    root_dirs = ['_all32', '_cup_one', '_cup_stable', '_final_chk', '_frame30', 
                 '_pip_anim', '_src_b', '_test_frames', '_test_st', '.tmp', '.pytest_cache']
    for d in root_dirs:
        p = os.path.join(ROOT, d)
        if os.path.exists(p):
            c, s = remove_path(p)
            total_cnt += c
            total_sz += s
            print(f"  - 已删除目录: {d} ({c} 文件, {fmt_size(s)})")
            
    root_files = ['_curate_daily.py', '_dewatermark_20260823.py', '_gen_20260823_parsed.py', '_probe_feeds.py']
    for f in root_files:
        p = os.path.join(ROOT, f)
        if os.path.exists(p):
            c, s = remove_path(p)
            total_cnt += c
            total_sz += s
            print(f"  - 已删除废弃脚本: {f} ({fmt_size(s)})")

    # 2. Remotion 编译构建缓存
    print("\n[2/5] 清理 Remotion 可再生缓存...")
    rem_targets = [
        os.path.join(ROOT, 'remotion_poc', 'node_modules', '.cache'),
        os.path.join(ROOT, 'remotion_poc', 'out')
    ]
    for p in rem_targets:
        if os.path.exists(p):
            rel = os.path.relpath(p, ROOT)
            c, s = remove_path(p)
            total_cnt += c
            total_sz += s
            print(f"  - 已清理缓存: {rel} ({c} 文件, {fmt_size(s)})")

    # 3. output 根目录下调试音频与对比目录
    print("\n[3/5] 清理 output 根目录调试文件...")
    out_dir = os.path.join(ROOT, 'output')
    if os.path.exists(out_dir):
        for item in list(os.listdir(out_dir)):
            p = os.path.join(out_dir, item)
            # 保护指纹与重要目录
            if item in ['used_anchor_styles.json', 'used_cover_styles.json', 'used_daily_cover_styles.json', 
                        'channel_art', 'shared', 'daily', 'weekly']:
                continue
            if os.path.isfile(p):
                if (item.startswith(('cloud_', 'xunfei_', 'test_')) and item.endswith('.mp3')) or \
                   item in ['filtered_news.json', 'pass_news.json', 'raw_feed.json']:
                    c, s = remove_path(p)
                    total_cnt += c
                    total_sz += s
                    print(f"  - 已删除调试文件: output/{item} ({fmt_size(s)})")
            elif os.path.isdir(p):
                if item in ['_theme_preview_daily', '_ab_响度对比', 'mp3', 'video']:
                    c, s = remove_path(p)
                    total_cnt += c
                    total_sz += s
                    print(f"  - 已删除临时目录: output/{item} ({c} 文件, {fmt_size(s)})")

    # 4. output/daily 历史期分段中间件
    print("\n[4/5] 清理 output/daily 历史期分段中间件 (split_build/frames/cache)...")
    daily_dir = os.path.join(out_dir, 'daily')
    if os.path.exists(daily_dir):
        for d in sorted(os.listdir(daily_dir)):
            dp = os.path.join(daily_dir, d)
            if not os.path.isdir(dp): continue
            for sub in list(os.listdir(dp)):
                sp = os.path.join(dp, sub)
                if os.path.isdir(sp) and sub in ['split_build', 'frames_exact', '.cache', '_check_final', '_check_frames']:
                    c, s = remove_path(sp)
                    total_cnt += c
                    total_sz += s
                    print(f"  - 已清理: output/daily/{d}/{sub} ({c} 文件, {fmt_size(s)})")
                elif os.path.isfile(sp) and sub.startswith('_t_') and sub.endswith('.mp4'):
                    c, s = remove_path(sp)
                    total_cnt += c
                    total_sz += s
                    print(f"  - 已清理测试片段: output/daily/{d}/{sub} ({fmt_size(s)})")

    # 5. output/weekly 历史期分段中间件
    print("\n[5/5] 清理 output/weekly 历史期分段中间件与调优片段...")
    weekly_dir = os.path.join(out_dir, 'weekly')
    if os.path.exists(weekly_dir):
        for d in sorted(os.listdir(weekly_dir)):
            dp = os.path.join(weekly_dir, d)
            if not os.path.isdir(dp): continue
            for sub in list(os.listdir(dp)):
                sp = os.path.join(dp, sub)
                if os.path.isdir(sp) and sub in ['split_build', '_quota_test', 'audit_frames', '_vertical_test_30s', 'tts_probe']:
                    c, s = remove_path(sp)
                    total_cnt += c
                    total_sz += s
                    print(f"  - 已清理: output/weekly/{d}/{sub} ({c} 文件, {fmt_size(s)})")
                elif os.path.isfile(sp):
                    # 分段 mp4 零件 (如 part00.mp4)
                    if sub.startswith('part') and sub.endswith('.mp4'):
                        c, s = remove_path(sp)
                        total_cnt += c
                        total_sz += s
                        print(f"  - 已清理分段切片: output/weekly/{d}/{sub} ({fmt_size(s)})")
                    elif sub.startswith('_') and sub.endswith(('.mp4', '.wav')):
                        c, s = remove_path(sp)
                        total_cnt += c
                        total_sz += s
                        print(f"  - 已清理调试片段: output/weekly/{d}/{sub} ({fmt_size(s)})")
                    elif sub in ['signal_pop_weekly_20261002_norm.mp4', 'signal_pop_weekly_20261002_norm2.mp4',
                                'ovf2.mp4', 'opening_v4_test.mp4', 'signal_pop_weekly_20261016_merged.mp4',
                                'signal_pop_weekly_20261016_merged_final.mp4']:
                        c, s = remove_path(sp)
                        total_cnt += c
                        total_sz += s
                        print(f"  - 已清理中间版视频: output/weekly/{d}/{sub} ({fmt_size(s)})")

    print("\n==========================================")
    print(f"✅ 清理完成！")
    print(f"📊 累计清理文件/目录数: {total_cnt} 个")
    print(f"💾 实际累计释放磁盘空间: {fmt_size(total_sz)}")
    print("==========================================")

if __name__ == '__main__':
    main()
