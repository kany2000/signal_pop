import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Easing,
  Img,
  Video,
  staticFile,
  Sequence,
} from "remotion";

export interface TalkStat {
  num: number;
  suffix?: string;
  label: string;
}

export interface TalkSegment {
  speaker: string;
  voice: string;
  text: string;
  dur: number;
  bg: string;
  video?: string;
  videoDur?: number;
  isBreaking?: boolean;
  isInteractive?: boolean;
  cta?: boolean;
  /** 本周之最数字卡（count-up 数据），仅挂在对应阿信段 */
  data?: TalkStat[];
  /** 下周看点日程行，仅挂在对应阿信段 */
  agenda?: string[];
}

const AXIN_BLUE = "#3A82D2";
const XIAOLAN_PINK = "#DC5A96";
const GOLD = "#D4AF37";
const WHITE = "#F5F5FA";
const GREY = "#BEC6D2";

const easeOut = Easing.out(Easing.cubic);

// ============ 章节转场卡（⑤对撞 + ①标题浮现） ============
// 按 bg 文件名自动推导章节：breaking/news_XX/summary/watch/interactive
const CHAPTER_META: Record<string, { title: string; en: string; color: string }> = {
  breaking: { title: "突发消息", en: "BREAKING NEWS", color: "#E23B3B" },
  news: { title: "本周要闻", en: "THIS WEEK", color: "#3A82D2" },
  summary: { title: "本周之最", en: "WEEK'S BEST", color: "#D4AF37" },
  watch: { title: "下周看点", en: "NEXT WEEK", color: "#2FA88C" },
  interactive: { title: "互动话题", en: "TOPIC TIME", color: "#DC5A96" },
};

const chapterKeyOf = (bg: string): string => {
  // news_01.jpg / news_12.jpg 等 → 去掉扩展名与尾部 _数字，归一到章节键
  const k = (bg || "").split(".")[0].replace(/[_-]?\d+$/, "");
  return CHAPTER_META[k] ? k : "";
};

// 标题逐字浮现逻辑已合并进 ChapterOverlay 徽章内部（按字错峰上浮+去模糊）

const ChapterOverlay: React.FC<{ meta: { title: string; en: string; color: string }; localT: number }> = ({
  meta,
  localT,
}) => {
  // 时间轴：双滑 0→0.55s；徽章 0.6→1.15s back-out；整卡 2.5→3.0s 淡出
  const slide = easeOut(Math.max(0, Math.min(1, localT / 0.55)));
  const slideR = easeOut(Math.max(0, Math.min(1, (localT - 0.08) / 0.55)));
  const fadeOut =
    localT < 2.5 ? 1 : Math.max(0, 1 - (localT - 2.5) / 0.5);
  const bx = Math.max(0, Math.min(1, (localT - 0.6) / 0.55));
  // easeOutBack
  const c1 = 1.70158;
  const c3 = c1 + 1;
  const badge =
    bx >= 1 ? 1 : 1 + c3 * Math.pow(bx - 1, 3) + c1 * Math.pow(bx - 1, 2);
  if (fadeOut <= 0) return null;
  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: fadeOut }}>
      {/* 左右双滑暗板 */}
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          bottom: 0,
          width: "50%",
          background: "linear-gradient(90deg, rgba(8,12,24,0.92), rgba(8,12,24,0.55))",
          transform: `translateX(${-100 * (1 - slide)}%)`,
        }}
      />
      <div
        style={{
          position: "absolute",
          right: 0,
          top: 0,
          bottom: 0,
          width: "50%",
          background: "linear-gradient(270deg, rgba(8,12,24,0.92), rgba(8,12,24,0.55))",
          transform: `translateX(${100 * (1 - slideR)}%)`,
        }}
      />
      {/* 中心徽章 + 英文副标 + 逐字标题 */}
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: 470,
          transform: `translate(-50%, -50%) scale(${badge})`,
          opacity: Math.min(1, badge),
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        <div
          style={{
            padding: "14px 52px",
            borderRadius: 999,
            fontSize: 58,
            fontWeight: "bold",
            color: "#fff",
            fontFamily: "Noto Sans SC, sans-serif",
            letterSpacing: 8,
            background: `linear-gradient(90deg, ${meta.color}, ${meta.color}bb)`,
            boxShadow: `0 0 60px ${meta.color}88`,
            display: "flex",
          }}
        >
          {[...meta.title].map((ch, i) => {
            // ① 逐字浮现：徽章文字按字错峰上浮+去模糊
            const start = 0.75 + i * 0.09;
            const x = Math.max(0, Math.min(1, (localT - start) / 0.45));
            const e = easeOut(x);
            return (
              <span
                key={i}
                style={{
                  opacity: e,
                  transform: `translateY(${20 * (1 - e)}px)`,
                  display: "inline-block",
                }}
              >
                {ch}
              </span>
            );
          })}
        </div>
        <div
          style={{
            marginTop: 16,
            fontSize: 22,
            letterSpacing: 6,
            color: meta.color,
            fontWeight: "bold",
            opacity: Math.max(0, Math.min(1, (localT - 1.0) / 0.4)),
          }}
        >
          {meta.en}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ============ 数字滚动卡（② 本周之最数据） ============
