import React from "react";
import { Composition } from "remotion";
import { NewsSlide } from "./NewsSlide";
import { WeeklyTalk } from "./WeeklyTalk";
import { DailyNews, DailySeg } from "./DailyNews";
import { OpeningAnimation } from "./OpeningAnimation";
import { EndingCard } from "./EndingCard";
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
        defaultProps={{ segs: weeklySegs }}
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
        durationInFrames={300}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          title: "AI语播·信号弹每周精选",
          date: "2026年9月9日",
          weekday: "星期三",
        }}
      />
      <Composition
        id="EndingCard"
        component={EndingCard}
        durationInFrames={120}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{}}
      />
    </>
  );
};
