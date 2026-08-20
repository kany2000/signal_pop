#!/usr/bin/env python3
"""Step 3 (alt): 云端高质量 TTS —— 火山引擎 / 讯飞 双引擎统一接入

背景（2026-08-16 调研）：
  edge-tts 粤语（zh-HK-HiuGaaiNeural）音质偏硬、AI 感强；
  ViiTor 需强制购买 6.9/7 天套餐，放弃。
  免费且音质显著更好的云端方案：
    1) 火山引擎（字节）: console.volcengine.com 语音合成，每月 50 万字符免费，抖音/剪映同源
    2) 讯飞开放平台:   xfyun.cn 在线语音合成，个人免费 1 万次调用/3 个月，粤语「小梅」最地道

用法：
  export SIGNAL_POP_TTS_BACKEND=volcengine|xunfei|edge   (默认 edge，行为与旧版一致)
  export SIGNAL_POP_VOLC_API_KEY=xxx                      (火山引擎新版控制台 API Key)
  export SIGNAL_POP_XUNFEI_APPID=xxx SIGNAL_POP_XUNFEI_API_KEY=xxx SIGNAL_POP_XUNFEI_API_SECRET=xxx
  python tools/gen_cloud_tts.py 20260816                  # 与 win_pipeline_tts 同接口：读 parsed_news.json -> tts.wav

输出与 win_pipeline_tts 完全一致：audio/tts.wav + audio/tts_segments.json（float 时长列表）
"""
import sys, os, json, time, base64, hashlib, hmac, struct, wave, subprocess
from datetime import datetime, timedelta
from email.utils import formatdate

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 触发 config._load_dotenv() 注入 .env 密钥（豆包/讯飞）
sys.path.insert(0, PROJECT_ROOT)
import config  # noqa: E402, F401
FFMPEG = os.path.join(PROJECT_ROOT, "bin", "ffmpeg-9.0.1-essentials_build", "bin", "ffmpeg.exe")

BACKEND = os.environ.get("SIGNAL_POP_TTS_BACKEND", "volcengine")

# ---------- 音色映射（平日女声 / 周末男声 / 周末女声 / 粤语） ----------
# 火山引擎豆包语音 TTS 2.0（seed-tts-2.0 大模型音色，必须 *_uranus_bigtts 结尾）
VOLC_VOICE_WEEKDAY = "zh_female_vv_uranus_bigtts"   # Vivi 2.0（平日女声，活泼）✅用户 2026-08-16 选
VOLC_VOICE_WEEKEND = "zh_male_m191_uranus_bigtts"   # 云舟 2.0（周末男声·阿信）✅用户认可
VOLC_VOICE_WEEKEND_F = "zh_female_shuangkuaisisi_uranus_bigtts"  # 爽快思思 2.0（周末女声·小蓝）✅用户认可
# 火山粤语已弃用（用户 2026-08-16 反馈"粤语好奇怪"）
# 讯飞：普通话超拟人备用；粤语 = 小梅 xiaomei（广东女声，用户 2026-08-16 裁决"勉强可以用"）
XUNFEI_VOICE_WEEKDAY = "x4_yezi"                  # 超拟人女声叶子（如未开通用 xiaoyan 标准女声）
XUNFEI_VOICE_WEEKEND = "x4_qianmo"                # 超拟人男声（如未开通用 xiaoyu 标准男声）
XUNFEI_VOICE_YUE = "xiaomei"                      # 讯飞小梅（广东女声粤语）✅用户裁决"勉强可以用"
# 已否掉的粤语：讯飞小月 xiaoyue（普通话读粤语"很搞笑"）、x2_xiaoyue（付费未授权）、x4_guangdong、xiaogang
# 已否掉的平日女声候选：小何 xiaohe、贴心女声、知性女声（用户最终选 Vivi）

