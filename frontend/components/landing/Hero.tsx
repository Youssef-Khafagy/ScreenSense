export default function Hero() {
  return (
    <div className="relative text-center py-20 px-4 overflow-hidden">
      {/* Background grid */}
      <div
        className="absolute inset-0 opacity-40"
        style={{
          backgroundImage:
            "linear-gradient(rgba(99,102,241,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(99,102,241,0.08) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="w-[600px] h-[300px] rounded-full blur-3xl"
          style={{ background: "radial-gradient(ellipse, rgba(139,92,246,0.08) 0%, transparent 70%)" }} />
      </div>

      <div className="relative">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/10 bg-white/5 text-xs text-zinc-400 font-medium mb-6 animate-fade-up">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          Custom-trained CNN · SALICON dataset · 6.6M parameters
        </div>

        {/* Heading */}
        <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight leading-none mb-6 animate-fade-up-1">
          <span className="text-white">See what your users </span>
          <br />
          <span className="gradient-text">see before they do</span>
        </h1>

        <p className="text-lg text-zinc-400 max-w-xl mx-auto leading-relaxed animate-fade-up-2">
          Upload any image and get an instant AI-generated heatmap showing where
          human eyes will look first, powered by a CNN trained on 10,000 images
          with real human fixation data.
        </p>
      </div>
    </div>
  );
}
