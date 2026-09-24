import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Easing,
} from "remotion";

// ===== 信号弹周末版 · 开场动画（纸质编辑 / 杂志刊头风 · 3D 版）=====
// 设计语言（取自 EvidenceCard「新学到的技能」＋ 3D 升级）：
//   ① 白纸卡片 + 白边 + 真实投影（0 24px 60px 重阴影）
//   ② 微倾斜 -1.5°（纸张随意平铺感）：以 perspective + preserve-3d 实现真 3D
//      入场从 rotateX(-26°)/rotateY(16°)/translateZ(-260px) 缓缓「落定」到桌面视角，
//      之后叠加 ±2~3° 的轻微呼吸浮动，画面有生命但不眩晕。
//   ③ Ken-Burns 微推 1.0 → 1.022（画面持续生命力）
//   ④ 右上角红色「印章」标签 + 底部「来源/刊期」标头（均带 translateZ 景深）
//   ⑤ 背景巨型光环 + 前景扫光分处不同 Z 深度，形成视差层次。
// 纯 CSS/SVG 实现，无外部素材依赖；背景乐由外部钢琴片段 mux 进正片。

const INK = "#0b0f1a"; // 背景墨色
const INK_2 = "#161c2e"; // 背景次色
const PAPER = "#FCFBF7"; // 纸张米白
const PAPER_LINE = "#E7E3D8"; // 纸面分隔线
const STAMP = "#FF375F"; // 印章红（与 EvidenceCard 一致）
const GOLD = "#C9A24B"; // 烫金点缀
const INK_TEXT = "#1E293B"; // 卡片正文墨色
const SUB_TEXT = "#64748B"; // 次级灰
const PERSPECTIVE = 1400; // 3D 透视距离

const easeOutCubic = Easing.out(Easing.cubic);
const easeOutBack = (x: number) => {
  const c1 = 1.9;
  const c3 = c1 + 1;
  return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2);
};

// ---------- 背景巨型光环（置于卡片后方 Z 深度，缓慢自转）----------
export const BackHalo: React.FC<{ p: number }> = ({ p }) => (
  <AbsoluteFill
    style={{
      alignItems: "center",
      justifyContent: "center",
      transform: `translateZ(-340px) rotateY(${p * 24}deg)`,
      transformStyle: "preserve-3d",
      opacity: 0.5,
    }}
  >
    <svg width={1180} height={1180} viewBox="0 0 200 200">
      <defs>
        <radialGradient id="haloG" cx="50%" cy="50%" r="50%">
          <stop offset="60%" stopColor="rgba(201,162,75,0)" />
          <stop offset="82%" stopColor="rgba(201,162,75,0.22)" />
          <stop offset="100%" stopColor="rgba(55,225,255,0)" />
        </radialGradient>
      </defs>
      <circle cx="100" cy="100" r="96" fill="url(#haloG)" />
      <circle cx="100" cy="100" r="78" fill="none" stroke="rgba(255,255,255,0.10)" strokeWidth="0.6" />
    </svg>
  </AbsoluteFill>
);

// ---------- 信号弹小徽标（纸面刊头左上的品牌点）----------
export const BulletMark: React.FC<{ opacity: number }> = ({ opacity }) => (
  <div
    style={{
      display: "flex",
      alignItems: "center",
      gap: 10,
      opacity,
      transform: `translateY(${(1 - opacity) * 10}px)`,
    }}
  >
    <svg width={30} height={30} viewBox="0 0 30 30">
      <defs>
        <linearGradient id="bmGrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#37E1FF" />
          <stop offset="100%" stopColor="#FF375F" />
        </linearGradient>
      </defs>
      <path d="M4 22 Q14 4 26 8" stroke="url(#bmGrad)" strokeWidth="3.4" fill="none" strokeLinecap="round" />
      <circle cx="26" cy="8" r="4.4" fill="#fff" stroke="url(#bmGrad)" strokeWidth="2.4" />
    </svg>
    <span
      style={{
        fontSize: 22,
        fontWeight: 800,
        letterSpacing: 1,
        color: INK_TEXT,
        fontFamily: "Noto Sans SC, sans-serif",
      }}
    >
      信号弹 · Signal Pop
    </span>
  </div>
);

