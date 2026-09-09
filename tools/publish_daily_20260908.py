#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop 20260908（周三 2026-09-09 播出）三平台发布：抖音/快手/B站（即时发布，非定时）

⚠️ 运行前提：用户已确认最终视频（两级确认铁律），并已明确「发布吧」。
坑位提醒（signal-pop-weekly-publish skill 固化）：
- 抖音必须 --headed（headless 卡创作平台弹窗）；快手 --headed 正常
- B站偶发 invalid peer certificate: Expired → 外层重试循环（本脚本已包）
- 沙箱/AI 会话跑 B站需 PROCESSOR_ARCHITECTURE=AMD64（在 Bash 环境 export）
- 不要重跑整套（防重复预约）；失败平台单家重试
"""
import sys, os, re, subprocess, time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
DATE = '20260908'
PUB = '2026-09-09'
OUT = f'E:/projects/signal_pop/output/daily/{DATE}'
VIDEO = os.path.join(OUT, f'signal_pop_daily_{DATE}.mp4')
COVER_34 = os.path.join(OUT, f'cover_{PUB.replace("-", "")}_3x4.png')


def read_md(f):
    return open(os.path.join(OUT, f), encoding='utf-8').read()


def extract(t, k):
    m = re.search(rf'^{k}[：:]\s*(.+?)(?:\n\n|\Z)', t, re.S | re.M)
    m = m or re.search(rf'^{k}[：:]\s*(.+)$', t, re.S | re.M)
    return m.group(1).strip() if m else ''


def tags(t):
    ls = [l for l in t.splitlines() if l.startswith('#')]
    if not ls:
        return 'AI语播信号弹每周精选,每日新闻,今日热点'
    return ','.join(x.strip('#') for x in ls[-1].split())


results = {}

# === 抖音（--headed 铁律；即时发布不带 --schedule） ===
md = read_md('douyin.md')
title = extract(md, '标题')
desc = extract(md, '简介')
tg = tags(md)
print('=== 抖音 ===', flush=True)
print('title:', title[:60], flush=True)
r = subprocess.run(['sau', 'douyin', 'upload-video', '--account', 'her2home', '--file', VIDEO,
                    '--title', title, '--desc', desc, '--tags', tg, '--headed'],
                   capture_output=True, text=True, timeout=1800)
print('exit=', r.returncode, flush=True)
print((r.stdout or '')[-1500:], flush=True)
if r.returncode != 0:
    print('STDERR:', (r.stderr or '')[-800:], flush=True)
results['douyin'] = r.returncode == 0

# === 快手（--headed + 竖封面） ===
md2 = read_md('kuaishou.md')
title2 = extract(md2, '标题')
desc2 = extract(md2, '简介')
tg2 = tags(md2)
print('\n=== 快手 ===', flush=True)
print('title:', title2[:60], flush=True)
r2 = subprocess.run(['sau', 'kuaishou', 'upload-video', '--account', 'her2home', '--file', VIDEO,
                     '--title', title2, '--desc', desc2, '--tags', tg2,
                     '--thumbnail', COVER_34, '--headed'],
                    capture_output=True, text=True, timeout=1800)
print('exit=', r2.returncode, flush=True)
print((r2.stdout or '')[-1500:], flush=True)
if r2.returncode != 0:
    print('STDERR:', (r2.stderr or '')[-800:], flush=True)
results['kuaishou'] = r2.returncode == 0

# === B站（外层重试循环，应对偶发证书错误） ===
md3 = read_md('bilibili.md')
lines3 = md3.strip().splitlines()
title3 = lines3[0].strip() if lines3 else f'{PUB}AI语播·信号弹每周精选'
body3 = '\n'.join(lines3[1:]).strip() if len(lines3) > 1 else title3
title3 = (title3[:78].rstrip() + '…') if len(title3) > 78 else title3
print('\n=== B站 ===', flush=True)
print('title:', title3[:60], flush=True)
ok_bili = False
for attempt in range(1, 4):
    print(f'--- B站 尝试 {attempt}/3 ---', flush=True)
    r3 = subprocess.run(['sau', 'bilibili', 'upload-video', '--account', 'her2home', '--file', VIDEO,
                         '--title', title3, '--desc', body3,
                         '--tid', '249'],
                        capture_output=True, text=True, timeout=1800)
    print('exit=', r3.returncode, flush=True)
    print((r3.stdout or '')[-1500:], flush=True)
    if r3.returncode == 0:
        ok_bili = True
        break
    print('STDERR:', (r3.stderr or '')[-800:], flush=True)
    if attempt < 3:
        print('⚠️ 疑似证书/网络错误，5s 后外层重试...', flush=True)
        time.sleep(5)
results['bilibili'] = ok_bili

print('\n' + '=' * 60, flush=True)
for k, ok in results.items():
    print(f"  {'✅' if ok else '❌'} {k}", flush=True)
print('\n发布模式：即时发布（无 --schedule）', flush=True)
print('📌 知乎/Facebook/Twitter：sau 不支持，需手动。小红书/YouTube 可由 sau 发，按约定暂手动。', flush=True)
