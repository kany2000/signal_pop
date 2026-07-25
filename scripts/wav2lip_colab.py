#!/usr/bin/env python3
"""Signal Pop Wav2Lip — Colab一键脚本

用法：
  1. 上传到 Colab（T4 GPU）
  2. 传到 Colab 左侧文件面板：
     - anchor.jpg （主播头像，方形）
     - tts.wav （TTS音频）
  3. 运行本脚本
  4. 下载生成的 lip-sync 视频
"""
import os, sys, subprocess, urllib.request, urllib.parse, glob, time, shutil, site

def run(cmd, show=True):
    print(f"$ {cmd[:200]}")
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    out = (r.stderr or "") + (r.stdout or "")
    if out and show:
        print(out.strip()[-2000:])
    if r.returncode != 0:
        print(f"  exit code {r.returncode}")
    return r

os.chdir("/content")

# 1. 系统依赖
print("="*60 + "\n1/5 系统依赖\n" + "="*60)
run("apt-get -qq install ffmpeg")

# 2. 克隆 Wav2Lip
print("="*60 + "\n2/5 克隆 Wav2Lip\n" + "="*60)
if os.path.exists("Wav2Lip"):
    shutil.rmtree("Wav2Lip")
run("git clone https://github.com/Rudrabha/Wav2Lip.git")
os.chdir("Wav2Lip")

# 3. 安装依赖
print("="*60 + "\n3/5 安装依赖\n" + "="*60)
run("pip install -q --only-binary :all: numpy opencv-python-headless imageio scipy scikit-image 2>&1 | tail -3")
run("pip install -q torch torchvision --index-url https://download.pytorch.org/whl/cu118 2>&1 | tail -3")
run("pip install -q tqdm librosa face_detection 2>&1 | tail -3")

# 4. 下载模型
print("="*60 + "\n4/5 下载模型\n" + "="*60)
os.makedirs("checkpoints", exist_ok=True)
if not os.path.exists("checkpoints/wav2lip_gan.pth"):
    run("wget -q 'https://github.com/Rudrabha/Wav2Lip/releases/download/v0.1/wav2lip_gan.pth' -O checkpoints/wav2lip_gan.pth 2>&1")
    sz = os.path.getsize("checkpoints/wav2lip_gan.pth") / 1048576
    print(f"  wav2lip_gan.pth: {sz:.1f}MB")

# 5. 检查输入文件
print("="*60 + "\n5/5 检查输入\n" + "="*60)
for f in ["/content/anchor.jpg", "/content/tts.wav"]:
    if not os.path.exists(f):
        print(f"  ERROR: 请上传 {f} 到 Colab 左侧文件面板")
        sys.exit(1)
    print(f"  {os.path.basename(f)}: {os.path.getsize(f)//1024}KB")

# 复制文件到工作目录
shutil.copy("/content/anchor.jpg", "anchor.jpg")
shutil.copy("/content/tts.wav", "tts.wav")

# 6. 生成主播视频（从静态图片+音频）
print("="*60 + "\n生成主播视频帧\n" + "="*60)
# 先获取音频时长
r = run("ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 tts.wav")
dur = float(r.stdout.strip()) + 1.0
print(f"  Audio duration: {dur:.1f}s")

# 用图片生成视频（25fps）
run(f"ffmpeg -y -loop 1 -i anchor.jpg -c:v libx264 -t {dur} -pix_fmt yuv420p -r 25 input_video.mp4 2>&1 | tail -3")

# 7. 运行 Wav2Lip 推理
print("="*60 + "\nWav2Lip 推理（约5-10分钟）\n" + "="*60)
run("python inference.py --checkpoint_path checkpoints/wav2lip_gan.pth --face input_video.mp4 --audio tts.wav --outfile output_lipsync.mp4 --pads 0 0 0 0 2>&1")

# 8. 结果
print("="*60 + "\n完成！\n" + "="*60)
for v in sorted(glob.glob("*.mp4")):
    if os.path.getsize(v) > 1e5:
        print(f"  {v} ({os.path.getsize(v)//1048576}MB)")
        from google.colab import files
        files.download(v)