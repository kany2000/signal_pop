import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Easing,
} from "remotion";
import { BackHalo, BulletMark } from "./OpeningAnimation";

// ===== 片尾 Logo 卡（与 OpeningAnimation 同款 3D 纸张刊头语言）=====
// 参考 Easel video-intro-outro 的「片尾关注引导卡」：品牌 + 订阅 CTA。
// 视觉与开场完全统一：白纸卡 + 真实投影 + -1.5° 微倾斜 + 3D 透视 + Ken-Burns + 红色印章。
// 未来管线：OpeningAnimation(10s) + DailyNews(正片) + EndingCard(4s) 顺序 concat。

const INK = "#0b0f1a";
const PAPER = "#FCFBF7";
const PAPER_LINE = "#E7E3D8";
const STAMP = "#FF375F";
const GOLD = "#C9A24B";
const INK_TEXT = "#1E293B";
const SUB_TEXT = "#64748B";
const PERSPECTIVE = 1400;

const easeOutCubic = Easing.out(Easing.cubic);
const easeOutBack = (x: number) => {
  const c1 = 1.9;
  const c3 = c1 + 1;
  return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2);
};

export const EndingCard: React.FC<{
  brand?: string;
  program?: string;
  cta?: string;
}> = ({
  brand = "MARK哥的创想引擎",
  program = "AI语播·信号弹每周精选",
  cta = "关注 · 点赞 · 转发　每周三 08:00 更新",
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const t = frame / fps;

  // —— 背景层淡入 ——
  const bgFade = interpolate(frame, [0, 14], [0, 1], { extrapolateRight: "clamp" });

  // —— 3D 入场（与开场同幅度：正常、不夸张）——
  const enter = interpolate(frame, [6, 42], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: easeOutCubic,
  });
  const eScale = interpolate(enter, [0, 1], [0.9, 1.0]);
  const eOpacity = interpolate(enter, [0, 1], [0, 1]);
  const eRX = interpolate(enter, [0, 1], [-26, 4]);
  const eRY = interpolate(enter, [0, 1], [16, -5]);
  const eRZ = interpolate(enter, [0, 1], [0, -1.5]);
  const eTZ = interpolate(enter, [0, 1], [-260, 0]);

  // —— 入场后轻微呼吸浮动（±1.6/±2.4°，与开场一致）——
  const floatRX = enter * Math.sin(t * 1.05) * 1.6;
  const floatRY = enter * Math.sin(t * 0.85 + 0.6) * 2.4;

  // —— Ken-Burns 微推（全程 1.0 → 1.022）——
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
  const subP = interpolate(frame, [46, 64], [0, 1], { extrapolateRight: "clamp", easing: easeOutCubic });
  const ctaP = interpolate(frame, [58, 80], [0, 1], { extrapolateRight: "clamp", easing: easeOutCubic });
  const footerP = interpolate(frame, [64, 86], [0, 1], { extrapolateRight: "clamp", easing: easeOutCubic });

  return (
    <AbsoluteFill style={{ backgroundColor: INK, opacity: bgFade }}>
      {/* 墨色径向底 + 暖光池 */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(circle at 50% 42%, rgba(40,52,82,0.55) 0%, rgba(11,15,26,0) 58%), radial-gradient(circle at 50% 120%, rgba(201,162,75,0.10) 0%, rgba(11,15,26,0) 50%)",
        }}
      />
      {/* 纸面细点纹理 */}
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
      <AbsoluteFill style={{ boxShadow: "inset 0 0 360px 80px rgba(0,0,0,0.55)" }} />

      {/* ============ 3D 场景 ============ */}
      <AbsoluteFill style={{ perspective: PERSPECTIVE }}>
        <AbsoluteFill style={{ transformStyle: "preserve-3d", alignItems: "center", justifyContent: "center" }}>
          {/* 背景巨型光环（与开场一致）*/}
          <BackHalo p={t} />

          {/* ============ 刊头纸张卡片（真 3D）============ */}
          <div
            style={{
              position: "relative",
              width: "min(1080px, 84%)",
              opacity: eOpacity,
              transform: cardTransform,
              transformStyle: "preserve-3d",
              transformOrigin: "center center",
            }}
          >
            <div
              style={{
                position: "relative",
                background: PAPER,
                borderRadius: 14,
                padding: "52px 58px 44px 58px",
                boxShadow: "0 24px 60px rgba(0,0,0,0.65), 0 4px 12px rgba(0,0,0,0.4)",
                border: "1px solid rgba(255,255,255,0.6)",
                transformStyle: "preserve-3d",
              }}
            >
              {/* 顶部刊头行：左品牌 / 右印章 */}
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "flex-start",
                  transform: "translateZ(8px)",
                }}
              >
                <BulletMark opacity={markP} />
                {/* 右上角红色印章标签：感谢观看 */}
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
                  感谢观看 · THANKS
                </div>
              </div>

              {/* 主标题（节目名）*/}
              <div
                style={{
                  marginTop: 42,
                  textAlign: "center",
                  opacity: titleP,
                  transform: `translateZ(28px) translateY(${(1 - titleP) * 24}px)`,
                }}
              >
                <div
                  style={{
                    fontSize: 84,
                    fontWeight: 900,
                    color: INK_TEXT,
                    fontFamily: "Noto Sans SC, sans-serif",
                    letterSpacing: 2,
                    lineHeight: 1.12,
                    textShadow: "0 2px 0 rgba(0,0,0,0.04)",
                  }}
                >
                  {program}
                </div>
              </div>

              {/* 分隔细线 + 出品方副标 */}
              <div
                style={{
                  marginTop: 28,
                  opacity: subP,
                  transform: `translateZ(14px) translateY(${(1 - subP) * 14}px)`,
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
                    fontSize: 28,
                    fontWeight: 700,
                    letterSpacing: 4,
                    color: SUB_TEXT,
                    fontFamily: "Noto Sans SC, sans-serif",
                  }}
                >
                  {brand}
                </div>
              </div>

              {/* 订阅 CTA 横幅（金边胶囊，呼应 Easel 关注引导卡）*/}
              <div
                style={{
                  marginTop: 32,
                  textAlign: "center",
                  opacity: ctaP,
                  transform: `translateZ(20px) translateY(${(1 - ctaP) * 16}px)`,
                }}
              >
                <div
                  style={{
                    display: "inline-block",
                    padding: "14px 34px",
                    borderRadius: 999,
                    border: `2px solid ${GOLD}`,
                    background: "rgba(201,162,75,0.08)",
                    color: INK_TEXT,
                    fontSize: 26,
                    fontWeight: 700,
                    letterSpacing: 2,
                    fontFamily: "Noto Sans SC, sans-serif",
                    boxShadow: "0 6px 18px rgba(201,162,75,0.18)",
                  }}
                >
                  {cta}
                </div>
              </div>

              {/* 底部来源 / 出品标头 */}
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
                  {brand} · 出品
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
                  周末特别版
                </div>
              </div>
            </div>
          </div>
        </AbsoluteFill>
      </AbsoluteFill>

      {/* 顶部烫金细线（与开场呼应）*/}
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
