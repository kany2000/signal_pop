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

// ===== 数据契约（由 tools/export_daily_remotion.py 导出）=====
export interface DailySeg {
  type: "intro" | "history" | "news" | "outro";
  num: number;      // 新闻编号（0=历史；1..10=新闻）
  section: string;  // 分类
  title: string;    // 标题
  body: string;     // 正文
  image: string;    // public/ 下的配图文件名（staticFile 引用）
  dur: number;      // 时长（秒，来自 tts_segments.json）
}

const GOLD = "#FFD700";
const WHITE = "#F0F5F0";
const LIGHT_GREY = "#C8D2C8";
const PANEL_W = 384;
const BG = "#10151c";

const easeOut = Easing.out(Easing.cubic);
// easeOutBack：轻微回弹（Celebration 风格 overshoot ~10%），用于「播报日期」盖章动画
const easeOutBack = (x: number) => {
  const c1 = 1.70158;
  const c3 = c1 + 1;
  return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2);
};

// ---------- 左上品牌条 ----------
const BrandBar: React.FC<{ text: string }> = ({ text }) => (
  <>
    <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 90, background: "linear-gradient(180deg, rgba(10,16,30,0.95), rgba(10,16,30,0))" }} />
    <div style={{ position: "absolute", top: 26, left: 0, right: 0, textAlign: "center", fontSize: 30, fontWeight: "bold", color: GOLD, fontFamily: "Noto Sans SC, sans-serif", letterSpacing: 2 }}>
      {text}
    </div>
  </>
);

