#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop — 全平台发布编排器（sau 三平台 + Playwright 五平台）

流程：
  1. 跑 tools/publish_daily_{date}.py（sau：抖音/快手/B站，即时或定时由该脚本决定）
  2. 依次跑 Playwright 发布脚本（小红书/知乎/视频号）；未抓登录态的平台标记为 pending
  3. 汇总结果写入 output/<kind>/<date>/publish_status.json
  4. 调 publish_notify 推送结果（需配置 PUBLISH_NOTIFY_WEBHOOK）

用法：
  python tools/publish_all_daily.py 20260908
  python tools/publish_all_daily.py 20260908 --kind weekly

⚠️ Playwright 平台强依赖登录态：首次需 `python publish_xhs.py --date 20260908 --login` 等。
"""
import os
import sys
import json
import subprocess
import argparse

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable

SAU_PLATFORMS = []  # sau 三平台在 publish_daily_{date}.py 内已含
PLAYWRIGHT_PLATFORMS = ["xiaohongshu", "zhihu", "channels"]


def run_cmd(cmd):
    print("+ " + " ".join(cmd), flush=True)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        out = (r.stdout or "") + (r.stderr or "")
        return r.returncode == 0, out[-1200:]
    except subprocess.TimeoutExpired:
        return False, "超时(>30min)"
    except Exception as e:  # noqa
        return False, str(e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("date")
    ap.add_argument("--kind", default="daily")
    args = ap.parse_args()
    date, kind = args.date, args.kind
    base = os.path.join(PROJECT_ROOT, "output", kind, date)
    results = {}

    # 1) sau 三平台（抖音/快手/B站）
    sau_script = os.path.join(PROJECT_ROOT, "tools", f"publish_daily_{date}.py")
    if os.path.exists(sau_script):
        ok, msg = run_cmd([PY, sau_script])
        # sau 脚本自身已打印三平台结果；这里把已知三平台标记为已跑
        for p in ["douyin", "kuaishou", "bilibili"]:
            results[p] = ok
        print(f"  sau 三平台: {'✅' if ok else '❌'} {msg[:200]}")
    else:
        print(f"  ⚠️ 未找到 {sau_script}，跳过 sau 三平台")

    # 2) Playwright 五平台
    for plat in PLAYWRIGHT_PLATFORMS:
        script = os.path.join(PROJECT_ROOT, "tools", f"publish_{plat}.py")
        if not os.path.exists(script):
            results[plat] = None
            continue
        ok, msg = run_cmd([PY, script, "--date", date, "--kind", kind])
        results[plat] = ok
        print(f"  {plat}: {'✅' if ok else '❌'} {msg[:160]}")

    # 3) 写状态
    status = {"date": date, "kind": kind, "results": results}
    sj = os.path.join(base, "publish_status.json")
    with open(sj, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)
    print(f"✅ 状态已写: {sj}")

    # 4) 通知
    run_cmd([PY, os.path.join(PROJECT_ROOT, "tools", "publish_notify.py"),
             "--date", date, "--kind", kind])

    print("\n═══ 全平台结果 ═══")
    for k, v in results.items():
        tag = "✅" if v else ("⏸" if v is None else "❌")
        print(f"  {tag} {k}")


if __name__ == "__main__":
    main()
