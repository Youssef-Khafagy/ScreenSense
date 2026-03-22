"use client";
import { useEffect, useRef } from "react";

interface Props {
  originalSrc:    string;
  heatmapBase64:  string;
  overlayBase64:  string;
  opacity:        number;   // 0-1
  showHeatmapOnly?: boolean;
}

/**
 * Canvas-based heatmap renderer.
 * Blends the original image with the heatmap using the given opacity.
 */
export default function HeatmapOverlay({
  originalSrc,
  heatmapBase64,
  overlayBase64,
  opacity,
  showHeatmapOnly,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const origImg    = new Image();
    const heatmapImg = new Image();

    origImg.src    = originalSrc;
    heatmapImg.src = `data:image/png;base64,${heatmapBase64}`;

    let loaded = 0;
    const onLoad = () => {
      loaded++;
      if (loaded < 2) return;

      canvas.width  = origImg.naturalWidth  || origImg.width;
      canvas.height = origImg.naturalHeight || origImg.height;

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      if (showHeatmapOnly) {
        ctx.drawImage(heatmapImg, 0, 0, canvas.width, canvas.height);
        return;
      }

      // Draw original image
      if (opacity < 1) {
        ctx.globalAlpha = 1;
        ctx.drawImage(origImg, 0, 0, canvas.width, canvas.height);
      }

      // Blend heatmap on top
      if (opacity > 0) {
        ctx.globalAlpha = opacity;
        ctx.drawImage(heatmapImg, 0, 0, canvas.width, canvas.height);
      }

      ctx.globalAlpha = 1;
    };

    origImg.onload    = onLoad;
    heatmapImg.onload = onLoad;
  }, [originalSrc, heatmapBase64, opacity, showHeatmapOnly]);

  return (
    <canvas
      ref={canvasRef}
      className="w-full h-full object-contain rounded-lg heatmap-canvas animate-fade-in"
    />
  );
}
