import { bundle } from "@remotion/bundler";
import { getCompositions, renderFrames, stitchFramesToVideo } from "@remotion/renderer";
import { mkdirSync } from "fs";

const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const ENTRY = "E:/projects/signal_pop/remotion_poc/src/index.ts";
const OUT = "E:/projects/signal_pop/remotion_poc/out";
const TMP = "C:/Users/ADMINI~1/AppData/Local/TEMP/remotion_frames";
const chromeFlags = ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", "--disable-software-rasterizer"];

console.log("Bundling...");
const serveUrl = await bundle({ entryPoint: ENTRY, onProgress: () => {} });
console.log("Bundle OK:", serveUrl);

const comps = await getCompositions({
  serveUrl,
  browserExecutable: CHROME,
  chromiumOptions: { chromeFlags },
  logLevel: "info",
});
console.log("Compositions:", comps.map((c) => c.id).join(", "));

const jobs = [
  {
    id: "OpeningAnimation",
    outputLocation: OUT + "/OpeningAnimation_preview.mp4",
    inputProps: { title: "AI语播·信号弹每周精选", date: "2026年9月26日", weekday: "星期六" },
  },
];

for (const job of jobs) {
  const comp = comps.find((c) => c.id === job.id);
  if (!comp) throw new Error("composition not found: " + job.id);
  const framesDir = TMP + "/" + job.id;
  mkdirSync(framesDir, { recursive: true });
  console.log(`\n=== renderFrames ${job.id} (${comp.durationInFrames} frames) ===`);
  const t0 = Date.now();
  const { frameCount, assetsInfo } = await renderFrames({
    serveUrl,
    composition: comp,
    inputProps: job.inputProps,
    browserExecutable: CHROME,
    chromiumOptions: { chromeFlags },
    imageFormat: "jpeg",
    outputDir: framesDir,
    overwrite: true,
    logLevel: "info",
    onProgress: ({ renderedFrames, totalFrames }) => {
      if (totalFrames) process.stdout.write(`\r${job.id} ${((renderedFrames / totalFrames) * 100).toFixed(1)}%`);
    },
  });
  console.log(`\n${job.id} frames rendered in ${((Date.now() - t0) / 1000).toFixed(1)}s (${frameCount} frames)`);
  console.log(`=== stitchFramesToVideo ${job.id} ===`);
  const t1 = Date.now();
  await stitchFramesToVideo({
    dir: framesDir,
    assetsInfo,
    outputLocation: job.outputLocation,
    codec: "h264",
    fps: comp.fps,
    width: comp.width,
    height: comp.height,
    overwrite: true,
    logLevel: "info",
  });
  console.log(`${job.id} stitched in ${((Date.now() - t1) / 1000).toFixed(1)}s -> ${job.outputLocation}`);
}
console.log("\nALL_DONE");
