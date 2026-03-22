"use client";
import { useState } from "react";

interface Props { onFile: (file: File) => void; }

const EXAMPLES = [
  { url: "https://picsum.photos/id/1018/800/600", thumb: "https://picsum.photos/id/1018/120/90", label: "Nature"       },
  { url: "https://picsum.photos/id/164/800/600",  thumb: "https://picsum.photos/id/164/120/90",  label: "Architecture" },
  { url: "https://picsum.photos/id/177/800/600",  thumb: "https://picsum.photos/id/177/120/90",  label: "Portrait"     },
  { url: "https://picsum.photos/id/29/800/600",   thumb: "https://picsum.photos/id/29/120/90",   label: "Landscape"    },
];

export default function ExampleImages({ onFile }: Props) {
  const [loading, setLoading] = useState<string | null>(null);
  const [error,   setError]   = useState<string | null>(null);

  async function loadExample(url: string, label: string) {
    setLoading(label);
    setError(null);
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      if (!blob.type.startsWith("image/")) throw new Error("Not an image");
      onFile(new File([blob], `${label.toLowerCase()}.jpg`, { type: blob.type }));
    } catch {
      setError(`Could not load ${label}. Check your internet connection.`);
    } finally {
      setLoading(null);
    }
  }

  return (
    <div className="mt-6">
      <p className="text-center text-xs text-zinc-600 mb-4 uppercase tracking-widest font-semibold">
        or try an example
      </p>
      <div className="flex flex-wrap justify-center gap-3">
        {EXAMPLES.map(ex => (
          <button
            key={ex.label}
            onClick={() => loadExample(ex.url, ex.label)}
            disabled={loading !== null}
            className={[
              "flex flex-col items-center gap-2 rounded-xl border p-2.5 w-28 transition-all duration-200",
              loading === ex.label
                ? "border-brand-500/50 bg-brand-500/10 cursor-wait"
                : "border-white/8 bg-white/3 hover:border-brand-500/30 hover:bg-white/5",
              loading !== null && loading !== ex.label ? "opacity-30" : "",
            ].join(" ")}
          >
            <div className="w-full h-16 rounded-lg overflow-hidden bg-zinc-800">
              {loading === ex.label ? (
                <div className="w-full h-full flex items-center justify-center">
                  <div className="w-4 h-4 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
                </div>
              ) : (
                <img src={ex.thumb} alt={ex.label} className="w-full h-full object-cover" draggable={false} />
              )}
            </div>
            <span className="text-xs text-zinc-400 font-medium">{ex.label}</span>
          </button>
        ))}
      </div>
      {error && <p className="mt-3 text-center text-xs text-red-400">{error}</p>}
    </div>
  );
}
