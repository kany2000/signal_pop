#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop 9/2 平日版 — B站单家重试（发布整套失败后的补发）

⚠️ 仅用于重发失败平台，绝不要重跑 publish_daily_20260901.py（会重复预约抖音/快手）。
坑位（signal-pop-weekly-publish 固化）：
- B站偶发 invalid peer certificate: Expired，重试一次即过
- B站命令不带 --headed（sau bilibili 不接受该参数，只有 douyin 需要）
"""
import sys, os, re, subprocess, time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
DATE = '20260901'
PUB = '2026-09-02'
OUT = 'E:/projects/signal_pop/output/daily/20260901'
VIDEO = os.path.join(OUT, f'signal_pop_daily_{DATE}.mp4')


def read_md(f):
    return open(os.path.join(OUT, f), encoding='utf-8').read()


md3 = read_md('bilibili.md')
lines3 = md3.strip().splitlines()
title3 = lines3[0].strip() if lines3 else f'{PUB}信号弹'
body3 = '\n'.join(lines3[1:]).strip() if len(lines3) > 1 else title3

print('=== B站（单家重试）===', flush=True)
print('title:', title3[:50], flush=True)

MAX_TRY = 2
for attempt in range(1, MAX_TRY + 1):
    r = subprocess.run(['sau', 'bilibili', 'upload-video', '--account', 'her2home', '--file', VIDEO,
                        '--title', title3, '--desc', body3,
                        '--tid', '249', '--schedule', f'{PUB} 08:00'],
                       capture_output=True, text=True, timeout=1800)
    print(f'--- attempt {attempt} exit={r.returncode} ---', flush=True)
    print((r.stdout or '')[-1200:], flush=True)
    if r.returncode == 0:
        print('B站发布成功 ✅', flush=True)
        break
    err = (r.stderr or '') + (r.stdout or '')
    print('STDERR:', (r.stderr or '')[-500:], flush=True)
    # 坑②：证书过期错误，重试一次即过
    if 'invalid peer certificate' in err and attempt < MAX_TRY:
        print('⚠️ 命中证书错误，1.5s 后重试一次...', flush=True)
        time.sleep(1.5)
        continue
    print('B站发布失败，需人工排查。', flush=True)
    break

print('\n=== B站重试结束 ===', flush=True)
