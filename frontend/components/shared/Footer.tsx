export default function Footer() {
  return (
    <footer className="mt-20 border-t border-white/5 py-10">
      <div className="max-w-5xl mx-auto px-4 text-center">
        <div className="flex items-center justify-center gap-2 mb-3">
          <div className="w-5 h-5 rounded-md bg-gradient-to-br from-brand-500 to-violet-500 flex items-center justify-center">
            <svg width="10" height="10" viewBox="0 0 14 14" fill="none">
              <ellipse cx="7" cy="7" rx="3" ry="5" stroke="white" strokeWidth="1.5" />
              <circle cx="7" cy="7" r="1.5" fill="white" />
              <line x1="1" y1="7" x2="13" y2="7" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </div>
          <span className="text-sm font-semibold text-zinc-400">ScreenSense</span>
        </div>
        <p className="text-sm text-zinc-600">
          Trained on{" "}
          <a href="https://salicon.net" target="_blank" rel="noopener noreferrer"
            className="text-zinc-500 hover:text-zinc-300 underline underline-offset-2 transition-colors">
            SALICON
          </a>
          {" "}· 10,000 images with crowd-sourced human fixation annotations
        </p>
        <p className="text-xs text-zinc-700 mt-2">
          MobileNetV2 · PyTorch · FastAPI · Next.js
          {" · "}AUC-Judd 0.961 · CC 0.876 · NSS 2.163
        </p>
      </div>
    </footer>
  );
}
