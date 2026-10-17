import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Easing,
} from "remotion";

// ===== 信号弹周末版 · 开场动画 V4「新闻联播式过场」（2026-10-12）=====
//
// MARK哥反馈路线：V3 真实头像「还是不好，不要出现人物头像」，
// 要求「设计一个像新闻联播一样的过场」。
//
// 为什么前两版都不对（根因累积）：
//   V1 纸卡 3D：magazine/编辑风，太时尚，不像播新闻
//   V2 火柴人：引入了正片不存在的形象 → 突兀
//   V3 真实头像：形象连续了，但「人物」本身就不该出现在片头
//→ 共同点：**都在「设计一个东西」**，而不是「建立一个仪式感」。
//
// V4 的参照：央视《新闻联播》片头的视觉语法
//   ① 深蓝夜空（#0a1a3a → #01050f），庄重、克制、不抢戏
//   ② 地球弧线 + 大气辉光（世界视野，"面向世界"的隐喻）
//   ③ 横向光带缓慢横掠（代替人物做"动"的元素）
//   ④ **衬线**大字居中（Noto Serif SC＝宋体＝播音楼的字）
//   ⑤ 上下金色细线严格对称（新闻联播的招牌构图）
//   ⑥ 零人物、零 Logo、零印章、零卡片
//
// 与正片的关系：不追求「形象连续」，而追求「调性连续」——
// 片头是庄重的PBS 级间奏，正片是轻快的脱口秀，这个反差是有意的，
// 就像电视台节目开头严肃、节目里轻松。
//
// 动效原则：**全部极缓**。新闻联播片头没有弹跳、没有位移入场，
// 只有淡入和持续的水平运动。这是「庄重」的物理来源。

const DEEP = "#01050f"; // 最深夜空
const NAVY = "#0a1a3a"; // 主蓝
const GOLD = "#D4AF37"; // 金（与正片 WeeklyTalk 一致）
const WHITE = "#FFFFFF";
const SERIF = "Noto Serif SC, SimSun, serif"; // 宋体＝播音楼字体

const easeOut = Easing.out(Easing.cubic);

