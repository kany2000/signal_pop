import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Easing,
} from "remotion";

// ===== 信号弹周末版 · 开场动画 v2（双主播登场版）=====
//
// 为什么换思路（原 OpeningAnimation 的问题）：
//   原版是「一张纸卡从3D 空间落定」—— 静物展示型，**没有人**。
//   观众点进来看到的是一张会动的卡片，不是两个即将聊天的人。
//   周末版的钩子本来就是「双主播脱口秀」，片头理应先立住这两个人。
//
// v2 的做法：沿用 signal-motion 的火柴人「豆子花叔」造型语言（纯 SVG，零素材），
// 让阿信与小蓝在片头真的「活」过来 —— 挥手、张嘴、点头、击掌，
// 然后标题从两人中间的「信号弹弹道」里升起。
//
// 三种风格变体（--variant 切换，便于 A/B 实测后再定）：
//   v2a "handshake" 双主播击掌开场，标题居中升起（最稳、最通用）
//   v2b "duo"      左右分屏式对话感，两人同时开口（信息密度高）
//   v2c "launch"   信号弹从屏幕下打出去，拖尾拉出标题（动势最强）
//
// 纯 CSS/SVG，无外部素材；背景乐沿用外部钢琴片段 mux。

const INK = "#0b0f1a";
const INK_2 = "#161c2e";
const CYAN = "#37E1FF";
const STAMP = "#FF375F";
const GOLD = "#C9A24B";
const PAPER = "#FCFBF7";
const INK_TEXT = "#1E293B";
const SUB_TEXT = "#64748B";

const FONT = "Noto Sans SC, sans-serif";

type Variant = "handshake" | "duo" | "launch";
type BeanPose = "wave" | "talk" | "cheer" | "clap" | "rest" | "nod" | "pointUp";
type BeanExpr = "talk" | "happy" | "blank" | "shock";

