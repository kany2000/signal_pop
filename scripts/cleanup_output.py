#!/usr/bin/env python3
"""每次做新视频前运行：旧输出移到 output_old，保持 output 干净"""
import os, shutil, datetime

BASE = "E:/projects/signal_pop"
OUTPUT = os.path.join(BASE, "output")
OLD = os.path.join(BASE, "output_old")

os.makedirs(OLD, exist_ok=True)

for item in os.listdir(OUTPUT):
    path = os.path.join(OUTPUT, item)
    if os.path.isdir(path) or item.endswith(".json"):
        dest = os.path.join(OLD, item)
        if os.path.exists(dest):
            ts = datetime.datetime.now().strftime("%H%M%S")
            dest = os.path.join(OLD, f"{item}_{ts}")
        shutil.move(path, dest)
        print(f"  Moved: {item} -> output_old/")

print("Done. output/ is clean.")