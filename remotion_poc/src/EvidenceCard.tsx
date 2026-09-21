import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Easing,
  Img,
} from "remotion";

export interface EvidenceCardProps {
  imageSrc: string;              // 核心截图/图表本地路径或静态资源
  title?: string;                // 卡片主标题（例如：可口可乐 2023 年股价与市盈率走势）
  source?: string;               // 来源标注（例如：财报披露 / 东方财富 2023）
  tag?: string;                  // 右上角印章标签（例如：核心证据 / 避坑指南）
  rotateDeg?: number;            // 微倾斜角度，默认 -1.5 度（模拟纸张随意平铺感）
  scale?: number;                // 整体缩放比例，默认 1.0
}

const easeOutCubic = Easing.out(Easing.cubic);

export const EvidenceCard: React.FC<EvidenceCardProps> = ({
  imageSrc,
  title,
  source = "事实依据",
  tag = "核心要点",
  rotateDeg = -1.5,
  scale = 1.0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  // 入场动画：前 18 帧从轻微缩放 + 偏移平滑归位
  const enterProgress = interpolate(frame, [0, 18], [0, 1], {
    extrapolateRight: "clamp",
    easing: easeOutCubic,
  });

  const cardScale = interpolate(enterProgress, [0, 1], [0.93 * scale, 1.0 * scale]);
  const cardOpacity = interpolate(enterProgress, [0, 1], [0, 1]);
  const cardTranslateY = interpolate(enterProgress, [0, 1], [30, 0]);

  // 微缓推镜头（Ken Burns），保持画面动态生命力
  const ambientScale = interpolate(t, [0, 15], [1.0, 1.025], {
    extrapolateRight: "clamp",
    easing: Easing.linear,
  });

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        width: "100%",
        height: "100%",
        opacity: cardOpacity,
        transform: `translateY(${cardTranslateY}px) scale(${cardScale * ambientScale}) rotate(${rotateDeg}deg)`,
        transformOrigin: "center center",
      }}
    >
      {/* 纸片卡片外框 */}
      <div
        style={{
          position: "relative",
          background: "#FFFFFF",
          padding: "14px 14px 20px 14px",
          borderRadius: "8px",
          boxShadow: "0 24px 60px rgba(0, 0, 0, 0.65), 0 4px 12px rgba(0, 0, 0, 0.4)",
          maxWidth: "82%",
          maxHeight: "82%",
          display: "flex",
          flexDirection: "column",
          border: "1px solid rgba(255, 255, 255, 0.4)",
        }}
      >
        {/* 顶部标签印章 */}
        {tag && (
          <div
            style={{
              position: "absolute",
              top: "-14px",
              right: "24px",
              background: "#FF375F",
              color: "#FFFFFF",
              fontSize: "18px",
              fontWeight: 800,
              padding: "4px 14px",
              borderRadius: "4px",
              boxShadow: "0 4px 12px rgba(255, 55, 95, 0.4)",
              letterSpacing: "1px",
            }}
          >
            {tag}
          </div>
        )}

        {/* 核心主图 */}
        <div
          style={{
            overflow: "hidden",
            borderRadius: "4px",
            background: "#0A0D14",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Img
            src={imageSrc}
            style={{
              width: "100%",
              height: "auto",
              maxHeight: "680px",
              objectFit: "contain",
              display: "block",
            }}
          />
        </div>

        {/* 底部信息栏（纸片手写/印刷质感说明） */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginTop: "12px",
            padding: "0 4px",
          }}
        >
          {title ? (
            <div
              style={{
                color: "#1E293B",
                fontSize: "22px",
                fontWeight: 700,
                letterSpacing: "0.5px",
                maxWidth: "70%",
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
              }}
            >
              {title}
            </div>
          ) : (
            <div />
          )}

          {source && (
            <div
              style={{
                color: "#64748B",
                fontSize: "16px",
                fontWeight: 600,
                letterSpacing: "0.5px",
              }}
            >
              来源：<span style={{ color: "#0F172A" }}>{source}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
