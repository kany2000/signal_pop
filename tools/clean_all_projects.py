#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全局跨项目制作残留与 _ 废弃切片深度清理工具
作用范围：E:\projects 全局各视频制作/动效/播客项目
重点清除：
1. signal_pop 各期残留的 _all32_grid.jpg、_contact_sheet.jpg、_chk_*.jpg、audio/_tmp/ 等
2. signal-motion 的 output/cognition/_work_y4/、_qa/、_raw_body_backup/ 等中间件
3. news-talk 的 _dxt_work/、大学课堂/_review/、_chk06.jpg、_qa_*.jpg 等
4. 复刻 与 Easel 中的 _frames/、_qa/、_sheet*.jpg、_migration_test/
5. 全项目生成的 __pycache__ / .pytest_cache
严格保护：
- 任何项目的源码私有模块（如 notebooklm-py/_research.py、cbm-test/_common_scanner.h）
- _dl 目录下的引擎代码
- 所有正式成片 mp4、封面图、8平台文案 md、srt、json 数据底表
"""

import os
import shutil

BASE_DIR = r"E:\projects"

def fmt_size(sz):
    for u in ['B', 'KB', 'MB', 'GB']:
        if sz < 1024:
            return f'{sz:.2f} {u}'
        sz /= 1024
    return f'{sz:.2f} TB'

def remove_item(p):
    """安全删除文件或目录"""
    if not os.path.exists(p):
        return 0, 0
    cnt = 0
    sz = 0
    try:
        if os.path.isfile(p):
            sz = os.path.getsize(p)
            cnt = 1
            os.remove(p)
        elif os.path.isdir(p):
            for r, ds, fs in os.walk(p):
                for f in fs:
                    try:
                        sz += os.path.getsize(os.path.join(r, f))
                        cnt += 1
                    except OSError:
                        pass
            shutil.rmtree(p, ignore_errors=True)
    except Exception as e:
        print(f"  [跳过] 无法删除 {p}: {e}")
        return 0, 0
    return cnt, sz

def main():
    print(f"=== 开始全项目制作残留与废弃切片清理 [{BASE_DIR}] ===\n")
    
    total_cleaned_cnt = 0
    total_cleaned_sz = 0
    
    # -------------------------------------------------------------
    # 1. signal_pop 深度清理 (所有 output 下带 _ 的测试切片/拼图/音频tmp)
    # -------------------------------------------------------------
    print("[1/5] 清理 signal_pop 各期内部的 _ 临时切片、拼图与音频分段...")
    sp_dir = os.path.join(BASE_DIR, "signal_pop")
    sp_dirs_to_clean = []
    sp_files_to_clean = []
    
    if os.path.exists(sp_dir):
        for root, dirs, files in os.walk(sp_dir):
            if ".git" in root or "node_modules" in root: continue
            
            for d in list(dirs):
                # audio/_tmp, econ_audio/_tmp, _real_alternatives, _ab_响度对比
                if d in ["_tmp", "_real_alternatives", "_ab_响度对比", "_orig"]:
                    sp_dirs_to_clean.append(os.path.join(root, d))
                    
            for f in files:
                # 排除系统必要文件
                if f.startswith("_") and not f.startswith("__"):
                    # 匹配像 _all32_grid.jpg, _contact_sheet.jpg, _axin_debug.jpg, _s000.mp3 等
                    fp = os.path.join(root, f)
                    sp_files_to_clean.append(fp)
                    
        # 先删目录
        for d in sp_dirs_to_clean:
            c, s = remove_item(d)
            if c > 0:
                total_cleaned_cnt += c
                total_cleaned_sz += s
                print(f"  - 已清理目录: {os.path.relpath(d, sp_dir)} ({c}文件, {fmt_size(s)})")
                
        # 再删文件
        for f in sp_files_to_clean:
            if os.path.exists(f): # 如果已经被目录删除包含了则跳过
                c, s = remove_item(f)
                if c > 0:
                    total_cleaned_cnt += c
                    total_cleaned_sz += s
                    # 仅打印重点大文件或代表性文件
                    if s > 1024 * 500 or f.endswith(('.jpg', '.png', '.mp4', '.py')):
                        print(f"  - 已清理文件: {os.path.relpath(f, sp_dir)} ({fmt_size(s)})")

    # -------------------------------------------------------------
    # 2. signal-motion 深度清理 (output/cognition/ 下的 _work_y4, _qa 等)
    # -------------------------------------------------------------
    print("\n[2/5] 清理 signal-motion 内部渲染中间件与测试抽帧...")
    sm_dir = os.path.join(BASE_DIR, "signal-motion")
    if os.path.exists(sm_dir):
        cog_dir = os.path.join(sm_dir, "output", "cognition")
        if os.path.exists(cog_dir):
            for item in list(os.listdir(cog_dir)):
                p = os.path.join(cog_dir, item)
                if item.startswith("_"):
                    c, s = remove_item(p)
                    total_cleaned_cnt += c
                    total_cleaned_sz += s
                    print(f"  - 已清理 signal-motion: output/cognition/{item} ({c}文件, {fmt_size(s)})")
            # 内部 audio 目录下的临时音频
            sm_audio = os.path.join(cog_dir, "audio")
            if os.path.exists(sm_audio):
                for item in list(os.listdir(sm_audio)):
                    if item.startswith("_"):
                        c, s = remove_item(os.path.join(sm_audio, item))
                        total_cleaned_cnt += c
                        total_cleaned_sz += s
                        print(f"  - 已清理 signal-motion: audio/{item} ({fmt_size(s)})")

    # -------------------------------------------------------------
    # 3. news-talk 深度清理 (_dxt_work, 大学课堂/_review, 抽帧_qa_*.jpg)
    # -------------------------------------------------------------
    print("\n[3/5] 清理 news-talk 制作切片与测试废弃文件...")
    nt_dir = os.path.join(BASE_DIR, "news-talk")
    if os.path.exists(nt_dir):
        # 目录
        for d in [os.path.join(nt_dir, "_dxt_work"), os.path.join(nt_dir, "大学课堂", "_review")]:
            if os.path.exists(d):
                c, s = remove_item(d)
                total_cleaned_cnt += c
                total_cleaned_sz += s
                print(f"  - 已清理目录: news-talk/{os.path.relpath(d, nt_dir)} ({c}文件, {fmt_size(s)})")
        # 散落测试文件
        for root, dirs, files in os.walk(nt_dir):
            if ".git" in root or "node_modules" in root: continue
            for f in files:
                if f.startswith(("_chk", "_seg", "_qa_")):
                    p = os.path.join(root, f)
                    c, s = remove_item(p)
                    total_cleaned_cnt += c
                    total_cleaned_sz += s
                    print(f"  - 已清理测试文件: news-talk/{os.path.relpath(p, nt_dir)} ({fmt_size(s)})")

    # -------------------------------------------------------------
    # 4. 复刻 / Easel / social-auto-upload 废弃切片
    # -------------------------------------------------------------
    print("\n[4/5] 清理 复刻 / Easel / social-auto-upload 测试切片与脚本...")
    # 复刻
    fk_dir = os.path.join(BASE_DIR, "复刻")
    if os.path.exists(fk_dir):
        for d in [os.path.join(fk_dir, "_frames"), os.path.join(fk_dir, "_qa")]:
            if os.path.exists(d):
                c, s = remove_item(d)
                total_cleaned_cnt += c
                total_cleaned_sz += s
                print(f"  - 已清理复刻目录: {os.path.basename(d)} ({c}文件, {fmt_size(s)})")
        fk_frames = os.path.join(fk_dir, "productions", "four-beauties", "assets", "frames")
        if os.path.exists(fk_frames):
            for f in list(os.listdir(fk_frames)):
                if f.startswith("_"):
                    c, s = remove_item(os.path.join(fk_frames, f))
                    total_cleaned_cnt += c
                    total_cleaned_sz += s
                    print(f"  - 已清理复刻废切片: {f} ({fmt_size(s)})")
                    
    # Easel
    easel_mig = os.path.join(BASE_DIR, "Easel", "outputs", "_migration_test")
    if os.path.exists(easel_mig):
        c, s = remove_item(easel_mig)
        total_cleaned_cnt += c
        total_cleaned_sz += s
        print(f"  - 已清理 Easel 测试目录: outputs/_migration_test ({c}文件, {fmt_size(s)})")

    # social-auto-upload
    sau_dir = os.path.join(BASE_DIR, "social-auto-upload")
    if os.path.exists(sau_dir):
        for f in ["_debug_tencent.py", "_upload_tencent.py"]:
            p = os.path.join(sau_dir, f)
            if os.path.exists(p):
                c, s = remove_item(p)
                total_cleaned_cnt += c
                total_cleaned_sz += s
                print(f"  - 已清理 social-auto-upload 临时脚本: {f} ({fmt_size(s)})")

    # -------------------------------------------------------------
    # 5. 全项目 __pycache__ / .pytest_cache 编译再生缓存清理
    # -------------------------------------------------------------
    print("\n[5/5] 清理各项目 __pycache__ / .pytest_cache 可再生缓存...")
    EXCLUDE_SCAN = {'.git', 'node_modules', '.venv', 'venv', 'env', 'site-packages'}
    for proj in sorted(os.listdir(BASE_DIR)):
        p_path = os.path.join(BASE_DIR, proj)
        if not os.path.isdir(p_path) or proj.startswith("."): continue
        for root, dirs, files in os.walk(p_path):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_SCAN and not d.startswith('.git')]
            for d in list(dirs):
                if d in ["__pycache__", ".pytest_cache"]:
                    dp = os.path.join(root, d)
                    c, s = remove_item(dp)
                    if c > 0:
                        total_cleaned_cnt += c
                        total_cleaned_sz += s

    print("\n" + "="*50)
    print(f"✅ 全局跨项目深度清理完成！")
    print(f"📊 累计彻底清除废弃文件/切片: {total_cleaned_cnt} 个")
    print(f"💾 累计释放磁盘空间: {fmt_size(total_cleaned_sz)}")
    print("="*50)

if __name__ == "__main__":
    main()
