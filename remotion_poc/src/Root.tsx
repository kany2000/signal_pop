import React from "react";
import { Composition } from "remotion";
import { NewsSlide } from "./NewsSlide";
import { WeeklyTalk } from "./WeeklyTalk";
import newsData from "./news.json";
import weeklySegs from "./weekly_segs.json";

const weeklyTotal = weeklySegs.reduce((s, x) => s + x.dur, 0);

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
    </>
  );
};
