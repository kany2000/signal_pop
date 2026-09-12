import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Easing,
  Sequence,
} from "remotion";

// ===== 信号弹周末版 · 开场动画（活泼漫画风 × 科技感）=====
// 设计语言：深蓝科技底 + 霓虹网格 + 漫画速度线/网点 + 爆炸星形徽标 +
// 信号弹拖尾掠过 + 标题逐字 comic bounce + 收尾 glitch 闪烁。
// 纯 CSS/SVG 实现，无外部素材依赖；背景乐由外部钢琴片段 mux 进正片。

const NAVY = "#0a0e27";
const NEON_BLUE = "#37E1FF";
const NEON_PINK = "#FF4FD8";
const COMIC_YEL = "#FFE23D";
const PURPLE = "#8A6BE0";
const WHITE = "#F5F7FF";

const easeOut = Easing.out(Easing.cubic);
const easeOutBack = (x: number) => {
  const c1 = 2.2; // 更弹的 back
  const c3 = c1 + 1;
  return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2);
};

// ---------- 漫画爆炸星形（徽标底）----------
const BurstStar: React.FC<{ spin: number; scale: number; glow: number }> = ({
  spin,
  scale,
  glow,
}) => (
  <AbsoluteFill
    style={{
      alignItems: "center",
      justifyContent: "center",
      opacity: glow,
      transform: `scale(${scale}) rotate(${spin}deg)`,
      transformOrigin: "50% 50%",
    }}
  >
    <svg width={860} height={860} viewBox="0 0 200 200">
      {/* 外层光晕 */}
      <defs>
        <radialGradient id="burstGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor={COMIC_YEL} stopOpacity="0.55" />
          <stop offset="55%" stopColor={NEON_PINK} stopOpacity="0.22" />
          <stop offset="100%" stopColor={NEON_PINK} stopOpacity="0" />
        </radialGradient>
        <linearGradient id="burstFill" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#FFF3B0" />
          <stop offset="50%" stopColor={COMIC_YEL} />
          <stop offset="100%" stopColor="#FFB01F" />
        </linearGradient>
      </defs>
      <circle cx="100" cy="100" r="98" fill="url(#burstGlow)" />
      {/* 12 角爆炸星 */}
      <polygon
        points="100,6 118,64 176,40 140,92 196,108 140,124 176,176 118,140 100,194 82,140 24,176 60,124 4,108 60,92 24,40 82,64"
        fill="url(#burstFill)"
        stroke="#1a1206"
        strokeWidth="4"
        strokeLinejoin="round"
      />
      {/* 内圈描边（漫画双线）*/}
      <polygon
        points="100,30 114,74 158,56 130,96 172,108 130,120 158,164 114,146 100,178 86,146 42,164 70,120 28,108 70,96 42,56 86,74"
        fill="none"
        stroke="#1a1206"
        strokeWidth="2"
        strokeLinejoin="round"
        opacity="0.55"
      />
    </svg>
  </AbsoluteFill>
);

// ---------- 信号弹拖尾（掠过）----------
const SignalBullet: React.FC<{ progress: number; opacity: number }> = ({
  progress,
  opacity,
}) => {
  // progress 0→1 从左下飞到右上
  const x = -300 + progress * 2200;
  const y = 1150 - progress * 1000;
  return (
    <AbsoluteFill style={{ opacity, pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          left: x,
          top: y,
          width: 520,
          height: 26,
          transform: "translate(-50%,-50%) rotate(-24deg)",
          borderRadius: 999,
          background: `linear-gradient(90deg, rgba(55,225,255,0) 0%, ${NEON_BLUE} 55%, #fff 100%)`,
          boxShadow: `0 0 40px 8px ${NEON_BLUE}, 0 0 80px 16px rgba(55,225,255,0.45)`,
          filter: "blur(1px)",
        }}
      />
      <div
        style={{
          position: "absolute",
          left: x + 250,
          top: y,
          width: 34,
          height: 34,
          transform: "translate(-50%,-50%)",
          borderRadius: "50%",
          background: "#fff",
          boxShadow: `0 0 30px 10px ${NEON_BLUE}, 0 0 60px 20px rgba(255,79,216,0.5)`,
        }}
      />
    </AbsoluteFill>
  );
};

