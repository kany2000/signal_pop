import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Easing,
  Img,
  staticFile,
} from "remotion";

// ===== 信号弹周末版 · 开场动画 V3（极简真实头像版 · 2026-10-12）=====
//
// 为什么推翻 V2 火柴人版（MARK哥反馈「太突兀」）：
//   V2 引入了两个全新的手绘 SVG 人物形象，但正片 WeeklyTalk 用的是**真实圆形头像**
//   （anchor_axin.jpg / anchor_xiaolan.jpg，带色环 + 光晕）。
//   → 观众在片头看到的是「火柴人」，一进正片变成「真人头像」，
//     视觉语言在第0 秒和第 9 秒之间断裂，这就是「突兀」的真正来源。
//   火柴人本身没问题，问题在于它是**另一个项目的东西**放在同一支片子里。
//
// V3 的取舍（用户要求「换一种较简单一点的风格」）：
//   ① **零新角色**：只用正片已在用的两张真实头像，不创造任何新形象。
//      片头和正片之间形象完全连续 → 天然不突兀。
//   ② **零 3D**：去掉 translateZ / preserve-3d / perspective / 呼吸浮动。
//      V1 的 3D 落定效果虽好看，但和正片（2D 平面 + 光晕脉冲）也对不上。
//   ③ **只做一件事**：让两张头像「亮起来」。全部动效退到一个词——淡入 + 极缓推近。
//   ④沿用正片的全部配色常量，不引入新色系：
//      底色 #0d1220 / 阿信 #9CC3EC / 小蓝 #F2B8D4 / 金 #D4AF37。
//
// 与 V1（纸卡 3D）的区别：V1 是「一张纸落定」，没有人；
// V3 是「两个人已经在那儿了，只是还没开口」——与正片第一帧的叙事更连贯。

const BG = "#0d1220"; // 正片 WeeklyTalk 底色（WeeklyTalk.tsx:647）
const AXIN = "#9CC3EC"; // 阿信名色（WeeklyTalk.tsx:618）
const XIAOLAN = "#F2B8D4"; // 小蓝名色
const GOLD = "#D4AF37"; // 顶部品牌条金色（WeeklyTalk.tsx:662）
const GREY = "#A0AEC0"; // 次级灰

const easeOut = Easing.out(Easing.cubic);