// ---------- 豆子花叔式火柴人（简化版：只保留片头要用的部件）----------
// 与 signal-motion 的 toon.js 同源造型：圆头 + 豆身 + 面条手臂 + 渔夫帽。
// 这里手写 SVG 而非复用引擎，因为片头只需要 4 个姿势，引入整个引擎不划算。
const Bean: React.FC<{
  x: number;
  y: number;
  s: number;                 // 头半径（整体缩放基准）
  flip?: boolean;            // 是否水平镜像
  pose: "wave" | "talk" | "cheer" | "clap" | "rest" | "nod";
  expr: "talk" | "happy" | "blank" | "shock";
  mouth: 0 | 1 | 2;          // 0 闭 1 半 2 张
  flipHair?: boolean;
  accent: string;            // 服装主色（区分两人）
  opacity?: number;
}> = ({ x, y, s, flip = false, pose, expr, mouth, accent, opacity = 1 }) => {
  // 各姿势的手臂目标（相对肩，单位＝头半径；与 toon.js 的 l/r 定义一致）
  const arms: Record<string, [number, number, number, number]> = {
    wave: [-0.95, 1.05, 1.0, -1.35],   // 右手举起挥动
    talk: [-0.95, 1.05, 1.15, 0.45],    // 一手微抬
    cheer: [-1.5, -1.35, 1.5, -1.35],   // 双手举高
    clap: [-0.45, 0.5, 0.45, 0.5],      // 双手拍拢
    rest: [-0.95, 1.05, 0.95, 1.05],
    nod: [-0.95, 1.05, 1.3, 0.8],
    pointUp: [-0.95, 1.05, 0.55, -1.55],// 举手指天（呼应信号弹飞出）
  };
  const [lx, ly, rx, ry] = arms[pose] ?? arms.rest;

  // 全部相对「脚底原点」的局部坐标，单位＝头半径 1。
// 外层 <g transform=translate(x y) scale(s)> 已完成定位与缩放，
// 内部**不能再乘 s**（会二次缩放把人缩成一个点），也不能减 x/y（会推出画面）。
const shoulderY = -1.42;
  const hipY = -0.78;
  const bodyW = 0.86;
  const hipW = 0.6;
  const shL = { x: -bodyW * 0.5, y: shoulderY };
  const shR = { x: bodyW * 0.5, y: shoulderY };
  const handL = { x: shL.x + lx, y: shL.y + ly };
  const handR = { x: shR.x + rx, y: shR.y + ry };
  const headY = -2.52;

  const eyeY = headY + 0.06;
  const eyeR = 0.1;
  const eyeDX = 0.3;

  const mouthShapes = [
    { ry: 0.05, fill: "#8B3A3A" },  // 闭（一条线）
    { ry: 0.14, fill: "#8B3A3A" },  // 半开
    { ry: 0.26, fill: "#8B3A3A" },  // 张
  ];
  const m = mouthShapes[mouth];
  // 表情：睁眼程度（happy 眯眼、shock 睁大）
  const openMap: Record<string, number> = { talk: 1, happy: 0.25, blank: 1, shock: 1.35 };
  const eyeOpen = openMap[expr] ?? 1;

  return (
    //铺满 1920×1080 的画布：人物靠自身 translate 定位，容器不裁剪。
    <svg width={1920} height={1080} viewBox="0 0 1920 1080"
         style={{ position: "absolute", inset: 0, overflow: "visible" }}>
      <g transform={`translate(${x} ${y}) scale(${flip ? -s : s} ${s})`} opacity={opacity}>
      {/* 影子 */}
      <ellipse cx={0} cy={0.05} rx={0.92} ry={0.16} fill="rgba(0,0,0,0.35)" />
      {/* 腿 */}
      <line x1={-hipW * 0.5} y1={hipY} x2={-hipW * 0.62} y2={-0.02}
            stroke="#2A3550" strokeWidth={0.19} strokeLinecap="round" />
      <line x1={hipW * 0.5} y1={hipY} x2={hipW * 0.62} y2={-0.02}
            stroke="#2A3550" strokeWidth={0.19} strokeLinecap="round" />
      {/* 手臂（面条手臂：肩→肘→手，用二次贝塞尔做轻微下垂） */}
      <path d={`M ${shL.x} ${shL.y} Q ${(shL.x + handL.x) / 2 - 0.12} ${(shL.y + handL.y) / 2} ${handL.x} ${handL.y}`}
            fill="none" stroke={accent} strokeWidth={0.17} strokeLinecap="round" />
      <path d={`M ${shR.x} ${shR.y} Q ${(shR.x + handR.x) / 2 + 0.12} ${(shR.y + handR.y) / 2} ${handR.x} ${handR.y}`}
            fill="none" stroke={accent} strokeWidth={0.17} strokeLinecap="round" />
      {/* 豆身 */}
      <path d={`M ${-bodyW * 0.5} ${shoulderY}
                Q ${-bodyW * 0.56} ${hipY} 0 ${hipY + 0.04}
                Q ${bodyW * 0.56} ${hipY} ${bodyW * 0.5} ${shoulderY}
                Q 0 ${shoulderY - 0.3} ${-bodyW * 0.5} ${shoulderY} Z`}
            fill={accent} />
      {/* 头 */}
      {/* 头：r 必须是 1（局部单位），外层 scale(s) 才是头半径。
          写成 r={s} 会得到 s*s 的半径（本机 s=96 → 9216px，整屏被肤色填满）。*/}
      <circle cx={0} cy={headY} r={0.86} fill="#FFE2CC" />
      {/* 渔夫帽 */}
      <path d={`M ${-0.92} ${headY - 0.72} Q 0 ${headY - 1.62} ${0.92} ${headY - 0.72} Z`}
            fill="#F4F1E8" stroke="#D8D2C4" strokeWidth={0.03} />
      <ellipse cx={0} cy={headY - 0.7} rx={1.06} ry={0.17} fill="#FFFFFF" />
      <rect x={-0.92} y={headY - 0.8} width={1.84} height={0.11}
            fill="#E4E4E8" rx={0.06} />
      {/* 眼镜（圆框黑框，豆子花叔标志物） */}
      <circle cx={-eyeDX} cy={eyeY} r={eyeR * 1.75} fill="none" stroke="#1B1B1F" strokeWidth={0.055} />
      <circle cx={eyeDX} cy={eyeY} r={eyeR * 1.75} fill="none" stroke="#1B1B1F" strokeWidth={0.055} />
      <line x1={-eyeDX + eyeR * 1.75} y1={eyeY} x2={eyeDX - eyeR * 1.75} y2={eyeY}
            stroke="#1B1B1F" strokeWidth={0.05} />
      {/* 眼睛 */}
      {eyeOpen > 0.4 ? (
        <>
          <circle cx={-eyeDX} cy={eyeY} r={eyeR * Math.min(1.3, eyeOpen)} fill="#1B1B1F" />
          <circle cx={eyeDX} cy={eyeY} r={eyeR * Math.min(1.3, eyeOpen)} fill="#1B1B1F" />
        </>
      ) : (
        <>
          <path d={`M ${-eyeDX - eyeR} ${eyeY} Q ${-eyeDX} ${eyeY + 0.12} ${-eyeDX + eyeR} ${eyeY}`}
                fill="none" stroke="#1B1B1F" strokeWidth={0.06} strokeLinecap="round" />
          <path d={`M ${eyeDX - eyeR} ${eyeY} Q ${eyeDX} ${eyeY + 0.12} ${eyeDX + eyeR} ${eyeY}`}
                fill="none" stroke="#1B1B1F" strokeWidth={0.06} strokeLinecap="round" />
        </>
      )}
      {/* 嘴 */}
      <ellipse cx={0} cy={headY + 0.38} rx={0.21} ry={m.ry} fill={m.fill} />
      </g>
    </svg>
  );
};