export const OpeningAnimation: React.FC<{
  title: string;
  date: string;
  weekday: string;
}> = ({ title, date, weekday }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const t = frame / fps;

  // —— 背景层动效 ——
  const gridPan = (t * 40) % 80; // 网格横向流动
  const speedSweep = interpolate(frame, [0, 18], [0, 1], {
    extrapolateRight: "clamp",
    easing: easeOut,
  });
  const haloPulse = 0.5 + 0.5 * Math.sin(t * 2.4);

  // —— 爆炸星入场 ——
  const burstScale = interpolate(frame, [6, 26], [0.2, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: easeOutBack,
  });
  const burstGlow = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
  const burstSpin = t * 22;

  // —— 信号弹掠过（约 1.1s→2.2s）——
  const bulletP = interpolate(frame, [33, 66], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });
  const bulletOpacity = interpolate(frame, [30, 36, 64, 70], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // —— 标题逐字 comic bounce（0.8s→2.4s stagger）——
  const titleChars = [...title];
  const charAppear = (i: number) => {
    const start = 24 + i * 4;
    const x = Math.max(0, Math.min(1, (frame - start) / 12));
    return easeOutBack(x);
  };
  const titleFade = interpolate(frame, [22, 40], [0, 1], { extrapolateRight: "clamp" });

  // —— 副标题 / 日期 ——
  const subP = interpolate(frame, [60, 84], [0, 1], { extrapolateRight: "clamp", easing: easeOut });
  const dateP = interpolate(frame, [78, 102], [0, 1], { extrapolateRight: "clamp", easing: easeOut });
  const brandP = interpolate(frame, [96, 120], [0, 1], { extrapolateRight: "clamp" });

  // —— glitch 闪烁（约 3.0s 与 6.6s 两处）——
  const glitchAt = (c: number, dur: number) =>
    Math.max(0, Math.min(1, 1 - Math.abs(t - c) / dur));
  const g1 = glitchAt(3.0, 0.18);
  const g2 = glitchAt(6.6, 0.18);
  const glitch = Math.max(g1, g2);
  const glitchShift = glitch * 10 * Math.sin(frame * 1.3);

  // —— 收尾提亮（最后 0.6s 不闪）——
  const endHold = interpolate(frame, [durationInFrames - 18, durationInFrames], [1, 1], {
    extrapolateLeft: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: NAVY }}>
      {/* 科技网格底 */}
      <AbsoluteFill
        style={{
          backgroundImage: `linear-gradient(rgba(55,225,255,0.10) 1px, transparent 1px), linear-gradient(90deg, rgba(55,225,255,0.10) 1px, transparent 1px)`,
          backgroundSize: "80px 80px",
          backgroundPositionX: -gridPan,
          opacity: 0.55,
        }}
      />
      {/* 径向霓虹辉光 */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(circle at 50% 44%, rgba(138,107,224,0.30) 0%, rgba(10,14,39,0) 55%), radial-gradient(circle at 22% 78%, rgba(255,79,216,0.18) 0%, rgba(10,14,39,0) 45%)",
        }}
      />
      {/* 漫画速度线（斜向，入场扫入）*/}
      <AbsoluteFill style={{ opacity: 0.22 * speedSweep, mixBlendMode: "screen" }}>
        <div
          style={{
            position: "absolute",
            inset: -200,
            backgroundImage:
              "repeating-linear-gradient(36deg, transparent 0 26px, rgba(255,255,255,0.5) 26px 28px)",
            transform: `translateX(${gridPan * 1.4}px)`,
          }}
        />
      </AbsoluteFill>
      {/* 漫画网点（halftone 同心点）*/}
      <AbsoluteFill style={{ opacity: 0.12, mixBlendMode: "screen" }}>
        <div
          style={{
            position: "absolute",
            inset: -200,
            backgroundImage:
              "radial-gradient(rgba(255,226,61,0.9) 1.4px, transparent 1.6px)",
            backgroundSize: "18px 18px",
          }}
        />
      </AbsoluteFill>

      {/* 信号弹掠过 */}
      <SignalBullet progress={bulletP} opacity={bulletOpacity} />

      {/* 爆炸星形徽标 */}
      <BurstStar spin={burstSpin} scale={burstScale} glow={burstGlow} />

      {/* 标题区 */}
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div style={{ position: "relative", textAlign: "center" }}>
          {/* 标题（漫画粗描边 + 霓虹辉光 + 逐字弹入）*/}
          <div
            style={{
              display: "flex",
              justifyContent: "center",
              gap: 2,
              opacity: titleFade,
              transform: `translateX(${glitchShift}px)`,
            }}
          >
            {titleChars.map((ch, i) => {
              const a = charAppear(i);
              const isMid = i >= 4 && i <= 6; // “信号弹” 三字用粉强调
              const col = isMid ? NEON_PINK : NEON_BLUE;
              return (
                <span
                  key={i}
                  style={{
                    fontSize: 104,
                    fontWeight: 900,
                    fontFamily: "Noto Sans SC, sans-serif",
                    color: WHITE,
                    letterSpacing: 2,
                    opacity: Math.min(1, a),
                    transform: `translateY(${(1 - a) * 60}px) scale(${0.6 + a * 0.4}) rotate(${(1 - a) * -8}deg)`,
                    textShadow: `3px 3px 0 #1a1206, -2px -2px 0 ${col}, 0 0 26px ${col}, 0 0 50px ${col}88`,
                  }}
                >
                  {ch}
                </span>
              );
            })}
          </div>
          {/* glitch 残影（RGB 错位）*/}
          {glitch > 0.01 && (
            <div
              style={{
                position: "absolute",
                left: 0,
                right: 0,
                top: 0,
                display: "flex",
                justifyContent: "center",
                gap: 2,
                opacity: glitch * 0.7,
                transform: `translateX(${-glitchShift * 1.6}px)`,
                mixBlendMode: "screen",
                pointerEvents: "none",
              }}
            >
              {titleChars.map((ch, i) => (
                <span
                  key={i}
                  style={{
                    fontSize: 104,
                    fontWeight: 900,
                    fontFamily: "Noto Sans SC, sans-serif",
                    color: NEON_PINK,
                    letterSpacing: 2,
                    transform: `translateY(${(1 - charAppear(i)) * 60}px)`,
                  }}
                >
                  {ch}
                </span>
              ))}
            </div>
          )}

          {/* 副标题 Signal Pop Weekly */}
          <div
            style={{
              marginTop: 22,
              fontSize: 38,
              fontWeight: 700,
              letterSpacing: 10,
              color: NEON_BLUE,
              fontFamily: "Consolas, monospace",
              opacity: subP,
              transform: `translateY(${(1 - subP) * 18}px)`,
              textShadow: `0 0 18px ${NEON_BLUE}aa`,
            }}
          >
            SIGNAL POP · WEEKLY
          </div>

          {/* 日期副标 */}
          <div
            style={{
              marginTop: 16,
              fontSize: 40,
              fontWeight: 700,
              color: "#cfe0ff",
              fontFamily: "Noto Sans SC, sans-serif",
              letterSpacing: 4,
              opacity: dateP,
              transform: `translateY(${(1 - dateP) * 16}px)`,
              textShadow: "0 2px 14px rgba(0,0,0,0.5)",
            }}
          >
            {date} · {weekday}
          </div>
        </div>
      </AbsoluteFill>

      {/* 工作室品牌（底部）*/}
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "flex-end", paddingBottom: 48 }}>
        <div
          style={{
            fontSize: 26,
            color: "rgba(200,215,245,0.9)",
            fontFamily: "Noto Sans SC, sans-serif",
            letterSpacing: 3,
            opacity: brandP,
            textShadow: `0 0 16px ${PURPLE}88`,
          }}
        >
          MARK哥的创想引擎 · 出品
        </div>
      </AbsoluteFill>

      {/* 顶部/底部霓虹光带（漫画分镜感）*/}
      <AbsoluteFill style={{ opacity: 0.9 }}>
        <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 8, background: `linear-gradient(90deg, transparent, ${NEON_PINK}, ${NEON_BLUE}, transparent)` }} />
        <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: 8, background: `linear-gradient(90deg, transparent, ${NEON_BLUE}, ${NEON_PINK}, transparent)` }} />
      </AbsoluteFill>

      {/* 聚光扫光（质感）*/}
      <AbsoluteFill style={{ opacity: 0.18 + 0.12 * haloPulse, mixBlendMode: "screen" }}>
        <div
          style={{
            position: "absolute",
            top: -240,
            left: 0,
            right: 0,
            height: 800,
            transform: `translateX(${(frame / durationInFrames) * 2600 - 700}px) rotate(12deg)`,
            background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent)",
            filter: "blur(24px)",
          }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