const StatRoll: React.FC<{ stats: TalkStat[]; localT: number; color: string }> = ({
  stats,
  localT,
  color,
}) => {
  const shown = stats.slice(0, 3);
  return (
    <div
      style={{
        position: "absolute",
        left: 560,
        top: 140,
        width: 800,
        padding: "26px 30px",
        borderRadius: 22,
        background: "rgba(14,20,34,0.88)",
        border: `2px solid ${color}66`,
        boxShadow: `0 14px 44px rgba(0,0,0,0.55), 0 0 26px ${color}44`,
        display: "flex",
        justifyContent: "center",
        gap: 46,
        opacity: easeOut(Math.max(0, Math.min(1, localT / 0.4))),
      }}
    >
      {shown.map((st, i) => {
        const start = 0.5 + i * 0.3;
        const x = Math.max(0, Math.min(1, (localT - start) / 0.6));
        const appear = easeOut(x);
        // 数字 count-up 1.2s easeOutCubic
        const cx = Math.max(0, Math.min(1, (localT - start) / 1.2));
        const eased = 1 - Math.pow(1 - cx, 3);
        const isInt = Number.isInteger(st.num);
        const val = st.num * eased;
        const numText = isInt
          ? Math.round(val).toLocaleString()
          : val.toFixed(1);
        // 长数字自动缩号，防止三列布局溢出
        const fullLen = (isInt
          ? Math.round(st.num).toLocaleString()
          : st.num.toFixed(1)
        ).length;
        const numFontSize = fullLen > 7 ? 40 : fullLen > 5 ? 52 : 68;
        return (
          <div
            key={i}
            style={{
              textAlign: "center",
              opacity: appear,
              transform: `translateY(${18 * (1 - appear)}px)`,
              minWidth: 180,
            }}
          >
            <div
              style={{
                fontSize: numFontSize,
                fontWeight: 800,
                fontFamily: "Consolas, monospace",
                fontVariantNumeric: "tabular-nums",
                color,
                textShadow: `0 0 24px ${color}66`,
                whiteSpace: "nowrap",
              }}
            >
              {numText}
              {st.suffix ? (
                <span style={{ fontSize: 34, marginLeft: 4 }}>{st.suffix}</span>
              ) : null}
            </div>
            <div style={{ marginTop: 6, fontSize: 22, color: GREY, fontFamily: "Noto Sans SC, sans-serif" }}>
              {st.label}
            </div>
          </div>
        );
      })}
    </div>
  );
};