export const OpeningAnimationV3: React.FC<{
  title: string;
  date: string;
  weekday: string;
}> = ({ title, date, weekday }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const t = frame / fps;

  // 背景淡入（前 0.5s）
  const bgFade = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: "clamp" });

  // 结尾淡出（最后 0.8s 淡至黑，平滑接入正片，避免硬切）
  const fadeOut = interpolate(frame, [durationInFrames - 26, durationInFrames - 1], [1, 0], {
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });

  // 背景极缓推近（1.0 → 1.03），比 V1 的 1.022 更慢，只提供「画面活着」的感觉
  const ambient = interpolate(t, [0, durationInFrames / fps], [1.0, 1.03], {
    extrapolateRight: "clamp",
    easing: Easing.linear,
  });

  // 两张头像错峰入场：左先右后，间隔 9 帧（0.3s）
  const avinP = interpolate(frame, [10, 30], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: easeOut,
  });
  const xiaolanP = interpolate(frame, [19, 39], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: easeOut,
  });

  // 名字标签比头像晚 8 帧淡入（先见人、后见名，符合阅读顺序）
  const nameP = interpolate(frame, [24, 42], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: easeOut,
  });

  // 标题卡：1.0s 后浮现，整段只做一次极缓上浮
  const titleP = interpolate(frame, [34, 62], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: easeOut,
  });

  // 顶部品牌条下方金色细线（呼应正片顶部 GOLD 品牌条）
  const lineP = interpolate(frame, [52, 76], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: easeOut,
  });

  // 光环呼吸：与正片 speakPulse 同频（5×2π），但幅度减半（0.05 → 0.03）
  // 正片里说话者光晕以1±0.05 脉冲，这里让静态头像也保持轻微生命感。
  const pulse = 1 + 0.03 * Math.sin(t * 5 * Math.PI * 2);

  return (
    <AbsoluteFill style={{ backgroundColor: BG, opacity: bgFade * fadeOut }}>
      {/* 背景极缓推近（整幅一起推，不做分层视差——V1 的多层Z 深度是「复杂感」的主要来源）*/}
      <AbsoluteFill
        style={{
          transform: `scale(${ambient})`,
          transformOrigin: "50% 42%",
        }}
      >
        {/* 与正片开场段完全一致的径向渐变底（WeeklyTalk.tsx:653 复刻）*/}
        <AbsoluteFill
          style={{
            background: "radial-gradient(circle at 50% 30%, #2a416d 0%, #152038 55%, #0c1424 100%)",
          }}
        />

        {/* 左：阿信（位置/尺寸对齐正片 WeeklyTalk.tsx:742的 left:0 / width:540 / 300×300）*/}
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", left: 0, width: 540 }}>
          <div
            style={{
              transform: `scale(${avinP * pulse})`,
              transformOrigin: "center",
              width: 300,
              height: 300,
              position: "relative",
              opacity: avinP,
            }}
          >
            {/* 持续光晕环（正片里是「正在说…」时才亮，这里作为片头识别符号常亮）*/}
            <div
              style={{
                position: "absolute",
                inset: -28,
                borderRadius: "50%",
                border: `4px solid ${AXIN}`,
                opacity: 0.55,
                boxShadow: `0 0 60px ${AXIN}`,
              }}
            />
            <Img
              src={staticFile("anchor_axin.jpg")}
              style={{ width: "100%", height: "100%", borderRadius: "50%", objectFit: "cover", border: `3px solid ${AXIN}` }}
            />
          </div>
          <div
            style={{
              marginTop: 18,
              fontSize: 34,
              fontWeight: "bold",
              color: AXIN,
              fontFamily: "Noto Sans SC, sans-serif",
              opacity: nameP,
            }}
          >
            阿信
          </div>
        </AbsoluteFill>

        {/* 右：小蓝（对齐正片 WeeklyTalk.tsx:756 的 left:1380 / width:540 / 300×300）*/}
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", left: 1380, width: 540 }}>
          <div
            style={{
              transform: `scale(${xiaolanP * pulse})`,
              transformOrigin: "center",
              width: 300,
              height: 300,
              position: "relative",
              opacity: xiaolanP,
            }}
          >
            <div
              style={{
                position: "absolute",
                inset: -28,
                borderRadius: "50%",
                border: `4px solid ${XIAOLAN}`,
                opacity: 0.55,
                boxShadow: `0 0 60px ${XIAOLAN}`,
              }}
            />
            <Img
              src={staticFile("anchor_xiaolan.jpg")}
              style={{ width: "100%", height: "100%", borderRadius: "50%", objectFit: "cover", border: `3px solid ${XIAOLAN}` }}
            />
          </div>
          <div
            style={{
              marginTop: 18,
              fontSize: 34,
              fontWeight: "bold",
              color: XIAOLAN,
              fontFamily: "Noto Sans SC, sans-serif",
              opacity: nameP,
            }}
          >
            小蓝
          </div>
        </AbsoluteFill>

        {/* 中间标题卡（无卡片底、无3D、无扫光——V1/V2 的「复杂」都在这些装饰上）*/}
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", left: 540, width: 840 }}>
          <div style={{ opacity: titleP, transform: `translateY(${(1 - titleP) * 20}px)` }}>
            <div
              style={{
                fontSize: 60,
                fontWeight: 900,
                color: "#fff",
                fontFamily: "Noto Sans SC, sans-serif",
                letterSpacing: 2,
                lineHeight: 1.2,
                textAlign: "center",
              }}
            >
              {title}
            </div>
            <div
              style={{
                marginTop: 24,
                height: 2,
                width: "58%",
                margin: "24px auto 0 auto",
                background: `linear-gradient(90deg, transparent, ${GOLD}, transparent)`,
                transform: `scaleX(${lineP})`,
              }}
            />
            <div
              style={{
                marginTop: 22,
                textAlign: "center",
                fontSize: 24,
                fontWeight: 700,
                letterSpacing: 6,
                color: GOLD,
                fontFamily: "Noto Sans SC, sans-serif",
                opacity: lineP,
              }}
            >
              周末特别版 · 每周六更新
            </div>
            <div
              style={{
                marginTop: 16,
                textAlign: "center",
                fontSize: 20,
                fontWeight: 600,
                letterSpacing: 1,
                color: GREY,
                fontFamily: "Noto Sans SC, sans-serif",
                opacity: lineP,
              }}
            >
              发布 {date} · {weekday}
            </div>
          </div>
        </AbsoluteFill>
      </AbsoluteFill>

      {/* 顶部品牌条（完全复刻正片 WeeklyTalk.tsx:661-664，保证片头正片视觉连续）*/}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 90,
          background: "linear-gradient(180deg, rgba(10,16,30,0.95), rgba(10,16,30,0))",
        }}
      />
      <div
        style={{
          position: "absolute",
          top: 26,
          left: 0,
          right: 0,
          textAlign: "center",
          fontSize: 30,
          fontWeight: "bold",
          color: GOLD,
          fontFamily: "Noto Sans SC, sans-serif",
          letterSpacing: 2,
        }}
      >
        隔天信号弹 · 周末特别版
      </div>
    </AbsoluteFill>
  );
};