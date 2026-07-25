#!/usr/bin/env python3
"""Signal Pop Wav2Lip v2 — 带人脸检测调试"""
import os, sys, subprocess, urllib.request, glob, shutil

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

# 2. 克隆 Wav2Lip（用更稳定的 fork）
print("="*60 + "\n2/5 克隆 Wav2Lip\n" + "="*60)
for d in ["Wav2Lip", "Wav2Lip_fork"]:
    if os.path.exists(d):
        shutil.rmtree(d)
run("git clone https://github.com/Rudrabha/Wav2Lip.git")
os.chdir("Wav2Lip")

# 3. 安装依赖
print("="*60 + "\n3/5 安装依赖\n" + "="*60)
run("pip install -q --only-binary :all: numpy opencv-python-headless imageio 2>&1 | tail -3")
run("pip install -q torch torchvision --index-url https://download.pytorch.org/whl/cu118 2>&1 | tail -3")
run("pip install -q tqdm librosa 2>&1 | tail -3")

# 安装 face_detection（分开装，失败不致命）
run("pip install -q face_detection 2>&1 | tail -5")

# 4. 下载模型
print("="*60 + "\n4/5 下载模型\n" + "="*60)
os.makedirs("checkpoints", exist_ok=True)
if not os.path.exists("checkpoints/wav2lip_gan.pth"):
    run("wget -q 'https://github.com/Rudrabha/Wav2Lip/releases/download/v0.1/wav2lip_gan.pth' -O checkpoints/wav2lip_gan.pth")
    sz = os.path.getsize("checkpoints/wav2lip_gan.pth") / 1048576
    print(f"  wav2lip_gan.pth: {sz:.1f}MB")

# 5. 检查输入
print("="*60 + "\n5/5 检查输入\n" + "="*60)
for f in ["/content/anchor.jpg", "/content/tts.wav"]:
    if not os.path.exists(f):
        print(f"ERROR: 请上传 {f}")
        sys.exit(1)
    print(f"  {os.path.basename(f)}: {os.path.getsize(f)//1024}KB")

shutil.copy("/content/anchor.jpg", "anchor.jpg")
shutil.copy("/content/tts.wav", "tts.wav")

# 6. 人脸检测测试
print("="*60 + "\n人脸检测测试\n" + "="*60)
run("""
python -c "
import cv2, numpy as np
from PIL import Image

# 用 opencv 自带的检测器试一下
img = cv2.imread('anchor.jpg')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
faces = face_cascade.detectMultiScale(gray, 1.1, 4)
print(f'OpenCV face detection: {len(faces)} faces')
for (x,y,w,h) in faces:
    print(f'  face at x={x} y={y} w={w} h={h}')
    # 裁剪人脸区域
    crop = img[y:y+h, x:x+w]
    cv2.imwrite('face_crop.jpg', crop)
    print('  saved face_crop.jpg')

# 如果没检测到，试一下全图
if len(faces) == 0:
    print('No face detected with OpenCV, trying full image...')
    cv2.imwrite('face_crop.jpg', img)
" 2>&1
""")

# 7. 生成主播视频
print("="*60 + "\n生成主播视频帧\n" + "="*60)
r = run("ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 tts.wav")
dur = float(r.stdout.strip()) + 1.0
print(f"  Audio duration: {dur:.1f}s")

# 用裁剪后的人脸做视频（如果检测到的话）
face_src = "face_crop.jpg" if os.path.exists("face_crop.jpg") else "anchor.jpg"
run(f"ffmpeg -y -loop 1 -i {face_src} -c:v libx264 -t {dur} -pix_fmt yuv420p -r 25 input_video.mp4 2>&1 | tail -3")

# 8. 运行 Wav2Lip
print("="*60 + "\nWav2Lip 推理\n" + "="*60)
# 不加 pads，用默认值
run("python inference.py --checkpoint_path checkpoints/wav2lip_gan.pth --face input_video.mp4 --audio tts.wav --outfile output_lipsync.mp4 2>&1")

# 9. 如果不行，试 --pads 参数
if not os.path.exists("output_lipsync.mp4") or os.path.getsize("output_lipsync.mp4") < 1e5:
    print("Trying with --pads...")
    run("python inference.py --checkpoint_path checkpoints/wav2lip_gan.pth --face input_video.mp4 --audio tts.wav --outfile output_lipsync.mp4 --pads 0 20 0 0 2>&1")

# 10. 结果
print("="*60 + "\n完成！\n" + "="*60)
for v in sorted(glob.glob("*.mp4")):
    if os.path.getsize(v) > 1e5:
        print(f"  {v} ({os.path.getsize(v)//1048576}MB)")
        from google.colab import files
        files.download(v)