import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      colors: {
        brand: {
          50:  "#eef2ff",
          100: "#e0e7ff",
          300: "#a5b4fc",
          400: "#818cf8",
          500: "#6366f1",
          600: "#4f46e5",
          700: "#4338ca",
          900: "#312e81",
        },
        violet: {
          400: "#a78bfa",
          500: "#8b5cf6",
          600: "#7c3aed",
        },
        zinc: {
          800: "#27272a",
          850: "#1f1f23",
          900: "#18181b",
          925: "#121215",
          950: "#09090b",
        },
      },
      animation: {
        "fade-in":       "fadeIn 0.5s ease-in-out",
        "fade-up":       "fadeUp 0.5s ease-out",
        "slide-up":      "slideUp 0.4s ease-out",
        "hotspot-in":    "hotspotIn 0.4s cubic-bezier(0.34,1.56,0.64,1) both",
        "pulse-slow":    "pulse 3s cubic-bezier(0.4,0,0.6,1) infinite",
        "gradient-x":   "gradientX 6s ease infinite",
        "shimmer":       "shimmer 2s linear infinite",
        "border-pulse":  "borderPulse 2s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          from: { opacity: "0" },
          to:   { opacity: "1" },
        },
        fadeUp: {
          from: { opacity: "0", transform: "translateY(16px)" },
          to:   { opacity: "1", transform: "translateY(0)" },
        },
        slideUp: {
          from: { transform: "translateY(24px)", opacity: "0" },
          to:   { transform: "translateY(0)",    opacity: "1" },
        },
        hotspotIn: {
          from: { transform: "scale(0) translateX(-50%) translateY(-50%)", opacity: "0" },
          to:   { transform: "scale(1) translateX(-50%) translateY(-50%)", opacity: "1" },
        },
        gradientX: {
          "0%, 100%": { backgroundPosition: "0% 50%" },
          "50%":      { backgroundPosition: "100% 50%" },
        },
        shimmer: {
          "0%":   { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition:  "200% 0" },
        },
        borderPulse: {
          "0%, 100%": { borderColor: "rgba(99,102,241,0.4)" },
          "50%":      { borderColor: "rgba(139,92,246,0.8)" },
        },
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "grid-pattern":
          "linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)",
      },
      backgroundSize: {
        "grid": "32px 32px",
      },
      boxShadow: {
        "glow":       "0 0 40px -8px rgba(99,102,241,0.5)",
        "glow-sm":    "0 0 20px -4px rgba(99,102,241,0.4)",
        "glow-violet":"0 0 40px -8px rgba(139,92,246,0.5)",
        "card":       "0 1px 3px rgba(0,0,0,0.4), 0 1px 2px -1px rgba(0,0,0,0.4)",
        "card-hover": "0 4px 24px rgba(0,0,0,0.5)",
      },
    },
  },
  plugins: [],
};
export default config;
