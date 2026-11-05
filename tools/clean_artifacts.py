#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Signal Pop 项目缓存与制作残留安全清理脚本
执行规则：
1. 清理根目录下临时抽帧与探针目录 (_all32, _test_st 等)
2. 清理 Remotion 可再生编译缓存 (node_modules/.cache, remotion_poc/out)
3. 清理 output 根目录下遗留调试音频与对比目录
4. 清理 output/daily 与 output/weekly 下各期分段切片中间件 (split_build, frames_exact, part*.mp4)
5. 严格白名单保护：成片mp4、封面图、8平台md、srt、json账本、used_*_styles.json指纹、
   channel_art、output/shared、output/weekly/shared（片头配乐/片尾动画/板块模板图）、
   output/video（用户提供的原始视频素材）、output/mp3（BGM 正式素材）、
   econ_talk_*_huashu.mp4（经济环节素材，文件名可能带旧期日期，留给下期复用）、
   audio/tts.wav 与 tts_segments.json（成片音轨真源与账本）。
   ⚠️ 2026-11-05 修正：原第 3 步把 'mp3' / 'video' 当临时目录整个删除，
   会误删用户原素材与将来入库的 BGM，已从删除名单移除。
6. 清理全部期次的深层制作遗物：audio/_tmp、econ_audio/_tmp（TTS 分句临时 wav）、
   *.log / *.tmp，以及「同名正式文件仍在」的 *.bak。

🔴 2026-11-05 21:10 用户定：「以后这些制作遗物都删掉，保持清爽」
   → **默认清理全部期次**，不再需要传日期，也不再保留历史期次的审图拼图/合并中间件/日志。

用法：
  python tools/clean_artifacts.py            # 推荐：清理全部期次的所有制作遗物
  python tools/clean_artifacts.py 20261106   # 兼容旧调用，行为与默认完全一致（日期参数已废弃）

