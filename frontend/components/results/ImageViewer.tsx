"use client";
import { useState } from "react";
import type { PredictionResult, ViewMode } from "@/lib/types";
import HeatmapOverlay from "./HeatmapOverlay";
import HotspotMarkers from "./HotspotMarkers";
import OpacitySlider  from "./OpacitySlider";

interface Props {
  result:     PredictionResult;
  previewUrl: string;
}

const MODES: { id: ViewMode; label: string }[] = [
  { id: "overlay",      label: "Overlay"      },
  { id: "original",     label: "Original"     },
  { id: "heatmap",      label: "Heatmap"      },
  { id: "side-by-side", label: "Side by Side" },
];

export default function ImageViewer({ result, previewUrl }: Props) {
  const [mode,         setMode]         = useState<ViewMode>("overlay");
  const [opacity,      setOpacity]      = useState(65);
  const [showHotspots, setShowHotspots] = useState(true);

  const { image_size, attention_regions, heatmap_base64, overlay_base64 } = result;

  function renderImage(m: ViewMode) {
    if (m === "original") return (
      <img src={previewUrl} alt="Original" className="w-full h-full object-contain animate-fade-in" />
    );
    if (m === "heatmap") return (
      <img src={`data:image/png;base64,${heatmap_base64}`} alt="Heatmap" className="w-full h-full object-contain animate-fade-in" />
    );
    return (
      <HeatmapOverlay
        originalSrc={previewUrl}
        heatmapBase64={heatmap_base64}
        overlayBase64={overlay_base64}
        opacity={opacity / 100}
      />
    );
  }

  return (
    <div className="space-y-3">
      {/* Controls */}
      <div className="flex items-center gap-2 flex-wrap">
        {/* Mode tabs */}
        <div className="flex rounded-xl overflow-hidden border border-white/8 bg-zinc-950/80">
          {MODES.map((m, idx) => (
            <button
              key={m.id}
              onClick={() => setMode(m.id)}
              className={[
                "px-3 py-1.5 text-xs font-medium transition-all duration-150",
                idx > 0 ? "border-l border-white/8" : "",
                mode === m.id
                  ? "bg-brand-500 text-white"
                  : "text-zinc-400 hover:text-white hover:bg-white/5",
              ].join(" ")}
            >
              {m.label}
            </button>
          ))}
        </div>

        {/* Hotspot toggle */}
        <button
          onClick={() => setShowHotspots(p => !p)}
          className={[
            "ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium border transition-all duration-150",
            showHotspots
              ? "border-brand-500/40 text-brand-400 bg-brand-500/10"
              : "border-white/8 text-zinc-500 hover:text-zinc-300 bg-transparent",
          ].join(" ")}
        >
          <span className={`w-1.5 h-1.5 rounded-full ${showHotspots ? "bg-brand-400" : "bg-zinc-600"}`} />
          Hotspots
        </button>
      </div>

      {/* Image */}
      {mode === "side-by-side" ? (
        <div className="grid grid-cols-2 gap-2">
          {[
            { src: previewUrl,                              label: "Original", isBase64: false },
            { src: `data:image/png;base64,${heatmap_base64}`, label: "Heatmap",  isBase64: true  },
          ].map(({ src, label }) => (
            <div key={label} className="rounded-xl overflow-hidden bg-black flex flex-col">
              <div className="flex-1 min-h-48 flex items-center justify-center">
                <img src={src} alt={label} className="w-full h-full object-contain animate-fade-in" />
              </div>
              <p className="text-center text-xs text-zinc-600 py-1.5">{label}</p>
            </div>
          ))}
        </div>
      ) : (
        <div className="relative rounded-xl overflow-hidden bg-black min-h-56 flex items-center justify-center">
          {renderImage(mode)}
          {showHotspots && mode !== "original" && (
            <div className="absolute inset-0 pointer-events-none">
              <HotspotMarkers
                regions={attention_regions}
                imageWidth={image_size.width}
                imageHeight={image_size.height}
              />
            </div>
          )}
        </div>
      )}

      {/* Opacity slider */}
      {mode === "overlay" && (
        <div className="rounded-xl border border-white/8 bg-zinc-950/80 p-3">
          <OpacitySlider value={opacity} onChange={setOpacity} />
        </div>
      )}

      {/* Colour legend */}
      {(mode === "overlay" || mode === "heatmap") && (
        <div className="flex items-center gap-3 px-1">
          <span className="text-[11px] text-zinc-600">Low attention</span>
          <div className="flex-1 h-2 rounded-full shadow-inner" style={{
            background: "linear-gradient(to right, #00007f, #0000ff, #00ffff, #00ff00, #ffff00, #ff7f00, #ff0000)"
          }} />
          <span className="text-[11px] text-zinc-600">High attention</span>
        </div>
      )}
    </div>
  );
}