# 与 win_pipeline_tts 一致的音色选择规则
def select_voice(pub_weekday="星期六", lang="zh", speaker=None):
    """speaker 参数用于周末双人：'阿信'=男声 / '小蓝'=周末女声；其余按发布日自动。"""
    is_weekend = pub_weekday in ("星期六", "星期日")
    if BACKEND == "volcengine":
        if lang == "yue":
            return VOLC_VOICE_YUE
        if speaker == "阿信":
            return VOLC_VOICE_WEEKEND
        if speaker == "小蓝":
            return VOLC_VOICE_WEEKEND_F
        return VOLC_VOICE_WEEKEND if is_weekend else VOLC_VOICE_WEEKDAY
    if BACKEND == "xunfei":
        if lang == "yue":
            return XUNFEI_VOICE_YUE
        return XUNFEI_VOICE_WEEKEND if is_weekend else XUNFEI_VOICE_WEEKDAY
    # edge 兜底
    return ("zh-CN-YunyangNeural" if is_weekend else "zh-CN-XiaoxiaoNeural")


def build_segments(items, pub_date_fmt, pub_weekday):
    """与 win_pipeline_tts.build_segments 完全一致的分段逻辑。"""
    if any(it.get("rank") is not None for it in items):
        segs = [("intro", "这里是隔天信号弹·周末特别版！本周十大事件，倒计时揭晓——从第十名到第一名，哪条才是本周之最？")]
        for it in items:
            segs.append((f"item{it.get('num', 0)}", it["full_body"]))
        segs.append(("outro", "以上是本期信号弹周末特别版。您的一键三连，是我们更新制作的动力！互动话题：本周哪条新闻您觉得最值得关注？欢迎在评论区留言，我们下周见~"))
        return segs
    segs = [("intro", f"这里是隔天信号弹，今天是{pub_date_fmt}，{pub_weekday}。欢迎收看本期信号弹，以下是本期精选的{len(items)}条核心新闻。")]
    for i, item in enumerate(items, 1):
        n = item.get("num", i)
        if n == 0:
            segs.append(("item0", f"历史上的今天。{item['full_body']}"))
            continue
        txt = f"第{n}条，{item['section']}。{item['title']}。{item['full_body']}"
        if item["opinion"]:
            txt += f".主播观点：{item['opinion']}"
        segs.append((f"item{n}", txt))
    segs.append(("outro", "您的一键三连是我们更新制作的动力。互动话题：您最关注哪条新闻？欢迎在评论区留言讨论！感谢您的关注，我们下期见~"))
    return segs


# ================= 火山引擎豆包语音（V3 HTTP unidirectional，AppID + Access Token 鉴权） =================
def volc_synthesize(text, voice, out_mp3, resource_id="seed-tts-2.0"):
    """豆包语音合成大模型 2.0（seed-tts-2.0）。
    V3 HTTP unidirectional 接口（Chunked 流式，支持 bigtts 系列音色）。
    鉴权：X-Api-App-Id + X-Api-Access-Key（豆包语音控制台应用详情）。
    """
    import requests
    appid = os.environ.get("DOUBAO_APP_ID", "")
    token = os.environ.get("DOUBAO_ACCESS_TOKEN", "")
    if not (appid and token):
        raise RuntimeError("未配置 DOUBAO_APP_ID / DOUBAO_ACCESS_TOKEN（豆包语音控制台应用详情）")
    url = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"
    headers = {
        "Content-Type": "application/json",
        "X-Api-App-Id": appid,
        "X-Api-Access-Key": token,
        "X-Api-Resource-Id": resource_id,
        "Connection": "keep-alive",
    }
    payload = {
        "user": {"uid": f"signal_pop_{int(time.time())}"},
        "req_params": {
            "text": text,
            "speaker": voice,
            "speed_ratio": 1.0,
            "volume_ratio": 1.0,
            "audio_params": {"format": "mp3", "sample_rate": 24000},
        },
    }
    r = requests.post(url, json=payload, headers=headers, timeout=120, stream=True)
    if r.status_code != 200:
        raise RuntimeError(f"火山引擎 HTTP {r.status_code}: {r.text[:300]}")
    # NDJSON 流式：每行 {"code":0,"data":"base64"}，最后 {"code":20000000}
    audio = bytearray()
    for line in r.iter_lines(decode_unicode=True):
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        code = obj.get("code")
        if code == 0 and obj.get("data"):
            audio.extend(base64.b64decode(obj["data"]))
        elif code != 0 and code != 20000000:
            raise RuntimeError(f"火山引擎合成错误 code={code}: {obj.get('message', '')}")
    if not audio:
        raise RuntimeError("火山引擎返回空音频")
    with open(out_mp3, "wb") as f:
        f.write(bytes(audio))
    return out_mp3


