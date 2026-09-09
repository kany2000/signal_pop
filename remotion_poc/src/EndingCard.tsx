import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Easing,
} from "remotion";

// ===== 片尾 Logo 卡（与 OpeningAnimation 同视觉语言，可拼在主片尾部）=====
// 参考 Easel video-intro-outro 的「片尾关注引导卡」：品牌 + 订阅 CTA。
// 未来管线：OpeningAnimation(10s) + DailyNews(正片) + EndingCard(4s) 顺序 concat。

const NAVY = "#05102e";
const GOLD = "#FFD700";
const WHITE = "#F3F7FF";
const easeOut = Easing.out(Easing.cubic);

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

  // 整体入场（0 → 1.4s）
  const inP = interpolate(frame, [0, 42], [0, 1], { extrapolateRight: "clamp", easing: easeOut });
  const fade = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: "clamp" });
  // 结尾轻微脉冲（最后 0.6s）
  const pulse = interpolate(frame, [durationInFrames - 18, durationInFrames], [1, 1.04],
    { extrapolateLeft: "clamp" });

  return (
    <AbsoluteFill style={{ backgroundColor: NAVY }}>
      <AbsoluteFill
        style={{ background: "radial-gradient(circle at 50% 42%, #0c1f4d 0%, #071537 45%, #03081c 100%)" }}
      />
      <AbsoluteFill style={{ opacity: fade, transform: `scale(${0.94 + inP * 0.06})`, transformOrigin: "50% 50%" }}>
        <div style={{ position: "absolute", left: "50%", top: "46%", transform: "translate(-50%,-50%)", textAlign: "center" }}>
          {/* 圆形品牌徽标 */}
          <div style={{
            width: 150, height: 150, margin: "0 auto 30px",
            borderRadius: "50%",
            background: "radial-gradient(circle at 36% 30%, #2a6cff 0%, #1347a8 40%, #04173f 100%)",
            border: "2px solid rgba(170,215,255,0.75)",
            boxShadow: "inset 0 0 30px rgba(0,0,0,0.5), 0 0 34px rgba(47,123,255,0.5)",
            display: "flex", alignItems: "center", justifyContent: "center",
            transform: `scale(${pulse})`,
          }}>
            <span style={{ fontSize: 46, color: GOLD, fontWeight: 900, fontFamily: "Noto Sans SC, sans-serif" }}>M</span>
          </div>
          <div style={{
            fontSize: 56, fontWeight: 900, color: WHITE, fontFamily: "Noto Sans SC, sans-serif",
            letterSpacing: 6, textShadow: "0 4px 22px rgba(0,0,0,0.6), 0 0 16px rgba(47,123,255,0.4)",
          }}>{brand}</div>
          <div style={{
            marginTop: 18, fontSize: 30, fontWeight: 700, color: "#cfe0ff", fontFamily: "Noto Sans SC, sans-serif",
            letterSpacing: 3,
          }}>{program}</div>
          <div style={{
            marginTop: 30, fontSize: 26, color: "rgba(200,215,245,0.9)", fontFamily: "Noto Sans SC, sans-serif",
            letterSpacing: 2,
          }}>{cta}</div>
        </div>
      </AbsoluteFill>
      {/* 上下细光带，呼应开场 */}
      <AbsoluteFill style={{ opacity: 0.9 }}>
        <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 6, background: `linear-gradient(90deg, transparent, ${GOLD}, transparent)`, opacity: 0.5 }} />
        <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: 6, background: `linear-gradient(90deg, transparent, #2f7bff, transparent)`, opacity: 0.5 }} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
