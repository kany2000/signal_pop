import React from "react";
import { Composition } from "remotion";
import { NewsSlide } from "./NewsSlide";
import { WeeklyTalk } from "./WeeklyTalk";
import { DailyNews, DailySeg } from "./DailyNews";
import { OpeningAnimation } from "./OpeningAnimation";
import { OpeningAnimationV2 } from "./OpeningAnimationV2";
import { OpeningAnimationV3 } from "./OpeningAnimationV3";
import { OpeningAnimationV4 } from "./OpeningAnimationV4";
import { OpeningAnimationV5 } from "./OpeningAnimationV5";
import newsData from "./news.json";
import weeklySegs from "./weekly_segs.json";
import dailySegs from "./daily_segs.json";
import dailyMeta from "./daily_meta.json";

const weeklyTotal = weeklySegs.reduce((s: number, x: { dur: number }) => s + x.dur, 0);
const dailyTotal = (dailySegs as DailySeg[]).reduce((s, x) => s + x.dur, 0);

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="NewsSlide"
        component={NewsSlide}
        durationInFrames={30 * 8}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ item: newsData[0] }}
      />
      <Composition
        id="WeeklyTalk"
        component={WeeklyTalk}
        durationInFrames={Math.round(weeklyTotal * 30)}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          segs: weeklySegs,
          pickUrl: (weeklySegs && weeklySegs[0] && weeklySegs[0].pickUrl) || "https://fmhy.net",
        }}
      />
      <Composition
        id="DailyNews"
        component={DailyNews}
        durationInFrames={Math.max(1, Math.round(dailyTotal * 30))}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          segs: dailySegs as DailySeg[],
          pubDate: dailyMeta.pubDate,
          weekday: dailyMeta.weekday,
          avatar: dailyMeta.avatar,
        }}
      />
      <Composition
        id="OpeningAnimation"
        component={OpeningAnimation}
        durationInFrames={270}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          title: "AI语播·信号弹每周精选",
          date: "2026年10月3日",
          weekday: "星期六",
        }}
      />
      {/* ★★★ v4「新闻联播式过场」= 周末版每期标配片头（2026-10-12 MARK哥定版）★★★
          零人物 / 零 Logo / 零印章 / 零卡片；宋体（Noto Serif SC＝播音楼字体）+
          深蓝夜空 + 地球弧线 + 横向光带 + 对称金线。
          配套：片头配乐 = output/mp3/Romeo - Winds of Hope 钢琴曲，
          切34s 起 9s，**淡入 1.2s / 淡出 1.0s（esin 曲线）**，
          时长与画面 bgFade(0→36帧) / fadeOut(240→269帧) 严格对齐。
          渲染脚本 tools/render_weekly_segmented.sh 已默认 OPENING_ID=OpeningV4。
          v5（纯字卡· 更克制）保留作备选，需要时OPENING_ID=OpeningV5 覆盖即可。 */}
      <Composition
        id="OpeningV4"
        component={OpeningAnimationV4}
        durationInFrames={270}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          title: "AI语播·信号弹每周精选",
          date: "2026年10月3日",
          weekday: "星期六",
        }}
      />
      {/* ===== v5 纯字卡版（备选，未启用）=====
          同为「新闻联播式过场」，但连地球/光带都不要，只剩宋体大字 + 上下金线，
          唯一动效是字距从26px 收到 8px。MARK哥最终选了 v4，这版留作对照。 */}
      <Composition
        id="OpeningV5"
        component={OpeningAnimationV5}
        durationInFrames={270}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          title: "AI语播·信号弹每周精选",
          date: "2026年10月3日",
          weekday: "星期六",
        }}
      />
      {/* ===== v3 真实头像版（2026-10-12 已否决：MARK哥要求「不要出现人物」）===== */}
      <Composition
        id="OpeningV3"
        component={OpeningAnimationV3}
        durationInFrames={270}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          title: "AI语播·信号弹每周精选",
          date: "2026年10月3日",
          weekday: "星期六",
        }}
      />
      {/* ===== v2 双主播登场版（2026-10-12 已否决，仅保留用于对照，不作默认）=====
          原版是「纸卡 3D 落定」的静物展示，没有人物；v2 让阿信与小蓝先活过来。
          三个变体先并行注册，实测看完再决定默认用哪个。 */}
      {(["handshake", "duo", "launch"] as const).map((v) => (
        <Composition
          key={v}
          id={`OpeningV2-${v}`}
          component={OpeningAnimationV2}
          durationInFrames={270}
          fps={30}
          width={1920}
          height={1080}
          defaultProps={{
            title: "AI语播·信号弹每周精选",
            date: "2026年10月3日",
            weekday: "星期六",
            variant: v,
          }}
        />
      ))}
    </>
  );
};
