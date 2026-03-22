"use client";
import type { PredictionResult } from "@/lib/types";

interface Props { result: PredictionResult; }
interface Tip   { icon: string; title: string; body: string; }

function generateTips(result: PredictionResult): Tip[] {
  const tips: Tip[] = [];
  const { scores, attention_grid, attention_regions, image_size } = result;
  const flat = attention_grid.flat();

  if (scores.attention_spread < 0.35) {
    tips.push({
      icon: "🎯", title: "Highly concentrated attention",
      body: `${(scores.peak_intensity * 100).toFixed(0)}% of focus clusters in one area. Consider distributing key information to ensure other elements aren't missed.`,
    });
  } else if (scores.attention_spread > 0.75) {
    tips.push({
      icon: "🌊", title: "Widely distributed attention",
      body: "Focus is spread broadly. If you have a primary CTA, consider making it more visually dominant to anchor user attention.",
    });
  }

  const cornerAvg = [flat[0], flat[2], flat[6], flat[8]].reduce((a, b) => a + b, 0) / 4;
  if (cornerAvg < 2) {
    tips.push({
      icon: "↔️", title: "Corners receive almost no attention",
      body: "Content in corners is likely to go unnoticed. Move critical elements · CTAs, logos, key messages · toward the center or top-center.",
    });
  }

  const bottomAvg = (flat[6] + flat[7] + flat[8]) / 3;
  if (bottomAvg < 5) {
    tips.push({
      icon: "⬆️", title: "Bottom of image is being ignored",
      body: `Bottom row captures only ${bottomAvg.toFixed(1)}% of attention. If your CTA or key text is there, consider moving it higher.`,
    });
  }

  if (attention_regions.length > 0) {
    const cx = attention_regions[0].x / image_size.width;
    if (cx > 0.7 || cx < 0.3) {
      tips.push({
        icon: "👁", title: "Primary focus is off-centre",
        body: `Highest attention is at ${scores.top_region}. Users gravitate toward centre first · make sure your main message is near the hotspot.`,
      });
    }
  }

  if (scores.peak_intensity > 0.90) {
    tips.push({
      icon: "⚡", title: "One element dominates completely",
      body: "Almost all focus is on one element · great if it's your hero message or CTA. Make sure it's your most important piece of content.",
    });
  }

  return tips.slice(0, 3);
}

export default function DesignTips({ result }: Props) {
  const tips = generateTips(result);
  if (tips.length === 0) return null;

  return (
    <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4">
      <p className="text-[11px] font-semibold text-amber-500/70 uppercase tracking-wider mb-3 flex items-center gap-1.5">
        <span>💡</span> Design insights
      </p>
      <div className="space-y-3">
        {tips.map((tip, i) => (
          <div key={i} className="flex gap-3">
            <span className="text-base flex-shrink-0 mt-0.5">{tip.icon}</span>
            <div>
              <p className="text-xs font-semibold text-amber-200">{tip.title}</p>
              <p className="text-xs text-amber-200/50 mt-0.5 leading-relaxed">{tip.body}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
