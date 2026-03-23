"use client";
import { useEffect, useRef } from "react";

export default function Particles() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const resize = () => {
      canvas.width  = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener("resize", resize);

    const COUNT = 150;
    const particles = Array.from({ length: COUNT }, () => ({
      x:       Math.random() * window.innerWidth,
      y:       Math.random() * window.innerHeight,
      r:       Math.random() * 1.2 + 0.3,
      speed:   Math.random() * 0.3 + 0.1,
      opacity: Math.random() * 0.55 + 0.15,
      drift:   (Math.random() - 0.5) * 0.3,
    }));

    let raf: number;
    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      for (const p of particles) {
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(139, 92, 246, ${p.opacity})`;
        ctx.fill();

        p.y      -= p.speed;
        p.x      += p.drift;
        p.opacity = Math.max(0, p.opacity - 0.0003);

        if (p.y < -5 || p.opacity <= 0) {
          p.x       = Math.random() * canvas.width;
          p.y       = canvas.height + 5;
          p.opacity = Math.random() * 0.55 + 0.15;
          p.speed   = Math.random() * 0.3 + 0.1;
          p.drift   = (Math.random() - 0.5) * 0.3;
        }
      }
      raf = requestAnimationFrame(draw);
    };
    draw();

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-0"
      aria-hidden
    />
  );
}