⚠️ 只在「成片已终审通过」后运行；审图 checkpoint 期间跑会删掉当期审图拼图，
   可用 gen_contact_sheet_weekly.py 一条命令重生。删掉 merged_final.mp4 后，
   若日后要微调片头/片尾，须重跑全流程约 21 分钟（保留时仅需重跑最终编码约 4 分钟）。
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
    # 🔴 2026-11-05 21:10 用户定：默认清理全部期次的所有制作遗物，保持仓库清爽。
    # 可选日期参数仅为兼容 README / Skill 里的旧调用，行为与不传参完全一致。
    legacy_date = sys.argv[1] if len(sys.argv) > 1 else None
    print(f"=== 开始执行 Signal Pop 项目清理 [{ROOT}] ===")
    print("=== 范围：全部期次（默认全清，用户 2026-11-05 21:10 定）===")
    if legacy_date:
        print(f"=== 兼容提示：日期参数 {legacy_date} 已废弃，仍按全部期次清理 ===")

    total_cnt = 0
    total_sz = 0
    
    # 1. 根目录临时/测试/探针目录与文件
    print("\n[1/6] 清理根目录临时测试目录与废弃脚本...")
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
    print("\n[2/6] 清理 Remotion 可再生缓存...")
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
    print("\n[3/6] 清理 output 根目录调试文件...")
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
                # ⚠️ 'mp3' / 'video' 是用户素材目录（BGM、原始短视频），禁止清理。
                # 2026-11-05 修正：原先当临时目录整个删除，会误删用户提供的
                # 厄尔尼诺原视频 output/video/20261106_breaking.mp4。
                if item in ['_theme_preview_daily', '_ab_响度对比']:
                    c, s = remove_path(p)
                    total_cnt += c
                    total_sz += s
                    print(f"  - 已删除临时目录: output/{item} ({c} 文件, {fmt_size(s)})")

    # 4. output/daily 历史期分段中间件
    print("\n[4/6] 清理 output/daily 历史期分段中间件 (split_build/frames/cache)...")
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

    # 5. output/weekly 全部期次的分段中间件 / 审图拼图 / 合并中间件
    #    🔴 2026-11-05 21:10 用户定：「以后这些制作遗物都删掉，保持清爽」
    #    → 不再按日期限定，历史期次同类文件也一律清理。
    print("\n[5/6] 清理 output/weekly 全部期次制作遗物...")
    weekly_dir = os.path.join(out_dir, 'weekly')
    if os.path.exists(weekly_dir):
        for d in sorted(os.listdir(weekly_dir)):
            dp = os.path.join(weekly_dir, d)
            if not os.path.isdir(dp): continue
            # 共享素材目录：片头配乐、片尾三连动画、板块模板图，永不清理
            if d == 'shared':
                continue
            for sub in list(os.listdir(dp)):
                sp = os.path.join(dp, sub)
                if os.path.isdir(sp) and sub in ['split_build', '_quota_test', 'audit_frames', '_vertical_test_30s', 'tts_probe']:
                    c, s = remove_path(sp)
                    total_cnt += c
                    total_sz += s
                    print(f"  - 已清理: output/weekly/{d}/{sub} ({c} 文件, {fmt_size(s)})")
                elif os.path.isfile(sp):
                    # 🔴 经济环节学习视频属于「留给下期的素材」，文件名常带旧期日期
                    #    （如 econ_talk_20261102_huashu.mp4 放在 20261106 目录里），
                    #    绝不能被任何清理规则误删，包括以后新增的通配扩展。
                    if sub.startswith('econ_talk_') and sub.endswith('.mp4'):
                        continue
                    reason = None
                    if sub.startswith('part') and sub.endswith('.mp4'):
                        reason = '分段切片'
                    elif sub.startswith('_') and sub.endswith(('.mp4', '.wav')):
                        reason = '调试片段'
                    elif sub.startswith('contact_sheet') and sub.endswith(('.png', '.jpg')):
                        reason = '审图拼图'
                    elif sub.startswith('signal_pop_weekly_') and '_merged' in sub and sub.endswith('.mp4'):
                        reason = '合并中间件'
                    elif sub in ['ovf2.mp4', 'opening_v4_test.mp4']:
                        reason = '调试视频'
                    elif '_norm' in sub and sub.endswith('.mp4'):
                        reason = '响度试验中间件'
                    if reason:
                        c, s = remove_path(sp)
                        total_cnt += c
                        total_sz += s
                        print(f"  - 已清理{reason}: output/weekly/{d}/{sub} ({fmt_size(s)})")

    # 6. 深层制作遗物：TTS 分句临时目录 + 杂散日志/备份（全部期次）
    print("\n[6/6] 清理各期 TTS 分句临时目录与杂散日志/备份...")
    for base in ['weekly', 'daily']:
        bdir = os.path.join(out_dir, base)
        if not os.path.exists(bdir):
            continue
        for d in sorted(os.listdir(bdir)):
            dp = os.path.join(bdir, d)
            if not os.path.isdir(dp) or d == 'shared':
                continue
            for r, dirs, files in os.walk(dp):
                # 只清 audio/ 与 econ_audio/ 下的 _tmp（TTS 分句 wav），
                # 其它 _tmp 名称目录不动，避免误伤未知素材。
                for td in list(dirs):
                    if td == '_tmp' and os.path.basename(r) in ('audio', 'econ_audio'):
                        tp = os.path.join(r, td)
                        c, s = remove_path(tp)
                        total_cnt += c
                        total_sz += s
                        print(f"  - 已清理 TTS 分句临时目录: {os.path.relpath(tp, ROOT)} ({c} 文件, {fmt_size(s)})")
                        dirs.remove(td)
                for f in list(files):
                    fp = os.path.join(r, f)
                    drop = f.endswith(('.log', '.tmp'))
                    # .bak 仅在同名正式文件仍在时删除，避免丢掉唯一副本
                    if not drop and f.endswith('.bak') and os.path.exists(fp[:-4]):
                        drop = True
                    if drop:
                        c, s = remove_path(fp)
                        total_cnt += c
                        total_sz += s
                        print(f"  - 已清理杂散文件: {os.path.relpath(fp, ROOT)} ({fmt_size(s)})")

    # shared 是素材库（片头配乐 / 片尾动画 / 板块模板图），整体跳过；
    # 但生成脚本留下的 *.log 属制作遗物，单独清掉，其余文件一律不动。
    shared_dir = os.path.join(weekly_dir, 'shared')
    if os.path.exists(shared_dir):
        for f in list(os.listdir(shared_dir)):
            fp = os.path.join(shared_dir, f)
            if os.path.isfile(fp) and f.endswith('.log'):
                c, s = remove_path(fp)
                total_cnt += c
                total_sz += s
                print(f"  - 已清理共享目录日志: {os.path.relpath(fp, ROOT)} ({fmt_size(s)})")

    print("\n==========================================")
    print(f"✅ 清理完成！")
    print(f"📊 累计清理文件/目录数: {total_cnt} 个")
    print(f"💾 实际累计释放磁盘空间: {fmt_size(total_sz)}")
    print("==========================================")

if __name__ == '__main__':
    main()