// ---------- 背景（三个变体共用）----------
const Backdrop: React.FC<{ p: number; variant: Variant }> = ({ p, variant }) => (
  <>
    <AbsoluteFill
      style={{
        background: `radial-gradient(circle at 50% 38%, rgba(40,52,82,0.6) 0%, rgba(11,15,26,0) 60%),
                     radial-gradient(circle at 50% 118%, rgba(201,162,75,0.12) 0%, rgba(11,15,26,0) 52%)`,
      }}
    />
    <AbsoluteFill style={{ opacity: 0.045, mixBlendMode: "screen" }}>
      <div
        style={{
          position: "absolute",
          inset: -100,
          backgroundImage: "radial-gradient(rgba(255,255,255,0.9) 1px, transparent 1.4px)",
          backgroundSize: "26px 26px",
        }}
      />
    </AbsoluteFill>
    {/* 信号弹弹道弧线（launch 变体的视觉主体，其他变体弱化存在） */}
    <svg width={1920} height={1080} style={{ position: "absolute", inset: 0, opacity: variant === "launch" ? 0.9 : 0.35 }}>
      <defs>
        <linearGradient id="trailG" x1="0" y1="1" x2="1" y2="0">
          <stop offset="0%" stopColor="rgba(55,225,255,0)" />
          <stop offset="55%" stopColor="rgba(55,225,255,0.7)" />
          <stop offset="100%" stopColor="rgba(255,255,255,0.95)" />
        </linearGradient>
      </defs>
      <path
        d="M -100 1180 Q 700 1080 1180 420 Q 1420 60 1980 -40"
        fill="none"
        stroke="url(#trailG)"
        strokeWidth={variant === "launch" ? 5 : 2}
        strokeLinecap="round"
        strokeDasharray={variant === "launch" ? "0" : "14 12"}
        strokeDashoffset={-p * 40}
      />
    </svg>
    <AbsoluteFill style={{ boxShadow: "inset 0 0 340px 70px rgba(0,0,0,0.5)" }} />
  </>
);

