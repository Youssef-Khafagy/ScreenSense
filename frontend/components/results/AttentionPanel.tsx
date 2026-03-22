"use client";
import type { PredictionResult } from "@/lib/types";
import AttentionGrid from "./AttentionGrid";
import DesignTips    from "./DesignTips";

interface Props { result: PredictionResult; }

function SpreadBar({ value }: { value: number }) {
  const pct   = Math.round(value * 100);
  const label = pct < 35 ? "Focused" : pct > 65 ? "Distributed" : "Balanced";
  const color = pct < 35
    ? "from-blue-500 to-blue-400"
    : pct > 65
    ? "from-violet-500 to-purple-400"
    : "from-emerald-500 to-teal-400";

  return (
    <div>
      <div className="flex justify-between text-xs mb-2">
        <span className="text-zinc-600">Focused</span>
        <span className="font-semibold text-zinc-300">{label} · {pct}%</span>
        <span className="text-zinc-600">Distributed</span>
      </div>
      <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full bg-gradient-to-r ${color} transition-all duration-1000`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="text-[11px] text-zinc-600 mt-2 leading-snug">
        Entropy-based: 0% = all focus on one pixel · 100% = perfectly uniform
      </p>
    </div>
  );
}

const HOTSPOT = [
  { badge: "bg-red-500",    bar: "from-red-500 to-red-400",       border: "border-red-500/20",    bg: "bg-red-500/5"    },
  { badge: "bg-orange-500", bar: "from-orange-500 to-orange-400", border: "border-orange-500/20", bg: "bg-orange-500/5" },
  { badge: "bg-yellow-500", bar: "from-yellow-500 to-yellow-400", border: "border-yellow-500/20", bg: "bg-yellow-500/5" },
];

export default function AttentionPanel({ result }: Props) {
  const { scores, attention_regions, processing_time_s } = result;

  return (
    <div className="space-y-3 text-sm">

      {/* Score cards */}
      <div className="grid grid-cols-2 gap-2">
        <div className="rounded-xl border border-white/8 bg-zinc-950/80 p-4">
          <p className="text-[11px] font-semibold text-zinc-600 uppercase tracking-wider mb-2">Primary focus</p>
          <p className="font-bold text-white text-base capitalize">
            {scores.top_region.replace(/-/g, " ")}
          </p>
        </div>
        <div className="rounded-xl border border-white/8 bg-zinc-950/80 p-4">
          <p className="text-[11px] font-semibold text-zinc-600 uppercase tracking-wider mb-2">Peak intensity</p>
          <p className="font-bold text-white text-base">
            {(scores.peak_intensity * 100).toFixed(0)}%
          </p>
        </div>
      </div>

      {/* Spread */}
      <div className="rounded-xl border border-white/8 bg-zinc-950/80 p-4">
        <p className="text-[11px] font-semibold text-zinc-600 uppercase tracking-wider mb-3">
          Attention spread
        </p>
        <SpreadBar value={scores.attention_spread} />
      </div>

      {/* Hotspots */}
      <div className="rounded-xl border border-white/8 bg-zinc-950/80 p-4">
        <p className="text-[11px] font-semibold text-zinc-600 uppercase tracking-wider mb-3">
          Top attention zones
        </p>
        <div className="space-y-2">
          {attention_regions.map((r, i) => {
            const s = HOTSPOT[i] ?? HOTSPOT[2];
            return (
              <div
                key={i}
                className={`flex items-center gap-3 rounded-lg p-3 border ${s.border} ${s.bg}`}
                style={{ animationDelay: `${i * 100}ms` }}
              >
                <span className={`w-6 h-6 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold text-white ${s.badge}`}>
                  {i + 1}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline justify-between gap-2 mb-1.5">
                    <p className="text-xs font-semibold text-zinc-300 truncate">{r.label}</p>
                    <p className="text-sm font-bold text-white flex-shrink-0">
                      {(r.intensity * 100).toFixed(0)}%
                    </p>
                  </div>
                  <div className="h-1 bg-zinc-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full bg-gradient-to-r ${s.bar} transition-all duration-700`}
                      style={{ width: `${r.intensity * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3×3 grid */}
      <div className="rounded-xl border border-white/8 bg-zinc-950/80 p-4">
        <AttentionGrid grid={result.attention_grid} />
      </div>

      {/* Design tips */}
      <DesignTips result={result} />

      {/* Meta */}
      <div className="flex items-center justify-between px-1 text-[11px] text-zinc-700">
        <span>Processed in {processing_time_s.toFixed(2)}s</span>
        <span>MobileNetV2 · SALICON</span>
      </div>
    </div>
  );
}