export const OpeningAnimation: React.FC<{
  title: string;
  date: string;
  weekday: string;
}> = ({ title, date, weekday }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const t = frame / fps;

  // —— 背景层淡入 ——
  const bgFade = interpolate(frame, [0, 14], [0, 1], { extrapolateRight: "clamp" });

  // —— 3D 入场：rotateX/Y/Z + translateZ + scale + opacity ——
  const enter = interpolate(frame, [6, 34], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: easeOutCubic,
  });
  const eScale = interpolate(enter, [0, 1], [0.9, 1.0]);
  const eOpacity = interpolate(enter, [0, 1], [0, 1]);
  const eRX = interpolate(enter, [0, 1], [-26, 4]); // 落定桌面视角 X 倾角
  const eRY = interpolate(enter, [0, 1], [16, -5]); // 落定桌面视角 Y 倾角
  const eRZ = interpolate(enter, [0, 1], [0, -1.5]); // 招牌纸张微倾斜
  const eTZ = interpolate(enter, [0, 1], [-260, 0]); // 由远及近

  // —— 入场后轻微呼吸浮动（±2~3°，有生命不眩晕）——
  const floatRX = enter * Math.sin(t * 1.05) * 1.6;
  const floatRY = enter * Math.sin(t * 0.85 + 0.6) * 2.4;

  // —— Ken-Burns 微推（全程 1.0 → 1.022，按成片时长自适应）——
  const ambient = interpolate(t, [0, durationInFrames / fps], [1.0, 1.022], {
    extrapolateRight: "clamp",
    easing: Easing.linear,
  });

  const rx = eRX + floatRX;
  const ry = eRY + floatRY;
  const cardTransform = `scale(${eScale * ambient}) rotateX(${rx}deg) rotateY(${ry}deg) rotateZ(${eRZ}deg) translateZ(${eTZ}px)`;

  // —— 卡片内元素依次入场（带 translateZ 景深）——
  const markP = interpolate(frame, [16, 30], [0, 1], { extrapolateRight: "clamp", easing: easeOutCubic });
  const stampP = interpolate(frame, [24, 40], [0, 1], { extrapolateRight: "clamp", easing: easeOutBack });
  const titleP = interpolate(frame, [30, 56], [0, 1], { extrapolateRight: "clamp", easing: easeOutCubic });
  const kickerP = interpolate(frame, [46, 64], [0, 1], { extrapolateRight: "clamp", easing: easeOutCubic });
  const footerP = interpolate(frame, [60, 82], [0, 1], { extrapolateRight: "clamp", easing: easeOutCubic });

  // —— 一道斜向扫光（前景 Z 深度，约 1.3s→2.4s 掠过一次）——
  const sweepX = interpolate(frame, [40, 72], [-900, 2200], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });
  const sweepOpacity = interpolate(frame, [38, 46, 70, 78], [0, 0.5, 0.5, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // —— 信号弹拖尾（开场呼应品牌，自左上掠到中部一次）——
  const bulletP = interpolate(frame, [10, 34], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });
  const bulletOpacity = interpolate(frame, [8, 14, 32, 38], [0, 0.9, 0.9, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const bx = -260 + bulletP * 1080;
  const by = 240 - bulletP * 120;

  return (
    <AbsoluteFill style={{ backgroundColor: INK, opacity: bgFade }}>
      {/* 墨色径向底 + 暖光池 */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(circle at 50% 42%, rgba(40,52,82,0.55) 0%, rgba(11,15,26,0) 58%), radial-gradient(circle at 50% 120%, rgba(201,162,75,0.10) 0%, rgba(11,15,26,0) 50%)",
        }}
      />
      {/* 纸面细点纹理（极淡，呼应纸张质感）*/}
      <AbsoluteFill style={{ opacity: 0.05, mixBlendMode: "screen" }}>
        <div
          style={{
            position: "absolute",
            inset: -100,
            backgroundImage: "radial-gradient(rgba(255,255,255,0.9) 1px, transparent 1.4px)",
            backgroundSize: "26px 26px",
          }}
        />
      </AbsoluteFill>
      {/* 暗角 */}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 360px 80px rgba(0,0,0,0.55)" }} />

      {/* 信号弹拖尾（微弱呼应）*/}
      <AbsoluteFill style={{ opacity: bulletOpacity, pointerEvents: "none" }}>
        <div
          style={{
            position: "absolute",
            left: bx,
            top: by,
            width: 360,
            height: 16,
            transform: "translate(-50%,-50%) rotate(-18deg)",
            borderRadius: 999,
            background: "linear-gradient(90deg, rgba(55,225,255,0) 0%, rgba(55,225,255,0.85) 60%, #fff 100%)",
            boxShadow: "0 0 28px 6px rgba(55,225,255,0.5)",
            filter: "blur(1px)",
          }}
        />
      </AbsoluteFill>

      {/* ============ 3D 场景（perspective 容器）============ */}
      <AbsoluteFill style={{ perspective: PERSPECTIVE }}>
        <AbsoluteFill style={{ transformStyle: "preserve-3d", alignItems: "center", justifyContent: "center" }}>
          {/* 背景巨型光环（卡片后方 Z 深度）*/}
          <BackHalo p={t} />

          {/* ============ 刊头纸张卡片（真 3D）============ */}
          <div
            style={{
              position: "relative",
              width: "min(1120px, 86%)",
              opacity: eOpacity,
              transform: cardTransform,
              transformStyle: "preserve-3d",
              transformOrigin: "center center",
            }}
          >
            {/* 纸卡本体：白边 + 真实重投影 */}
            <div
              style={{
                position: "relative",
                background: PAPER,
                borderRadius: 14,
                padding: "54px 60px 46px 60px",
                boxShadow: "0 24px 60px rgba(0,0,0,0.65), 0 4px 12px rgba(0,0,0,0.4)",
                border: "1px solid rgba(255,255,255,0.6)",
                transformStyle: "preserve-3d",
              }}
            >
              {/* 顶部刊头行：左品牌 / 右印章（印章带 translateZ 景深）*/}
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "flex-start",
                  transform: "translateZ(8px)",
                }}
              >
                <BulletMark opacity={markP} />
                {/* 右上角红色印章标签（EvidenceCard 语言，弹出景深）*/}
                <div
                  style={{
                    background: STAMP,
                    color: "#fff",
                    fontSize: 20,
                    fontWeight: 800,
                    padding: "6px 16px",
                    borderRadius: 6,
                    letterSpacing: 2,
                    boxShadow: "0 4px 12px rgba(255,55,95,0.4)",
                    opacity: stampP,
                    transform: `translateZ(50px) scale(${0.5 + stampP * 0.5}) rotate(${(1 - stampP) * -10}deg)`,
                    transformOrigin: "center center",
                  }}
                >
                  本周精选 · WEEKLY
                </div>
              </div>

              {/* 主标题（刊头大标，整块上浮淡入，带 translateZ 景深）*/}
              <div
                style={{
                  marginTop: 46,
                  textAlign: "center",
                  opacity: titleP,
                  transform: `translateZ(28px) translateY(${(1 - titleP) * 24}px)`,
                }}
              >
                <div
                  style={{
                    fontSize: 86,
                    fontWeight: 900,
                    color: INK_TEXT,
                    fontFamily: "Noto Sans SC, sans-serif",
                    letterSpacing: 2,
                    lineHeight: 1.12,
                    textShadow: "0 2px 0 rgba(0,0,0,0.04)",
                  }}
                >
                  {title}
                </div>
              </div>

              {/* 分隔细线 + 副标（周末特别版）*/}
              <div
                style={{
                  marginTop: 30,
                  opacity: kickerP,
                  transform: `translateZ(14px) translateY(${(1 - kickerP) * 14}px)`,
                }}
              >
                <div
                  style={{
                    height: 2,
                    width: "62%",
                    margin: "0 auto 18px auto",
                    background: `linear-gradient(90deg, transparent, ${GOLD}, transparent)`,
                  }}
                />
                <div
                  style={{
                    textAlign: "center",
                    fontSize: 26,
                    fontWeight: 700,
                    letterSpacing: 8,
                    color: SUB_TEXT,
                    fontFamily: "Noto Sans SC, sans-serif",
                  }}
                >
                  周末特别版 · 每周六更新
                </div>
              </div>

              {/* 底部来源 / 刊期标头（EvidenceCard 来源行语言）*/}
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginTop: 34,
                  paddingTop: 18,
                  borderTop: `1px solid ${PAPER_LINE}`,
                  opacity: footerP,
                  transform: `translateZ(6px) translateY(${(1 - footerP) * 12}px)`,
                }}
              >
                <div
                  style={{
                    fontSize: 22,
                    fontWeight: 700,
                    color: INK_TEXT,
                    fontFamily: "Noto Sans SC, sans-serif",
                    letterSpacing: 1,
                  }}
                >
                  发布 {date} · {weekday}
                </div>
                <div
                  style={{
                    fontSize: 19,
                    fontWeight: 600,
                    letterSpacing: 1,
                    color: SUB_TEXT,
                    fontFamily: "Noto Sans SC, sans-serif",
                  }}
                >
                  MARK哥的创想引擎 · 出品
                </div>
              </div>
            </div>
          </div>

          {/* 前景斜向扫光（Z 深度前移，掠过纸面一次）*/}
          <AbsoluteFill
            style={{
              opacity: sweepOpacity,
              mixBlendMode: "screen",
              pointerEvents: "none",
              transform: "translateZ(140px)",
            }}
          >
            <div
              style={{
                position: "absolute",
                top: -200,
                left: 0,
                width: 260,
                height: 1500,
                transform: `translateX(${sweepX}px) rotate(14deg)`,
                background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.55), transparent)",
                filter: "blur(18px)",
              }}
            />
          </AbsoluteFill>
        </AbsoluteFill>
      </AbsoluteFill>

      {/* 顶部烫金细线（杂志分镜感）*/}
      <AbsoluteFill style={{ opacity: 0.85 }}>
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            height: 6,
            background: `linear-gradient(90deg, transparent, ${GOLD}, transparent)`,
          }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
