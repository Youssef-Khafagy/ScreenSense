"use client";

interface Props { grid: number[][]; }

function cellStyle(pct: number): string {
  if (pct > 20) return "bg-red-500/80 text-white border-red-500/30";
  if (pct > 10) return "bg-orange-500/60 text-white border-orange-500/30";
  if (pct >  5) return "bg-yellow-500/40 text-yellow-100 border-yellow-500/30";
  if (pct >  2) return "bg-emerald-500/20 text-emerald-300 border-emerald-500/20";
  return "bg-zinc-800/60 text-zinc-600 border-zinc-700/30";
}

const LABELS = [
  ["Top-left", "Top",    "Top-right"],
  ["Left",     "Center", "Right"    ],
  ["Bot-left", "Bottom", "Bot-right"],
];

export default function AttentionGrid({ grid }: Props) {
  return (
    <div>
      <p className="text-[11px] font-semibold text-zinc-600 uppercase tracking-wider mb-3">
        Attention by region
      </p>
      <div className="grid grid-cols-3 gap-1">
        {grid.map((row, r) =>
          row.map((pct, c) => (
            <div
              key={`${r}-${c}`}
              className={`rounded-lg p-2.5 flex flex-col items-center text-center border transition-all duration-200 ${cellStyle(pct)}`}
            >
              <span className="text-[10px] leading-none opacity-70">{LABELS[r][c]}</span>
              <span className="text-sm font-bold mt-1">{pct.toFixed(1)}%</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
