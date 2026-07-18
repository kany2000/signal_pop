#!/usr/bin/env python3
"""
Signal Pop — 监控流水线触发器
监控 /home/kan/shared/signal_pop/ 目录下的 filtered_news.json
发现新文件即触发完整流水线：生成脚本 → 女声 TTS → 男声 TTS → 归档
"""
import os
import sys
import json
import hashlib
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

SHARED_DIR = Path("/home/kan/shared/signal_pop")
DATA_DIR = Path("/home/kan/signal_pop/data")
OUTPUT_DIR = Path("/home/kan/signal_pop/output/daily")
ARCHIVE_DIR = Path("/home/kan/shared/signal_pop/archive")
STATE_FILE = Path("/home/kan/signal_pop/.pipeline_state.json")

# 确保目录存在
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_state():
    """加载已处理文件的状态记录"""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"processed": {}}

def save_state(state):
    """保存状态记录"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def file_hash(filepath):
    """计算文件内容 hash"""
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest()

def is_new_file(filepath, state):
    """判断文件是否为新文件（未处理过）"""
    fhash = file_hash(filepath)
    
    key = filepath.name
    if key in state["processed"]:
        prev = state["processed"][key]
        # 使用内容 hash 作为主要去重依据
        if prev.get("hash") == fhash:
            return False
    return True

def run_pipeline_step(cmd, cwd=None, desc=""):
    """运行流水线步骤，返回是否成功"""
    print(f"\n{'='*50}")
    print(f"▶ {desc}")
    print(f"   Command: {' '.join(cmd)}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(
            cmd, 
            cwd=cwd or "/home/kan/signal_pop",
            capture_output=True, 
            text=True, 
            timeout=300
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        if result.returncode != 0:
            print(f"❌ {desc} 失败 (exit code: {result.returncode})")
            return False
        print(f"✅ {desc} 完成")
        return True
    except subprocess.TimeoutExpired:
        print(f"❌ {desc} 超时")
        return False
    except Exception as e:
        print(f"❌ {desc} 异常: {e}")
        return False

def main():
    print(f"🔍 监控目录: {SHARED_DIR}")
    print(f"⏰ 检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 查找 filtered_news.json
    source_files = list(SHARED_DIR.glob("filtered_news.json"))
    if not source_files:
        print("📭 共享目录无新文件，退出")
        return 0
    
    source_file = source_files[0]
    print(f"📄 发现文件: {source_file}")
    
    # 加载状态
    state = load_state()
    
    # 检查是否已处理
    if not is_new_file(source_file, state):
        print("⏭️ 文件已处理过，跳过")
        return 0
    
    print("🆕 检测到新文件，开始流水线处理...")
    
    # 1. 复制到 data 目录
    target_file = DATA_DIR / "filtered_news.json"
    print(f"📋 复制 {source_file} → {target_file}")
    shutil.copy2(source_file, target_file)
    
    # 2. 运行 generate_script.py daily
    if not run_pipeline_step(
        [sys.executable, "src/generate_script.py", "daily"],
        desc="生成播报脚本 (daily)"
    ):
        return 1
    
    # 3. 读取生成的脚本文本
    script_files = sorted(OUTPUT_DIR.glob("signal_pop_daily_*.txt"))
    if not script_files:
        print("❌ 未找到生成的脚本文件")
        return 1
    latest_script = script_files[-1]
    with open(latest_script, 'r', encoding='utf-8') as f:
        script_text = f.read()
    print(f"📝 读取脚本: {latest_script} ({len(script_text)} 字符)")
    
    # 4. 女声 TTS
    female_wav = OUTPUT_DIR / f"signal_pop_daily_{datetime.now().strftime('%Y%m%d')}_female.wav"
    if not run_pipeline_step(
        [sys.executable, "src/tts_mimo.py", script_text, "--female", "--output", str(female_wav)],
        desc="女声 TTS 合成"
    ):
        return 1
    
    # 5. 男声 TTS (备用)
    male_wav = OUTPUT_DIR / f"signal_pop_daily_{datetime.now().strftime('%Y%m%d')}_male.wav"
    if not run_pipeline_step(
        [sys.executable, "src/tts_mimo.py", script_text, "--male", "--output", str(male_wav)],
        desc="男声 TTS 合成 (备用)"
    ):
        return 1
    
    # 6. 归档源文件 (先获取 stat 和 hash，再移动)
    stat_info = source_file.stat()
    mtime = stat_info.st_mtime
    fhash = file_hash(source_file)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"filtered_news_{timestamp}.json"
    archive_path = ARCHIVE_DIR / archive_name
    print(f"📦 归档: {source_file} → {archive_path}")
    shutil.move(str(source_file), str(archive_path))
    
    # 更新状态
    state["processed"][source_file.name] = {
        "mtime": mtime,
        "hash": fhash,
        "processed_at": datetime.now().isoformat(),
        "archive": archive_name
    }
    save_state(state)
    
    print(f"\n🎉 流水线完成！输出目录: {OUTPUT_DIR}")
    print(f"   - 脚本: {latest_script}")
    print(f"   - 女声: {female_wav.with_suffix('.mp3')}")
    print(f"   - 男声: {male_wav.with_suffix('.mp3')}")
    print(f"   - 归档: {archive_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())