// ---------- 右下角主播头像角标（遮 Sensenova 水印位，直径150px @ (1750,970)）----------
export const AvatarCorner: React.FC<{ avatar?: string }> = ({ avatar }) => {
  if (!avatar) return null;
  const frame = useCurrentFrame();
  const fade = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp", easing: easeOut });
  return (
    <AbsoluteFill style={{ opacity: fade }}>
      <div
        style={{
          position: "absolute",
          left: 1750 - 75,
          top: 970 - 75,
          width: 150,
          height: 150,
          borderRadius: "50%",
          background: "rgba(0,0,0,0.45)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Img src={staticFile(avatar)} style={{ width: 132, height: 132, borderRadius: "50%", objectFit: "cover", border: "3px solid rgba(255,255,255,0.9)" }} />
      </div>
    </AbsoluteFill>
  );
};

// ---------- 开场段 ----------
const IntroSlide: React.FC<{ seg: DailySeg; pubDate: string; weekday: string; total: number; avatar?: string }> = ({ seg, pubDate, weekday, total, avatar }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const ken = interpolate(t, [0, seg.dur], [1.0, 1.08], { extrapolateRight: "clamp", easing: easeOut });
  const titleIn = interpolate(frame, [6, 30], [0, 1], { extrapolateRight: "clamp", easing: easeOut });
  const subIn = interpolate(frame, [24, 50], [0, 1], { extrapolateRight: "clamp", easing: easeOut });
  const lineIn = interpolate(frame, [44, 74], [0, 1], { extrapolateRight: "clamp", easing: easeOut });

  return (
    <AbsoluteFill style={{ backgroundColor: BG }}>
      <AbsoluteFill style={{ transform: `scale(${ken})`, transformOrigin: "50% 45%" }}>
        <Img src={staticFile(seg.image)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "rgba(8,12,22,0.62)" }} />
      <BrandBar text="隔天信号弹 · 每周新闻" />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div style={{ width: 520, height: 5, background: GOLD, marginBottom: 30, opacity: lineIn }} />
        <div style={{ fontSize: 86, fontWeight: "bold", color: GOLD, fontFamily: "Noto Sans SC, sans-serif", letterSpacing: 6, opacity: titleIn, transform: `translateY(${(1 - titleIn) * 30}px)` }}>
          隔天信号弹
        </div>
        <div style={{ marginTop: 24, fontSize: 40, fontWeight: "bold", color: WHITE, fontFamily: "Noto Sans SC, sans-serif", opacity: subIn, transform: `translateY(${(1 - subIn) * 24}px)` }}>
          {pubDate} · {weekday}
        </div>
        {/* 新排期徽标：已调整为每周三播出 */}
        <div style={{ marginTop: 16, fontFamily: "Noto Sans SC, sans-serif", opacity: subIn, transform: `translateY(${(1 - subIn) * 18}px)` }}>
          <span style={{ padding: "8px 22px", background: "rgba(255,215,0,0.15)", border: `1px solid ${GOLD}`, borderRadius: 999, fontSize: 22, color: GOLD, letterSpacing: 1 }}>
            已调整为 · 每周三准时更新
          </span>
        </div>
        <div style={{ marginTop: 16, fontSize: 26, color: LIGHT_GREY, fontFamily: "Noto Sans SC, sans-serif", opacity: subIn }}>
          本期精选 {total} 条核心新闻
        </div>
        <div style={{ width: 520, height: 5, background: GOLD, marginTop: 34, opacity: lineIn }} />
      </AbsoluteFill>
      <AvatarCorner avatar={avatar} />
    </AbsoluteFill>
  );
};

// ---------- 历史上的今天 ----------
const HistorySlide: React.FC<{ seg: DailySeg; avatar?: string }> = ({ seg, avatar }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const ken = interpolate(t, [0, 8], [1.0, 1.06], { extrapolateRight: "clamp", easing: easeOut });
  const titleIn = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp", easing: easeOut });
  const bodyIn = interpolate(frame, [16, 42], [0, 1], { extrapolateRight: "clamp", easing: easeOut });

  return (
    <AbsoluteFill style={{ backgroundColor: BG }}>
      <AbsoluteFill style={{ transform: `scale(${ken})`, transformOrigin: "60% 40%" }}>
        <Img src={staticFile(seg.image)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </AbsoluteFill>
      {/* 左侧暗化面板 */}
      <AbsoluteFill style={{ width: PANEL_W, background: "rgba(10,14,22,0.85)", backdropFilter: "blur(10px)", boxShadow: "0 0 40px rgba(0,0,0,0.6)" }} />
      <AbsoluteFill style={{ left: PANEL_W - 60, width: 120, background: "linear-gradient(90deg, rgba(10,14,22,0.85) 0%, rgba(10,14,22,0) 100%)" }} />
      <AbsoluteFill style={{ left: 0, width: PANEL_W }}>
        <div style={{ position: "absolute", top: 60, left: 40, right: 40, height: 6, background: GOLD }} />
        <div style={{ position: "absolute", top: 190, left: 0, right: 0, textAlign: "center", fontSize: 52, fontWeight: "bold", color: GOLD, fontFamily: "Noto Sans SC, sans-serif", opacity: titleIn }}>
          历史上的今天
        </div>
        <div style={{ position: "absolute", top: 262, left: 152, right: 152, height: 5, background: GOLD, opacity: titleIn }} />
        <div style={{ position: "absolute", bottom: 40, left: 0, right: 0, textAlign: "center", fontSize: 20, color: "#DCEBDC", fontFamily: "Noto Sans SC, sans-serif" }}>
          隔天信号弹
        </div>
      </AbsoluteFill>
      {/* 右侧正文 */}
      <div style={{ position: "absolute", left: 460, right: 60, top: 110, fontSize: 42, color: LIGHT_GREY, fontFamily: "Noto Sans SC, sans-serif", textShadow: "2px 2px 0 #000", opacity: bodyIn, transform: `translateY(${(1 - bodyIn) * 20}px)`, lineHeight: 1.6 }}>
        {seg.body}
      </div>
      <AvatarCorner avatar={avatar} />
    </AbsoluteFill>
  );
};

// ---------- 新闻动效分屏（stagger + ken-burns + 标题滑入）----------
const NewsSlide: React.FC<{ seg: DailySeg; avatar?: string }> = ({ seg, avatar }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  const kenScale = interpolate(t, [0, 8], [1.0, 1.08], { extrapolateRight: "clamp", easing: easeOut });
  const numIn = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: "clamp", easing: easeOut });
  const catIn = interpolate(frame, [6, 21], [0, 1], { extrapolateRight: "clamp", easing: easeOut });
  const numScale = interpolate(numIn, [0, 1], [1.4, 1]);
  const catScale = interpolate(catIn, [0, 1], [0.6, 1]);
  const titleIn = interpolate(frame, [12, 34], [0, 1], { extrapolateRight: "clamp", easing: easeOut });
  const bodyIn = interpolate(frame, [30, 52], [0, 1], { extrapolateRight: "clamp", easing: easeOut });

  return (
    <AbsoluteFill style={{ backgroundColor: BG }}>
      <AbsoluteFill style={{ transform: `scale(${kenScale})`, transformOrigin: "70% 50%" }}>
        <Img src={staticFile(seg.image)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </AbsoluteFill>
      <AbsoluteFill style={{ width: PANEL_W, background: "rgba(10,14,22,0.82)", backdropFilter: "blur(10px)", boxShadow: "0 0 40px rgba(0,0,0,0.6)" }} />
      <AbsoluteFill style={{ left: PANEL_W - 60, width: 120, background: "linear-gradient(90deg, rgba(10,14,22,0.82) 0%, rgba(10,14,22,0) 100%)" }} />
      <AbsoluteFill style={{ left: 0, width: PANEL_W }}>
        <div style={{ position: "absolute", top: 60, left: 40, right: 40, height: 6, background: GOLD }} />
        <div style={{ position: "absolute", top: 200, left: 0, right: 0, textAlign: "center", opacity: numIn, transform: `scale(${numScale})`, fontSize: 150, fontWeight: "bold", color: GOLD, lineHeight: 1, fontFamily: "Noto Sans SC, sans-serif" }}>
          {String(seg.num).padStart(2, "0")}
        </div>
        <div style={{ position: "absolute", top: 360, left: 152, right: 152, height: 6, background: GOLD }} />
        <div style={{ position: "absolute", top: 400, left: 0, right: 0, display: "flex", justifyContent: "center", opacity: catIn, transform: `scale(${catScale})` }}>
          <div style={{ padding: "8px 20px", background: "rgba(255,215,0,0.15)", border: `1px solid ${GOLD}`, borderRadius: 8, fontSize: 34, color: WHITE, fontFamily: "Noto Sans SC, sans-serif" }}>
            {seg.section}
          </div>
        </div>
        <div style={{ position: "absolute", bottom: 40, left: 0, right: 0, textAlign: "center", fontSize: 20, color: "#DCEBDC", fontFamily: "Noto Sans SC, sans-serif" }}>
          隔天信号弹
        </div>
      </AbsoluteFill>
      <Sequence from={0}>
        <div style={{ position: "absolute", left: 460, right: 50, top: 90, fontSize: 46, fontWeight: "bold", color: WHITE, fontFamily: "Noto Sans SC, sans-serif", textShadow: "3px 3px 0 #000, -3px 3px 0 #000, 3px -3px 0 #000, -3px -3px 0 #000", opacity: titleIn, transform: `translateY(${(1 - titleIn) * 40}px)`, lineHeight: 1.4 }}>
          {seg.title}
        </div>
        <div style={{ position: "absolute", left: 460, right: 50, top: 290, fontSize: 36, color: LIGHT_GREY, fontFamily: "Noto Sans SC, sans-serif", textShadow: "2px 2px 0 #000", opacity: bodyIn, transform: `translateY(${(1 - bodyIn) * 24}px)`, lineHeight: 1.55 }}>
          {seg.body}
        </div>
      </Sequence>
      <AvatarCorner avatar={avatar} />
    </AbsoluteFill>
  );
};

// ---------- 结尾三连段（金钮 stagger 浮现 + 呼吸光晕，持续到片尾）----------
const OutroSlide: React.FC<{ seg: DailySeg; pubDate: string; weekday: string; avatar?: string }> = ({ seg, pubDate, weekday, avatar }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  const ken = interpolate(t, [0, seg.dur], [1.0, 1.05], { extrapolateRight: "clamp", easing: easeOut });
  const titleIn = interpolate(frame, [0, 18], [0, 1], { extrapolateRight: "clamp", easing: easeOut });

  // 「播报日期」盖章动画：三连之后（约 1.2s 起）回弹放大 + 金色光晕脉冲，持续到片尾
  const dsProg = interpolate(t, [1.2, 1.95], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const dsScale = 0.6 + 0.4 * easeOutBack(dsProg);
  const dsAlpha = interpolate(t, [1.2, 1.6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const dsGlow = 0.45 + 0.55 * (0.5 + 0.5 * Math.sin((t - 1.6) * Math.PI * 1.1));

  const sanlianCx = [560, 960, 1360];
  const sanlianIcons = ["订阅", "关注", "转发"];
  const in3 = (k: number) => {
    const start = 0.4 + k * 0.35;
    const end = start + 0.8;
    if (t < start) return 0;
    if (t > end) return 1;
    const x = (t - start) / (end - start);
    const c1 = 1.70158;
    const c3 = c1 + 1;
    return Math.max(0, Math.min(1.1, 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2)));
  };

  return (
    <AbsoluteFill style={{ backgroundColor: BG }}>
      <AbsoluteFill style={{ transform: `scale(${ken})`, transformOrigin: "50% 50%" }}>
        <Img src={staticFile(seg.image)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "rgba(8,12,22,0.72)" }} />
      <BrandBar text="隔天信号弹 · 每周新闻" />
      <div style={{ position: "absolute", top: 300, left: 0, right: 0, textAlign: "center", fontSize: 52, fontWeight: "bold", color: GOLD, fontFamily: "Noto Sans SC, sans-serif", opacity: titleIn, transform: `translateY(${(1 - titleIn) * 24}px)` }}>
        喜欢本期内容？一键三连支持我们！
      </div>
      <AbsoluteFill style={{ top: 380 }}>
        {sanlianIcons.map((label, k) => {
          const g = in3(k);
          return (
            <div key={label} style={{ position: "absolute", left: sanlianCx[k] - 100, top: 60, width: 200, height: 200, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", opacity: g, transform: `scale(${0.8 + g * 0.2})` }}>
              <div style={{ width: 120, height: 120, borderRadius: "50%", background: "rgba(20,26,36,0.92)", border: `3px solid ${GOLD}`, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: g > 0.5 ? `0 0 ${30 + 22 * (0.5 + 0.5 * Math.sin((t - 1.4) * Math.PI * 1.1))}px ${GOLD}88` : "none", fontSize: 44, color: "#FFF0BE", fontWeight: "bold" }}>
                {label === "订阅" ? "▶" : label === "关注" ? "★" : "↗"}
              </div>
              <div style={{ marginTop: 10, fontSize: 26, fontWeight: "bold", color: "#FFF", fontFamily: "Noto Sans SC, sans-serif" }}>{label}</div>
            </div>
          );
        })}
      </AbsoluteFill>
      <div style={{ position: "absolute", bottom: 120, left: 0, right: 0, textAlign: "center", fontSize: 30, color: WHITE, fontFamily: "Noto Sans SC, sans-serif", opacity: titleIn }}>
        互动话题：您最关注哪条新闻？欢迎在评论区留言讨论！
      </div>
      <div style={{ position: "absolute", bottom: 70, left: 0, right: 0, textAlign: "center", fontSize: 26, color: LIGHT_GREY, fontFamily: "Noto Sans SC, sans-serif", opacity: titleIn }}>
        感谢您的关注，我们下期见~
      </div>
      {/* 播报日期盖章动画（本节目已调整为每周三播出） */}
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", opacity: dsAlpha, pointerEvents: "none" }}>
        <div style={{ position: "absolute", top: 690, left: 0, right: 0, textAlign: "center", transform: `scale(${dsScale})` }}>
          <div style={{ fontSize: 28, color: GOLD, fontFamily: "Noto Sans SC, sans-serif", letterSpacing: 2 }}>
            本期播出 · 每周三准时更新
          </div>
          <div
            style={{
              marginTop: 8,
              fontSize: 48,
              fontWeight: "bold",
              color: WHITE,
              fontFamily: "Noto Sans SC, sans-serif",
              textShadow: `0 0 ${18 + 22 * Math.max(0, dsGlow)}px ${GOLD}`,
            }}
          >
            {pubDate} · {weekday}
          </div>
        </div>
      </AbsoluteFill>
      <AvatarCorner avatar={avatar} />
    </AbsoluteFill>
  );
};

// ===== 主组件：按段累计定位渲染 =====
export const DailyNews: React.FC<{
  segs: DailySeg[];
  pubDate: string;
  weekday: string;
  avatar?: string;
}> = ({ segs, pubDate, weekday, avatar }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  let cur: DailySeg | null = null;
  let acc = 0;
  for (const s of segs) {
    if (t >= acc && t < acc + s.dur) {
      cur = s;
      break;
    }
    acc += s.dur;
  }
  if (!cur) return <AbsoluteFill style={{ backgroundColor: BG }} />;

  switch (cur.type) {
    case "intro":
      return <IntroSlide seg={cur} pubDate={pubDate} weekday={weekday} total={segs.filter((s) => s.type === "news").length} avatar={avatar} />;
    case "history":
      return <HistorySlide seg={cur} avatar={avatar} />;
    case "outro":
      return <OutroSlide seg={cur} pubDate={pubDate} weekday={weekday} avatar={avatar} />;
    default:
      return <NewsSlide seg={cur} avatar={avatar} />;
  }
};
