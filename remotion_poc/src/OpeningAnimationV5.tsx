import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Easing,
} from "remotion";

// ===== 信号弹周末版 · 开场动画 V5「纯字卡·克制版」（2026-10-12）=====
//
// MARK哥：「不要出现人物头像，设计一个像新闻联播一样的过场」
//
// V5 的思路：**连装饰都不要**。
// V1纸卡3D（太时尚）→ V2 火柴人（形象断裂）→ V3 真实头像（不要人物）
// → V4 地球光带（做了很多"东西"）→ V5 只剩文字本身。
//
// 新闻联播片头真正打动人的从来不是地球或光带，而是：
//   **字很大、很正、很静**。它用极少的元素撑住了 8 秒不让人觉得空。
//
// 所以 V5 只做三件事：
//   ① 深蓝纯色底（不用任何渐变、纹理、图形）
//   ② 宋体大字（Noto Serif SC＝播音楼字体），淡入 + 极轻的字距收缩
//   ③ 上下金线从中间向两侧「生长」
//
// 「字距收缩」是唯一的"动效"——汉字从排版学的 looseness 向紧排收敛，
// 这是宋体标题最优雅的入场方式，比任何位移/缩放都克制。
// 全片零人物、零图形、零Logo、零卡片、零粒子。

const DEEP = "#01050f";
const NAVY = "#0a1a3a";
const GOLD = "#D4AF37";
const WHITE = "#FFFFFF";
const SERIF = "Noto Serif SC, SimSun, serif";

const easeOut = Easing.out(Easing.cubic);

export const OpeningAnimationV5: React.FC<{
  title: string;
  date: string;
  weekday: string;
}> = ({ title, date, weekday }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // 背景淡入（1.2s）
  const bgFade = interpolate(frame, [0, 36], [0, 1], { extrapolateRight: "clamp" });

  // 结尾淡出（1.0s）
  const fadeOut = interpolate(frame, [durationInFrames - 30, durationInFrames - 1], [1, 0], {
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });

  // 主标题：2.6s → 5.2s 淡入，同时字距从 26px 收到 8px（紧排收敛）
  const titleP = interpolate(frame, [78, 156], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: easeOut,
  });
  const titleLS = interpolate(titleP, [0, 1], [26, 8]);

  // 上下金线：比标题晚 12 帧，从中心向两侧生长
  const lineP = interpolate(frame, [96, 168], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: easeOut,
  });

  // 副标最后浮现
  const subP = interpolate(frame, [130, 186], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: easeOut,
  });

  return (
    <AbsoluteFill style={{ backgroundColor: DEEP, opacity: bgFade * fadeOut }}>
      {/* 深蓝径向底（唯一一处装饰：极轻的中央提亮，给纯色一点呼吸）*/}
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse 1200px 700px at 50% 46%, ${NAVY} 0%, #030c1c 60%, ${DEEP} 100%)`,
        }}
      />

      <AbsoluteFill
        style={{
          alignItems: "center",
          justifyContent: "center",
          flexDirection: "column",
        }}
      >
        {/* 上金线：从中心向两侧生长 */}
        <div
          style={{
            width: `${560 * lineP}px`,
            height: 1,
            background: `linear-gradient(90deg, transparent, ${GOLD}, transparent)`,
            boxShadow: `0 0 18px 3px ${GOLD}88`,
            marginBottom: 52,
          }}
        />
        {/* 小字：栏目标识（新闻联播先报栏目名再报内容）*/}
        <div
          style={{
            fontSize: 27,
            fontWeight: 600,
            letterSpacing: 14,
            color: GOLD,
            fontFamily: SERIF,
            opacity: titleP,
            marginBottom: 30,
            textIndent: 14,
          }}
        >
          周末特别版
        </div>
        {/* 主标题：宋体大字，唯一动效是字距收紧 */}
        <div
          style={{
            fontSize: 88,
            fontWeight: 700,
            color: WHITE,
            fontFamily: SERIF,
            letterSpacing: titleLS,
            lineHeight: 1.28,
            textAlign: "center",
            opacity: titleP,
            textShadow: "0 2px 26px rgba(110,170,255,0.3)",
          }}
        >
          {title}
        </div>
        {/* 下金线 */}
        <div
          style={{
            width: `${560 * lineP}px`,
            height: 1,
            background: `linear-gradient(90deg, transparent, ${GOLD}, transparent)`,
            boxShadow: `0 0 18px 3px ${GOLD}88`,
            marginTop: 52,
          }}
        />
        {/* 日期行 */}
        <div
          style={{
            marginTop: 34,
            fontSize: 24,
            fontWeight: 500,
            letterSpacing: 6,
            color: "rgba(255,255,255,0.7)",
            fontFamily: SERIF,
            opacity: subP,
            textIndent: 6,
          }}
        >
          {date} · {weekday}
        </div>
      </AbsoluteFill>

      {/* 四周暗角 */}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 240px 50px rgba(0,0,0,0.5)" }} />

      {/* 上下画框细线 */}
      <div
        style={{
          position: "absolute",
          top: 56,
          left: 0,
          right: 0,
          height: 1,
          background: `linear-gradient(90deg, transparent 18%, ${GOLD}3a 50%, transparent 82%)`,
          opacity: lineP,
        }}
      />
      <div
        style={{
          position: "absolute",
          bottom: 56,
          left: 0,
          right: 0,
          height: 1,
          background: `linear-gradient(90deg, transparent 18%, ${GOLD}3a 50%, transparent 82%)`,
          opacity: lineP,
        }}
      />
    </AbsoluteFill>
  );
};