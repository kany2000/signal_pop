# 申请阿里云百炼 DashScope API Key（Qwen TTS 用）

> 用途：Signal Pop 周末特别版 TTS 的第二条免费兜底后端（豆包配额耗尽时启用）。
> 项目代码已接好 Qwen 后端（`tools/gen_cloud_tts.py` + `tools/gen_dual_tts.py`），**只差这一个 Key** 即可用。
> 免费额度：模型 `qwen3-tts-flash` 在**中国大陆（北京）地域 = 免费 110,000 字符（11 万字符）/ 90 天**（按输入字符计费，输出不计费）。
> 超出免费额度后 **0.8 元 / 万字符**。控制台里模型带价格标签是「超出后的单价」，不是强制付费——新开通百炼会自动获得这 11 万字符免费额度。
> ⚠️ 免费额度**仅北京（中国大陆）地域**有；新加坡地域部分模型无免费额度，务必用北京。

---

## 一、申请流程（6 步，约 10 分钟）

### 步骤 1 ｜ 注册 / 登录阿里云
- 打开 <https://www.aliyun.com/>
- 右上角「登录 / 注册」；支持 **支付宝 / 淘宝 / 手机号** 一键登录
- 无账号先注册一个

### 步骤 2 ｜ 实名认证（必须，约 10 秒）
- 登录后点右上角**头像 → 实名认证**
- 选**个人认证 → 支付宝刷脸**（全程约 10 秒）
- 无需绑卡、无需充值
- ⚠️ 不完成实名认证**无法创建 API Key**，也领不到免费额度

### 步骤 3 ｜ 开通百炼模型服务（免费）
- 进入百炼控制台：<https://bailian.console.aliyun.com/>
- 首次进入会弹出「开通百炼大模型平台」→ 勾选服务协议 → 点「**立即开通 / 免费体验**」
- 开通**免费**，且 `qwen3-tts-flash` 的 **110,000 字符（11 万字符）/ 90 天免费额度自动到账**（无需单独领取；控制台「免费额度」页可查余量）
- 🌍 **地域注意**：本项目用**北京（华北2）**地域，对应接口 `dashscope.aliyuncs.com`。
  新加坡地域的 Key 与北京不通用，请勿选错地域。

### 步骤 4 ｜ 创建 API Key
- 百炼控制台左侧菜单找到 **「API-KEY 管理」**
- 点「**创建新的 API-KEY**」→ 复制生成的 `sk-xxxxxxxx`（形如 `sk-` 开头的一长串）
- 妥善保存：这是敏感凭证，**勿提交到 git、勿公开泄露**

### 步骤 5 ｜ 填入项目 `.env`
- 打开 `E:/projects/signal_pop/.env`
- 文件末尾已有预留空槽 `DASHSCOPE_API_KEY=`，把它改成：
  ```ini
  DASHSCOPE_API_KEY=sk-你刚复制的key
  ```
- 保存文件（无需重启任何服务，代码运行时会自动读取）

### 步骤 6 ｜ 测试是否接通
**单句试听**（验证 Key 有效 + 网络连通，最快）：
```bash
SIGNAL_POP_TTS_BACKEND=qwen WINPY tools/gen_cloud_tts.py test "大家好，我是阿信，欢迎收看信号弹周末特别版。" Ethan
```
成功会输出类似：`✅ 试听文件: output/cloud_tts_test.mp3 (32KB)`

**出本期双播音频**（断点续跑，只补失败段）：
```bash
SIGNAL_POP_TTS_BACKEND=qwen WINPY tools/weekend_pipeline.py 20260912 tts
```

---

## 二、音色说明（阿信 / 小蓝）

| 角色 | 默认音色 | 音色特点 | 想换可改 |
|------|----------|----------|----------|
| 阿信（男） | `Ethan`（晨煦） | 标准普通话、阳光温暖、有活力 | `Moon`（月白/率性帅气）、`Ryan`（甜茶/戏感男） |
| 小蓝（女） | `Cherry`（芊悦） | 阳光积极、亲切自然 | `Serena`（苏瑶/温柔）、`Cixuan` |

改音色位置：编辑 `tools/gen_cloud_tts.py` 顶部
```python
QWEN_VOICE_WEEKEND = "Ethan"      # 周末男声·阿信
QWEN_VOICE_WEEKEND_F = "Cherry"   # 周末女声·小蓝
```
完整音色目录见 <https://help.aliyun.com/zh/model-studio/qwen-tts-voice-list>

---

## 三、常见报错排查

| 现象 | 原因 | 处理 |
|------|------|------|
| `未配置 DASHSCOPE_API_KEY（...）` | `.env` 里 key 没填或变量名拼错 | 确认 `.env` 有 `DASHSCOPE_API_KEY=sk-...` 且无多余空格 |
| `DashScope HTTP 401` / `InvalidApiKey` | Key 无效，或北京 Key 配了新加坡接口 | 重新复制 Key；确认用北京地域（`dashscope.aliyuncs.com`） |
| 某男声报「不支持的音色」 | 该 voice 名不适用于非实时模型 | 换 `Moon` / `Ryan`（见上表） |
| 音频极短 / 空白 | 文本为空或超长（>600 字符） | 拆分长文本后重试 |

---

## 四、后端切换速查

```bash
# 豆包/火山引擎（原声，配额耗尽时不可用）
WINPY tools/weekend_pipeline.py 20260912 tts

# 讯飞（已接+实测通，免费 1 万次/3 个月）——本期就是用这个出的
SIGNAL_POP_TTS_BACKEND=xunfei WINPY tools/weekend_pipeline.py 20260912 tts

# 阿里云百炼 Qwen（本文件申请的 key，免费 1 万字符/90 天）
SIGNAL_POP_TTS_BACKEND=qwen WINPY tools/weekend_pipeline.py 20260912 tts
```

---

## 五、后续动作（交给 AI）
1. 你注册拿到 Key 后，直接把 `sk-xxx` 发给我（或自己填进 `.env`）
2. 我跑 **Qwen 单句 + 本期** 测试，确认接通
3. 测试通过后，把以下改动**一并提交 git**：
   - 讯飞后端接入（`gen_dual_tts.py`）
   - Qwen 后端接入（`gen_cloud_tts.py` + `gen_dual_tts.py` + `.env` 空槽）
   - 本期（20260912）讯飞音频产物（`tts.wav` / `tts_segments.json`）

---

## 参考链接
- 获取 API Key：<https://help.aliyun.com/zh/model-studio/get-api-key>
- Qwen-TTS API 参考：<https://help.aliyun.com/zh/model-studio/qwen-tts-api>
- 音色列表：<https://help.aliyun.com/zh/model-studio/qwen-tts-voice-list>
- 百炼模型价格（免费额度）：<https://help.aliyun.com/zh/document_detail/2987148.html>
