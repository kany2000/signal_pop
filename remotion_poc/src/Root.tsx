import React from "react";
import { Composition } from "remotion";
import { NewsSlide } from "./NewsSlide";
import { WeeklyTalk } from "./WeeklyTalk";
import { DailyNews, DailySeg } from "./DailyNews";
import newsData from "./news.json";
import weeklySegs from "./weekly_segs.json";
import dailySegs from "./daily_segs.json";

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
          pubDate: "2026年08月24日",
          weekday: "星期一",
          avatar: "avatar_daily_20260823.png",
        }}
      />
    </>
  );
};
