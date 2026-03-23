"use client";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Header        from "@/components/shared/Header";
import Footer        from "@/components/shared/Footer";
import Hero          from "@/components/landing/Hero";
import UploadZone    from "@/components/landing/UploadZone";
import ExampleImages from "@/components/landing/ExampleImages";
import HowItWorks    from "@/components/landing/HowItWorks";
import { useImageAnalysis } from "@/hooks/useImageAnalysis";
import { checkHealth } from "@/lib/api";

const METRICS = [
  { metric: "AUC-Judd", value: "0.9613", hint: "higher is better",
    plain:  "Can the model rank fixated pixels above non-fixated ones?",
    detail: "0.5 = random, 1.0 = perfect. 0.96 means the model almost always assigns higher saliency to pixels humans actually looked at." },
  { metric: "CC",        value: "0.8756", hint: "higher is better",
    plain:  "How closely does the predicted heatmap match the ground truth?",
    detail: "Pearson correlation: -1 = perfectly wrong, 0 = no relationship, 1 = perfect. 0.88 is a strong match." },
  { metric: "NSS",       value: "2.163",  hint: "higher is better",
    plain:  "How much above average is predicted saliency at fixation points?",
    detail: "Map normalised to mean 0, std 1. NSS is the average value at human fixation locations. 2.16 standard deviations above average is strong." },
  { metric: "SIM",       value: "0.7649", hint: "higher is better",
    plain:  "How much do the predicted and ground truth distributions overlap?",
    detail: "Histogram intersection: 0 = no overlap, 1 = identical. 0.76 means 76% of the probability mass is shared." },
  { metric: "KL-Div",    value: "0.2383", hint: "lower is better",
    plain:  "How different is the predicted distribution from the real one?",
    detail: "Lower is better. 0 = perfect. 0.24 is low, meaning the model closely matches where humans looked." },
];

type WakeStatus = "waking" | "ready" | "unknown";

