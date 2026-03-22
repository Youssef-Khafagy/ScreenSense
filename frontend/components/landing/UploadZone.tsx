"use client";
import { useRef, useState, useCallback } from "react";

interface Props {
  onFile:    (file: File) => void;
  disabled?: boolean;
}

export default function UploadZone({ onFile, disabled }: Props) {
  const inputRef   = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const handleFile = useCallback((file: File | null | undefined) => {
    if (!file) return;
    const allowed = ["image/jpeg", "image/png", "image/webp"];
    if (!allowed.includes(file.type)) {
      alert("Please upload a JPEG, PNG, or WebP image.");
      return;
    }
    onFile(file);
  }, [onFile]);

  const onDrop      = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setDragging(false);
    handleFile(e.dataTransfer.files?.[0]);
  }, [handleFile]);
  const onDragOver  = (e: React.DragEvent) => { e.preventDefault(); setDragging(true);  };
  const onDragLeave = (e: React.DragEvent) => { e.preventDefault(); setDragging(false); };

  return (
    <div
      onClick={() => !disabled && inputRef.current?.click()}
      onDrop={onDrop}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      className={[
        "relative group cursor-pointer rounded-2xl border-2 transition-all duration-300 p-14 text-center overflow-hidden",
        dragging
          ? "border-brand-500 bg-brand-500/8 scale-[1.01]"
          : "border-brand-500/40 bg-brand-500/5 hover:border-brand-500/70 hover:bg-brand-500/8",
        disabled ? "opacity-50 cursor-not-allowed pointer-events-none" : "",
      ].join(" ")}
    >
      {/* Animated corner accents */}
      <span className="absolute top-3 left-3 w-4 h-4 border-t-2 border-l-2 border-brand-500/60 rounded-tl-lg" />
      <span className="absolute top-3 right-3 w-4 h-4 border-t-2 border-r-2 border-brand-500/60 rounded-tr-lg" />
      <span className="absolute bottom-3 left-3 w-4 h-4 border-b-2 border-l-2 border-brand-500/60 rounded-bl-lg" />
      <span className="absolute bottom-3 right-3 w-4 h-4 border-b-2 border-r-2 border-brand-500/60 rounded-br-lg" />

      {/* Glow */}
      <div className={`absolute inset-0 transition-opacity duration-300 pointer-events-none ${dragging ? "opacity-100" : "opacity-0 group-hover:opacity-100"}`}
        style={{ background: "radial-gradient(ellipse at center, rgba(99,102,241,0.06) 0%, transparent 70%)" }} />

      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        className="hidden"
        onChange={e => handleFile(e.target.files?.[0])}
      />

      <div className="relative flex flex-col items-center gap-5">
        {/* Upload icon */}
        <div className={[
          "w-16 h-16 rounded-2xl flex items-center justify-center transition-all duration-300",
          dragging ? "bg-brand-500/25 scale-110" : "bg-brand-500/15 group-hover:bg-brand-500/20 group-hover:scale-105",
        ].join(" ")}>
          {dragging ? (
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#818cf8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          ) : (
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#818cf8" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <circle cx="8.5" cy="8.5" r="1.5" />
              <polyline points="21 15 16 10 5 21" />
            </svg>
          )}
        </div>

        <div>
          <p className="text-lg font-semibold text-white mb-1.5">
            {dragging ? "Drop your image here" : "Drop an image to analyse"}
          </p>
          <p className="text-sm text-zinc-400">
            or{" "}
            <span className="text-brand-400 underline underline-offset-2">click to browse</span>
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs text-zinc-600">
          <span className="px-2 py-0.5 rounded border border-white/8 bg-white/3">JPEG</span>
          <span className="px-2 py-0.5 rounded border border-white/8 bg-white/3">PNG</span>
          <span className="px-2 py-0.5 rounded border border-white/8 bg-white/3">WebP</span>
          <span className="text-zinc-700">·</span>
          <span>max 10 MB</span>
        </div>
      </div>
    </div>
  );
}
