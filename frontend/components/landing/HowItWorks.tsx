const steps = [
  {
    number: "01",
    title:  "Upload",
    desc:   "Drop any image · website screenshot, ad, poster, or UI design. JPEG, PNG, or WebP up to 10 MB.",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
        <polyline points="17 8 12 3 7 8" />
        <line x1="12" y1="3" x2="12" y2="15" />
      </svg>
    ),
  },
  {
    number: "02",
    title:  "AI Analysis",
    desc:   "A MobileNetV2 encoder-decoder CNN · trained on 10,000 images with human fixation data · predicts where people look.",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2a10 10 0 1010 10" />
        <path d="M12 6v6l4 2" />
        <circle cx="18" cy="6" r="3" fill="currentColor" fillOpacity="0.2" />
        <path d="M15.5 4.5l5 3-5 3" />
      </svg>
    ),
  },
  {
    number: "03",
    title:  "Attention Map",
    desc:   "Get a heatmap showing primary, secondary, and tertiary focus zones plus rule-based UX insights.",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="3" />
        <path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83" />
      </svg>
    ),
  },
];

export default function HowItWorks() {
  return (
    <section className="py-20">
      <div className="text-center mb-12">
        <p className="text-xs font-semibold text-brand-400 uppercase tracking-widest mb-3">Process</p>
        <h2 className="text-3xl font-bold text-white">How it works</h2>
      </div>

      <div className="grid md:grid-cols-3 gap-4">
        {steps.map((s, i) => (
          <div
            key={i}
            className="relative rounded-2xl border border-white/8 bg-white/3 p-6 hover:border-brand-500/30 hover:bg-white/5 transition-all duration-300 group"
          >
            {/* Connector arrow (desktop) */}
            {i < 2 && (
              <div className="hidden md:block absolute -right-2 top-1/2 -translate-y-1/2 z-10">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M6 3l5 5-5 5" stroke="#3f3f46" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
            )}

            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-400 group-hover:bg-brand-500/20 transition-colors duration-300">
                {s.icon}
              </div>
              <div>
                <p className="text-[11px] font-bold text-zinc-600 uppercase tracking-widest mb-1">{s.number}</p>
                <h3 className="font-semibold text-white mb-2">{s.title}</h3>
                <p className="text-sm text-zinc-400 leading-relaxed">{s.desc}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