// ============ 下周看点日程卡（③ 改造进度卡） ============
const AgendaCard: React.FC<{ items: string[]; localT: number; color: string }> = ({
  items,
  localT,
  color,
}) => {
  const shown = items.slice(0, 5);
  return (
    <div
      style={{
        position: "absolute",
        left: 560,
        top: 140,
        width: 800,
        padding: "24px 30px",
        borderRadius: 22,
        background: "rgba(14,20,34,0.88)",
        border: `2px solid ${color}66`,
        boxShadow: `0 14px 44px rgba(0,0,0,0.55), 0 0 26px ${color}44`,
        opacity: easeOut(Math.max(0, Math.min(1, localT / 0.4))),
      }}
    >
      {shown.map((it, i) => {
        const start = 0.6 + i * 0.45;
        const x = Math.max(0, Math.min(1, (localT - start) / 0.45));
        const e = easeOut(x);
        const label = it.length > 22 ? it.slice(0, 21) + "…" : it;
        return (
          <div
            key={i}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 14,
              padding: "10px 14px",
              marginBottom: 6,
              borderRadius: 12,
              background: i === 0 ? `${color}22` : "rgba(255,255,255,0.04)",
              opacity: e,
              transform: `translateX(${-24 * (1 - e)}px)`,
            }}
          >
            <div
              style={{
                width: 52,
                height: 52,
                borderRadius: 12,
                background: color,
                color: "#0d1220",
                fontSize: 26,
                fontWeight: 800,
                fontFamily: "Consolas, monospace",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
              }}
            >
              {String(i + 1).padStart(2, "0")}
            </div>
            <div style={{ fontSize: 27, color: WHITE, fontFamily: "Noto Sans SC, sans-serif", lineHeight: 1.35 }}>
              {label}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export const WeeklyTalk: React.FC<{ segs: TalkSegment[] }> = ({ segs }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  // 累计定位当前段
  let cur: TalkSegment | null = null;
  let segStart = 0;
  let segIndex = -1;
  let acc = 0;
  for (let i = 0; i < segs.length; i++) {
    const s = segs[i];
    if (t >= acc && t < acc + s.dur) {
      cur = s;
      segStart = acc;
      segIndex = i;
      break;
    }
    acc += s.dur;
  }
  if (!cur) return <AbsoluteFill style={{ backgroundColor: "#0d1220" }} />;

  const localT = t - segStart;

  // 章节检测：每个章节键（按 bg 推导）在 segs 中首次出现的段即章节开场
  const chapterStart: Record<string, number> = {};
  segs.forEach((s, i) => {
    const k = chapterKeyOf(s.bg);
    if (k && chapterStart[k] === undefined) chapterStart[k] = i;
  });
  const curChapterKey = chapterKeyOf(cur.bg);
  const isChapterStart =
    curChapterKey !== "" && chapterStart[curChapterKey] === segIndex;
  const curChapterMeta = curChapterKey ? CHAPTER_META[curChapterKey] : null;

  // 突发视频窗锚点：首个突发段绝对起点 + 素材时长（用于播一次 + 末尾淡出）
  let videoStart = -1;
  {
    let a = 0;
    for (const s of segs) {
      if (s.isBreaking && videoStart < 0) videoStart = a;
      a += s.dur;
    }
  }
  const videoSeg = segs.find((s) => s.video) || null;
  const videoDur = videoSeg && videoSeg.videoDur ? videoSeg.videoDur : 0;
  const videoRelFrame =
    videoStart >= 0 ? frame - Math.round(videoStart * fps) : 0;
  const videoLt = videoRelFrame / fps;
  const videoFade =
    videoSeg && videoStart >= 0 && videoDur > 0
      ? interpolate(
          videoLt,
          [videoDur, videoDur + 0.8],
          [1, 0],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
        )
      : 1;

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
  // 开场背景直接显示；其余段从 0.85 淡入，降低切换闪烁
  const bgFade =
    cur.bg === "opening_bg.jpg"
      ? 1
      : interpolate(localT, [0, 0.4], [0.85, 1], {
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

  // 三连动画检测：段文本含「一键三连」或最后 CTA 段 → 三连图标浮现后持续显示到视频结束
  const isSanlian = cur.cta || cur.text.includes("一键三连") || cur.text.includes("三连");
  const sanlianCx = [560, 960, 1360];
  const sanlianIcons = ["订阅", "关注", "转发"];
  // 图标从三连段开始 stagger 浮现（相对三连段起始时间，而非段内）
  const sanlianSegStart = (() => {
    let acc2 = 0;
    for (const s of segs) {
      if (s.cta || s.text.includes("一键三连") || s.text.includes("三连")) return acc2;
      acc2 += s.dur;
    }
    return Infinity;
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
      {/* 背景配图（随段轮换，淡入过渡；开场 bg 为空时渲染渐变底） */}
      <AbsoluteFill style={{ opacity: bgFade, transform: `scale(${bgScale})`, transformOrigin: "50% 40%" }}>
        {cur.bg ? (
          <Img src={staticFile(cur.bg)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        ) : (
          <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 35%, #1c2c4a 0%, #0d1220 70%)" }} />
        )}
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "rgba(8,12,24,0.62)" }} />

      {/* 顶部品牌条 */}
      <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 90, background: "linear-gradient(180deg, rgba(10,16,30,0.95), rgba(10,16,30,0))" }} />
      <div style={{ position: "absolute", top: 26, left: 0, right: 0, textAlign: "center", fontSize: 30, fontWeight: "bold", color: GOLD, fontFamily: "Noto Sans SC, sans-serif", letterSpacing: 2 }}>
        隔天信号弹 · 周末特别版
      </div>

      {/* 突发 / 互动话题 徽章（红色=突发，金色=互动话题，二者不同时出现） */}
      {(cur.isBreaking || cur.isInteractive) && (
        <div
          style={{
            position: "absolute",
            top: 100,
            left: 60,
            padding: "10px 28px",
            borderRadius: 999,
            fontSize: 30,
            fontWeight: "bold",
            color: "#fff",
            fontFamily: "Noto Sans SC, sans-serif",
            letterSpacing: 3,
            background: cur.isBreaking
              ? "linear-gradient(90deg,#E23B3B,#ff6b6b)"
              : "linear-gradient(90deg,#D4AF37,#f0c75e)",
            boxShadow: cur.isBreaking
              ? "0 0 26px rgba(226,59,59,0.65)"
              : "0 0 26px rgba(212,175,55,0.65)",
          }}
        >
          {cur.isBreaking ? "突 发" : "互动话题"}
        </div>
      )}

      {/* 突发消息现场视频窗（两主播中间偏上；锚定首个突发段起点播一次，末尾淡出消失；无文件不渲染） */}
      {videoSeg && videoStart >= 0 && videoDur > 0 && (
        <Sequence
          from={Math.round(videoStart * fps)}
          durationInFrames={Math.round((videoDur + 1.2) * fps)}
        >
          <AbsoluteFill style={{ opacity: videoFade, pointerEvents: "none" }}>
            <div
              style={{
                position: "absolute",
                left: 730,
                top: 120,
                width: 460,
                height: 259,
                borderRadius: 16,
                overflow: "hidden",
                border: "3px solid rgba(255,255,255,0.85)",
                boxShadow: "0 10px 34px rgba(0,0,0,0.6)",
                background: "#000",
              }}
            >
              <Video
                src={staticFile(videoSeg.video)}
                muted
                startFrom={0}
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
              />
            </div>
            <div
              style={{
                position: "absolute",
                left: 730,
                top: 80,
                fontSize: 22,
                fontWeight: "bold",
                color: "#fff",
                fontFamily: "Noto Sans SC, sans-serif",
                background: "rgba(226,59,59,0.92)",
                padding: "5px 16px",
                borderRadius: 8,
                letterSpacing: 1,
              }}
            >
              现场画面
            </div>
          </AbsoluteFill>
        </Sequence>
      )}

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

      {/* ② 本周之最数字滚动卡（仅挂 data 的阿信段） */}
      {cur.data && cur.data.length > 0 && (
        <StatRoll stats={cur.data} localT={localT} color={GOLD} />
      )}

      {/* ③ 下周看点日程卡（仅挂 agenda 的阿信段） */}
      {cur.agenda && cur.agenda.length > 0 && (
        <AgendaCard items={cur.agenda} localT={localT} color="#2FA88C" />
      )}

      {/* ⑤+① 章节转场卡（章节首段前 3 秒覆盖层，对撞滑入 + 徽章 + 逐字标题） */}
      {isChapterStart && curChapterMeta && (
        <ChapterOverlay meta={curChapterMeta} localT={localT} />
      )}
    </AbsoluteFill>
  );
};
