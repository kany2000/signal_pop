import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Easing,
  Sequence,
} from "remotion";

// ===== 央视《新闻联播》风格开场动画（深蓝旋转地球 + 发光标题）=====
// 复用 DailyNews 的中文字体 Noto Sans SC；本组件不依赖 3D 库，纯 CSS 线框地球。

const NAVY = "#05102e";
const BLUE = "#2f7bff";
const GRID = "rgba(150,200,255,0.55)";
const GRID2 = "rgba(150,200,255,0.30)";
const GOLD = "#FFD700";
const WHITE = "#F3F7FF";

const easeOut = Easing.out(Easing.cubic);
const easeOutBack = (x: number) => {
  const c1 = 1.70158;
  const c3 = c1 + 1;
  return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2);
};

// ---------- 旋转线框地球 ----------
const Globe: React.FC<{ frame: number; fps: number }> = ({ frame, fps }) => {
  const t = frame / fps;
  const slide = (t * 26) % 40; // 经线网格横向滑动（周期40px，无缝循环）→ 旋转感
  const spin = t * 360 * 0.18; // 缓慢自转角度（用于高光/轨道点）
  const latSlide = (t * 8) % 40;

  return (
    <div
      style={{
        position: "absolute",
        left: "50%",
        top: "44%",
        width: 540,
        height: 540,
        transform: "translate(-50%, -50%)",
      }}
    >
      {/* 外层大气辉光 */}
      <div
        style={{
          position: "absolute",
          inset: -70,
          borderRadius: "50%",
          background:
            "radial-gradient(circle, rgba(47,123,255,0.35) 0%, rgba(47,123,255,0.10) 45%, rgba(5,16,46,0) 70%)",
          filter: "blur(8px)",
        }}
      />
      {/* 球体本体 */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          borderRadius: "50%",
          overflow: "hidden",
          background:
            "radial-gradient(circle at 36% 30%, #2a6cff 0%, #1347a8 36%, #0a2f7e 64%, #04173f 100%)",
          border: "1.5px solid rgba(170,215,255,0.75)",
          boxShadow:
            "inset 0 0 60px rgba(0,0,0,0.55), inset 18px 14px 50px rgba(255,255,255,0.12), 0 0 40px rgba(47,123,255,0.55)",
        }}
      >
        {/* 纬线（静止横网格） */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            borderRadius: "50%",
            backgroundImage: `repeating-linear-gradient(0deg, transparent 0 38px, ${GRID2} 38px 40px)`,
            backgroundPositionY: latSlide,
            opacity: 0.9,
          }}
        />
        {/* 经线（滑动竖网格 → 自转） */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            borderRadius: "50%",
            backgroundImage: `repeating-linear-gradient(90deg, transparent 0 38px, ${GRID} 38px 40px)`,
            backgroundPositionX: -slide,
            mixBlendMode: "screen",
          }}
        />
        {/* 球面阴影（增强立体） */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            borderRadius: "50%",
            background:
              "radial-gradient(circle at 36% 30%, rgba(255,255,255,0.22) 0%, rgba(255,255,255,0) 38%), radial-gradient(circle at 70% 78%, rgba(0,0,0,0.45) 0%, rgba(0,0,0,0) 60%)",
          }}
        />
      </div>
      {/* 高光点（缓慢移动） */}
      <div
        style={{
          position: "absolute",
          left: `${40 + 8 * Math.cos((spin * Math.PI) / 180)}%`,
          top: `${32 + 6 * Math.sin((spin * Math.PI) / 180)}%`,
          width: 70,
          height: 70,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(255,255,255,0.5), rgba(255,255,255,0) 70%)",
          filter: "blur(6px)",
          mixBlendMode: "screen",
        }}
      />
      {/* 轨道环 + 飞行点（现代版点缀） */}
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: "50%",
          width: 720,
          height: 300,
          transform: "translate(-50%, -50%) rotate(-18deg)",
          borderRadius: "50%",
          border: "1px solid rgba(255,215,0,0.30)",
        }}
      >
        <div
          style={{
            position: "absolute",
            left: "50%",
            top: "50%",
            width: 0,
            height: 0,
            transform: `rotate(${spin * 2}deg)`,
          }}
        >
          <div
            style={{
              position: "absolute",
              left: -5,
              top: -150,
              width: 10,
              height: 10,
              borderRadius: "50%",
              background: GOLD,
              boxShadow: `0 0 14px 3px ${GOLD}`,
            }}
          />
        </div>
      </div>
    </div>
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

  // 球体入场（缩放+淡入）
  const globeIn = interpolate(frame, [0, 28], [0.78, 1], { extrapolateRight: "clamp", easing: easeOut });
  const globeFade = interpolate(frame, [0, 22], [0, 1], { extrapolateRight: "clamp" });

  // 标题入场（2.5s→4.2s）
  const titleP = interpolate(frame, [75, 126], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOutBack });
  const titleFade = interpolate(frame, [75, 120], [0, 1], { extrapolateRight: "clamp" });
  // 金色下划线展开（4s→5.2s）
  const lineP = interpolate(frame, [120, 162], [0, 1], { extrapolateRight: "clamp", easing: easeOut });
  // 日期副标题（5s→6.5s）
  const dateP = interpolate(frame, [150, 198], [0, 1], { extrapolateRight: "clamp", easing: easeOut });
  // 工作室品牌（6s→7.2s）
  const brandP = interpolate(frame, [180, 222], [0, 1], { extrapolateRight: "clamp" });
  // 收尾轻微提亮（最后 0.8s 不闪，保持满亮切出）
  const endHold = interpolate(frame, [durationInFrames - 20, durationInFrames], [1, 1], { extrapolateLeft: "clamp" });

  return (
    <AbsoluteFill style={{ backgroundColor: NAVY }}>
      {/* 背景径向渐变 + 暗角 */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(circle at 50% 42%, #0c1f4d 0%, #071537 45%, #03081c 100%)",
        }}
      />
      <AbsoluteFill style={{ opacity: globeFade, transform: `scale(${globeIn})`, transformOrigin: "50% 44%" }}>
        <Globe frame={frame} fps={fps} />
      </AbsoluteFill>

      {/* 标题区（球体中央偏下，深色衬底保证可读） */}
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div style={{ position: "relative", textAlign: "center" }}>
          <div
            style={{
              fontSize: 94,
              fontWeight: 900,
              color: WHITE,
              fontFamily: "Noto Sans SC, sans-serif",
              letterSpacing: 10,
              opacity: titleFade,
              transform: `translateY(${(1 - titleP) * 36}px) scale(${0.92 + titleP * 0.08})`,
              textShadow: "0 4px 26px rgba(0,0,0,0.6), 0 0 18px rgba(47,123,255,0.45)",
            }}
          >
            {title}
          </div>
          {/* 金色下划线 */}
          <div style={{ display: "flex", justifyContent: "center", marginTop: 26 }}>
            <div
              style={{
                height: 6,
                width: `${560 * lineP}px`,
                background: `linear-gradient(90deg, rgba(255,215,0,0), ${GOLD}, rgba(255,215,0,0))`,
                borderRadius: 3,
                boxShadow: `0 0 16px 2px rgba(255,215,0,0.5)`,
                opacity: lineP,
              }}
            />
          </div>
          {/* 日期副标题 */}
          <div
            style={{
              marginTop: 26,
              fontSize: 42,
              fontWeight: 700,
              color: "#cfe0ff",
              fontFamily: "Noto Sans SC, sans-serif",
              letterSpacing: 4,
              opacity: dateP,
              transform: `translateY(${(1 - dateP) * 22}px)`,
              textShadow: "0 2px 14px rgba(0,0,0,0.5)",
            }}
          >
            {date} · {weekday}
          </div>
        </div>
      </AbsoluteFill>

      {/* 工作室品牌（底部，保留品牌） */}
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "flex-end", paddingBottom: 54 }}>
        <div
          style={{
            fontSize: 24,
            color: "rgba(200,215,245,0.85)",
            fontFamily: "Noto Sans SC, sans-serif",
            letterSpacing: 3,
            opacity: brandP,
          }}
        >
          MARK哥的创想引擎 · 出品
        </div>
      </AbsoluteFill>

      {/* 聚光扫光（缓慢横扫，增强质感） */}
      <AbsoluteFill style={{ opacity: 0.22, mixBlendMode: "screen" }}>
        <div
          style={{
            position: "absolute",
            top: -220,
            left: 0,
            right: 0,
            height: 760,
            transform: `translateX(${(frame / durationInFrames) * 2600 - 700}px) rotate(12deg)`,
            background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.55), transparent)",
            filter: "blur(22px)",
          }}
        />
      </AbsoluteFill>

      {/* 顶部/底部新闻联播式细光带 */}
      <AbsoluteFill style={{ opacity: 0.9 }}>
        <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 6, background: `linear-gradient(90deg, transparent, ${GOLD}, transparent)`, opacity: 0.5 }} />
        <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: 6, background: `linear-gradient(90deg, transparent, ${BLUE}, transparent)`, opacity: 0.5 }} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
