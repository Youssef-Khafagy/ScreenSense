import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "ScreenSense · AI Visual Attention Predictor",
  description:
    "Upload any image and see where human eyes will look first. Powered by a custom-trained CNN trained on the SALICON dataset.",
  openGraph: {
    title: "ScreenSense",
    description: "AI-powered visual attention prediction",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen bg-[#09090b] text-white antialiased font-sans selection:bg-violet-500/30">
        {children}
      </body>
    </html>
  );
}