# ================= 讯飞（WebSocket v2 + HMAC-SHA256 签名） =================
def xunfei_synthesize(text, voice, out_mp3):
    import websocket
    appid = os.environ.get("SIGNAL_POP_XUNFEI_APPID", "")
    apikey = os.environ.get("SIGNAL_POP_XUNFEI_API_KEY", "")
    apisecret = os.environ.get("SIGNAL_POP_XUNFEI_API_SECRET", "")
    if not (appid and apikey and apisecret):
        raise RuntimeError("未配置讯飞 SIGNAL_POP_XUNFEI_APPID / API_KEY / API_SECRET")

    host = "tts-api.xfyun.cn"
    path = "/v2/tts"
    date = formatdate(timeval=None, localtime=False, usegmt=True)
    signature_origin = f"host: {host}\ndate: {date}\nGET {path} HTTP/1.1"
    signature_sha = base64.b64encode(
        hmac.new(apisecret.encode(), signature_origin.encode(), digestmod=hashlib.sha256).digest()
    ).decode()
    authorization_origin = (f'api_key="{apikey}", algorithm="hmac-sha256", '
                            f'headers="host date request-line", signature="{signature_sha}"')
    authorization = base64.b64encode(authorization_origin.encode()).decode()
    # URL 参数必须做百分号编码（date 含空格/逗号，authorization 含特殊字符）
    import urllib.parse
    query = urllib.parse.urlencode({
        "authorization": authorization,
        "date": date,
        "host": host,
    })
    url = f"wss://{host}{path}?{query}"

    ws = websocket.create_connection(url, timeout=120, enable_multithread=True)
    audio = bytearray()
    try:
        data = {
            "common": {"app_id": appid},
            "business": {
                "aue": "lame",       # mp3 输出（lame 仅支持 16000/8000 采样率）
                "sfl": 1,            # 流式返回
                "auf": "audio/L16;rate=16000",
                "vcn": voice,
                "speed": 50,         # 语速 0-100，50 默认
                "volume": 50,
                "pitch": 50,
                "tte": "UTF8",
            },
            "data": {
                "status": 2,  # 2=最后一片
                "text": base64.b64encode(text.encode("utf-8")).decode(),
            },
        }
        ws.send(json.dumps(data))
        while True:
            msg = json.loads(ws.recv())
            code = msg.get("code", -1)
            if code != 0:
                raise RuntimeError(f"讯飞合成错误 code={code}: {msg.get('message', '')}")
            audio_data = msg.get("data", {}).get("audio", "")
            if audio_data:
                audio.extend(base64.b64decode(audio_data))
            if msg.get("data", {}).get("status", 0) == 2:
                break
    finally:
        ws.close()
    if not audio:
        raise RuntimeError("讯飞返回空音频")
    with open(out_mp3, "wb") as f:
        f.write(bytes(audio))
    return out_mp3


# ================= 统一合成 + 时长 =================
def _safe_remove(path):
    """删除文件（兼容 Windows 沙箱回收站不可用场景：ctypes 直调 DeleteFileW）。"""
    import ctypes
    try:
        if os.path.exists(path):
            if not ctypes.windll.kernel32.DeleteFileW(os.path.abspath(path)):
                os.remove(path)
    except Exception:
        try:
            os.remove(path)
        except Exception:
            pass


def synthesize_one(idx, label, text, voice, audio_dir):
    mp3 = os.path.join(audio_dir, f"_s{idx:03d}.mp3")
    for attempt in range(3):
        try:
            if BACKEND == "volcengine":
                volc_synthesize(text, voice, mp3)
            elif BACKEND == "xunfei":
                xunfei_synthesize(text, voice, mp3)
            else:
                raise RuntimeError(f"未知后端: {BACKEND}")
            if os.path.getsize(mp3) > 500:
                return mp3
        except Exception as e:
            print(f"  [{label}] 尝试{attempt+1}失败: {str(e)[:80]}")
            time.sleep(3)
    return None