export default function LandingPage() {
  const router = useRouter();
  const { state, analyse } = useImageAnalysis();
  const isLoading = state.status === "uploading" || state.status === "processing";
  const [wakeStatus, setWakeStatus] = useState<WakeStatus>("waking");

  useEffect(() => {
    let attempts = 0;
    const ping = async () => {
      try {
        await checkHealth();
        setWakeStatus("ready");
      } catch {
        attempts++;
        if (attempts < 10) setTimeout(ping, 4000);
        else setWakeStatus("unknown");
      }
    };
    ping();
  }, []);

  async function handleFile(file: File) {
    await analyse(file);
  }

  if (state.status === "done") {
    sessionStorage.setItem("screensense_result",  JSON.stringify(state.result));
    sessionStorage.setItem("screensense_preview", state.previewUrl);
    router.push("/results");
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 max-w-5xl mx-auto w-full px-4 py-4">
        <Hero />

        {/* Backend wake-up status */}
        {wakeStatus === "waking" && (
          <div className="mb-3 flex items-center gap-2.5 px-4 py-2.5 rounded-xl border border-amber-500/20 bg-amber-500/5 text-xs text-amber-400/80">
            <div className="w-3 h-3 rounded-full border border-amber-400/60 border-t-transparent animate-spin flex-shrink-0" />
            <span>Backend is waking up on HuggingFace Spaces — first request may take up to 30 seconds. Hang tight.</span>
          </div>
        )}
        {wakeStatus === "ready" && (
          <div className="mb-3 flex items-center gap-2.5 px-4 py-2.5 rounded-xl border border-emerald-500/20 bg-emerald-500/5 text-xs text-emerald-400/80">
            <span className="w-2 h-2 rounded-full bg-emerald-400 flex-shrink-0" />
            <span>Backend is ready.</span>
          </div>
        )}

        {/* Upload area */}
        <div className="mb-4">
          {isLoading ? (
            <div className="rounded-2xl border border-white/8 bg-white/3 p-14 flex flex-col items-center gap-4">
              <div className="relative w-12 h-12">
                <div className="absolute inset-0 rounded-full border-2 border-brand-500/20" />
                <div className="absolute inset-0 rounded-full border-2 border-brand-500 border-t-transparent animate-spin" />
              </div>
              <div className="text-center">
                <p className="font-medium text-white">
                  {state.status === "uploading" ? "Uploading image..." : "Analysing attention patterns..."}
                </p>
                <p className="text-sm text-zinc-500 mt-1">Usually takes 1-2 seconds</p>
              </div>
            </div>
          ) : (
            <UploadZone onFile={handleFile} />
          )}

          {state.status === "error" && (
            <p className="mt-3 text-center text-sm text-red-400">{state.message}</p>
          )}
        </div>

        {!isLoading && <ExampleImages onFile={handleFile} />}

        <HowItWorks />

        {/* About the model */}
        <section className="py-16 border-t border-white/5">
          <div className="text-center mb-10">
            <p className="text-xs font-semibold text-brand-400 uppercase tracking-widest mb-3">Model</p>
            <h2 className="text-3xl font-bold text-white mb-3">About the model</h2>
            <p className="text-zinc-400 text-sm max-w-xl mx-auto">
              Trained from scratch on{" "}
              <a href="https://salicon.net" target="_blank" rel="noopener noreferrer"
                className="text-brand-400 hover:text-brand-300 underline underline-offset-2 transition-colors">
                SALICON
              </a>
              {" "}· 10,000 natural images annotated with crowd-sourced human fixation maps.
            </p>
          </div>

          {/* Metrics table */}
          <div className="rounded-2xl border border-white/8 overflow-hidden mb-6">
            <div className="px-5 py-3 border-b border-white/5 bg-white/3">
              <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
                Evaluation · SALICON validation set (5,000 images)
              </p>
            </div>
            <div className="grid grid-cols-5 divide-x divide-white/5">
              {METRICS.map(({ metric, value, hint }) => (
                <div key={metric} className="flex flex-col items-center text-center px-3 py-5 bg-zinc-950 hover:bg-white/2 transition-colors duration-200">
                  <span className="text-xs text-zinc-500 font-medium">{metric}</span>
                  <span className="text-xl font-extrabold gradient-text tabular-nums mt-1">{value}</span>
                  <span className="text-[10px] text-zinc-700 mt-1">{hint}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Metric explanations */}
          <div className="rounded-2xl border border-white/8 overflow-hidden divide-y divide-white/5 mb-10">
            <div className="px-5 py-3 bg-white/3">
              <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">What do these metrics mean?</p>
            </div>
            {METRICS.map(({ metric, value, plain, detail }) => (
              <div key={metric} className="flex gap-4 px-5 py-4 bg-zinc-950 hover:bg-white/2 transition-colors duration-150">
                <div className="flex-shrink-0 w-24 text-right pt-0.5">
                  <p className="text-xs font-medium text-zinc-500">{metric}</p>
                  <p className="text-lg font-extrabold gradient-text tabular-nums">{value}</p>
                </div>
                <div className="border-l border-white/5 pl-4">
                  <p className="text-sm font-medium text-zinc-200">{plain}</p>
                  <p className="text-xs text-zinc-500 mt-1 leading-relaxed">{detail}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Model detail cards */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {[
              { title: "Architecture",
                desc:  "MobileNetV2 encoder with U-Net-style skip connections and an upsampling decoder. 6.6M parameters." },
              { title: "Training data",
                desc:  "SALICON: 10,000 train + 5,000 val images from MS COCO 2014 with crowd-sourced human fixation maps." },
              { title: "Loss function",
                desc:  "KL Divergence (1.0x) + Correlation Coefficient (0.5x) + BCE (0.1x). Standard saliency research formulation." },
              { title: "Training",
                desc:  "13 epochs on GTX 1650 (4 GB), ~113 min. Early stopping. Mixed precision (AMP). Encoder frozen for first 5 epochs." },
              { title: "Inference",
                desc:  "Under 500 ms on GPU, under 2 s on CPU. MobileNetV2 keeps it fast enough for real-time interactive use." },
              { title: "Output",
                desc:  "Single-channel saliency map in [0,1], post-processed into a jet-coloured heatmap with attention region analysis." },
            ].map(({ title, desc }) => (
              <div key={title}
                className="p-5 rounded-xl border border-white/8 bg-white/3 hover:border-brand-500/30 hover:bg-white/5 transition-all duration-200">
                <p className="font-semibold text-zinc-200 text-sm mb-2">{title}</p>
                <p className="text-xs text-zinc-500 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