// ---------- 标题卡（保留原版的纸质感，但从 3D 落定改为「升起」）----------
const TitleCard: React.FC<{
  title: string; date: string; weekday: string; p: number; riseFrom: number;
}> = ({ title, date, weekday, p, riseFrom }) => {
  const y = interpolate(p, [0, 1], [riseFrom, 0]);
  const op = interpolate(p, [0, 0.4, 1], [0, 0.9, 1]);
  const sc = interpolate(p, [0, 1], [0.94, 1]);
  return (
    <div
      style={{
        position: "absolute",
        left: "50%",
        // 落在画面 38% 高度处（人物占下半屏），而不是居中 —— 居中会把两人挡住
        top: "31%",
        width: "min(940px, 70%)",
        transform: `translate(-50%, calc(-50% + ${y}px)) scale(${sc})`,
        opacity: op,
        background: PAPER,
        borderRadius: 14,
        padding: "28px 44px 26px",
        boxShadow: "0 22px 56px rgba(0,0,0,0.6), 0 4px 12px rgba(0,0,0,0.4)",
        border: "1px solid rgba(255,255,255,0.6)",
        textAlign: "center",
      }}
    >
      <div
        style={{
          display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <svg width={28} height={28} viewBox="0 0 30 30">
            <defs>
              <linearGradient id="bm2" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#37E1FF" />
                <stop offset="100%" stopColor="#FF375F" />
              </linearGradient>
            </defs>
            <path d="M4 22 Q14 4 26 8" stroke="url(#bm2)" strokeWidth="3.4" fill="none" strokeLinecap="round" />
            <circle cx={26} cy={8} r={4.4} fill="#fff" stroke="url(#bm2)" strokeWidth="2.4" />
          </svg>
          <span style={{ fontSize: 21, fontWeight: 800, color: INK_TEXT, fontFamily: FONT, letterSpacing: 1 }}>
            信号弹 · Signal Pop
          </span>
        </div>
        <div
          style={{
            background: STAMP, color: "#fff", fontSize: 19, fontWeight: 800,
            padding: "5px 15px", borderRadius: 6, letterSpacing: 2,
            boxShadow: "0 4px 12px rgba(255,55,95,0.35)",
          }}
        >
          本周精选 · WEEKLY
        </div>
      </div>
      <div
        style={{
          fontSize: 64, fontWeight: 900, color: INK_TEXT, fontFamily: FONT,
          letterSpacing: 2, lineHeight: 1.14,
        }}
      >
        {title}
      </div>
      <div
        style={{
          height: 2, width: "58%", margin: "16px auto 12px auto",
          background: `linear-gradient(90deg, transparent, ${GOLD}, transparent)`,
        }}
      />
      <div
        style={{
          display: "flex", justifyContent: "space-between", alignItems: "center",
          paddingTop: 12, borderTop: `1px solid #E7E3D8`,
          fontSize: 18, fontWeight: 700, color: INK_TEXT, fontFamily: FONT,
        }}
      >
        <span>发布 {date} · {weekday}</span>
        <span style={{ fontSize: 17, fontWeight: 600, color: SUB_TEXT }}>MARK哥的创想引擎 · 出品</span>
      </div>
    </div>
  );
};

// ================================================================
export const OpeningAnimationV2: React.FC<{
  title: string;
  date: string;
  weekday: string;
  variant: Variant;
}> = ({ title, date, weekday, variant }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const t = frame / fps;

  const bgFade = interpolate(frame, [0, 14], [0, 1], { extrapolateRight: "clamp" });
  const fadeOut = interpolate(frame, [durationInFrames - 24, durationInFrames - 2], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic),
  });

  // 标题卡入场时刻：三个变体不同
  const titleStart = variant === "launch" ? 82 : variant === "duo" ? 96 : 74;
  const titleP = interpolate(frame, [titleStart, titleStart + 34], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic),
  });

  // 双主播站位与动作时间线
  const beanIn = interpolate(frame, [6, 30], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.back(1.5)),
  });

  // 各自的动作拍点：演一遍「打招呼 → 说话 → 击掌/指天」
  let aPose: BeanPose = "rest", bPose: BeanPose = "rest";
  let aExpr: BeanExpr = "happy", bExpr: BeanExpr = "happy";

  if (variant === "handshake") {
    if (frame >= 34) { aPose = "wave"; aExpr = "talk"; }
    if (frame >= 50) { bPose = "wave"; bExpr = "talk"; }
    if (frame >= 74) { aPose = "clap"; bPose = "clap"; aExpr = "happy"; bExpr = "happy"; }
  } else if (variant === "duo") {
    if (frame >= 30) { aPose = "nod"; aExpr = "talk"; }
    if (frame >= 42) { bPose = "talk"; bExpr = "talk"; }
    if (frame >= 96) { aPose = "clap"; bPose = "talk"; aExpr = "happy"; bExpr = "talk"; }
  } else {
    // launch：先举手欢呼，信号弹打出后一起指向上方
    if (frame >= 28) { aPose = "cheer"; aExpr = "shock"; }
    if (frame >= 40) { bPose = "cheer"; bExpr = "shock"; }
    if (frame >= 86) { aPose = "pointUp"; bPose = "pointUp"; aExpr = "happy"; bExpr = "happy"; }
  }

  // 口型：讲话时开合（12 次/秒的简化版 —— 用帧号取模做「一拍二」）
  const talking = (p: BeanPose) => p === "talk" || p === "nod" || p === "wave";
  const mouthA: 0 | 1 | 2 = talking(aPose)
    ? (((Math.floor(frame / 2.5) % 3) === 0 ? 2 : (((frame + 11) % 3) === 0 ? 1 : 0)) as 0 | 1 | 2)
    : aExpr === "shock" ? 2 : aExpr === "happy" ? 1 : 0;
  const mouthB: 0 | 1 | 2 = talking(bPose)
    ? (((Math.floor(frame / 2.5 + 1.7) % 3) === 0 ? 2 : (((frame + 19) % 3) === 0 ? 1 : 0)) as 0 | 1 | 2)
    : bExpr === "shock" ? 2 : bExpr === "happy" ? 1 : 0;

  //人物总高 ≈ 3.28×头半径（帽顶 -3.28 → 脚底 0，见 Bean 内部局部坐标）。
  // 要让两人占到画面高度 ~55%（1080×0.55/3.28 ≈ 180），原先 96 太小像挂件。
  const groundY = 1020;
  const leftX = variant === "launch" ? 470 : 560;
  const rightX = variant === "launch" ? 1450 : 1360;
  const s = variant === "duo" ? 142 : 160;

  const rise = (1 - beanIn) * 90;
  const breathe = Math.sin(t * 1.6) * 4;

  // launch 变体：信号弹本体沿弹道飞出
  const bulletP = interpolate(frame, [30, 86], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.in(Easing.cubic),
  });
  const bx = interpolate(bulletP, [0, 1], [-120, 2020]);
  const by = interpolate(bulletP, [0, 1], [1180, -60]);
  const bulletOn = variant === "launch" && frame >= 30 && frame <= 96;

  return (
    <AbsoluteFill style={{ backgroundColor: INK, opacity: bgFade * fadeOut }}>
      <Backdrop p={t} variant={variant} />

      {/* 信号弹（launch 变体） */}
      {bulletOn && (
        <div
          style={{
            position: "absolute", left: bx, top: by, width: 340, height: 15,
            transform: "translate(-50%,-50%) rotate(-42deg)", borderRadius: 999,
            background: "linear-gradient(90deg, rgba(55,225,255,0) 0%, rgba(55,225,255,0.85) 58%, #fff 100%)",
            boxShadow: "0 0 30px 8px rgba(55,225,255,0.55)", filter: "blur(1px)",
          }}
        />
      )}

      {/* 双主播。
          注意：Bean 内部用 `translate(x, y) scale(s)` 且 y 是「脚底在 1080 画布上的位置」，
          所以外层容器必须铺满整个画面（inset 0），再由 Bean 自己定位 ——
          不能用 bottom:0 + 零尺寸容器，那样内容会被挤到视口外（踩过一次，人物整个消失）。*/}
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        <Bean x={leftX} y={groundY + rise + breathe} s={s * (0.86 + beanIn * 0.14)}
              pose={aPose} expr={aExpr} mouth={mouthA} accent="#3B82F6" opacity={beanIn} />
        <Bean x={rightX} y={groundY + rise + breathe} s={s * (0.86 + beanIn * 0.14)}
              pose={bPose} expr={bExpr} mouth={mouthB} accent="#F472B6" flip opacity={beanIn} />
      </AbsoluteFill>

      {/* 标题卡（最后升起，盖住两人之间）*/}
      {titleP > 0.01 && (
        <TitleCard title={title} date={date} weekday={weekday} p={titleP} riseFrom={70} />
      )}

      {/* 顶部烫金细线 */}
      <AbsoluteFill style={{ opacity: 0.85, position: "absolute", top: 0, left: 0, right: 0, height: 6,
        background: `linear-gradient(90deg, transparent, ${GOLD}, transparent)` }} />
    </AbsoluteFill>
  );
};

export default OpeningAnimationV2;