import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Easing,
  Img,
  Sequence,
  staticFile,
} from "remotion";

export interface NewsItem {
  num: number;
  section: string;
  title: string;
  body: string;
  image: string;
}

const ACCENT = "#FFD700";
const WHITE = "#F0F5F0";
const LIGHT_GREY = "#C8D2C8";
const PANEL_W = 384;

// motion-design 原则：
// - 入场 easeOutCubic（减速）
// - stagger 60ms（Corporate standard）
// - ken-burns 缓慢推近（ambient 层级）

const easeOut = Easing.out(Easing.cubic);

export const NewsSlide: React.FC<{ item: NewsItem }> = ({ item }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  // ---- 图片 ken-burns：从 1.0 缓慢推到 1.08（20s 周期）----
  const kenScale = interpolate(t, [0, 8], [1.0, 1.08], {
    extrapolateRight: "clamp",
    easing: easeOut,
  });

  // ---- 左侧面板元素 stagger 入场 ----
  const numIn = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
    easing: easeOut,
  });
  const catIn = interpolate(frame, [6, 21], [0, 1], {
    extrapolateRight: "clamp",
    easing: easeOut,
  });
  const numScale = interpolate(numIn, [0, 1], [1.4, 1]);
  const catScale = interpolate(catIn, [0, 1], [0.6, 1]);

  // ---- 右侧标题滑入 + 正文浮现 ----
  const titleIn = interpolate(frame, [12, 34], [0, 1], {
    extrapolateRight: "clamp",
    easing: easeOut,
  });
  const bodyIn = interpolate(frame, [30, 52], [0, 1], {
    extrapolateRight: "clamp",
    easing: easeOut,
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#10151c" }}>
      {/* 背景图：右 80% 清晰，左 20% 模糊面板（用两层模拟） */}
      <AbsoluteFill
        style={{
          transform: `scale(${kenScale})`,
          transformOrigin: "70% 50%",
        }}
      >
        <Img src={staticFile(item.image)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </AbsoluteFill>

      {/* 左侧模糊暗化面板 */}
      <AbsoluteFill
        style={{
          width: PANEL_W,
          background: "rgba(10,14,22,0.82)",
          backdropFilter: "blur(10px)",
          boxShadow: "0 0 40px rgba(0,0,0,0.6)",
        }}
      />

      {/* 左面板与右图渐变衔接 */}
      <AbsoluteFill
        style={{
          left: PANEL_W - 60,
          width: 120,
          background:
            "linear-gradient(90deg, rgba(10,14,22,0.82) 0%, rgba(10,14,22,0) 100%)",
        }}
      />

      {/* ===== 左侧面板内容 ===== */}
      <AbsoluteFill style={{ left: 0, width: PANEL_W }}>
        <div style={{ position: "absolute", top: 60, left: 40, right: 40, height: 6, background: ACCENT }} />
        <div
          style={{
            position: "absolute",
            top: 200,
            left: 0,
            right: 0,
            textAlign: "center",
            opacity: numIn,
            transform: `scale(${numScale})`,
            fontSize: 150,
            fontWeight: "bold",
            color: ACCENT,
            lineHeight: 1,
            fontFamily: "Noto Sans SC, sans-serif",
          }}
        >
          {String(item.num + 1).padStart(2, "0")}
        </div>
        <div style={{ position: "absolute", top: 360, left: 152, right: 152, height: 6, background: ACCENT }} />
        <div
          style={{
            position: "absolute",
            top: 400,
            left: 0,
            right: 0,
            display: "flex",
            justifyContent: "center",
            opacity: catIn,
            transform: `scale(${catScale})`,
          }}
        >
          <div
            style={{
              padding: "8px 20px",
              background: "rgba(255,215,0,0.15)",
              border: `1px solid ${ACCENT}`,
              borderRadius: 8,
              fontSize: 34,
              color: WHITE,
              fontFamily: "Noto Sans SC, sans-serif",
            }}
          >
            {item.section}
          </div>
        </div>
        <div style={{ position: "absolute", bottom: 40, left: 0, right: 0, textAlign: "center", fontSize: 20, color: "#DCEBDC", fontFamily: "Noto Sans SC, sans-serif" }}>
          隔天信号弹
        </div>
      </AbsoluteFill>

      {/* ===== 右侧文字 ===== */}
      <Sequence from={0}>
        <div
          style={{
            position: "absolute",
            left: 460,
            right: 50,
            top: 90,
            fontSize: 50,
            fontWeight: "bold",
            color: WHITE,
            fontFamily: "Noto Sans SC, sans-serif",
            textShadow: "3px 3px 0 #000, -3px 3px 0 #000, 3px -3px 0 #000, -3px -3px 0 #000",
            opacity: titleIn,
            transform: `translateY(${(1 - titleIn) * 40}px)`,
            lineHeight: 1.4,
          }}
        >
          {item.title}
        </div>
        <div
          style={{
            position: "absolute",
            left: 460,
            right: 50,
            top: 280,
            fontSize: 25,
            color: LIGHT_GREY,
            fontFamily: "Noto Sans SC, sans-serif",
            textShadow: "2px 2px 0 #000",
            opacity: bodyIn,
            transform: `translateY(${(1 - bodyIn) * 24}px)`,
            lineHeight: 1.6,
          }}
        >
          {item.body}
        </div>
      </Sequence>
    </AbsoluteFill>
  );
};