export const OpeningAnimationV4: React.FC<{
  title: string;
  date: string;
  weekday: string;
}> = ({ title, date, weekday }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const t = frame / fps;
  const DUR = durationInFrames / fps;

  // 背景淡入（1.2s，比 V3 慢——庄重需要更慢的起手）
  const bgFade = interpolate(frame, [0, 36], [0, 1], { extrapolateRight: "clamp" });

  // 结尾淡出（1.0s）
  const fadeOut = interpolate(frame, [durationInFrames - 30, durationInFrames - 1], [1, 0], {
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });

  // 地球弧线：整幅从下方极缓上浮 40px（8 秒才走完，看不出是动画，像在呼吸）
  const earthRise = interpolate(t, [0, DUR], [40, 0], {
    extrapolateRight: "clamp",
    easing: Easing.linear,
  });

  // 光带：三条，各自不同速度与初始位置，形成"多条气流"的层次
  // 速度刻意错开（26 / 34 / 44 px/s），避免机械的齐头并进
  // ⚠️ 纵向位置：必须落在标题区（中心540，占±180px）之外的夜空暗部，
  // 否则横穿大字显得杂乱。取0.16 / 0.235 / 0.31（画面上部空域）。
  const bandY = [0.16, 0.235, 0.31];
  const bandSpeed = [26, 34, 44];
  const bandWidth = [0.52, 0.68, 0.4];
  const bandOpacity = [0.5, 0.34, 0.22];

  // 大气辉光呼吸（周期≈全片时长，只做一个完整呼吸）
  const glowBreath = 0.72 + 0.28 * Math.sin((t /DUR) * Math.PI);

  // ⚠️ 标题区保持**居中**（曾试过下移到 43%，结果被地球辉光罩住反而更糟）。
  // 地球弧顶 640px + 辉光中心 730px，标题区中心 540px 恰在暗部，安全。
  const blockTop = undefined;

  // 标题：3.0s 后开始淡入，用 2.0s（比 V3 的 1s 慢一倍）
  const titleP = interpolate(frame, [90, 150], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: easeOut,
  });

  // 上下金线：比标题晚 10 帧，像「框」一样把字收进去
  const lineP = interpolate(frame, [104, 160], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: easeOut,
  });

  // 副标（日期 / 栏目）最后浮现
  const subP = interpolate(frame, [126, 180], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: easeOut,
  });

  // 地球本体：一个巨大的圆（下半部分被裁掉），带大气辉光圈
  // ⚠️ 位置校准（实测两轮）：
  //   第一版 EARTH_CY=1780 / R=1150 → 弧顶 370px，日期行被压到画面底边；
  //   第二版 CY=1980 / R=1180 但标题同时下移到 43% → 弧顶虽在 800px，
  //   **大气辉光椭圆（rx=R+120=1300, ry=220）向上溢出到 590px**，
  //   把标题区整个罩进亮部，反而更糟（截图确认）。
  // 现取中间值：地球弧顶落在 640px（约 60% 高），标题区回到**居中**，
  // 辉光椭圆同步下移，让标题区处于夜空暗部、金线可见。
  const EARTH_CY = 1820;
  const EARTH_R = 1180;
  const EARTH_TOP = EARTH_CY - EARTH_R; // 弧顶 = 640px
  const ATMO_Y = EARTH_TOP + 90;          // 辉光椭圆中心下移，避开标题区

  return (
    <AbsoluteFill style={{ backgroundColor: DEEP, opacity: bgFade * fadeOut }}>
      {/* ===== 夜空渐变：中心微亮的深蓝 radially ===== */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse 1400px 900px at 50% 78%, ${NAVY} 0%, #04102045 45%, ${DEEP} 78%)`,
        }}
      />

      {/* ===== 地球弧线（SVG，气氛层）===== */}
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{ display: "block" }}>
          <defs>
            {/* 地球表面：深蓝 → 边缘更暗，模拟大气层内的散射 */}
            <radialGradient id="earthFill" cx="50%" cy="0%" r="75%">
              <stop offset="0%" stopColor="#1b3f7a" />
              <stop offset="45%" stopColor="#0e2750" />
              <stop offset="100%" stopColor="#050d1f" />
            </radialGradient>
            {/* 大气辉光：地球边缘上方的暖色弧 */}
            <linearGradient id="atmo" x1="0" y1="1" x2="0" y2="0">
              <stop offset="0%" stopColor="#4a9eff" stopOpacity="0" />
              <stop offset="55%" stopColor="#4a9eff" stopOpacity="0.42" />
              <stop offset="88%" stopColor="#a8d4ff" stopOpacity="0.75" />
              <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
            </linearGradient>
            {/* 经纬线（新闻联播地球的标志性网格）*/}
            <clipPath id="globeClip">
              <circle cx="960" cy={EARTH_CY} r={EARTH_R} />
            </clipPath>
          </defs>

          <g transform={`translate(0, ${earthRise})`}>
            {/* 大气辉光（在地球之上的一圈，中心下移避免罩住标题区）*/}
            <ellipse
              cx="960"
              cy={ATMO_Y}
              rx={EARTH_R + 120}
              ry="200"
              fill="url(#atmo)"
              opacity={0.42 * glowBreath}
            />
            {/* 地球本体 */}
            <circle cx="960" cy={EARTH_CY} r={EARTH_R} fill="url(#earthFill)" />
            {/* 经纬网格 */}
            <g clipPath="url(#globeClip)" stroke="#5f9fe8" strokeWidth="1" opacity="0.2">
              {/* 纬线：水平椭圆，贴着弧顶往下排（相对 EARTH_TOP 定位，不再写死 340）*/}
              {[0, 1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
                <ellipse
                  key={`lat${i}`}
                  cx="960"
                  cy={EARTH_TOP + 26 + i * 34}
                  rx={Math.max(40, EARTH_R * Math.cos(0.34 + i * 0.1))}
                  ry="13"
                  fill="none"
                />
              ))}
              {/* 经线：竖直椭圆 */}
              {[0, 1, 2, 3, 4, 5].map((i) => (
                <ellipse
                  key={`lon${i}`}
                  cx="960"
                  cy={EARTH_CY}
                  rx={Math.abs((i - 2.5) * 300)}
                  ry={EARTH_R}
                  fill="none"
                />
              ))}
            </g>
            {/* 地平线亮边（正上方那一道，是"地球感"的关键）*/}
            <path
              d={`M ${960 - EARTH_R} ${EARTH_CY} A ${EARTH_R} ${EARTH_R} 0 0 1 ${960 + EARTH_R} ${EARTH_CY}`}
              fill="none"
              stroke="#9ccfff"
              strokeWidth="2"
              opacity={0.65 * glowBreath}
            />
          </g>
        </svg>
      </AbsoluteFill>

      {/* ===== 横向光带（代替人物做"动"）===== */}
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        {bandY.map((y, i) => {
          // 从右侧外进入、缓慢移向左侧外，位置取模实现无缝循环
          const span = 2200;
          const x = ((t * bandSpeed[i] + i * 620) % span) - 400;
          const bandIn = interpolate(frame, [40 + i * 18, 100 + i * 18], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                left: x,
                top: `${y * 100}%`,
                width: `${bandWidth[i] * 100}%`,
                height: i === 1 ? 3 : 2,
                background: `linear-gradient(90deg, transparent, ${i === 1 ? "#ffffff" : "#9ccfff"}, transparent)`,
                opacity: bandOpacity[i] * bandIn,
                filter: `blur(${i === 1 ? 1.4 : 2.6}px)`,
                boxShadow: i === 1 ? "0 0 22px 3px rgba(156,207,255,0.5)" : "none",
              }}
            />
          );
        })}
      </AbsoluteFill>

      {/* ===== 标题区（严格居中对称）===== */}
      <AbsoluteFill
        style={{
          alignItems: "center",
          justifyContent: "center",
          flexDirection: "column",
        }}
      >
        {/* 上金线 */}
        <div
          style={{
            width: `${520 * lineP}px`,
            height: 1,
            background: `linear-gradient(90deg, transparent, ${GOLD}, transparent)`,
            boxShadow: `0 0 18px 3px ${GOLD}88`,
            marginBottom: 34,
          }}
        />
        {/* 栏目标识（新闻联播式：先小字，再大标）*/}
        <div
          style={{
            fontSize: 26,
            fontWeight: 600,
            letterSpacing: 12,
            color: GOLD,
            fontFamily: SERIF,
            opacity: titleP,
            marginBottom: 22,
            textIndent: 12, // 补偿 letterSpacing 造成的视觉偏右
          }}
        >
          周末特别版
        </div>
        {/* 主标题：宋体大字 —— 播音楼的字*/}
        <div
          style={{
            fontSize: 78,
            fontWeight: 700,
            color: WHITE,
            fontFamily: SERIF,
            letterSpacing: 10,
            lineHeight: 1.25,
            textAlign: "center",
            opacity: titleP,
            textShadow: "0 2px 30px rgba(120,180,255,0.35)",
            textIndent: 10,
          }}
        >
          {title}
        </div>
        {/* 下金线（与上金线等宽，严格对称）*/}
        <div
          style={{
            width: `${520 * lineP}px`,
            height: 1,
            background: `linear-gradient(90deg, transparent, ${GOLD}, transparent)`,
            boxShadow: `0 0 18px 3px ${GOLD}88`,
            marginTop: 34,
          }}
        />
        {/* 日期行 */}
        <div
          style={{
            marginTop: 30,
            fontSize: 23,
            fontWeight: 500,
            letterSpacing: 5,
            color: "rgba(255,255,255,0.72)",
            fontFamily: SERIF,
            opacity: subP,
            textIndent: 5,
          }}
        >
          {date} · {weekday} · 每周六更新
        </div>
      </AbsoluteFill>

      {/* ===== 上下暗角（把视线压向中央）===== */}
      <AbsoluteFill
        style={{
          boxShadow: "inset 0 0 260px 60px rgba(0,0,0,0.55)",
        }}
      />

      {/* ===== 顶部/底部 细金边（新闻联播的画框感）===== */}
      <div
        style={{
          position: "absolute",
          top: 54,
          left: 0,
          right: 0,
          height: 1,
          background: `linear-gradient(90deg, transparent 15%, ${GOLD}44 50%, transparent 85%)`,
          opacity: lineP,
        }}
      />
      <div
        style={{
          position: "absolute",
          bottom: 54,
          left: 0,
          right: 0,
          height: 1,
          background: `linear-gradient(90deg, transparent 15%, ${GOLD}44 50%, transparent 85%)`,
          opacity: lineP,
        }}
      />
    </AbsoluteFill>
  );
};