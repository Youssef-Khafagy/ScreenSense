"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Footer         from "@/components/shared/Footer";
import ImageViewer    from "@/components/results/ImageViewer";
import AttentionPanel from "@/components/results/AttentionPanel";
import type { PredictionResult } from "@/lib/types";

export default function ResultsPage() {
  const router = useRouter();
  const [result,     setResult]     = useState<PredictionResult | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string>("");

  useEffect(() => {
    const raw     = sessionStorage.getItem("screensense_result");
    const preview = sessionStorage.getItem("screensense_preview");
    if (!raw || !preview) { router.replace("/"); return; }
    setResult(JSON.parse(raw) as PredictionResult);
    setPreviewUrl(preview);
  }, [router]);

  if (!result) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-zinc-950">
        <div className="relative w-10 h-10">
          <div className="absolute inset-0 rounded-full border-2 border-brand-500/20" />
          <div className="absolute inset-0 rounded-full border-2 border-brand-500 border-t-transparent animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-zinc-950">
      {/* Minimal top bar */}
      <div className="sticky top-0 z-50 border-b border-white/5 bg-zinc-950/80 backdrop-blur-xl">
        <div className="max-w-[1400px] mx-auto px-4 h-12 flex items-center justify-between">
          <Link href="/" className="text-xs font-semibold text-zinc-500 hover:text-white transition-colors flex items-center gap-1.5">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <path d="M19 12H5M12 5l-7 7 7 7" />
            </svg>
            Back
          </Link>
          <p className="text-xs text-zinc-600 font-medium uppercase tracking-widest">ScreenSense</p>
          <Link
            href="/"
            className="px-3 py-1.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-white text-xs font-semibold transition-all duration-150 shadow-glow-sm"
          >
            Analyse another
          </Link>
        </div>
      </div>

      <main className="flex-1 max-w-[1400px] mx-auto w-full px-4 py-5 animate-fade-up">
        {/* Meta line */}
        <p className="text-xs text-zinc-600 mb-4">
          {result.image_size.width} x {result.image_size.height}px · {result.processing_time_s.toFixed(2)}s inference · MobileNetV2 · SALICON
        </p>

        {/* Main layout */}
        <div className="grid lg:grid-cols-[1fr_370px] gap-4 items-start">
          <div className="rounded-2xl border border-white/8 bg-zinc-900/50 p-4">
            <ImageViewer result={result} previewUrl={previewUrl} />
          </div>
          <div className="lg:sticky lg:top-16 lg:max-h-[calc(100vh-5rem)] lg:overflow-y-auto rounded-2xl border border-white/8 bg-zinc-900/50 p-4">
            <AttentionPanel result={result} />
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
