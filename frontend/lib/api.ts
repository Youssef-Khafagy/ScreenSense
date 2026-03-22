import type { PredictionResult } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function predictSaliency(file: File): Promise<PredictionResult> {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${API_BASE}/api/predict`, {
    method: "POST",
    body:   form,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail ?? `Request failed: ${res.status}`);
  }

  return res.json() as Promise<PredictionResult>;
}

export async function checkHealth(): Promise<{ status: string; model_loaded: boolean }> {
  const res = await fetch(`${API_BASE}/api/health`);
  return res.json();
}