def gen_tts(items_path, output_wav, pub_date_fmt="2026年07月25日", pub_weekday="星期六", lang="zh"):
    with open(items_path, encoding="utf-8") as f:
        items = json.load(f)
    segs = build_segments(items, pub_date_fmt, pub_weekday)
    voice = select_voice(pub_weekday, lang)
    print(f"[{BACKEND}] {len(segs)} 段, 语音: {voice}")

    audio_dir = os.path.dirname(output_wav)
    os.makedirs(audio_dir, exist_ok=True)

    # 串行（云端 API 有 QPS 限制，串行最稳）
    durations = []
    all_pcm = bytearray()
    for i, (label, text) in enumerate(segs):
        mp3 = synthesize_one(i, label, text, voice, audio_dir)
        if not mp3 or not os.path.exists(mp3):
            print(f"  ⚠️ [{label}] 3 次尝试均失败，跳过")
            durations.append(1.0)
            continue
        wav = mp3.replace(".mp3", ".wav")
        subprocess.run([FFMPEG, "-y", "-i", mp3, "-acodec", "pcm_s16le", "-ar", "24000", "-ac", "1", wav],
                       check=True, capture_output=True, timeout=60)
        _safe_remove(mp3)
        with wave.open(wav, "rb") as w:
            rate = w.getframerate()
            raw = w.readframes(w.getnframes())
        samples = [int.from_bytes(raw[i:i+2], "little", signed=True) for i in range(0, len(raw), 2)]
        # trim silence
        start, end = 0, len(samples)
        for i in range(min(len(samples), int(rate * 0.5))):
            if abs(samples[i]) > 200:
                start = i
                break
        for i in range(len(samples) - 1, max(0, len(samples) - int(rate * 0.3)) - 1, -1):
            if abs(samples[i]) > 200:
                end = i + 1
                break
        trimmed = samples[start:end]
        dur = len(trimmed) / rate
        for s in trimmed:
            all_pcm.extend(struct.pack("<h", s))
        durations.append(dur)
        _safe_remove(wav)
        print(f"  [{label}] {dur:.2f}s")

    with wave.open(output_wav, "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(24000)
        out.writeframes(bytes(all_pcm))
    seg_path = output_wav.replace(".wav", "_segments.json")
    with open(seg_path, "w", encoding="utf-8") as f:
        json.dump(durations, f)
    print(f"✅ [{BACKEND}] 完成: {sum(durations):.2f}s, {len(durations)} 段 -> {output_wav}")
    return output_wav, durations


def test_single(text="这里是隔天信号弹，测试云端语音合成效果。", voice=None, out="output/cloud_tts_test.mp3"):
    """单句试听（填 Key 后先跑这个验证）。"""
    voice = voice or select_voice("星期六")
    print(f"[{BACKEND}] 试听: {voice}")
    if BACKEND == "volcengine":
        volc_synthesize(text, voice, out)
    elif BACKEND == "xunfei":
        xunfei_synthesize(text, voice, out)
    else:
        raise RuntimeError("请先设置 SIGNAL_POP_TTS_BACKEND=volcengine 或 xunfei")
    print(f"✅ 试听文件: {out} ({os.path.getsize(out)//1024}KB)")
    return out


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # python tools/gen_cloud_tts.py test "文本" [音色]
        text = sys.argv[2] if len(sys.argv) > 2 else "这里是隔天信号弹，测试云端语音合成效果。"
        voice = sys.argv[3] if len(sys.argv) > 3 else None
        test_single(text, voice)
    else:
        prep = sys.argv[1] if len(sys.argv) > 1 else "20260816"
        items_path = os.path.join(PROJECT_ROOT, "output", "daily", prep, "parsed_news.json")
        wav = os.path.join(PROJECT_ROOT, "output", "daily", prep, "audio", "tts.wav")
        pub_dt = datetime.strptime(prep, "%Y%m%d") + timedelta(days=1)
        pub_fmt = f"{pub_dt.year}年{pub_dt.month:02d}月{pub_dt.day:02d}日"
        wk = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][pub_dt.weekday()]
        gen_tts(items_path, wav, pub_date_fmt=pub_fmt, pub_weekday=wk)
