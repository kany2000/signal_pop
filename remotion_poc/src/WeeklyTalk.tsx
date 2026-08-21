import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Easing,
  Img,
  staticFile,
  Sequence,
} from "remotion";

export interface TalkSegment {
  speaker: string;
  voice: string;
  text: string;
  dur: number;
  bg: string;
}

const AXIN_BLUE = "#3A82D2";
const XIAOLAN_PINK = "#DC5A96";
const GOLD = "#D4AF37";
const WHITE = "#F5F5FA";
const GREY = "#BEC6D2";

const easeOut = Easing.out(Easing.cubic);

export const WeeklyTalk: React.FC<{ segs: TalkSegment[] }> = ({ segs }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  // 累计定位当前段
  let cur: TalkSegment | null = null;
  let segStart = 0;
  let acc = 0;
  for (const s of segs) {
    if (t >= acc && t < acc + s.dur) {
      cur = s;
      segStart = acc;
      break;
    }
    acc += s.dur;
  }
  if (!cur) return <AbsoluteFill style={{ backgroundColor: "#0d1220" }} />;

  const localT = t - segStart;
  const isAxin = cur.speaker === "阿信";
  const accent = isAxin ? AXIN_BLUE : XIAOLAN_PINK;

  // 头像：说话者光晕脉冲（sin 呼吸）+ 入场弹跳
  const speakPulse = 1 + 0.05 * Math.sin(localT * 5 * Math.PI * 2);
  const enter = interpolate(frame, [0, 12], [0, 1], {
    extrapolateRight: "clamp",
    easing: easeOut,
  });
  const axinScale = (isAxin ? speakPulse : 1) * interpolate(enter, [0, 1], [0.8, 1]);
  const xiaolanScale = (!isAxin ? speakPulse : 1) * interpolate(enter, [0, 1], [0.8, 1]);

  // 气泡：入场缩放 0.92 -> 1 + 说话者边框高亮
  const bubbleIn = interpolate(frame, [3, 18], [0, 1], {
    extrapolateRight: "clamp",
    easing: easeOut,
  });

  // 配图背景（段切换淡入 0.4s + 轻微推近）
  const bgFade = interpolate(localT, [0, 0.4], [0.6, 1], {
    extrapolateRight: "clamp",
    easing: easeOut,
  });
  const bgScale = interpolate(localT, [0, cur.dur], [1.0, 1.06], {
    extrapolateRight: "clamp",
    easing: easeOut,
  });

  // 文本按 4 行截断（气泡内）
  const maxChars = 42;
  let text = cur.text;
  if (text.length > maxChars * 3) text = text.slice(0, maxChars * 3 - 1) + "…";

  const nameColor = isAxin ? "#9CC3EC" : "#F2B8D4";

  // 三连动画检测：段文本含「一键三连」→ 三连图标浮现后持续显示到视频结束（CTA 常驻）
  const isSanlian = cur.text.includes("一键三连") || cur.text.includes("三连");
  const sanlianCx = [560, 960, 1360];
  const sanlianIcons = ["订阅", "关注", "转发"];
  // 图标从三连段开始 stagger 浮现（相对三连段起始时间，而非段内）
  const sanlianSegStart = (() => {
    let acc2 = 0;
    for (const s of segs) {
      if (s.text.includes("一键三连") || s.text.includes("三连")) return acc2;
      acc2 += s.dur;
    }
    return 0;
  })();
  const sanlianLocalT = t - sanlianSegStart;
  const sanlianIn = (k: number) => {
    const start = 0.4 + k * 0.35;
    const end = start + 0.8;
    if (sanlianLocalT < start) return 0;
    if (sanlianLocalT > end) return 1;
    const x = (sanlianLocalT - start) / (end - start);
    // easeOutBack: 1 + c3*(x-1)^3 + c1*(x-1)^2
    const c1 = 1.70158;
    const c3 = c1 + 1;
    return Math.max(0, Math.min(1.1, 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2)));
  };

  return (
    <AbsoluteFill style={{ backgroundColor: "#0d1220" }}>
      {/* 背景配图（随段轮换，淡入过渡） */}
      <AbsoluteFill style={{ opacity: bgFade, transform: `scale(${bgScale})`, transformOrigin: "50% 40%" }}>
        <Img src={staticFile(cur.bg)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "rgba(8,12,24,0.62)" }} />

      {/* 顶部品牌条 */}
      <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 90, background: "linear-gradient(180deg, rgba(10,16,30,0.95), rgba(10,16,30,0))" }} />
      <div style={{ position: "absolute", top: 26, left: 0, right: 0, textAlign: "center", fontSize: 30, fontWeight: "bold", color: GOLD, fontFamily: "Noto Sans SC, sans-serif", letterSpacing: 2 }}>
        隔天信号弹 · 周末特别版
      </div>

      {/* 左阿信 */}
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", left: 0, width: 540 }}>
        <div style={{ transform: `scale(${axinScale})`, transformOrigin: "center", width: 300, height: 300, position: "relative" }}>
          {isAxin && (
            <div style={{ position: "absolute", inset: -28, borderRadius: "50%", border: `4px solid ${accent}`, opacity: 0.55, boxShadow: `0 0 60px ${accent}` }} />
          )}
          <Img src={staticFile("anchor_axin.jpg")} style={{ width: "100%", height: "100%", borderRadius: "50%", objectFit: "cover", border: `3px solid ${accent}` }} />
        </div>
        <div style={{ marginTop: 18, fontSize: 34, fontWeight: "bold", color: nameColor, fontFamily: "Noto Sans SC, sans-serif" }}>
          阿信
          {isAxin && <span style={{ color: GOLD, fontSize: 20, marginLeft: 8 }}>正在说…</span>}
        </div>
      </AbsoluteFill>

      {/* 右小蓝 */}
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", left: 1380, width: 540 }}>
        <div style={{ transform: `scale(${xiaolanScale})`, transformOrigin: "center", width: 300, height: 300, position: "relative" }}>
          {!isAxin && (
            <div style={{ position: "absolute", inset: -28, borderRadius: "50%", border: `4px solid ${accent}`, opacity: 0.55, boxShadow: `0 0 60px ${accent}` }} />
          )}
          <Img src={staticFile("anchor_xiaolan.jpg")} style={{ width: "100%", height: "100%", borderRadius: "50%", objectFit: "cover", border: `3px solid ${accent}` }} />
        </div>
        <div style={{ marginTop: 18, fontSize: 34, fontWeight: "bold", color: nameColor, fontFamily: "Noto Sans SC, sans-serif" }}>
          小蓝
          {!isAxin && <span style={{ color: GOLD, fontSize: 20, marginLeft: 8 }}>正在说…</span>}
        </div>
      </AbsoluteFill>

      {/* 三连图标（三连段开始持续显示到结尾，stagger 浮现后常驻 CTA） */}
      {t >= sanlianSegStart - 0.05 && (
        <AbsoluteFill>
          {sanlianIcons.map((label, k) => {
            const g = sanlianIn(k);
            return (
              <div
                key={label}
                style={{
                  position: "absolute",
                  left: sanlianCx[k] - 100,
                  top: 560,
                  width: 200,
                  height: 200,
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  opacity: g,
                  transform: `scale(${0.8 + g * 0.2})`,
                }}
              >
                <div
                  style={{
                  width: 120,
                  height: 120,
                  borderRadius: "50%",
                  background: "rgba(20,26,36,0.92)",
                  border: `3px solid ${GOLD}`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  boxShadow:
                    g > 0.5
                      ? `0 0 ${30 + 22 * (0.5 + 0.5 * Math.sin((sanlianLocalT - 1.4) * Math.PI * 1.1))}px ${GOLD}88`
                      : "none",
                  fontSize: 44,
                  color: "#FFF0BE",
                  fontWeight: "bold",
                  }}
                >
                  {label === "订阅" ? "▶" : label === "关注" ? "★" : "↗"}
                </div>
                <div style={{ marginTop: 10, fontSize: 26, fontWeight: "bold", color: "#FFF", fontFamily: "Noto Sans SC, sans-serif" }}>
                  {label}
                </div>
              </div>
            );
          })}
        </AbsoluteFill>
      )}

      {/* 底部对话气泡 */}
      <div
        style={{
          position: "absolute",
          bottom: 70,
          left: "50%",
          transform: `translateX(-50%) scale(${0.92 + bubbleIn * 0.08})`,
          width: 1560,
          minHeight: 190,
          padding: "26px 44px",
          background: "rgba(18,26,42,0.92)",
          border: `3px solid ${accent}`,
          borderRadius: 26,
          boxShadow: `0 0 40px rgba(0,0,0,0.5), 0 0 24px ${accent}55`,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", marginBottom: 10 }}>
          <span style={{ width: 14, height: 14, borderRadius: "50%", background: accent, marginRight: 12, display: "inline-block" }} />
          <span style={{ fontSize: 26, fontWeight: "bold", color: nameColor, fontFamily: "Noto Sans SC, sans-serif" }}>
            {isAxin ? "阿信" : "小蓝"}
          </span>
        </div>
        <div style={{ fontSize: 34, color: WHITE, fontFamily: "Noto Sans SC, sans-serif", lineHeight: 1.55 }}>
          {text}
        </div>
      </div>

      {/* 底部进度条 */}
      <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: 8, background: "rgba(255,255,255,0.08)" }}>
        <div style={{ height: "100%", width: `${(t / (acc + 0.01)) * 100}%`, background: accent }} />
      </div>
    </AbsoluteFill>
  );
};
