"use client";
import type { AttentionRegion } from "@/lib/types";

interface Props {
  regions:     AttentionRegion[];
  imageWidth:  number;
  imageHeight: number;
}

const COLORS = ["#ef4444", "#f97316", "#eab308"];
const DELAYS = ["0ms", "300ms", "600ms"];

export default function HotspotMarkers({ regions, imageWidth, imageHeight }: Props) {
  return (
    <>
      {regions.map((r, i) => {
        const left = `${(r.x / imageWidth)  * 100}%`;
        const top  = `${(r.y / imageHeight) * 100}%`;

        return (
          <div
            key={i}
            style={{
              left,
              top,
              animationDelay: DELAYS[i] ?? "0ms",
              borderColor:    COLORS[i] ?? "#6366f1",
            }}
            className="absolute -translate-x-1/2 -translate-y-1/2 animate-hotspot-in"
          >
            {/* Pulsing ring */}
            <span
              className="absolute inset-0 rounded-full opacity-30 animate-ping"
              style={{ backgroundColor: COLORS[i] ?? "#6366f1" }}
            />
            {/* Number badge */}
            <span
              className="relative flex items-center justify-center w-7 h-7 rounded-full text-white text-xs font-bold shadow-lg border-2"
              style={{ backgroundColor: COLORS[i] ?? "#6366f1", borderColor: "white" }}
              title={`${r.label}: ${(r.intensity * 100).toFixed(0)}% intensity`}
            >
              {i + 1}
            </span>
          </div>
        );
      })}
    </>
  );
}
