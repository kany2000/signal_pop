#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop 9/2（周三）三平台定时发布：抖音/快手/B站（9/2 08:00）

⚠️ 运行前提：用户已确认最终视频（两级确认铁律）。
坑位提醒（signal-pop-weekly-publish skill 固化）：
- 抖音必须 --headed（headless 卡创作平台弹窗）
- B站偶发 invalid peer certificate: Expired，重试一次即过
- 重跑整套会重复预约已成功平台；失败平台请单家重试
"""
import sys, os, re, subprocess

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
DATE = '20260901'
PUB = '2026-09-02'
OUT = 'E:/projects/signal_pop/output/daily/20260901'
VIDEO = os.path.join(OUT, f'signal_pop_daily_{DATE}.mp4')


def read_md(f):
    return open(os.path.join(OUT, f), encoding='utf-8').read()


def extract(t, k):
    m = re.search(rf'^{k}[：:]\s*(.+?)(?:\n\n|\Z)', t, re.S | re.M)
    m = m or re.search(rf'^{k}[：:]\s*(.+)$', t, re.S | re.M)
    return m.group(1).strip() if m else ''


def tags(t):
    ls = [l for l in t.splitlines() if l.startswith('#')]
    if not ls:
        return '隔天信号弹,每日新闻,今日热点'
    return ','.join(x.strip('#') for x in ls[-1].split())


# === 抖音（--headed 铁律） ===
md = read_md('douyin.md')
title = extract(md, '标题')
desc = extract(md, '简介')
tg = tags(md)
print('=== 抖音 ===', flush=True)
print('title:', title[:50], flush=True)
r = subprocess.run(['sau', 'douyin', 'upload-video', '--account', 'her2home', '--file', VIDEO,
                    '--title', title, '--desc', desc, '--tags', tg,
                    '--schedule', f'{PUB} 08:00', '--headed'],
                   capture_output=True, text=True, timeout=1800)
print('exit=', r.returncode, flush=True)
print((r.stdout or '')[-1200:], flush=True)
if r.returncode != 0:
    print('STDERR:', (r.stderr or '')[-500:], flush=True)

# === 快手 ===
md2 = read_md('kuaishou.md')
title2 = extract(md2, '标题')
desc2 = extract(md2, '简介')
tg2 = tags(md2)
cover = os.path.join(OUT, f'cover_{PUB.replace("-", "")}_3x4.png')
print('\n=== 快手 ===', flush=True)
print('title:', title2[:50], flush=True)
r2 = subprocess.run(['sau', 'kuaishou', 'upload-video', '--account', 'her2home', '--file', VIDEO,
                     '--title', title2, '--desc', desc2, '--tags', tg2,
                     '--thumbnail', cover,
                     '--schedule', f'{PUB} 08:00', '--headed'],
                    capture_output=True, text=True, timeout=1800)
print('exit=', r2.returncode, flush=True)
print((r2.stdout or '')[-1200:], flush=True)
if r2.returncode != 0:
    print('STDERR:', (r2.stderr or '')[-500:], flush=True)

# === B站 ===
md3 = read_md('bilibili.md')
lines3 = md3.strip().splitlines()
title3 = lines3[0].strip() if lines3 else f'{PUB}信号弹'
body3 = '\n'.join(lines3[1:]).strip() if len(lines3) > 1 else title3
print('\n=== B站 ===', flush=True)
print('title:', title3[:50], flush=True)
r3 = subprocess.run(['sau', 'bilibili', 'upload-video', '--account', 'her2home', '--file', VIDEO,
                     '--title', title3, '--desc', body3,
                     '--tid', '249', '--schedule', f'{PUB} 08:00'],
                    capture_output=True, text=True, timeout=1800)
print('exit=', r3.returncode, flush=True)
print((r3.stdout or '')[-1200:], flush=True)
if r3.returncode != 0:
    print('STDERR:', (r3.stderr or '')[-500:], flush=True)

print('\n=== 发布流程结束 ===', flush=True)
