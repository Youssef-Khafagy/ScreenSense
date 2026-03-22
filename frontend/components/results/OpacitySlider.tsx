"use client";

interface Props {
  value:    number;   // 0-100
  onChange: (v: number) => void;
}

export default function OpacitySlider({ value, onChange }: Props) {
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-slate-500 w-16">Original</span>
      <input
        type="range"
        min={0}
        max={100}
        value={value}
        onChange={e => onChange(Number(e.target.value))}
        className="flex-1 h-2 cursor-pointer accent-brand-500"
      />
      <span className="text-xs text-slate-500 w-12 text-right">Heatmap</span>
      <span className="text-xs font-mono text-slate-400 w-8 text-right">{value}%</span>
    </div>
  );
}
