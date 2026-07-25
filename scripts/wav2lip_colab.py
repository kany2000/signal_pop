#!/usr/bin/env python3
"""Signal Pop Wav2Lip v3 — 修复模型下载+librosa兼容+尺寸"""
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

# 2. 克隆
print("="*60 + "\n2/5 克隆 Wav2Lip\n" + "="*60)
if os.path.exists("Wav2Lip"): shutil.rmtree("Wav2Lip")
run("git clone https://github.com/Rudrabha/Wav2Lip.git")
os.chdir("Wav2Lip")

# 3. 安装依赖（固定librosa版本避免mel()报错）
print("="*60 + "\n3/5 安装依赖\n" + "="*60)
run("pip install -q --only-binary :all: numpy opencv-python-headless imageio 2>&1 | tail -3")
run("pip install -q torch torchvision --index-url https://download.pytorch.org/whl/cu118 2>&1 | tail -3")
run("pip install -q tqdm 2>&1 | tail -3")
run("pip install -q 'librosa<0.10' 2>&1 | tail -3")  # 旧版 librosa 兼容 mel()
run("pip install -q face_detection 2>&1 | tail -3")

# 4. 下载模型（备用URL）
print("="*60 + "\n4/5 下载模型\n" + "="*60)
os.makedirs("checkpoints", exist_ok=True)
if not os.path.exists("checkpoints/wav2lip_gan.pth") or os.path.getsize("checkpoints/wav2lip_gan.pth") < 1e5:
    # 主URL（用curl -L 跟随重定向）
    run("curl -L -o checkpoints/wav2lip_gan.pth 'https://github.com/Rudrabha/Wav2Lip/releases/download/v0.1/wav2lip_gan.pth' 2>&1 | tail -5")
    # 备用
    if not os.path.exists("checkpoints/wav2lip_gan.pth") or os.path.getsize("checkpoints/wav2lip_gan.pth") < 1e5:
        print("Main URL failed, trying pip...")
        run("pip install -q wav2lip 2>/dev/null || true")
    sz = os.path.getsize("checkpoints/wav2lip_gan.pth") / 1048576 if os.path.exists("checkpoints/wav2lip_gan.pth") else 0
    print(f"  wav2lip_gan.pth: {sz:.1f}MB")

# 5. 输入检查
print("="*60 + "\n检查输入\n" + "="*60)
for f in ["/content/anchor.jpg", "/content/tts.wav"]:
    if not os.path.exists(f):
        print(f"ERROR: 请上传 {f}")
        sys.exit(1)
    print(f"  {os.path.basename(f)}: {os.path.getsize(f)//1024}KB")
shutil.copy("/content/anchor.jpg", "anchor.jpg")
shutil.copy("/content/tts.wav", "tts.wav")

# 6. 人脸检测+裁剪（确保偶数尺寸）
print("="*60 + "\n人脸检测\n" + "="*60)
run("""
python -c "
import cv2
img = cv2.imread('anchor.jpg')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
fc = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
faces = fc.detectMultiScale(gray, 1.1, 4)
print(f'Faces: {len(faces)}')
if len(faces) > 0:
    x,y,w,h = faces[0]
    # 确保偶数尺寸
    w = w if w%2==0 else w+1
    h = h if h%2==0 else h+1
    print(f'  face: x={x} y={y} w={w} h={h}')
    crop = img[y:y+h, x:x+w]
    crop = cv2.resize(crop, (512, 512))  # 统一缩放到512x512
    cv2.imwrite('face_crop.jpg', crop)
    print('  saved face_crop.jpg (512x512)')
else:
    print('  no face, using full image')
    img = cv2.resize(img, (512, 512))
    cv2.imwrite('face_crop.jpg', img)
" 2>&1
""")

# 7. 生成视频
print("="*60 + "\n生成视频\n" + "="*60)
r = run("ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 tts.wav")
dur = float(r.stdout.strip()) + 1.0
print(f"  Duration: {dur:.1f}s")
run(f"ffmpeg -y -loop 1 -i face_crop.jpg -c:v libx264 -t {dur} -pix_fmt yuv420p -r 25 input_video.mp4 2>&1 | tail -3")

# 8. Wav2Lip 推理
print("="*60 + "\nWav2Lip 推理\n" + "="*60)
if os.path.exists("checkpoints/wav2lip_gan.pth") and os.path.getsize("checkpoints/wav2lip_gan.pth") > 1e5:
    run("python inference.py --checkpoint_path checkpoints/wav2lip_gan.pth --face input_video.mp4 --audio tts.wav --outfile output_lipsync.mp4 2>&1")
else:
    print("Model file missing, skipping inference")

# 9. 结果
print("="*60 + "\n完成！\n" + "="*60)
for v in sorted(glob.glob("*.mp4")):
    if os.path.getsize(v) > 1e5:
        print(f"  {v} ({os.path.getsize(v)//1048576}MB)")
        from google.colab import files
        files.download(v)